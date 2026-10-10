"""Cadence adapter and read-only audits; explicit dependencies, no import IO."""
from contextlib import closing, contextmanager
import copy
import hashlib
import json
import os
import re
import sqlite3
import time

from scripts.missing_link_checkpoint_cadence import CheckpointCadence, FilePin, PinnedFiles
from scripts.missing_link_repository_only_evaluator import require, verify_prefix


class Checks:
    """Meter each actual callback once, including callbacks in forced barriers.

    The reader attaches its stream timer only during the returned-response phase.
    Cadence overhead remains active time; callback work is excluded from active
    time but always counts toward the 600-second observed wall limit.
    """
    def __init__(self, *, fast, critical, history, clock=time.monotonic):
        self.timing = None
        self.failure = None
        def measured(kind, callback):
            def invoke():
                if self.timing is None:
                    callback()
                else:
                    self.timing.checkpoint(kind, callback)
            return invoke
        self.controller = CheckpointCadence(fast=measured('light', fast),
            critical=measured('full', critical), history=measured('full', history), clock=clock)

    @contextmanager
    def stream(self, timing):
        require(self.timing is None, 'Overlapping stream timing')
        self.timing = timing
        try:
            yield
        finally:
            self.timing = None

    def abort(self, error):
        if self.failure is None:
            self.failure = error

    def _perform(self, callback):
        if self.failure is not None:
            raise self.failure
        try:
            return callback()
        except BaseException as exc:
            self.abort(exc)
            raise

    def start(self): self._perform(self.controller.start)
    def poll(self): self._perform(self.controller.poll)
    def barrier(self): self._perform(self.controller.barrier)
    def finish(self): self._perform(self.controller.finish)

    def snapshot(self):
        value = self.controller.snapshot()
        if self.failure is not None:
            value['state'] = 'failed'
        return value

    def write(self, callback):
        def operation():
            self.barrier()
            result = callback()
            self.barrier()
            return result
        return self._perform(operation)


def held_leases(leases):
    for lease in leases:
        require(lease.file is not None and not lease.file.closed and lease.path.is_file(),
                'Held lease disappeared')
        held, path = os.fstat(lease.file.fileno()), lease.path.stat()
        require((held.st_dev, held.st_ino) == (path.st_dev, path.st_ino), 'Held lease replaced')


def database_snapshot(path, allowance):
    """Same canonical table digest as the frozen audit, one read-only transaction.

    Encode one row at a time, preserving json.dumps(fetchall()) separators and
    ordering exactly. Memory is bounded by one row instead of the entire DB.
    """
    with closing(sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)) as db:
        db.execute('BEGIN')
        tables = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'ml_%'")]
        require(all(re.fullmatch(r'ml_[A-Za-z0-9_]+', name) for name in tables), 'Invalid audit table')
        hashes = {}
        for table in tables:
            digest = hashlib.sha256(b'[')
            separator = b''
            for row in db.execute(f'SELECT * FROM "{table}" ORDER BY rowid'):
                digest.update(separator)
                digest.update(json.dumps(row, sort_keys=True, ensure_ascii=False).encode())
                separator = b', '
            digest.update(b']')
            hashes[table] = digest.hexdigest()
        rows = [list(r) for r in db.execute('SELECT * FROM ml_ai_reservations ORDER BY id')]
        allowances = [list(r) for r in db.execute('SELECT * FROM ml_ai_allowances ORDER BY id')]
        active = []
        for row in db.execute('SELECT payload FROM ml_jobs'):
            job = json.loads(row[0])
            if job['status'] in {'queued', 'running'}:
                active.append(job['id'])
        count, cost = db.execute('SELECT COUNT(*),SUM(cost) FROM ml_ai_reservations WHERE allowance_id=?',
                                 (allowance,)).fetchone()
    return {'tables': hashes, 'artifacts': {}, 'reservations': count, 'reserved_usd': cost,
            'reservation_rows': rows, 'allowance_rows': allowances, 'active_jobs': active}


class HistoryAudit:
    """Compiled content pins plus exact DB prefix and independently supplied Git gate.

    No recursive manifest rebuilding during polls. Inventories are compiled from
    previously verified seals; directories are enumerated anew on every audit.
    """
    def __init__(self, *, root, database, baseline, allowance, ceiling, rows, tree, inventories,
                 measure=lambda name, callback: callback()):
        self.database, self.allowance, self.ceiling = database, allowance, ceiling
        self.rows, self.tree = rows, tree
        self.measure = measure
        self.before = copy.deepcopy(baseline)
        self.files = PinnedFiles(FilePin(root/name, value) for name, value in baseline['artifacts'].items())
        self.inventories = tuple((path, frozenset(names)) for path, names in inventories)
        self.last = None

    def __call__(self):
        self.measure('git', self.tree)
        def inventories():
            for folder, expected in self.inventories:
                entries = list(folder.iterdir())
                require(all(p.is_file() and not p.is_symlink() for p in entries)
                        and {p.name for p in entries} == expected,
                        'Protected inventory changed')
        self.measure('inventories', inventories)
        self.measure('historical_files', self.files.verify)
        after = self.measure('original_database', lambda: database_snapshot(self.database, self.allowance))
        # The real hashes have just been checked; do not hash all paths twice.
        after['artifacts'] = dict(self.before['artifacts'])
        verify_prefix(self.before, after, self.rows(), allowance=self.allowance, ceiling=self.ceiling)
        self.measure('git', self.tree)
        self.last = after
