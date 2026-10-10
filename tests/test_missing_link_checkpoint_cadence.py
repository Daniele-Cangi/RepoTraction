"""Authored timing/failure controls and real temporary files; no paid IO."""
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor, wait as real_wait
import unittest
from unittest.mock import Mock, patch

from scripts.missing_link_checkpoint_cadence import CheckpointCadence, CheckpointFailure, FilePin, PinnedFiles


class Clock:
    def __init__(self):
        self.value = 0.0

    def __call__(self):
        return self.value


class CheckpointCadenceTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.fast, self.critical, self.history = Mock(), Mock(), Mock()
        self.engine = CheckpointCadence(fast=self.fast, critical=self.critical,
                                        history=self.history, clock=self.clock)

    def test_ten_thousand_buffered_lines_do_not_multiply_file_audits(self):
        self.engine.start()
        for _ in range(10000):
            self.engine.poll()  # Before a read.
            self.engine.poll()  # After a read, including blank/comment lines.
        self.engine.finish()
        self.assertEqual(self.history.call_count, 2)
        self.assertEqual(self.critical.call_count, 4)
        self.assertGreaterEqual(self.fast.call_count, 20000)
        self.assertEqual(self.engine.snapshot()['state'], 'finished')

    def test_periods_fire_at_equality_and_full_replaces_due_critical(self):
        self.engine.start()
        self.clock.value = .999
        self.engine.poll()
        self.assertEqual(self.critical.call_count, 2)
        self.clock.value = 1
        self.engine.poll()
        self.assertEqual(self.critical.call_count, 3)
        for second in range(2, 30):
            self.clock.value = second
            self.engine.poll()
        self.assertEqual(self.history.call_count, 1)
        before = self.critical.call_count
        self.clock.value = 30
        self.engine.poll()
        self.assertEqual(self.history.call_count, 2)
        self.assertEqual(self.critical.call_count, before + 2)

    def test_intervals_start_at_successful_completion(self):
        self.history.side_effect = lambda: setattr(self.clock, 'value', self.clock.value + 8)
        self.engine.start()
        self.clock.value = 37.999
        self.engine.poll()
        self.assertEqual(self.history.call_count, 1)
        self.clock.value = 38
        self.engine.poll()
        self.assertEqual(self.history.call_count, 2)
        self.assertEqual(self.clock.value, 46)

    def test_forced_barrier_never_uses_freshness_as_acceptance(self):
        self.engine.start()
        self.engine.barrier()
        self.engine.finish()
        self.assertEqual(self.history.call_count, 3)
        self.assertEqual(self.critical.call_count, 6)

    def test_due_history_after_a_blocked_read_is_checked_on_return(self):
        self.engine.start()
        self.engine.poll()
        self.clock.value = 55
        self.engine.poll()
        self.assertEqual(self.history.call_count, 2)

    def test_failures_at_each_layer_are_latched_without_retry(self):
        for name in ('fast', 'critical', 'history'):
            with self.subTest(name=name):
                self.setUp()
                self.engine.start()
                error = OSError('PRIVATE checkpoint failure')
                getattr(self, name).side_effect = error
                with self.assertRaises(OSError) as first:
                    self.engine.barrier()
                calls = {key: getattr(self, key).call_count for key in ('fast', 'critical', 'history')}
                getattr(self, name).side_effect = None
                for action in (self.engine.poll, self.engine.barrier, self.engine.finish, self.engine.start):
                    with self.assertRaises(OSError) as later:
                        action()
                    self.assertIs(later.exception, first.exception)
                self.assertEqual(calls, {key: getattr(self, key).call_count for key in calls})
                self.assertNotIn('PRIVATE', json.dumps(self.engine.snapshot()))

    def test_cancellation_and_lease_loss_are_immediate_even_with_fresh_audit(self):
        self.engine.start()
        self.fast.side_effect = CheckpointFailure('Authored lease replacement')
        with self.assertRaises(CheckpointFailure):
            self.engine.poll()
        self.assertEqual(self.history.call_count, 1)

    def test_state_changed_during_history_cannot_pass_barrier(self):
        self.engine.start()
        self.history.side_effect = lambda: setattr(self.fast, 'side_effect', CheckpointFailure('Changed during audit'))
        with self.assertRaises(CheckpointFailure):
            self.engine.finish()
        self.assertEqual(self.engine.snapshot()['state'], 'failed')

    def test_code_changed_during_history_is_rechecked_before_acceptance(self):
        self.engine.start()
        self.history.side_effect = lambda: setattr(self.critical, 'side_effect', CheckpointFailure('Code changed'))
        with self.assertRaises(CheckpointFailure):
            self.engine.finish()

    def test_clock_errors_are_latched_and_missing_durations_are_not_zero(self):
        for value in (False, float('nan'), float('inf'), -1):
            with self.subTest(value=value):
                self.setUp()
                self.engine.start()
                self.clock.value = value
                with self.assertRaises(CheckpointFailure):
                    self.engine.poll()
                trace = self.engine.snapshot()
                self.assertFalse(trace['clock_valid'])
                self.assertEqual(set(trace['seconds'].values()), {None})

    def test_clock_failure_does_not_mask_primary_callback_failure(self):
        error = RuntimeError('Original integrity failure')
        def fail():
            self.clock.value = float('nan')
            raise error
        self.critical.side_effect = fail
        with self.assertRaises(RuntimeError) as caught:
            self.engine.start()
        self.assertIs(caught.exception, error)
        self.assertFalse(self.engine.snapshot()['clock_valid'])

    def test_caught_reentrancy_still_poisons_outer_operation(self):
        def recurse():
            try:
                self.engine.poll()
            except CheckpointFailure:
                pass
        self.fast.side_effect = recurse
        with self.assertRaisesRegex(CheckpointFailure, 'Reentrant'):
            self.engine.start()
        self.assertEqual(self.engine.snapshot()['state'], 'failed')

    def test_clock_reentrancy_at_every_sample_cannot_return_success(self):
        for action in ('start', 'poll', 'barrier', 'critical_barrier', 'finish'):
            # Discover the clock boundaries of a successful operation, including
            # finalization and poll's sample outside a callback measurement.
            probe_clock = Mock(return_value=0)
            probe = CheckpointCadence(fast=lambda: None, critical=lambda: None,
                                      history=lambda: None, clock=probe_clock)
            if action != 'start':
                probe.start()
            probe_clock.reset_mock()
            getattr(probe, action)()
            for target in range(1, probe_clock.call_count + 1):
                with self.subTest(action=action, sample=target):
                    state = {'armed': False, 'calls': 0, 'caught': []}
                    def clock():
                        if state['armed']:
                            state['calls'] += 1
                            if state['calls'] == target:
                                try:
                                    engine.poll()
                                except CheckpointFailure as exc:
                                    state['caught'].append(exc)
                        return 0
                    engine = CheckpointCadence(fast=lambda: None, critical=lambda: None,
                                               history=lambda: None, clock=clock)
                    if action != 'start':
                        engine.start()
                    state['armed'] = True
                    with self.assertRaises(CheckpointFailure) as caught:
                        getattr(engine, action)()
                    self.assertIs(caught.exception, state['caught'][0])
                    self.assertEqual(engine.snapshot()['state'], 'failed')
                    self.assertFalse(engine.snapshot()['clock_valid'])
                    calls = state['calls']
                    with self.assertRaises(CheckpointFailure) as later:
                        engine.finish()
                    self.assertIs(later.exception, caught.exception)
                    self.assertEqual(state['calls'], calls)

    def test_invalid_lifecycle_never_restarts_or_reuses_finished_controller(self):
        with self.assertRaises(CheckpointFailure):
            self.engine.poll()
        with self.assertRaises(CheckpointFailure):
            self.engine.start()
        self.setUp()
        self.engine.start()
        self.engine.finish()
        with self.assertRaises(CheckpointFailure):
            self.engine.start()

    def test_snapshot_does_not_sample_clock_and_bounds_telemetry(self):
        self.engine.start()
        self.engine._clock = Mock(side_effect=AssertionError('No observation in snapshot'))
        self.engine._counts['fast'] = 10**20
        self.engine._seconds['fast'] = 10**20
        trace = self.engine.snapshot()
        self.assertTrue(trace['saturated'])
        self.assertEqual(trace['counts']['fast'], 32_000_032)
        self.assertEqual(trace['seconds']['fast'], 86400)

    def test_slow_authored_audits_do_not_scale_with_delta_count(self):
        def advance(seconds):
            self.clock.value += seconds
        self.fast.side_effect = lambda: advance(.00002)
        self.critical.side_effect = lambda: advance(.046)
        self.history.side_effect = lambda: advance(15.85)
        self.engine.start()
        start = self.clock.value
        for _ in range(12000):
            self.engine.poll()
            advance(.02)  # 240 seconds of authored returned-read time.
            self.engine.poll()
        self.engine.finish()
        self.assertLess(self.clock.value - start, 600)
        self.assertLess(self.history.call_count, 20)


class PinnedFilesTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name) / 'pinned.txt'
        self.path.write_bytes(b'line\r\nnext\rline\n')

    def pin(self, raw=None, canonical=False):
        raw = self.path.read_bytes() if raw is None else raw
        return FilePin(self.path, hashlib.sha256(raw).hexdigest(), canonical)

    def test_raw_and_canonical_bindings_share_one_read_and_preserve_lf_semantics(self):
        raw = self.path.read_bytes()
        pins = PinnedFiles([self.pin(), self.pin(b'line\nnext\nline\n', True), self.pin()])
        with patch.object(Path, 'open', return_value=io.BytesIO(raw)) as read:
            pins.verify()
        read.assert_called_once()

    def test_same_size_same_mtime_mutation_is_not_cached(self):
        pins = PinnedFiles([self.pin()])
        pins.verify()
        previous = self.path.stat()
        self.path.write_bytes(b'X' * previous.st_size)
        os.utime(self.path, ns=(previous.st_atime_ns, previous.st_mtime_ns))
        with self.assertRaises(CheckpointFailure):
            pins.verify()

    def test_replacement_and_deletion_are_detected(self):
        pins = PinnedFiles([self.pin()])
        replacement = self.path.with_suffix('.replacement')
        replacement.write_bytes(b'changed')
        replacement.replace(self.path)
        with self.assertRaises(CheckpointFailure):
            pins.verify()
        self.path.unlink()
        with self.assertRaises(FileNotFoundError):
            pins.verify()

    def test_external_pin_list_mutation_does_not_change_inventory(self):
        values = [self.pin()]
        pins = PinnedFiles(values)
        values.clear()
        self.path.write_bytes(b'changed')
        with self.assertRaises(CheckpointFailure):
            pins.verify()

    def test_invalid_or_conflicting_bindings_fail_before_io(self):
        for values in ([], [FilePin(Path('relative'), 'a'*64)], [FilePin(self.path, 'bad')],
                       [self.pin(), FilePin(self.path, 'a'*64)], [FilePin(self.path, 'a'*64, 1)]):
            with self.subTest(values=values), patch.object(Path, 'read_bytes', side_effect=AssertionError('No IO')):
                with self.assertRaises(ValueError):
                    PinnedFiles(values)

    def test_history_mutation_is_caught_by_terminal_barrier_inside_fresh_interval(self):
        pins = PinnedFiles([self.pin()])
        engine = CheckpointCadence(fast=lambda: None, critical=lambda: None, history=pins.verify, clock=Clock())
        engine.start()
        self.path.write_bytes(b'changed')
        engine.poll()  # Explicitly within the documented detection window.
        with self.assertRaises(CheckpointFailure):
            engine.finish()

    def test_parallel_failure_joins_all_running_reads_and_bounds_outstanding_work(self):
        body = b'authored'
        pins = PinnedFiles([FilePin(self.path.parent/f'{n:02}.txt', hashlib.sha256(body).hexdigest())
                            for n in range(40)])
        lock = threading.Lock()
        all_started, failure, release = threading.Event(), threading.Event(), threading.Event()
        active, maximum, reads = 0, 0, []

        def read(path, mode):
            self.assertEqual(mode, 'rb')
            nonlocal active, maximum
            with lock:
                active += 1
                maximum = max(maximum, active)
                reads.append(path.name)
                if active == 8:
                    all_started.set()
            try:
                if path.name == '00.txt':
                    if not all_started.wait(10):
                        raise AssertionError('Eight authored readers did not start.')
                    raise OSError('Authored read failure')
                if not release.wait(10):
                    raise AssertionError('Authored reader was not released.')
                return io.BytesIO(body)
            finally:
                with lock:
                    active -= 1

        def observed_wait(*args, **kwargs):
            done, pending = real_wait(*args, **kwargs)
            if any(future.exception() is not None for future in done):
                failure.set()
            return done, pending

        with patch.object(Path, 'open', read), \
                patch('scripts.missing_link_checkpoint_cadence.wait', observed_wait), \
                ThreadPoolExecutor(max_workers=1) as caller:
            result = caller.submit(pins.verify)
            try:
                self.assertTrue(failure.wait(10))
                self.assertFalse(result.done())  # The failed audit still owns seven reads.
            finally:
                release.set()
            with self.assertRaisesRegex(OSError, 'Authored read failure'):
                result.result(timeout=10)
        self.assertEqual(active, 0)
        self.assertEqual(maximum, 8)
        self.assertEqual(len(reads), 8)

    def test_parallel_success_reads_each_path_once_for_multiple_digest_modes(self):
        body = b'authored\r\n'
        canonical = body.replace(b'\r\n', b'\n')
        values = []
        for number in range(20):
            path = self.path.parent/f'{number:02}.txt'
            values.extend((FilePin(path, hashlib.sha256(body).hexdigest()),
                           FilePin(path, hashlib.sha256(canonical).hexdigest(), True)))
        with patch.object(Path, 'open', side_effect=lambda *_: io.BytesIO(body)) as read:
            PinnedFiles(values).verify()
        self.assertEqual(read.call_count, 20)

    def test_uneven_batches_verify_every_file_again_and_detect_a_late_change(self):
        values = []
        for number in range(39):
            path = self.path.parent/f'{number:02}.txt'
            path.write_bytes(b'authored')
            values.append(FilePin(path, hashlib.sha256(b'authored').hexdigest()))
        pins = PinnedFiles(values)
        pins.verify()
        last = values[-1].path
        stamp = last.stat()
        last.write_bytes(b'mutated!')
        os.utime(last, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
        with self.assertRaises(CheckpointFailure): pins.verify()

    def test_failure_in_later_batch_round_stops_new_reads_and_joins_active_reads(self):
        body = b'authored'
        pins = PinnedFiles(FilePin(self.path.parent/f'{n:02}.txt', hashlib.sha256(body).hexdigest())
                           for n in range(40))
        first_round = threading.Barrier(8)
        second_started, failure, release = threading.Event(), threading.Event(), threading.Event()
        lock = threading.Lock()
        reads, second = [], []

        def read(path, mode):
            number = int(path.stem)
            with lock: reads.append(number)
            if number < 8:
                first_round.wait(timeout=10)
            elif number < 16:
                with lock:
                    second.append(number)
                    if len(second) == 8: second_started.set()
                if number == 8:
                    if not second_started.wait(10): raise AssertionError('Second read round did not start')
                    raise OSError('Authored later-round read failure')
                if not release.wait(10): raise AssertionError('Authored read was not released')
            else:
                raise AssertionError('Read started after global failure')
            return io.BytesIO(body)

        def observed_wait(*args, **kwargs):
            done, pending = real_wait(*args, **kwargs)
            if any(future.exception() is not None for future in done): failure.set()
            return done, pending

        with patch.object(Path, 'open', read), \
                patch('scripts.missing_link_checkpoint_cadence.wait', observed_wait), \
                ThreadPoolExecutor(max_workers=1) as caller:
            result = caller.submit(pins.verify)
            try:
                self.assertTrue(failure.wait(10))
                self.assertFalse(result.done())
            finally:
                release.set()
            with self.assertRaisesRegex(OSError, 'Authored later-round read failure'):
                result.result(timeout=10)
        self.assertEqual(sorted(reads), list(range(16)))

    def test_incremental_canonical_hash_handles_chunked_utf8_and_newlines(self):
        raw = ('A'*65535 + '\r\n' + 'B'*65533 + '€\r' + '\nend\r').encode('utf-8')
        self.path.write_bytes(raw)
        canonical = raw.decode('utf-8').replace('\r\n', '\n').replace('\r', '\n').encode('utf-8')
        PinnedFiles([self.pin(), self.pin(canonical, True)]).verify()
        # Force every UTF-8 and CRLF sequence across read boundaries as well.
        class TinyReads(io.BytesIO):
            def read(self, size):
                self.asserted_size = size
                return super().read(1)
        stream = TinyReads('€\r\nx\r\ry\r'.encode())
        digest = hashlib.sha256('€\nx\n\ny\n'.encode()).hexdigest()
        with patch.object(Path, 'open', return_value=stream):
            PinnedFiles([FilePin(self.path, digest, True)]).verify()
        self.assertTrue(stream.closed)
        self.assertEqual(stream.asserted_size, 65536)

    def test_mid_file_failure_closes_handle_without_accepting_partial_hash(self):
        class BrokenRead(io.BytesIO):
            def read(self, size):
                if self.tell():
                    raise OSError('Authored mid-file read error')
                return super().read(1)
        stream = BrokenRead(b'authored')
        with patch.object(Path, 'open', return_value=stream):
            with self.assertRaises(OSError):
                PinnedFiles([FilePin(self.path, 'a'*64)]).verify()
        self.assertTrue(stream.closed)

    def test_incomplete_utf8_fails_canonical_hash_but_not_raw_hash(self):
        raw = b'end\xe2\x82'
        self.path.write_bytes(raw)
        PinnedFiles([self.pin()]).verify()
        with self.assertRaises(UnicodeDecodeError):
            PinnedFiles([self.pin(raw, True)]).verify()
