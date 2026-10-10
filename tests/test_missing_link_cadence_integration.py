"""Authored streams and isolated ledgers; no credentials, sockets or acquired code."""
import copy
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import Mock, patch

from missing_link.service import Budget
from missing_link.provider_errors import ProviderTransportError
from scripts.missing_link_checkpoint_cadence import FilePin, CheckpointFailure
from scripts.missing_link_cadence_checks import Checks, HistoryAudit, database_snapshot
from scripts import missing_link_cadence_reader as reader
from scripts import missing_link_cadence_executor as executor
from scripts.missing_link_cadence_owned import run_offline_owned
from scripts.missing_link_repository_only_evaluator import EvaluationStopped
from scripts.missing_link_stream_successor_receipts import TelemetryPersistenceError
from test_missing_link_stream_successor_receipts import Clock, Stream
from test_missing_link_repository_only_evaluator import terminal
from test_missing_link_demand_operation_policy import unknown
import test_missing_link_demand_operation_policy_v3_executor as authored_v3
from scripts.missing_link_repository_only_run import sha, load


def event(value):
    return b'data: ' + json.dumps(value).encode() + b'\n'


class CadenceIntegrationTests(unittest.TestCase):
    operation_units = False
    executor_module = executor

    def setUp(self):
        self.fixture = authored_v3.PolicyV3ExecutorTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        f = self.fixture
        self.clock, self.traces, self.receipts = Clock(), [], []
        source = copy.deepcopy(f.source)
        source['semantic_policy_revision'] = 3
        self.manifest = self.executor_module.successor_manifest(source)
        self.bound = self.executor_module.bind_requests(f.provider, f.packets, self.manifest, f.files.__getitem__)
        self.fast, self.critical, self.history = Mock(), Mock(), Mock()
        checks_type = reader.ProtectedOperations if self.operation_units else Checks
        self.checks = checks_type(fast=self.fast, critical=self.critical, history=self.history, clock=self.clock)
        self.checks.start()
        self.job = {'id': 'authored', 'ai_calls_used': 0, 'cost_reserved_usd': 0, 'checkpoint': {}}
        self.charges = []
        if self.operation_units:
            self.budget = Budget(self.job, lambda: self.checks.commit('checkpoint', lambda: None),
                lambda: False, self.checks.guard,
                lambda cost: self.checks.commit('reservation', lambda: self.charges.append(cost)))
        else:
            self.budget = Budget(self.job, lambda: None, lambda: False, self.checks.barrier, self.charges.append)
        self.fault = lambda: None
        self.addCleanup(patch.stopall)
        patch('socket.socket', side_effect=AssertionError('Offline sockets forbidden')).start()
        patch('missing_link.config.provider_environment', side_effect=AssertionError('No credentials')).start()

    def read(self, lines=None, *, delay=0, retain=None, on_read=lambda: None, on_open=lambda: None):
        self.stream = Stream(lines if lines is not None else [event(terminal(unknown()))], self.clock, delay, on_read)
        opener = Mock()
        def open_response(*args, **kwargs):
            self.assertEqual(kwargs['timeout'], 55)
            on_open()
            return self.stream
        opener.open.side_effect = open_response
        try:
            return reader.complete_with_receipt(self.fixture.provider, self.bound[0].slot(), self.bound[0].body,
                self.budget, checks=self.checks, retain_terminal=retain or self.receipts.append,
                retain_telemetry=self.traces.append, reservation_observed=lambda: bool(self.charges),
                before_open=lambda: None, opener_factory=lambda: opener, clock=self.clock,
                operations=self.checks if self.operation_units else None)
        finally:
            self.assertLessEqual(opener.open.call_count, 1)

    def test_60000_lines_do_not_trigger_line_count_audits(self):
        self.read([b': authored\n'] * 60000 + [event(terminal(unknown()))])
        trace = self.traces[0]
        self.assertEqual(trace['lines'], 60001)
        self.assertEqual(trace['full_checkpoints'], 6)  # Two unconditional terminal barriers: 2*(critical/history/critical).
        self.assertEqual(trace['active_stream_seconds'], 0)
        self.assertEqual(self.stream.close_calls, 1)

    def test_callbacks_count_once_and_are_excluded_only_from_active_time(self):
        self.critical.side_effect = lambda: setattr(self.clock, 'value', self.clock.value + 2)
        self.history.side_effect = lambda: setattr(self.clock, 'value', self.clock.value + 3)
        self.read(delay=1)
        trace = self.traces[0]
        self.assertEqual(trace['active_stream_seconds'], 1)
        self.assertEqual(trace['wall_stream_seconds'], 1 + trace['full_checkpoint_seconds'])
        self.assertGreater(trace['full_checkpoint_seconds'], 0)

    def test_returned_slow_read_expires_before_terminal_retention(self):
        with self.assertRaises(ProviderTransportError): self.read(delay=241)
        self.assertEqual(self.traces[0]['deadline_kind'], 'active_stream')
        self.assertFalse(self.traces[0]['terminal_retained'])
        self.assertNotIn('reported_usage', self.job)
        self.assertTrue(self.stream.closed)

    def test_wall_deadline_after_slow_audit_stops_usage(self):
        def slow():
            if self.stream.active:
                self.clock.value += 601
        self.history.side_effect = slow
        # The stream field is accessed by pre-open barriers too.
        with self.assertRaises(ProviderTransportError): self.read()
        self.assertEqual(self.traces[0]['deadline_kind'], 'wall_stream')
        self.assertNotIn('reported_usage', self.job)

    def test_post_terminal_mutation_blocks_usage_even_inside_fresh_interval(self):
        def retain(value):
            self.receipts.append(value)
            self.critical.side_effect = EvaluationStopped('Authored changed code')
        with self.assertRaises(EvaluationStopped): self.read(retain=retain)
        self.assertTrue(self.traces[0]['terminal_retained'])
        self.assertNotIn('reported_usage', self.job)
        with self.assertRaises(EvaluationStopped): self.checks.finish()

    def test_missing_usage_is_global_and_stays_missing(self):
        native = terminal(unknown()); del native['response']['usage']
        with self.assertRaises(reader.CandidateValidationError): self.read([event(native)])
        self.assertEqual(self.receipts, [native])
        self.assertNotIn('reported_usage', self.job)
        self.assertTrue(self.traces[0]['reservation_committed'])

    def test_native_type_status_and_size_limits(self):
        for line, code in ((b'data: []\n', 'ai_stream_invalid_event'),
                (event({'type': 'response.completed', 'response': {'status': 'incomplete'}}), 'ai_stream_invalid_event'),
                (b'x'*512001, 'ai_transport_size_exceeded'), (b'', 'ai_stream_missing_terminal')):
            with self.subTest(code=code):
                self.setUp()
                with self.assertRaises(ProviderTransportError) as caught: self.read([line])
                self.assertEqual(caught.exception.code, code)
                self.assertFalse(self.receipts)

    def test_response_cleanup_preserves_callback_primary(self):
        primary = OSError('Authored guard failure')
        def changed(): self.fast.side_effect = primary
        with patch.object(Stream, '__exit__', side_effect=ValueError('Authored cleanup')):
            with self.assertRaises(OSError) as caught: self.read(on_read=changed)
        self.assertIs(caught.exception, primary)

    def test_immutable_request_binding_does_not_use_mutated_input_objects(self):
        original = self.bound[0].body
        self.manifest['requests'][0]['native_sha256'] = '0'*64
        self.fixture.packets[0]['id'] = 'changed'
        self.assertEqual(self.bound[0].body, original)
        self.read()
        with self.assertRaises(Exception): self.bound[0].body = b'changed'

    def test_new_settings_job_ids_and_concrete_types_are_verified(self):
        for change in (lambda m: m.update(critical_interval_seconds=True),
                       lambda m: m.update(full_checkpoint_nonterminal_lines=128),
                       lambda m: m['requests'][0].update(job_id='consumed'),
                       lambda m: m['requests'][0].update(native_sha256='0'*64)):
            modified = copy.deepcopy(self.manifest); change(modified)
            with self.assertRaises(EvaluationStopped):
                self.executor_module.bind_requests(self.fixture.provider, self.fixture.packets, modified,
                                                   self.fixture.files.__getitem__)

    def owned(self, *, observe=lambda stage, owner: None, lines=None, history=None, identity=None, read=None,
              case_limit=11):
        workspace = self.fixture.root/'cadence-owned'
        f = self.fixture
        opens = []
        def factory():
            stream = Stream(lines or [event(terminal(unknown()))], self.clock)
            def opening(*a, **k): opens.append(True); return stream
            return Mock(open=opening)
        try:
            return run_offline_owned(workspace, provider=f.provider, packets=f.packets,
                manifest=self.manifest, read=read or f.files.__getitem__,
                code_pins=[FilePin(f.root/'code.txt', sha(f.root/'code.txt', canonical=True), True)],
                historical_audit=history or (lambda: None), identity=identity or (lambda **kwargs: None),
                opener_factory=factory, allowance=f.source['allowance'], account=f.source['account'],
                base_reserved=.1, ceiling=.2, observe=observe, clock=self.clock, case_limit=case_limit,
                operation_units=self.operation_units)
        finally:
            self.opens, self.workspace = len(opens), workspace

    def test_owned_whole_cohort_keeps_receipts_exact_prefix_and_rejects_replay(self):
        original = database_snapshot(self.fixture.db, self.fixture.source['allowance'])
        result = self.owned()
        self.assertEqual(self.opens, 11)
        out = self.workspace/'evidence'
        self.assertTrue((out/'owned-artifacts.json').exists())
        self.assertFalse((out/'owned-artifacts.provisional.json').exists())
        self.assertEqual(result['receipt_sha256'], sha(out/'owned-artifacts.json'))
        self.assertEqual(set(load(out/'owned-artifacts.json')) | {'owned-artifacts.json'},
                         {path.name for path in out.iterdir()})
        self.assertEqual(len(list(out.glob('terminal-*.json'))), 11)
        self.assertEqual(database_snapshot(self.fixture.db, self.fixture.source['allowance']), original)
        final = load(out/'final-integrity.json')
        self.assertEqual(final['reservations'], 12)  # One synthetic prior row + eleven new synthetic rows.
        with self.assertRaises(FileExistsError): self.owned()
        self.assertEqual(self.opens, 0)

    def test_owned_failure_after_atomic_reserve_keeps_charge_and_consumes_scope(self):
        def fail(stage, owner):
            if stage == 'reservation': raise OSError('Authored journal failure')
        with self.assertRaises(OSError): self.owned(observe=fail)
        after = database_snapshot(self.workspace/'authored-ledger.sqlite3', self.fixture.source['allowance'])
        self.assertEqual(after['reservations'], 2)
        self.assertEqual(self.opens, 0)
        self.assertFalse((self.workspace/'evidence/owned-artifacts.json').exists())
        with self.assertRaises(FileExistsError): self.owned()

    def test_owned_terminal_mutation_stops_cohort(self):
        def changed(stage, owner):
            if stage == 'terminal':
                (owner.out/'terminal-01.json').write_text('changed')
        with self.assertRaises(EvaluationStopped): self.owned(observe=changed)
        self.assertEqual(self.opens, 1)
        self.assertFalse((self.workspace/'evidence/attempt-02.json').exists())
        self.assertFalse((self.workspace/'evidence/owned-artifacts.json').exists())

    def test_owned_config_mutation_after_claim_stops_before_reserve(self):
        def changed(stage, owner):
            if stage == 'claim': self.fixture.provider.model = 'changed'
        with self.assertRaises(EvaluationStopped): self.owned(observe=changed)
        self.assertEqual(self.opens, 0)
        self.assertFalse((self.workspace/'evidence/reservation-01.json').exists())

    def test_owned_local_normalizer_refusal_continues(self):
        invalid = unknown(); invalid['fields']['runtime']['text'] = 'Authored unsupported guess'
        self.owned(lines=[event(terminal(invalid))])
        self.assertEqual(self.opens, 11)
        self.assertEqual(load(self.workspace/'evidence/result-01.json')['disposition'], 'local_rejection')

    def test_owned_missing_usage_never_advances_to_next_slot(self):
        native = terminal(unknown()); del native['response']['usage']
        with self.assertRaises(reader.CandidateValidationError): self.owned(lines=[event(native)])
        self.assertEqual(self.opens, 1)
        self.assertTrue((self.workspace/'evidence/terminal-01.json').exists())
        self.assertFalse((self.workspace/'evidence/result-01.json').exists())

    def test_database_row_streaming_hash_matches_frozen_fetchall_format(self):
        actual = database_snapshot(self.fixture.db, self.fixture.source['allowance'])
        with closing(sqlite3.connect(self.fixture.db)) as db:
            for name, value in actual['tables'].items():
                expected = hashlib.sha256(json.dumps(db.execute(f'SELECT * FROM "{name}" ORDER BY rowid').fetchall(),
                    sort_keys=True, ensure_ascii=False).encode()).hexdigest()
                self.assertEqual(value, expected)

    def test_owned_write_failure_latches_even_when_caller_catches_it(self):
        failure = OSError('Authored storage')
        def fail(): raise failure
        with self.assertRaises(OSError): self.checks.write(fail)
        count = self.history.call_count
        for operation in (self.checks.poll, self.checks.barrier, self.checks.finish):
            with self.assertRaises(OSError) as caught: operation()
            self.assertIs(caught.exception, failure)
        self.assertEqual(self.history.call_count, count)

    def test_history_audit_rechecks_content_inventory_database_and_tree(self):
        folder = self.fixture.root/'audit-control'
        folder.mkdir()
        path = folder/'pinned.txt'; path.write_text('original')
        baseline = database_snapshot(self.fixture.db, self.fixture.source['allowance'])
        baseline['artifacts'] = {'audit-control/pinned.txt': sha(path)}
        tree = Mock()
        audit = HistoryAudit(root=self.fixture.root, database=self.fixture.db, baseline=baseline,
            allowance=self.fixture.source['allowance'], ceiling=.1, rows=lambda: [], tree=tree,
            inventories=[(folder, {'pinned.txt'})])
        audit()
        # Matching size and restored mtime cannot bypass real content reads.
        import os
        stamp = path.stat()
        path.write_text('modified')
        os.utime(path, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
        with self.assertRaises(CheckpointFailure): audit()
        path.write_text('original')
        (folder/'unexpected').mkdir()
        with self.assertRaises(EvaluationStopped): audit()
        (folder/'unexpected').rmdir()
        self.fixture.original.reserve_ai_allowance(self.fixture.source['allowance'], 'foreign', .001, 10)
        with self.assertRaises(EvaluationStopped): audit()
        tree.side_effect = EvaluationStopped('Authored Git tree change')
        with self.assertRaises(EvaluationStopped): audit()

    def test_lease_loss_after_claim_stops_before_any_reservation(self):
        def changed(stage, owner):
            if stage == 'claim': owner.leases[1].release()
        with self.assertRaises(EvaluationStopped): self.owned(observe=changed)
        self.assertEqual(self.opens, 0)
        self.assertFalse((self.workspace/'evidence/reservation-01.json').exists())

    def test_identity_failure_after_reservation_stops_before_open(self):
        def identity(*, force=False):
            if force and (self.fixture.root/'cadence-owned/evidence/reservation-01.json').exists():
                raise EvaluationStopped('Authored changed account')
        with self.assertRaises(EvaluationStopped): self.owned(identity=identity)
        self.assertEqual(self.opens, 0)
        self.assertTrue((self.workspace/'evidence/reservation-01.json').exists())

    def test_history_failure_before_finalization_cannot_mint_success_seal(self):
        def history():
            if (self.fixture.root/'cadence-owned/evidence/summary.json').exists():
                raise EvaluationStopped('Authored final history failure')
        with self.assertRaises(EvaluationStopped): self.owned(history=history)
        self.assertFalse((self.workspace/'evidence/owned-artifacts.json').exists())

    def test_history_failure_after_staging_cannot_publish_success_seal(self):
        primary = EvaluationStopped('Authored final history failure after staging')
        def history():
            if (self.fixture.root/'cadence-owned/evidence/owned-artifacts.provisional.json').exists():
                raise primary
        with self.assertRaises(EvaluationStopped) as caught:
            self.owned(history=history, case_limit=1)
        self.assertIs(caught.exception, primary)
        out = self.workspace/'evidence'
        self.assertTrue((out/'owned-artifacts.provisional.json').exists())
        self.assertFalse((out/'owned-artifacts.json').exists())
        self.assertFalse(load(out/'failure.json')['sealed'])
        self.assertEqual(database_snapshot(self.workspace/'authored-ledger.sqlite3',
                         self.fixture.source['allowance'])['reservations'], 2)
        with self.assertRaises(FileExistsError): self.owned()
        self.assertEqual(self.opens, 0)

    def test_staged_seal_mutation_is_audited_before_publication(self):
        def changed(stage, owner):
            provisional = owner.out/'owned-artifacts.provisional.json'
            if stage == 'history' and provisional.exists():
                provisional.write_text('Authored damaged provisional seal')
        with self.assertRaises(EvaluationStopped): self.owned(observe=changed, case_limit=1)
        out = self.workspace/'evidence'
        self.assertFalse((out/'owned-artifacts.json').exists())
        self.assertFalse(load(out/'failure.json')['sealed'])

    def test_seal_publication_failure_keeps_scope_failed(self):
        primary = OSError('Authored seal publication failure')
        with patch.object(Path, 'rename', side_effect=primary) as publish:
            with self.assertRaises(OSError) as caught: self.owned(case_limit=1)
        self.assertIs(caught.exception, primary)
        publish.assert_called_once()
        out = self.workspace/'evidence'
        self.assertTrue((out/'owned-artifacts.provisional.json').exists())
        self.assertFalse((out/'owned-artifacts.json').exists())
        self.assertFalse(load(out/'failure.json')['sealed'])

    def test_clock_exception_has_missing_timing_and_cannot_replace_guard_primary(self):
        primary = OSError('Authored guard')
        clock = Mock(side_effect=[0, RuntimeError('Authored damaged clock')])
        timing = reader.StreamTiming(clock)
        with self.assertRaises(OSError) as caught:
            timing.measure('opening', lambda: (_ for _ in ()).throw(primary))
        self.assertIs(caught.exception, primary)
        self.assertFalse(timing.snapshot(primary)['clock_valid'])
        self.assertIsNone(timing.snapshot(primary)['opening_seconds'])

    def test_config_changed_by_last_body_read_cannot_be_reanchored(self):
        last = self.manifest['requests'][-1]['native_body']
        calls = 0
        def read(name):
            nonlocal calls
            if name == last:
                calls += 1
                if calls == 2: self.fixture.provider.model = 'changed-at-final-bind'
            return self.fixture.files[name]
        with self.assertRaises(EvaluationStopped): self.owned(read=read)
        self.assertEqual(self.opens, 0)
        self.assertFalse((self.workspace/'evidence/attempt-01.json').exists())

    def test_identity_callback_config_change_at_final_poll_blocks_open(self):
        forces, pending = 0, False
        def identity(*, force=False):
            nonlocal forces, pending
            if force:
                forces += 1
                pending = forces == 2
            elif pending:
                self.fixture.provider.model = 'changed-at-last-immediate-guard'
                pending = False
        with self.assertRaises(EvaluationStopped): self.owned(identity=identity)
        self.assertEqual(self.opens, 0)
        self.assertTrue((self.workspace/'evidence/reservation-01.json').exists())
