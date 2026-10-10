"""Authored live-wiring controls; only isolated databases and fake transports."""
import copy
from contextlib import closing
import hashlib
import importlib
import json
import sqlite3
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from scripts import missing_link_operation_owned as owned
from scripts import missing_link_operation_run as runner
from scripts.missing_link_cadence_owned import OwnedEvidence
from scripts.missing_link_checkpoint_cadence import FilePin, CheckpointFailure
from scripts.missing_link_database_audit import ContentVerifiedSnapshot, database_snapshot
from scripts.missing_link_repository_only_evaluator import EvaluationStopped
from scripts.missing_link_repository_only_run import load, save, sha
from test_missing_link_demand_operation_policy import unknown
import test_missing_link_demand_operation_policy_v3_executor as authored_v3
from test_missing_link_repository_only_evaluator import terminal
from test_missing_link_stream_successor_receipts import Clock, Stream


class OperationRunTests(unittest.TestCase):
    def setUp(self):
        self.fixture = authored_v3.PolicyV3ExecutorTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        f = self.fixture
        self.root, self.out = f.root, f.root/'operation-scope'
        self.out.mkdir()
        self.addCleanup(patch.stopall)
        patch.object(runner, 'ROOT', self.root).start()
        patch('socket.socket', side_effect=AssertionError('Authored tests cannot use sockets')).start()
        self.credentials = patch.object(runner, 'provider_environment',
            side_effect=AssertionError('Authored tests cannot read credentials')).start()
        self.clock, self.opens, self.streams = Clock(), 0, []
        self.tree, self.identity = Mock(), Mock()
        source = copy.deepcopy(f.source)
        source['semantic_policy_revision'] = 3
        self.source = runner.operation_source(source)
        self.before = database_snapshot(f.db, runner.ALLOWANCE)
        self.before['artifacts'] = {p.relative_to(self.root).as_posix(): sha(p) for p in f.prep.iterdir()}
        code = self.root/'code.txt'
        self.compiled = {'source': source, 'root': self.root, 'baseline': self.before,
            'code_pins': (FilePin(code, sha(code, canonical=True), True),),
            'database_audit': ContentVerifiedSnapshot(f.db, runner.ALLOWANCE),
            'audit': SimpleNamespace(inventories=((f.prep, {p.name for p in f.prep.iterdir()}),))}
        save(self.out, 'baseline.json', self.before)
        self.manifest = runner.freeze_values(self.compiled, head='a'*40, tree='b'*40,
            reviewed_head='c'*40, baseline_sha=sha(self.out/'baseline.json'))
        save(self.out, 'prepared.json', self.manifest)
        self.anchor = sha(self.out/'prepared.json')
        self.authorization = runner.authorization_scope(self.anchor, self.manifest)

    def execute(self, *, on_read=lambda: None, lines=None, approved=None):
        f = self.fixture
        opener = Mock()
        def open_response(*args, **kwargs):
            self.opens += 1
            self.assertEqual(kwargs['timeout'], 55)
            stream = Stream(lines or [b'data: '+json.dumps(terminal(unknown())).encode()+b'\n'],
                            self.clock, 0, on_read)
            self.streams.append(stream)
            return stream
        opener.open.side_effect = open_response
        return owned.run_bound_owned(self.out, manifest=self.manifest, anchor=self.anchor,
            source=self.source, authorization=self.authorization if approved is None else approved,
            provider=f.provider, packets=f.packets, read=f.files.__getitem__, database=f.db,
            account=runner.ACCOUNT, allowance=runner.ALLOWANCE, ceiling=runner.CEILING,
            compiled=self.compiled, tree=self.tree, identity=self.identity,
            opener_factory=lambda: opener, clock=self.clock)

    def mutate_db(self, statement, args=()):
        with closing(sqlite3.connect(self.fixture.db)) as db:
            db.execute(statement, args)
            db.commit()

    def assert_stopped(self, opens=1):
        self.assertEqual(self.opens, opens)
        self.assertFalse((self.out/'attempt-02.json').exists())
        self.assertFalse((self.out/'owned-artifacts.json').exists())
        self.assertTrue((self.out/'failure.json').exists())

    def test_all_eleven_calls_use_original_atomic_store_and_seal_only_at_end(self):
        with patch.object(owned.Store, '__init__', side_effect=AssertionError('No constructor DDL')):
            result = self.execute()
        self.assertEqual(self.opens, 11)
        self.assertEqual(len(result['results']), 11)
        self.assertEqual(result['receipt_manifest_sha256'], sha(self.out/'owned-artifacts.json'))
        after = database_snapshot(self.fixture.db, runner.ALLOWANCE)
        self.assertEqual(after['reservation_rows'][:1], self.before['reservation_rows'])
        self.assertEqual([r[2] for r in after['reservation_rows'][1:]], self.authorization['job_ids'])
        for name, value in self.before['tables'].items():
            if name not in {'ml_ai_reservations', 'ml_ai_allowances'}:
                self.assertEqual(after['tables'][name], value)
        self.assertEqual(load(self.out/'summary.json')['unattempted'], [])
        self.assertEqual([s.close_calls for s in self.streams], [1]*11)
        self.credentials.assert_not_called()
        with self.assertRaises(EvaluationStopped): self.execute()
        self.assertEqual(self.opens, 11)

    def test_native_cleanup_mutation_blocks_accounting_and_next_attempt(self):
        exit_stream = Stream.__exit__
        def cleanup(stream, *args):
            result = exit_stream(stream, *args)
            self.mutate_db('INSERT INTO ml_cache VALUES (?, ?, ?)', ('foreign', 1, '{}'))
            return result
        with patch.object(Stream, '__exit__', cleanup):
            with self.assertRaises(EvaluationStopped): self.execute()
        self.assert_stopped()
        self.assertFalse((self.out/'checkpoint-01-002.json').exists())

    def test_foreign_reservation_inside_account_unit_is_detected_at_next_commit(self):
        save_owned = OwnedEvidence.save
        def saving(owner, name, value):
            save_owned(owner, name, value)
            if name == 'checkpoint-01-002.json':
                self.fixture.original.reserve_ai_allowance(runner.ALLOWANCE, 'foreign', .001, 10)
        with patch.object(OwnedEvidence, 'save', saving):
            with self.assertRaises(EvaluationStopped): self.execute()
        self.assert_stopped()
        self.assertFalse((self.out/'checkpoint-01-003.json').exists())

    def test_identity_change_between_account_writes_stops_the_cohort(self):
        save_owned = OwnedEvidence.save
        def saving(owner, name, value):
            save_owned(owner, name, value)
            if name == 'checkpoint-01-002.json': self.mutate_db('UPDATE ml_identity SET account=?', ('other',))
        with patch.object(OwnedEvidence, 'save', saving):
            with self.assertRaises(EvaluationStopped): self.execute()
        self.assert_stopped()
        self.assertFalse((self.out/'checkpoint-01-003.json').exists())

    def test_failed_journal_persistence_keeps_charge_and_never_opens_transport(self):
        save_owned, primary = OwnedEvidence.save, OSError('Authored journal failure')
        def saving(owner, name, value):
            if name == 'reservation-01.json': raise primary
            save_owned(owner, name, value)
        with patch.object(OwnedEvidence, 'save', saving):
            with self.assertRaises(OSError) as caught: self.execute()
        self.assertIs(caught.exception, primary)
        self.assert_stopped(0)
        self.assertEqual(database_snapshot(self.fixture.db, runner.ALLOWANCE)['reservations'], 2)

    def test_historical_file_change_before_native_retention_blocks_acceptance(self):
        def changed(): (self.fixture.prep/'inputs.json').write_text('{}', encoding='utf-8')
        with self.assertRaises(CheckpointFailure): self.execute(on_read=changed)
        self.assert_stopped()
        self.assertFalse((self.out/'terminal-01.json').exists())

    def test_final_provisional_receipt_tamper_never_promotes_success(self):
        save_owned = OwnedEvidence.save
        def saving(owner, name, value):
            save_owned(owner, name, value)
            if name == 'owned-artifacts.provisional.json': (owner.out/name).write_bytes(b'{}')
        with patch.object(OwnedEvidence, 'save', saving):
            with self.assertRaises(EvaluationStopped): self.execute()
        self.assertEqual(self.opens, 11)
        self.assertFalse((self.out/'owned-artifacts.json').exists())

    def test_atomic_ceiling_cannot_be_relaxed_by_approval_or_callback(self):
        approved = dict(self.authorization, atomic_cumulative_ceiling_usd=10)
        with self.assertRaises(EvaluationStopped): self.execute(approved=approved)
        self.assertEqual(self.opens, 0)
        self.assertEqual(database_snapshot(self.fixture.db, runner.ALLOWANCE)['reservations'], 1)

    def test_original_atomic_ceiling_stops_before_opening_an_over_budget_request(self):
        self.fixture.original.reserve_ai_allowance(runner.ALLOWANCE, 'authored-cap-prior', 8.1398513, 10)
        before = database_snapshot(self.fixture.db, runner.ALLOWANCE)
        before['artifacts'] = dict(self.before['artifacts'])
        self.compiled['baseline'] = before
        (self.out/'baseline.json').write_text(json.dumps(before), encoding='utf-8')
        self.manifest['baseline_sha256'] = sha(self.out/'baseline.json')
        (self.out/'prepared.json').write_text(json.dumps(self.manifest), encoding='utf-8')
        self.anchor = sha(self.out/'prepared.json')
        self.authorization = runner.authorization_scope(self.anchor, self.manifest)
        with self.assertRaises(ValueError): self.execute()
        self.assert_stopped(0)
        self.assertEqual(database_snapshot(self.fixture.db, runner.ALLOWANCE)['reservations'], 2)

    def test_new_active_job_blocks_the_next_accounting_commit(self):
        save_owned = OwnedEvidence.save
        def saving(owner, name, value):
            save_owned(owner, name, value)
            if name == 'checkpoint-01-002.json':
                self.mutate_db('INSERT INTO ml_jobs VALUES (?, ?)', ('foreign', json.dumps({'id': 'foreign', 'status': 'running'})))
        with patch.object(OwnedEvidence, 'save', saving):
            with self.assertRaises(EvaluationStopped): self.execute()
        self.assert_stopped()
        self.assertFalse((self.out/'checkpoint-01-003.json').exists())

    def test_prefix_rejects_prior_row_changes(self):
        self.mutate_db('UPDATE ml_ai_reservations SET created=created+1')
        with self.assertRaises(EvaluationStopped):
            owned.verify_owned_prefix(self.fixture.db, self.before, [], account=runner.ACCOUNT,
                allowance=runner.ALLOWANCE, ceiling=runner.CEILING)

    def test_accounting_id_reuse_is_rejected_even_for_completed_jobs(self):
        job_id = self.authorization['job_ids'][0]
        self.mutate_db('INSERT INTO ml_jobs VALUES (?, ?)', (job_id, json.dumps({'id': job_id, 'status': 'completed'})))
        with self.assertRaises(EvaluationStopped): owned.unused_job_ids(self.fixture.db, [job_id])

    def test_missing_or_changed_authorization_precedes_credentials_and_execution(self):
        self.fixture.out.joinpath('authorization.json').write_text('{}', encoding='utf-8')
        approval = self.fixture.out/'authorization.json'
        with patch.object(runner, 'frozen', return_value=(self.manifest, self.compiled)), \
                patch.object(runner, 'run_bound_owned') as execute:
            for path in (None, approval):
                with self.assertRaises(EvaluationStopped): runner.run(self.out, self.anchor, path)
            for field, value in (('calls', True), ('prepared_manifest_sha256', 'd'*64),
                    ('required_main', 'd'*40), ('segment_cap_usd', .2), ('native_sha256', [])):
                approval.write_text(json.dumps(dict(self.authorization, **{field: value})), encoding='utf-8')
                with self.assertRaises(EvaluationStopped): runner.run(self.out, self.anchor, approval)
            execute.assert_not_called()
        self.credentials.assert_not_called()

    def test_authorized_facade_binds_live_provider_before_constructing_execution(self):
        approval = self.fixture.out/'authorization.json'
        approval.write_text(json.dumps(self.authorization), encoding='utf-8')
        with patch.object(runner, 'frozen', return_value=(self.manifest, self.compiled)), \
                patch.object(runner, 'provider_environment', return_value=dict(self.fixture.env)), \
                patch.object(runner, 'consumed', SimpleNamespace(PREP=self.fixture.prep)), \
                patch.object(runner, 'run_bound_owned', return_value={}) as execute:
            runner.run(self.out, self.anchor, approval)
            self.assertEqual(execute.call_count, 1)
            self.assertNotIn('case_limit', execute.call_args.kwargs)
        self.assertEqual(self.opens, 0)

    def test_new_modules_import_without_credentials_files_network_or_threads(self):
        with patch('pathlib.Path.open', side_effect=AssertionError('Import IO forbidden')), \
                patch('subprocess.run', side_effect=AssertionError('Import process forbidden')), \
                patch('threading.Thread.start', side_effect=AssertionError('Import thread forbidden')):
            importlib.reload(owned)
            importlib.reload(runner)

    def git(self, *args):
        if args == ('rev-parse', self.manifest['reviewed_head']+'^{tree}'): return self.manifest['reviewed_tree']
        raise AssertionError('Unexpected authored Git call: '+str(args))

    def test_frozen_checks_independent_anchor_baseline_code_and_concrete_scope(self):
        with patch.object(runner, 'owned_path'), patch.object(runner, 'execution_tree'), \
                patch.object(runner, 'compiled_history', return_value=self.compiled), \
                patch.object(runner, 'public_bind'), patch.object(runner, 'unused_job_ids'), \
                patch.object(runner, 'git', self.git):
            runner.frozen(self.out, self.anchor)
            for anchor in (None, 'd'*64, True):
                with self.assertRaises(EvaluationStopped): runner.frozen(self.out, anchor)
            for field, value in (('segment_cap_usd', .2), ('call_authorization_granted', True),
                                 ('code_sha256_canonical_lf', {})):
                raw = json.dumps(dict(self.manifest, **{field: value})).encode()
                (self.out/'prepared.json').write_bytes(raw)
                with self.assertRaises(EvaluationStopped):
                    runner.frozen(self.out, hashlib.sha256(raw).hexdigest())
        self.credentials.assert_not_called()

    def test_execution_tree_rejects_changed_origin_dirty_branch_and_tree(self):
        values = {('rev-parse', 'HEAD', 'HEAD^{tree}', 'origin/main'): '\n'.join(['a'*40, 'b'*40, 'a'*40]),
                  ('branch', '--show-current'): 'main', ('status', '--porcelain'): ''}
        with patch.object(runner, 'git', side_effect=lambda *args: values[args]):
            runner.execution_tree('a'*40, 'b'*40)
            for args, value in ((('branch', '--show-current'), 'other'),
                    (('status', '--porcelain'), ' M changed.py'),
                    (('rev-parse', 'HEAD', 'HEAD^{tree}', 'origin/main'), '\n'.join(['a'*40, 'b'*40, 'c'*40]))):
                old = values[args]
                values[args] = value
                with self.assertRaises(EvaluationStopped): runner.execution_tree('a'*40, 'b'*40)
                values[args] = old

    def test_prepare_exclusively_freezes_zero_call_scope_without_credentials(self):
        out = self.root/'prospective-freeze'
        compiled = dict(self.compiled, baseline=dict(self.before, reservations=579, reserved_usd=runner.BASE_RESERVED))
        def git(*args):
            return {'HEAD': 'a'*40, 'HEAD^{tree}': 'b'*40, 'c'*40+'^{tree}': 'b'*40}.get(args[-1], '')
        with patch.object(runner, 'owned_path'), patch.object(runner, 'execution_tree'), \
                patch.object(runner, 'compiled_history', return_value=compiled), \
                patch.object(runner, 'public_bind') as bind, patch.object(runner, 'DB', self.fixture.db), \
                patch.object(runner, 'git', git):
            result = runner.prepare(out, 'c'*40)
            self.assertEqual(result['prepared_manifest_sha256'], sha(out/'prepared.json'))
            self.assertFalse(load(out/'prepared.json')['call_authorization_granted'])
            self.assertEqual(result['new_calls'], 0)
            bind.assert_called_once()
            with self.assertRaises(EvaluationStopped): runner.prepare(out, 'c'*40)
        self.credentials.assert_not_called()
        self.assertEqual(database_snapshot(self.fixture.db, runner.ALLOWANCE)['reservations'], 1)

    def test_lease_cleanup_failure_never_issues_a_success_receipt(self):
        release = owned.WorkerLease.release
        primary = OSError('Authored lease cleanup failure')
        def failing(lease):
            release(lease)
            raise primary
        with patch.object(owned.WorkerLease, 'release', failing):
            with self.assertRaises(OSError) as caught: self.execute()
        self.assertIs(caught.exception, primary)
        self.assertFalse((self.out/'owned-artifacts.json').exists())
        self.assertTrue((self.out/'owned-artifacts.rejected.json').exists())

    def test_lease_cleanup_error_cannot_replace_primary_execution_failure(self):
        release = owned.WorkerLease.release
        primary = OSError('Authored start persistence failure')
        save_owned = OwnedEvidence.save
        def saving(owner, name, value):
            if name == 'started.json': raise primary
            save_owned(owner, name, value)
        def failing(lease):
            release(lease)
            raise OSError('Authored secondary cleanup failure')
        with patch.object(owned.WorkerLease, 'release', failing), patch.object(OwnedEvidence, 'save', saving):
            with self.assertRaises(OSError) as caught: self.execute()
        self.assertIs(caught.exception, primary)
        self.assert_stopped(0)

    def test_rejected_output_lease_cannot_write_into_another_owners_evidence(self):
        def rejected(lease):
            lease.path.write_bytes(b'0')
            return False
        with patch.object(owned.WorkerLease, 'acquire', rejected):
            with self.assertRaises(EvaluationStopped): self.execute()
        self.assertEqual(self.opens, 0)
        self.assertFalse((self.out/'failure.json').exists())
        self.assertFalse((self.out/'started.json').exists())


if __name__ == '__main__':
    unittest.main()
