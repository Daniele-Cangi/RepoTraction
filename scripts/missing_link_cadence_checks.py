"""Cadence adapter and read-only audits; explicit dependencies, no import IO."""
from contextlib import contextmanager
import copy
import os
import time

from scripts.missing_link_checkpoint_cadence import CheckpointCadence, FilePin, PinnedFiles
from scripts.missing_link_database_audit import database_snapshot
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


class HistoryAudit:
    """Compiled content pins plus exact DB prefix and independently supplied Git gate.

    No recursive manifest rebuilding during polls. Inventories are compiled from
    previously verified seals; directories are enumerated anew on every audit.
    """
    def __init__(self, *, root, database, baseline, allowance, ceiling, rows, tree, inventories,
                 measure=lambda name, callback: callback(), database_audit=None):
        self.database, self.allowance, self.ceiling = database, allowance, ceiling
        self.rows, self.tree = rows, tree
        self.measure = measure
        self.database_audit = database_audit or (lambda: database_snapshot(self.database, self.allowance))
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
        after = self.measure('original_database', self.database_audit)
        # The real hashes have just been checked; do not hash all paths twice.
        after['artifacts'] = dict(self.before['artifacts'])
        verify_prefix(self.before, after, self.rows(), allowance=self.allowance, ceiling=self.ceiling)
        self.measure('git', self.tree)
        self.last = after
