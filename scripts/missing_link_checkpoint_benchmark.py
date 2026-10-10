"""Fixed offline checkpoint workload; synthetic temporary files/SQLite only.

Run with --filesystem for measured IO. No original state, credentials, provider,
CLI identity or network is read. Results measure this component, not a live run.
"""
import argparse
from contextlib import closing
import hashlib
import io
import json
import os
from pathlib import Path
import sqlite3
import statistics
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from missing_link.lease import WorkerLease
from scripts.missing_link_checkpoint_cadence import CheckpointCadence, CheckpointFailure, FilePin, PinnedFiles


LINE = b': authored buffered stream; no upstream content or credentials\n'


def drive(lines, engine):
    """Stress actual before/after-read boundaries; no SSE interpretation."""
    stream = io.BytesIO(LINE * lines)
    engine.start()
    count = 0
    while True:
        engine.poll()
        line = stream.readline(512001)
        engine.poll()
        if not line:
            break
        count += 1
    engine.finish()
    if count != lines:
        raise AssertionError('Authored stream was not completely drained.')
    return engine.snapshot()


def authored_control():
    engine = CheckpointCadence(fast=lambda: None, critical=lambda: None,
                               history=lambda: None, clock=lambda: 0)
    return {'scope': 'authored_zero_cost_callbacks', 'lines': 10000,
            'checkpoint_trace': drive(10000, engine), 'provider_calls': 0}


def filesystem_benchmark():
    with tempfile.TemporaryDirectory(prefix='repotraction-checkpoint-bench-') as directory:
        root = Path(directory).resolve()
        code, historical = root/'code', root/'history'
        code.mkdir(); historical.mkdir()

        def fixtures(folder, count, size):
            pins = []
            for number in range(count):
                body = (f'Authored fixture {number:04}\n'.encode() * (size // 20 + 1))[:size]
                path = folder/f'{number:04}.txt'
                path.write_bytes(body)
                pins.append(FilePin(path, hashlib.sha256(body).hexdigest()))
            return PinnedFiles(pins)

        critical_files = fixtures(code, 58, 16384)
        history_files = fixtures(historical, 1740, 32768)
        database = root/'authored.sqlite3'
        rows = [(i, f'authored-{i}', i * 10) for i in range(579)]
        with closing(sqlite3.connect(database)) as connection:
            connection.execute('CREATE TABLE authored_ledger (id INTEGER PRIMARY KEY, job TEXT, value INTEGER)')
            connection.executemany('INSERT INTO authored_ledger VALUES (?,?,?)', rows)
            connection.commit()
        lease = WorkerLease(database)
        if not lease.acquire():
            raise CheckpointFailure('Authored temporary lease unavailable.')
        cancelled = root/'cancel'
        frozen_request = ('authored-account', 'authored-model', 'authored-slot')
        request = list(frozen_request)
        try:
            def fast():
                if cancelled.exists() or lease.file is None or lease.file.closed:
                    raise CheckpointFailure('Authored immediate guard failed.')
                held, current = os.fstat(lease.file.fileno()), lease.path.stat()
                if (held.st_dev, held.st_ino) != (current.st_dev, current.st_ino) or tuple(request) != frozen_request:
                    raise CheckpointFailure('Authored lease or request changed.')

            def critical():
                critical_files.verify()
                if {p.name for p in code.iterdir()} != {f'{n:04}.txt' for n in range(58)}:
                    raise CheckpointFailure('Authored code inventory changed.')

            def history():
                history_files.verify()
                if {p.name for p in historical.iterdir()} != {f'{n:04}.txt' for n in range(1740)}:
                    raise CheckpointFailure('Authored history inventory changed.')
                with closing(sqlite3.connect(database.as_uri()+'?mode=ro', uri=True)) as connection:
                    connection.execute('BEGIN')
                    if connection.execute('SELECT * FROM authored_ledger ORDER BY id').fetchall() != rows:
                        raise CheckpointFailure('Authored ledger changed.')

            calibration = {}
            for name, callback in (('critical', critical), ('history', history)):
                values = []
                for _ in range(3):
                    start = time.perf_counter()
                    callback()
                    values.append(time.perf_counter() - start)
                calibration[name] = {'samples_seconds': values, 'median_seconds': statistics.median(values),
                                     'max_seconds': max(values)}
            workloads = []
            for lines, limit in ((10000, 30), (60000, 120)):
                engine = CheckpointCadence(fast=fast, critical=critical, history=history)
                start = time.perf_counter()
                trace = drive(lines, engine)
                elapsed = time.perf_counter() - start
                workloads.append({'lines': lines, 'bytes': len(LINE)*lines,
                                  'wall_seconds_including_barriers': elapsed,
                                  'component_budget_seconds': limit,
                                  'within_component_budget': elapsed <= limit, 'checkpoint_trace': trace})
            return {'scope': 'synthetic_filesystem_component_only', 'code_files': 58, 'history_files': 1740,
                    'code_bytes_each': 16384, 'history_bytes_each': 32768, 'authored_ledger_rows': len(rows),
                    'provider_calls': 0, 'original_state_accessed': False,
                    'calibration': calibration, 'workloads': workloads,
                    'within_component_budget': (calibration['critical']['max_seconds'] <= .1
                        and calibration['history']['max_seconds'] <= 5
                        and all(row['within_component_budget'] for row in workloads)),
                    'live_runner_readiness_established': False}
        finally:
            lease.release()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--filesystem', action='store_true', help='Measure fixed temporary filesystem fixtures.')
    args = parser.parse_args()
    result = filesystem_benchmark() if args.filesystem else authored_control()
    print(json.dumps(result, indent=2))
    if args.filesystem and not result['within_component_budget']:
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
