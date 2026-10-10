"""Read-only logical audit with optional complete SQLite-image reuse.

Every reuse hashes a new serialization inside a fresh read transaction. No
mtime/stat/data_version shortcut, persistent cache, raw database file handle,
write, connection lifetime cache, or import-time IO belongs to this module.
"""
from contextlib import closing, contextmanager
import hashlib
import json
import re
import sqlite3
from threading import Lock

from scripts.missing_link_repository_only_evaluator import EvaluationStopped, require


@contextmanager
def _transaction(path):
    require(path.is_file() and not path.is_symlink(), 'Invalid audit database path')
    initial = path.stat()
    with closing(sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)) as db:
        db.execute('BEGIN')
        # BEGIN alone does not acquire a read snapshot/lock. Complete a SELECT
        # before serializing, also when a cache hit avoids the logical queries.
        db.execute('SELECT COUNT(*) FROM sqlite_master').fetchall()
        yield db
    # Closing releases SQLite's read lock and can itself replace the path. Check
    # only after cleanup succeeds, before any caller can return or cache a result.
    final = path.stat()
    require(not path.is_symlink() and (initial.st_dev, initial.st_ino) == (final.st_dev, final.st_ino),
            'Audit database path changed')


def _logical_snapshot(db, allowance):
    """Byte-exact predecessor json.dumps(fetchall()) table hashes, row by row."""
    tables = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'ml_%'")]
    require(all(re.fullmatch(r'ml_[A-Za-z0-9_]+', name) for name in tables), 'Invalid audit table')
    hashes = {}
    for table in tables:
        digest, separator = hashlib.sha256(b'['), b''
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


def database_snapshot(path, allowance):
    with _transaction(path) as db:
        return _logical_snapshot(db, allowance)


class ContentVerifiedSnapshot:
    """Single bound database/allowance, one private logical result, fail-stop.

    SHA-256 covers every byte of SQLite's current transaction image, including
    WAL-backed pages. A hit returns a fresh copy of a previously computed exact
    logical snapshot; the caller still compares its independent baseline/prefix.
    Python 3.10 or an oversized image uses the full logical audit every time.
    The image is transient; the cache retains only a digest and logical JSON.
    """
    def __init__(self, path, allowance, *, max_image_bytes=512*1024*1024):
        require(type(max_image_bytes) is int and max_image_bytes >= 0, 'Invalid audit image bound')
        require(type(allowance) is str and allowance, 'Invalid audit allowance binding')
        self._path, self._allowance, self._max_image_bytes = path, allowance, max_image_bytes
        self._key, self._value, self._failure = None, None, None
        self._lock = Lock()
        self._counts = dict(audits=0, image_reads=0, logical_scans=0, cache_hits=0, fallback_scans=0)

    def snapshot(self):
        return dict(self._counts)

    def __call__(self):
        if self._failure is not None:
            raise self._failure
        if not self._lock.acquire(blocking=False):
            if self._failure is None:
                self._failure = EvaluationStopped('Overlapping database audit')
            raise self._failure
        try:
            self._counts['audits'] += 1
            with _transaction(self._path) as db:
                serialize = getattr(db, 'serialize', None)
                pages = db.execute('PRAGMA page_count').fetchone()[0]
                page_size = db.execute('PRAGMA page_size').fetchone()[0]
                eligible = callable(serialize) and pages*page_size <= self._max_image_bytes
                key = None
                if eligible:
                    image = serialize()
                    require(type(image) is bytes and len(image) == pages*page_size,
                            'Invalid serialized audit image')
                    key = hashlib.sha256(image).digest()
                    del image
                    self._counts['image_reads'] += 1
                if key is not None and key == self._key:
                    self._counts['cache_hits'] += 1
                    value = self._value
                else:
                    self._counts['logical_scans'] += 1
                    if not eligible:
                        self._counts['fallback_scans'] += 1
                    value = json.dumps(_logical_snapshot(db, self._allowance), ensure_ascii=False).encode()
            # Path checks and transaction/connection cleanup must succeed before
            # any refreshed cache becomes usable or any result is returned.
            if self._failure is not None:
                raise self._failure
            self._key, self._value = key, value
            return json.loads(value)
        except BaseException as exc:
            if self._failure is None:
                self._failure = exc
            raise self._failure
        finally:
            self._lock.release()
