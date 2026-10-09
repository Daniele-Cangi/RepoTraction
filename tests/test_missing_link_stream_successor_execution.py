"""Authored owned successor lifecycle; temporary DB/history and mocked IO only."""
import copy
from contextlib import closing
import json
from pathlib import Path
import subprocess
import sqlite3
import sys
import unittest
from unittest.mock import patch

from missing_link.service import Cancelled
from github_cli import ActiveAccountChangedError
from scripts import missing_link_stream_successor_executor as executor
from scripts import missing_link_stream_successor_run as runner
from scripts import missing_link_demand_operation_policy_v3_executor as v3
from scripts.missing_link_repository_only_evaluator import EvaluationStopped
from test_missing_link_demand_operation_policy import unknown
import test_missing_link_demand_operation_policy_v3_executor as authored_v3
from test_missing_link_repository_only_evaluator import Stream, terminal
from test_missing_link_stream_successor_receipts import Clock


class StreamSuccessorExecutionTests(unittest.TestCase):
    def setUp(self):
        # Reuse authored predecessor seals/packets without inheriting its tests.
        self.fixture = authored_v3.PolicyV3ExecutorTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        f = self.fixture
        self.root, self.stack, self.provider = f.root, f.stack, f.provider
        self.prep, self.out = self.root/'stream-prep', self.root/runner.OWNED_RELATIVE
        self.prep.mkdir(); self.out.mkdir(parents=True)
        self.source = copy.deepcopy(f.source)
        self.source.update(semantic_policy_revision=3, transport_revision='stream_successor_1',
            status='offline_only_no_stream_successor_executor', source_preparation_sha256=runner.predecessor.PREP_SHA,
            atomic_cumulative_ceiling_usd=runner.CEILING, **executor.STREAM_SETTINGS)
        for number, row in enumerate(self.source['requests'],1):
            row['job_id'] = executor.JOB_PREFIX+f'{number:02}'
        for name in ('inputs.json',): (self.prep/name).write_bytes((f.prep/name).read_bytes())
        (f.prep/'references.json').write_text('{}')
        # The predecessor seal was already made: add reference to its authored seal.
        f.source['owned_files_sha256']['references.json'] = runner.sha(f.prep/'references.json')
        (f.prep/'prepared.json').write_text(json.dumps(f.source))
        self.stack.enter_context(patch.object(runner.predecessor,'PREP_SHA',runner.sha(f.prep/'prepared.json')))
        self.source['source_preparation_sha256'] = runner.predecessor.PREP_SHA
        (self.prep/'references.json').write_bytes((f.prep/'references.json').read_bytes())
        for name, raw in f.files.items(): (self.prep/name).write_bytes(raw)
        (self.prep/'protocol.md').write_bytes(f.protocol.read_bytes())
        diagnostic = self.root/'docs/missing-link-policy-v3-stream-diagnostics-2026-10-09.md'
        diagnostic.parent.mkdir(parents=True); diagnostic.write_text('Authored diagnostic report')
        protected = dict(f.before['artifacts'])
        protected.update({p.relative_to(self.root).as_posix():runner.sha(p) for p in f.prep.iterdir()})
        for relative, prepared_key, receipt_key in runner.HISTORIES[4:]:
            folder = self.root/relative; folder.mkdir(parents=True)
            runner.save(folder,'prepared.json',{'authored':'consumed'})
            runner.save(folder,'evidence.json',{'authored':'private'})
            runner.save(folder,'owned-artifacts.json',{p.name:runner.sha(p) for p in folder.iterdir()})
            self.source['historical_anchors'][prepared_key] = runner.sha(folder/'prepared.json')
            self.source['historical_anchors'][receipt_key] = runner.sha(folder/'owned-artifacts.json')
            protected.update({p.relative_to(self.root).as_posix():runner.sha(p) for p in folder.iterdir()})
        baseline = runner.snapshot({'artifacts':protected})
        runner.save(self.prep,'baseline.json',baseline)
        self.source.update(protocol_sha256_lf=runner.sha(f.protocol,canonical=True),
            diagnostic_report_sha256_lf=runner.sha(diagnostic,canonical=True),
            inputs_sha256=runner.sha(self.prep/'inputs.json'),
            references_sha256_lf=runner.sha(self.prep/'references.json',canonical=True),
            baseline_sha256=runner.sha(self.prep/'baseline.json'))
        self.source['owned_files_sha256'] = {p.name:runner.sha(p) for p in self.prep.iterdir()}
        runner.save(self.prep,'prepared.json',self.source)
        (self.root/'adapter.txt').write_text('Authored separate adapter')
        for key,value in {'ROOT':self.root,'PREP':self.prep,'PREP_SHA':runner.sha(self.prep/'prepared.json'),
                'PROTOCOL':f.protocol,'PROTOCOL_SHA':self.source['protocol_sha256_lf'],
                'DB':f.db,'ADAPTERS':('adapter.txt',),'EXISTING_CODE':1,
                'HISTORY_ARTIFACTS':len(protected),'BASE_RESERVATIONS':1,'BASE_RESERVED':.10}.items():
            self.stack.enter_context(patch.object(runner,key,value))
        protected.update({p.relative_to(self.root).as_posix():runner.sha(p) for p in self.prep.iterdir()})
        self.before = runner.snapshot({'artifacts':protected})
        runner.save(self.out,'baseline.json',self.before)
        self.owned = {'required_main':'a'*40,'reviewed_head':'a'*40,'reviewed_tree':'a'*40,
            'owned_output':runner.OWNED_RELATIVE,
            'baseline_sha256':runner.sha(self.out/'baseline.json'), 'preparation_sha256':runner.PREP_SHA,
            'protocol_sha256_lf':runner.PROTOCOL_SHA,'new_calls':0,'new_reservations':0,
            'code_sha256_canonical_lf':dict(self.source['code_sha256_canonical_lf'],
                                          **{'adapter.txt':runner.sha(self.root/'adapter.txt',canonical=True)})}
        runner.save(self.out,'prepared.json',self.owned)
        self.anchor = runner.sha(self.out/'prepared.json')
        self.authorization = self.root/'stream-authorization.json'
        runner.save(self.root,self.authorization.name,runner.authorization_scope(self.anchor,self.source))
        self.environment = self.stack.enter_context(patch.object(runner,'provider_environment',return_value=f.env))
        self.identity = self.stack.enter_context(patch.object(runner,'verify_cli_account',return_value=runner.ACCOUNT))
        def git(*args):
            if args == ('branch','--show-current'): return 'main'
            if args and args[0] == 'rev-parse': return 'a'*40
            return ''
        self.git = self.stack.enter_context(patch.object(runner,'git',side_effect=git))
        self.stack.enter_context(patch('socket.socket',side_effect=AssertionError('No real sockets')))
        self.opener = f.opener

    def slots(self):
        return executor.verify_requests(self.provider,self.fixture.packets,self.source,
                                       lambda name:(self.prep/name).read_bytes())

    def run_owned(self): runner.run(self.out,self.anchor,self.authorization)

    def test_success_retains_native_diagnostics_and_exact_prefix_blocks_replay(self):
        self.run_owned()
        self.assertEqual(self.opener.return_value.open.call_count,11)
        trace = runner.load(self.out/'diagnostics-01.json')
        self.assertTrue(trace['reservation_committed']); self.assertTrue(trace['terminal_retained'])
        self.assertIsNone(trace['failure'])
        self.assertEqual(runner.load(self.out/'terminal-01.json'),terminal(unknown()))
        after = runner.snapshot(self.before)
        self.assertEqual(after['reservation_rows'][:1],self.before['reservation_rows'])
        for table in self.before['tables']:
            if table not in {'ml_ai_allowances','ml_ai_reservations'}:
                self.assertEqual(after['tables'][table],self.before['tables'][table])
        runner.verify(self.out,self.anchor,runner.sha(self.out/'owned-artifacts.json'))
        with self.assertRaises(EvaluationStopped): self.run_owned()
        self.assertEqual(self.opener.return_value.open.call_count,11)

    def test_timeout_keeps_one_reservation_and_typed_absence_stops_all_remaining(self):
        self.opener.return_value.open.side_effect = TimeoutError('PRIVATE')
        with self.assertRaises(EvaluationStopped): self.run_owned()
        self.assertEqual(self.opener.return_value.open.call_count,1)
        trace = runner.load(self.out/'diagnostics-01.json')
        self.assertEqual(trace['failure']['code'],'ai_transport_timeout')
        self.assertTrue(trace['reservation_committed']); self.assertIsNone(trace['terminal_retained'])
        self.assertIsNone(trace['lines']); self.assertNotIn('PRIVATE',json.dumps(trace))
        self.assertFalse((self.out/'attempt-02.json').exists())
        self.assertEqual(runner.load(self.out/'summary.json')['unattempted'],list(range(2,12)))
        runner.verify(self.out,self.anchor,runner.sha(self.out/'owned-artifacts.json'))

    def test_native_schema_failure_is_global_after_receipt_and_telemetry(self):
        self.opener.return_value.open.side_effect = lambda *a,**k:Stream(terminal({'wrong':'shape'}))
        with self.assertRaises(EvaluationStopped): self.run_owned()
        self.assertEqual(self.opener.return_value.open.call_count,1)
        self.assertTrue(runner.load(self.out/'diagnostics-01.json')['terminal_retained'])
        self.assertFalse((self.out/'result-01.json').exists())

    def test_missing_native_usage_keeps_one_charge_and_receipt_without_result_or_continuation(self):
        native = terminal(unknown())
        del native['response']['usage']
        self.opener.return_value.open.side_effect = lambda *a,**k:Stream(native)
        with self.assertRaises(EvaluationStopped): self.run_owned()
        self.assertEqual(self.opener.return_value.open.call_count,1)
        self.assertEqual(runner.load(self.out/'terminal-01.json'),native)
        trace = runner.load(self.out/'diagnostics-01.json')
        self.assertTrue(trace['terminal_retained']); self.assertTrue(trace['reservation_committed'])
        self.assertEqual(trace['failure'],{'category':'candidate_validation'})
        summary = runner.load(self.out/'summary.json')
        self.assertEqual(summary['results'],[])
        self.assertEqual(summary['failure'],{'diagnostic':{'category':'candidate_validation'},'stopped_slot':1})
        self.assertEqual(summary['unattempted'],list(range(2,12)))
        self.assertFalse((self.out/'result-01.json').exists())
        self.assertFalse((self.out/'attempt-02.json').exists())
        for path in self.out.glob('checkpoint-*.json'):
            job = runner.load(path)
            self.assertNotIn('reported_usage',job)
            self.assertNotIn('ai_trace',job)
            self.assertNotIn('ai_outputs',job['checkpoint'])
        after = runner.snapshot(self.before)
        self.assertEqual(after['reservations'],self.before['reservations']+1)
        self.assertGreater(after['reserved_usd'],self.before['reserved_usd'])
        # A closed failed-run receipt records absence; it does not mark success.
        runner.verify(self.out,self.anchor,runner.sha(self.out/'owned-artifacts.json'))
        with self.assertRaises(EvaluationStopped): self.run_owned()
        self.assertEqual(self.opener.return_value.open.call_count,1)

    def test_post_schema_local_rejection_continues_once_without_output_repair(self):
        invalid = unknown(); invalid['fields']['runtime']['text'] = 'Authored unsupported guess'
        self.opener.return_value.open.side_effect = [Stream(terminal(invalid))]+[Stream(terminal(unknown())) for _ in range(10)]
        self.run_owned()
        result = runner.load(self.out/'result-01.json')
        self.assertEqual(result['prediction'],invalid)
        self.assertEqual(result['disposition'],'local_rejection')
        self.assertEqual(self.opener.return_value.open.call_count,11)

    def test_changed_raw_during_local_normalization_cannot_continue(self):
        def mutate(raw,*args,**kwargs):
            raw['context_gaps'].append('Authored mutation')
            raise ValueError('Authored local-looking error')
        with patch.object(v3,'normalize_prediction',side_effect=mutate), self.assertRaises(EvaluationStopped):
            self.run_owned()
        self.assertEqual(self.opener.return_value.open.call_count,1)
        self.assertFalse((self.out/'attempt-02.json').exists())

    def test_global_standalone_schema_error_never_enters_normalizer(self):
        with patch.object(v3,'normalize_prediction') as normalize, self.assertRaises(ValueError):
            v3.check_prediction({'wrong':'shape'},self.slots()[0],lambda:None)
        normalize.assert_not_called()

    def test_new_scope_settings_configuration_types_and_native_hash_are_bound(self):
        changes = [lambda m:m['requests'][0].update(slot=True),
            lambda m:m['requests'][0].update(job_id='demand-operation-policy-v3-owned-2026-10-09-01'),
            lambda m:m['requests'][0].update(native_sha256='0'*64),
            lambda m:m['config_without_key'].update(max_calls=True),
            lambda m:m.update(full_checkpoint_nonterminal_lines=True),
            lambda m:m.update(wall_stream_deadline_seconds=601),
            lambda m:m.update(semantic_policy_revision=True)]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(EvaluationStopped):
                modified=copy.deepcopy(self.source); change(modified)
                executor.verify_requests(self.provider,self.fixture.packets,modified,lambda name:(self.prep/name).read_bytes())
        self.opener.assert_not_called()

    def test_boolean_scope_and_wrong_authorization_fail_before_keys_or_start(self):
        scope=runner.load(self.authorization); scope['stream_settings']['full_checkpoint_nonterminal_lines']=True
        self.authorization.write_text(json.dumps(scope))
        with self.assertRaises(EvaluationStopped): self.run_owned()
        self.environment.assert_not_called(); self.identity.assert_not_called()
        self.assertFalse((self.out/'started.json').exists()); self.opener.assert_not_called()

    def test_older_execution_tree_dirty_code_and_wrong_anchor_fail_before_payment(self):
        with patch.object(runner,'execution_tree',side_effect=EvaluationStopped('Authored later tree')), self.assertRaises(EvaluationStopped):
            self.run_owned()
        self.environment.assert_not_called(); self.opener.assert_not_called()
        with self.assertRaises(EvaluationStopped): runner.run(self.out,'0'*64,self.authorization)

    def test_prepare_is_key_free_exclusive_and_binds_all_adapters(self):
        other=self.root/'new-freeze'
        with patch.object(runner,'OWNED_RELATIVE','new-freeze'):
            runner.prepare(other,'a'*40)
        manifest=runner.load(other/'prepared.json')
        self.assertEqual(set(manifest['code_sha256_canonical_lf']),{'code.txt','adapter.txt'})
        self.assertEqual(runner.snapshot(self.before),self.before)
        self.environment.assert_not_called(); self.identity.assert_not_called(); self.opener.assert_not_called()
        with patch.object(runner,'OWNED_RELATIVE','new-freeze'), self.assertRaises(EvaluationStopped):
            runner.prepare(other,'a'*40)

    def test_held_database_lease_blocks_start_and_reservation(self):
        lease=runner.WorkerLease(self.fixture.db)
        self.assertTrue(lease.acquire())
        try:
            with self.assertRaises(EvaluationStopped): self.run_owned()
        finally: lease.release()
        self.assertFalse((self.out/'started.json').exists()); self.opener.assert_not_called()
        self.assertEqual(runner.snapshot(self.before),self.before)

    def test_cancellation_after_start_consumes_without_open_or_reservation(self):
        (self.out.parent/(self.out.name+'.cancel')).write_text('authored')
        with self.assertRaises(EvaluationStopped): self.run_owned()
        self.assertTrue((self.out/'started.json').exists()); self.opener.assert_not_called()
        self.assertEqual(runner.snapshot(self.before),self.before)
        with self.assertRaises(EvaluationStopped): self.run_owned()

    def test_code_or_owned_lease_mutation_during_read_is_detected_before_retention(self):
        for target in ('code','lease'):
            with self.subTest(target=target):
                # Independent new fixture for each destructive authored mutation.
                if target == 'lease': self.doCleanups(); self.setUp()
                base = Stream(terminal(unknown()))
                leases, lease_type = [], runner.WorkerLease
                def lease_factory(path):
                    lease=lease_type(path); leases.append(lease); return lease
                def read(limit):
                    if target=='code': (self.root/'adapter.txt').write_text('Authored changed executable')
                    else: leases[0].release()
                    return next(base.lines,b'')
                base.readline=read
                self.opener.return_value.open.side_effect=lambda *a,**k:base
                with patch.object(runner,'WorkerLease',side_effect=lease_factory), self.assertRaises(EvaluationStopped):
                    self.run_owned()
                self.assertFalse((self.out/'result-01.json').exists())
                self.assertEqual(self.opener.return_value.open.call_count,1)
                self.assertFalse((self.out/'owned-artifacts.json').exists())

    def test_history_mutation_after_native_retention_never_creates_result_or_complete_seal(self):
        real_save=runner.save
        def save(folder,name,value):
            real_save(folder,name,value)
            if name=='terminal-01.json':
                with closing(sqlite3.connect(self.fixture.db)) as db, db:
                    db.execute("UPDATE ml_ai_reservations SET cost=cost+0.001 WHERE job_id='prior'")
        with patch.object(runner,'save',side_effect=save), self.assertRaises(EvaluationStopped): self.run_owned()
        self.assertTrue((self.out/'terminal-01.json').exists())
        self.assertFalse((self.out/'result-01.json').exists())
        self.assertFalse((self.out/'owned-artifacts.json').exists())
        self.assertTrue(runner.load(self.out/'diagnostics-01.json')['terminal_retained'])
        failure=runner.load(self.out/'finalization-failure.json')
        self.assertEqual(failure['primary_failure']['diagnostic']['category'],'integrity')

    def test_telemetry_write_failure_is_global_and_primary_transport_is_not_lost(self):
        self.opener.return_value.open.side_effect=TimeoutError('PRIVATE')
        real_save=runner.save
        def save(folder,name,value):
            if name=='diagnostics-01.json': raise OSError('PRIVATE')
            return real_save(folder,name,value)
        with patch.object(runner,'save',side_effect=save), self.assertRaises(EvaluationStopped): self.run_owned()
        failure=runner.load(self.out/'summary.json')['failure']['diagnostic']
        self.assertEqual(failure['category'],'telemetry_persistence')
        self.assertEqual(failure['primary']['code'],'ai_transport_timeout')
        self.assertNotIn('PRIVATE',json.dumps(failure))
        self.assertEqual(self.opener.return_value.open.call_count,1)
        self.assertFalse((self.out/'owned-artifacts.json').exists())
        self.assertTrue((self.out/'finalization-failure.json').exists())

    def test_lost_journal_keeps_committed_charge_and_cannot_seal_or_continue(self):
        real_save=runner.save
        def save(folder,name,value):
            if name=='reservation-01.json': raise OSError('Authored lost journal')
            return real_save(folder,name,value)
        with patch.object(runner,'save',side_effect=save), self.assertRaises(EvaluationStopped): self.run_owned()
        after=runner.snapshot(self.before)
        self.assertEqual(after['reservations'],2)
        self.assertGreater(after['reserved_usd'],self.before['reserved_usd'])
        self.assertFalse((self.out/'owned-artifacts.json').exists())
        self.assertFalse((self.out/'attempt-02.json').exists()); self.opener.assert_not_called()
        self.assertTrue((self.out/'finalization-failure.json').exists())

    def test_cloned_zero_call_owned_directory_cannot_reuse_scope_or_authorization(self):
        clone=self.root/'cloned-owned'; clone.mkdir()
        for path in self.out.iterdir():
            (clone/path.name).write_bytes(path.read_bytes())
        with self.assertRaises(EvaluationStopped): runner.run(clone,self.anchor,self.authorization)
        with self.assertRaises(EvaluationStopped): runner.prepare(self.root/'another-owned','a'*40)
        self.environment.assert_not_called(); self.opener.assert_not_called()

    def test_account_change_during_stream_stops_before_terminal_retention(self):
        clock=Clock()
        self.identity.side_effect=[runner.ACCOUNT,runner.ACCOUNT,ActiveAccountChangedError('Authored changed account')]
        base=Stream(terminal(unknown()))
        def read(limit):
            clock.value=4
            return next(base.lines,b'')
        base.readline=read
        self.opener.return_value.open.side_effect=lambda *a,**k:base
        with patch('scripts.missing_link_stream_successor_run.time.monotonic',side_effect=clock), self.assertRaises(EvaluationStopped):
            self.run_owned()
        self.assertFalse((self.out/'terminal-01.json').exists())
        self.assertEqual(runner.load(self.out/'diagnostics-01.json')['failure']['category'],'identity')
        self.assertEqual(self.opener.return_value.open.call_count,1)

    def test_direct_execution_rejects_changed_concrete_slot_before_claim_or_payment(self):
        from unittest.mock import Mock
        slots=self.slots(); slots[0]['metadata']['native_bytes']=float(slots[0]['metadata']['native_bytes'])
        claim, reserve=Mock(),Mock()
        with self.assertRaises(EvaluationStopped):
            executor.execute_cases(self.provider,slots,manifest=self.source,read=lambda name:(self.prep/name).read_bytes(),
                gate=Mock(),light_gate=Mock(),identity=Mock(),claim=claim,reserve=reserve,
                reservation_observed=Mock(),persist=Mock(),retain_terminal=Mock(),retain_telemetry=Mock(),
                record=Mock(),cancelled=lambda:False)
        claim.assert_not_called(); reserve.assert_not_called(); self.opener.assert_not_called()

    def test_imports_do_not_read_configuration_open_files_start_threads_or_network(self):
        # Preload immutable dependencies so the audit measures only new modules.
        code='''from contextlib import ExitStack
from unittest.mock import patch
import scripts.missing_link_demand_operation_policy_v3_run
with ExitStack() as stack:
    for target in ("builtins.open","pathlib.Path.read_bytes","pathlib.Path.read_text",
                   "missing_link.config.provider_environment","socket.socket",
                   "urllib.request.build_opener","threading.Thread.start"):
        stack.enter_context(patch(target,side_effect=AssertionError(target)))
    import scripts.missing_link_stream_successor_receipts
    import scripts.missing_link_stream_successor_executor
    import scripts.missing_link_stream_successor_run
'''
        result=subprocess.run([sys.executable,'-c',code],cwd=Path(__file__).resolve().parents[1],
                              capture_output=True,text=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stderr)


if __name__ == '__main__': unittest.main()
