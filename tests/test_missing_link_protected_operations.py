"""Authored unit ownership, integrity, ordering and clock controls; no IO."""
from concurrent.futures import ThreadPoolExecutor
import unittest
from unittest.mock import Mock

from scripts.missing_link_checkpoint_cadence import CheckpointFailure
from scripts.missing_link_protected_operations import ProtectedOperations


class ProtectedOperationsTests(unittest.TestCase):
    def setUp(self):
        self.now = 0
        self.fast, self.critical, self.history = Mock(), Mock(), Mock()
        self.engine = ProtectedOperations(fast=self.fast, critical=self.critical,
            history=self.history, clock=lambda: self.now)
        self.engine.start()

    def telemetry(self, callback=lambda: None):
        return self.engine.operation('telemetry', lambda: self.engine.commit('telemetry', callback))

    def test_each_unit_has_fresh_full_boundaries_even_at_the_same_clock_value(self):
        self.telemetry(); self.telemetry()
        self.assertEqual(self.history.call_count, 5)  # Start + two pairs, no freshness shortcut.
        self.assertEqual(self.engine.snapshot()['protected_commits'], 2)
        self.assertEqual(self.engine.snapshot()['protected_units']['telemetry'], 2)

    def test_accounting_writes_share_only_their_owned_full_boundaries(self):
        writes = []
        def account():
            for number in range(3):
                self.engine.commit('checkpoint', lambda: writes.append(number))
        self.engine.operation('account', account)
        self.assertEqual(writes, [0, 1, 2])
        self.assertEqual(self.history.call_count, 3)
        self.assertGreaterEqual(self.critical.call_count, 10)

    def test_failed_entry_cannot_write_or_retry(self):
        primary = OSError('Authored original history failure')
        self.history.side_effect = primary
        write = Mock()
        with self.assertRaises(OSError) as caught: self.telemetry(write)
        self.assertIs(caught.exception, primary)
        write.assert_not_called()
        calls = self.history.call_count
        self.history.side_effect = None
        for action in (self.telemetry, self.engine.poll, self.engine.finish):
            with self.assertRaises(OSError) as later: action()
            self.assertIs(later.exception, primary)
        self.assertEqual(calls, self.history.call_count)

    def test_post_boundary_failure_prevents_return_or_a_following_unit(self):
        primary = OSError('Authored mutation during internal write')
        def write(): self.history.side_effect = primary; return 'provisional'
        accepted = []
        with self.assertRaises(OSError): accepted.append(self.telemetry(write))
        self.assertEqual(accepted, [])
        with self.assertRaises(OSError) as caught: self.telemetry()
        self.assertIs(caught.exception, primary)

    def test_critical_change_blocks_the_next_accounting_write_and_unit_exit(self):
        writes = []
        primary = OSError('Authored changed code or owned journal')
        def first(): writes.append(1); self.critical.side_effect = primary
        def account():
            self.engine.commit('checkpoint', first)
            self.engine.commit('checkpoint', lambda: writes.append(2))
            self.engine.commit('checkpoint', lambda: writes.append(3))
        with self.assertRaises(OSError) as caught: self.engine.operation('account', account)
        self.assertIs(caught.exception, primary)
        self.assertEqual(writes, [1])

    def test_overdue_history_is_forced_inside_a_unit_before_its_next_write(self):
        def account():
            self.engine.commit('checkpoint', lambda: None)
            self.now = 30
            self.engine.commit('checkpoint', lambda: None)
            self.engine.commit('checkpoint', lambda: None)
        self.engine.operation('account', account)
        self.assertEqual(self.history.call_count, 4)  # Entry, due poll, exit, plus start.

    def test_missing_out_of_order_extra_and_outside_writes_fail_closed(self):
        for callback in (lambda: None, lambda: self.engine.commit('result', lambda: None),
                         lambda: (self.engine.commit('telemetry', lambda: None),
                                  self.engine.commit('telemetry', lambda: None))):
            self.setUp()
            with self.assertRaises(CheckpointFailure): self.engine.operation('telemetry', callback)
            self.assertEqual(self.engine.snapshot()['state'], 'failed')
        self.setUp()
        with self.assertRaises(CheckpointFailure): self.engine.commit('telemetry', lambda: None)

    def test_caught_nested_unit_and_commit_errors_still_poison_outer_unit(self):
        for nested in (lambda: self.telemetry(),
                       lambda: self.engine.commit('telemetry', lambda: None)):
            self.setUp()
            def write():
                with self.assertRaises(CheckpointFailure): nested()
            with self.assertRaises(CheckpointFailure): self.telemetry(write)
            self.assertEqual(self.engine.snapshot()['state'], 'failed')

    def test_cross_thread_operation_cannot_write_and_poisons_current_owner(self):
        write = Mock()
        def body():
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(self.telemetry, write)
                with self.assertRaises(CheckpointFailure): future.result()
        with self.assertRaises(CheckpointFailure): self.engine.operation('telemetry', body)
        write.assert_not_called()

    def test_inner_failure_keeps_the_same_primary_even_if_the_body_catches_it(self):
        primary = OSError('Authored storage failure')
        def body():
            with self.assertRaises(OSError): self.engine.commit('telemetry', Mock(side_effect=primary))
        with self.assertRaises(OSError) as caught: self.engine.operation('telemetry', body)
        self.assertIs(caught.exception, primary)

    def test_normal_barriers_remain_unconditional_and_snapshot_does_not_sample_clock(self):
        self.engine.barrier(); self.engine.barrier()
        self.assertEqual(self.history.call_count, 3)
        self.engine.controller._clock = Mock(side_effect=AssertionError('No clock read'))
        self.engine.snapshot()


if __name__ == '__main__': unittest.main()
