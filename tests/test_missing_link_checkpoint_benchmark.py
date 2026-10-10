"""Check fixed offline workload without running a timing benchmark in CI."""
import json
import unittest
from unittest.mock import patch

from scripts import missing_link_checkpoint_benchmark as benchmark
from scripts.missing_link_checkpoint_cadence import CheckpointCadence, CheckpointFailure


class CheckpointBenchmarkTests(unittest.TestCase):
    def test_fixed_buffered_workload_has_no_network_or_original_state(self):
        with patch('socket.socket', side_effect=AssertionError('No network')), \
                patch('sqlite3.connect', side_effect=AssertionError('No original DB')), \
                patch('pathlib.Path.read_bytes', side_effect=AssertionError('No files')):
            result = benchmark.authored_control()
        self.assertEqual(result['provider_calls'], 0)
        self.assertEqual(result['lines'], 10000)
        self.assertEqual(result['checkpoint_trace']['state'], 'finished')
        self.assertEqual(result['checkpoint_trace']['counts']['history'], 2)
        self.assertEqual(result['checkpoint_trace']['counts']['critical'], 4)

    def test_failed_terminal_audit_cannot_report_finished_workload(self):
        count = 0
        def history():
            nonlocal count
            count += 1
            if count == 2:
                raise CheckpointFailure('Authored end mutation')
        engine = CheckpointCadence(fast=lambda: None, critical=lambda: None, history=history, clock=lambda: 0)
        with self.assertRaises(CheckpointFailure):
            benchmark.drive(10000, engine)
        self.assertEqual(engine.snapshot()['state'], 'failed')
        self.assertNotIn('Authored end mutation', json.dumps(engine.snapshot()))
