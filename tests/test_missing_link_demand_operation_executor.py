"""Authored offline stream/ownership controls, never model or acquired code."""
import copy
from contextlib import ExitStack
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from missing_link.provider import Provider
from missing_link.store import Store
from scripts import missing_link_demand_operation_executor as executor
from scripts import missing_link_demand_operation_run as runner
from scripts import missing_link_repository_only_run as legacy
from scripts.missing_link_repository_only_evaluator import configuration, EvaluationStopped
from test_missing_link_demand_operation_policy import packet, unknown
from test_missing_link_repository_only_evaluator import Stream, terminal


class ExecutorTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.temp = self.stack.enter_context(tempfile.TemporaryDirectory())
        self.root = Path(self.temp)
        self.prep, self.out = self.root/'prep', self.root/'owned'
        self.prep.mkdir(); self.out.mkdir()
        self.db = self.root/'original.sqlite3'
        self.original = Store(self.db, runner.ACCOUNT)
        self.original.reserve_ai_allowance(runner.ALLOWANCE,'prior',.10,10)
        self.env = dict(runner.settings(),REPOTRACTION_AI_KEY='authored')
        self.provider = Provider(self.env)
        self.packets, self.files, self.requests = [], {}, []
        for n in range(1,12):
            item = packet('Authored request '+str(n))
            item['id'] = f'authored-{n}'
            env = executor.build_request(item)
            endpoint, payload, body = self.provider._encode_prompt(env['instructions'],env['context'],env['schema'],'request')
            env_name, native_name = f'envelope-{n:02}.json', f'native-{n:02}.json'
            self.files[env_name], self.files[native_name] = executor._bytes(env), body
            cost = ((len(body)+2048)*self.provider.input_price + self.provider.max_tokens*self.provider.output_price)/1e6
            self.requests.append({'slot':n,'operator_id':item['id'],'opaque_id':env['context']['id'],
                'input_sha256':env['context']['input_sha256'],'phase':'request','endpoint':endpoint,'job_id':f'owned-{n}',
                'policy_envelope':env_name,'envelope_sha256':executor.digest(self.files[env_name]),
                'native_body':native_name,'native_bytes':len(body),'native_sha256':executor.digest(body),'reservation_usd':cost})
            self.packets.append(item)
        self.source = {'config_without_key':configuration(self.provider),'requests':self.requests,
            'planned_reservations_usd':sum(r['reservation_usd'] for r in self.requests),'segment_cap_usd':.1,
            'protocol_revision':2,'status':'offline_only_no_executor','new_calls':0,'new_predictions':0,'new_reservations':0}
        for name, raw in self.files.items(): (self.prep/name).write_bytes(raw)
        runner.save(self.prep,'inputs.json',{'cases':self.packets})
        (self.root/'code.txt').write_text('Authored pinned implementation')
        self.protocol = self.root/'protocol.md'
        self.protocol.write_text('Authored frozen protocol')
        (self.prep/'protocol.md').write_bytes(self.protocol.read_bytes())
        self.source.update(execution_protocol_sha256_lf=legacy.sha(self.protocol,canonical=True),
                           code_sha256_canonical_lf={'code.txt':legacy.sha(self.root/'code.txt',canonical=True)})
        for module, names in ((runner,{'ROOT':self.root,'PREP':self.prep,'DB':self.db,'PROTOCOL':self.protocol,
                                       'PROTOCOL_SHA':self.source['execution_protocol_sha256_lf'],'ADAPTERS':('code.txt',)}),
                              (legacy,{'ROOT':self.root,'DB':self.db})):
            for key, value in names.items(): self.stack.enter_context(patch.object(module,key,value))
        baseline = legacy.snapshot({'artifacts':{'code.txt':legacy.sha(self.root/'code.txt')}})
        runner.save(self.prep,'baseline.json',baseline)
        self.source['owned_files_sha256'] = {p.name:legacy.sha(p) for p in self.prep.iterdir()}
        runner.save(self.prep,'prepared.json',self.source)
        self.stack.enter_context(patch.object(runner,'PREP_SHA',legacy.sha(self.prep/'prepared.json')))
        protected = dict(baseline['artifacts'])
        protected.update({p.relative_to(self.root).as_posix():legacy.sha(p) for p in self.prep.iterdir()})
        self.before = legacy.snapshot({'artifacts':protected})
        runner.save(self.out,'baseline.json',self.before)
        self.owned = {'required_main':'a'*40,'baseline_sha256':legacy.sha(self.out/'baseline.json'),
            'reviewed_head':'a'*40,'reviewed_tree':'a'*40,'new_calls':0,'new_reservations':0,
            'code_sha256_canonical_lf':self.source['code_sha256_canonical_lf'],
            'preparation_sha256':runner.PREP_SHA,'protocol_sha256_lf':runner.PROTOCOL_SHA}
        runner.save(self.out,'prepared.json',self.owned)
        self.anchor = legacy.sha(self.out/'prepared.json')
        def git(*args):
            if args == ('branch','--show-current'): return 'main'
            if args and args[0] == 'rev-parse': return 'a'*40
            return ''
        self.stack.enter_context(patch.object(runner,'git',side_effect=git))
        self.environment = self.stack.enter_context(patch.object(runner,'provider_environment',return_value=self.env))
        self.identity = self.stack.enter_context(patch.object(runner,'verify_cli_account',return_value=runner.ACCOUNT))
        self.opener = self.stack.enter_context(patch('urllib.request.build_opener'))
        self.opener.return_value.open.side_effect = lambda *a,**k:Stream(terminal(unknown()))
        self.stack.enter_context(patch('builtins.print'))

    def slots(self):
        return executor.verify_requests(self.provider,self.packets,self.source,lambda name:self.files[name])

    def test_exact_bodies_are_verified_before_payment(self):
        slots = self.slots()
        self.assertEqual(len(slots),11)
        self.assertEqual([s['metadata']['slot'] for s in slots],list(range(1,12)))
        self.opener.assert_not_called()
        self.assertEqual(self.original.ai_reserved(runner.ALLOWANCE),.10)

    def test_request_config_scope_order_and_cost_tampering_are_global(self):
        changes = [lambda m:m['requests'][0].update(slot=True),lambda m:m['requests'].reverse(),
            lambda m:m['requests'][0].update(phase='analysis'),lambda m:m['requests'][0].update(reservation_usd=0),
            lambda m:m['requests'][1].update(job_id=m['requests'][0]['job_id']),
            lambda m:m['config_without_key'].update(model='other'),lambda m:m.update(segment_cap_usd=.001),
            lambda m:m['requests'][0].update(native_sha256='0'*64)]
        for change in changes:
            modified = copy.deepcopy(self.source); change(modified)
            with self.subTest(change=change), self.assertRaises(EvaluationStopped):
                executor.verify_requests(self.provider,self.packets,modified,lambda name:self.files[name])
        self.opener.assert_not_called()

    def test_readiness_rejected_without_key_diagnostics(self):
        with self.assertRaisesRegex(EvaluationStopped,'not ready'):
            executor.verify_requests(Provider(runner.settings()),self.packets,self.source,lambda name:self.files[name])
        self.opener.assert_not_called()

    def test_standalone_schema_failure_never_enters_local_handler(self):
        with patch.object(executor,'normalize_prediction') as normalize, self.assertRaises(ValueError):
            executor.check_prediction({'wrong':'shape'},self.slots()[0],lambda:None)
        normalize.assert_not_called()

    def test_schema_valid_local_inconsistency_preserves_raw_and_unknowns(self):
        raw = unknown(); raw['fields']['runtime']['text'] = 'Unstated guess'
        before = copy.deepcopy(raw)
        result = executor.check_prediction(raw,self.slots()[0],lambda:None)
        self.assertEqual(result['disposition'],'local_rejection')
        self.assertEqual(result['prediction'],before)
        self.assertEqual(raw,before)

    def test_changed_raw_or_context_cannot_be_downgraded_by_value_error(self):
        for target in ('raw','context'):
            raw, slot = unknown(), self.slots()[0]
            def normalize(*args,**kwargs):
                if target == 'raw': args[0]['context_gaps'].append('Changed')
                else: args[1]['query'] = 'Changed'
                raise ValueError('Authored local-looking failure')
            with self.subTest(target=target), patch.object(executor,'normalize_prediction',side_effect=normalize), \
                    self.assertRaises(EvaluationStopped):
                executor.check_prediction(raw,slot,lambda:None)

    def test_arbitrary_normalizer_exception_is_global(self):
        with patch.object(executor,'normalize_prediction',side_effect=TypeError('Authored')), self.assertRaises(TypeError):
            executor.check_prediction(unknown(),self.slots()[0],lambda:None)

    def test_success_seals_native_usage_and_exact_original_prefix_and_blocks_replay(self):
        runner.run(self.out,self.anchor)
        self.assertEqual(self.opener.return_value.open.call_count,11)
        after = legacy.snapshot(self.before)
        self.assertEqual(after['reservation_rows'][:len(self.before['reservation_rows'])],self.before['reservation_rows'])
        for table in self.before['tables']:
            if table not in {'ml_ai_allowances','ml_ai_reservations'}:
                self.assertEqual(after['tables'][table],self.before['tables'][table])
        self.assertEqual(runner.load(self.out/'terminal-01.json'),terminal(unknown()))
        checkpoints = [runner.load(p) for p in self.out.glob('checkpoint-01-*.json')]
        self.assertTrue(any(j.get('reported_usage') for j in checkpoints))
        receipt_anchor = legacy.sha(self.out/'owned-artifacts.json')
        runner.verify(self.out,self.anchor,receipt_anchor)
        with self.assertRaises(EvaluationStopped): runner.run(self.out,self.anchor)
        self.assertEqual(self.opener.return_value.open.call_count,11)

    def test_local_rejection_retained_and_next_slots_attempted_once(self):
        invalid = unknown(); invalid['fields']['runtime']['text']='Invented'
        events = [terminal(invalid)] + [terminal(unknown())]*10
        self.opener.return_value.open.side_effect = [Stream(e) for e in events]
        runner.run(self.out,self.anchor)
        self.assertEqual(self.opener.return_value.open.call_count,11)
        result = runner.load(self.out/'result-01.json')
        self.assertEqual(result['disposition'],'local_rejection')
        self.assertEqual(result['prediction'],invalid)

    def test_schema_invalid_native_terminal_stops_after_one_and_is_preserved(self):
        event = terminal({'wrong':'shape'})
        self.opener.return_value.open.side_effect = lambda *a,**k:Stream(event)
        with self.assertRaises(EvaluationStopped): runner.run(self.out,self.anchor)
        self.assertEqual(self.opener.return_value.open.call_count,1)
        self.assertEqual(runner.load(self.out/'terminal-01.json'),event)
        self.assertFalse((self.out/'attempt-02.json').exists())
        runner.verify(self.out,self.anchor,legacy.sha(self.out/'owned-artifacts.json'))

    def test_transport_failure_keeps_charge_and_records_absent_terminal(self):
        self.opener.return_value.open.side_effect = TimeoutError()
        with self.assertRaises(EvaluationStopped): runner.run(self.out,self.anchor)
        self.assertEqual(self.opener.return_value.open.call_count,1)
        self.assertFalse((self.out/'terminal-01.json').exists())
        self.assertEqual(len(runner.journal(self.out)),1)
        self.assertEqual(len(runner.load(self.out/'summary.json')['unattempted']),10)

    def test_bad_independent_anchor_stops_before_credential_lookup(self):
        with self.assertRaises(EvaluationStopped): runner.run(self.out,'0'*64)
        self.environment.assert_not_called(); self.opener.assert_not_called()

    def test_account_failure_before_start_never_reserves(self):
        self.identity.side_effect = RuntimeError('Authored identity uncertainty')
        with self.assertRaises(EvaluationStopped): runner.run(self.out,self.anchor)
        self.assertFalse((self.out/'started.json').exists())
        self.assertEqual(self.original.ai_reserved(runner.ALLOWANCE),.10)
        self.opener.assert_not_called()

    def test_foreign_worker_lease_prevents_start_and_payment(self):
        from missing_link.lease import WorkerLease
        lease = WorkerLease(self.db)
        self.assertTrue(lease.acquire())
        try:
            with self.assertRaises(EvaluationStopped): runner.run(self.out,self.anchor)
        finally: lease.release()
        self.opener.assert_not_called()
        self.assertFalse((self.out/'started.json').exists())

    def test_atomic_reservation_journal_failure_keeps_charge_and_cannot_seal(self):
        original_save = runner.save
        def save(out,name,value):
            if name.startswith('reservation-'): raise OSError('Authored disk failure')
            original_save(out,name,value)
        with patch.object(runner,'save',side_effect=save), self.assertRaises(EvaluationStopped):
            runner.run(self.out,self.anchor)
        self.assertGreater(self.original.ai_reserved(runner.ALLOWANCE),.10)
        self.opener.assert_not_called()
        self.assertFalse((self.out/'owned-artifacts.json').exists())
        with self.assertRaises(EvaluationStopped): runner.run(self.out,self.anchor)

    def test_receipt_persistence_failure_is_global_and_no_second_attempt(self):
        original_save = runner.save
        def save(out,name,value):
            if name.startswith('terminal-'): raise OSError('Authored disk failure')
            original_save(out,name,value)
        with patch.object(runner,'save',side_effect=save), self.assertRaises(EvaluationStopped):
            runner.run(self.out,self.anchor)
        self.assertEqual(self.opener.return_value.open.call_count,1)
        self.assertFalse((self.out/'attempt-02.json').exists())

    def test_tampered_preparation_or_history_fails_before_network(self):
        (self.prep/self.requests[0]['native_body']).write_bytes(b'changed')
        with self.assertRaises(EvaluationStopped): runner.run(self.out,self.anchor)
        self.opener.assert_not_called(); self.environment.assert_not_called()

    def test_changed_pinned_code_after_receipt_stops_without_local_continuation(self):
        def receive(*a,**k):
            (self.root/'code.txt').write_text('Changed')
            return Stream(terminal(unknown()))
        self.opener.return_value.open.side_effect = receive
        with self.assertRaises(EvaluationStopped): runner.run(self.out,self.anchor)
        self.assertEqual(self.opener.return_value.open.call_count,1)
        self.assertFalse((self.out/'owned-artifacts.json').exists())
        self.assertFalse((self.out/'attempt-02.json').exists())

    def test_receipt_anchor_and_extra_file_are_rejected(self):
        runner.run(self.out,self.anchor)
        with self.assertRaises(EvaluationStopped): runner.verify(self.out,self.anchor,'0'*64)
        receipt_anchor = legacy.sha(self.out/'owned-artifacts.json')
        (self.out/'extra.json').write_text('{}')
        with self.assertRaises(EvaluationStopped): runner.verify(self.out,self.anchor,receipt_anchor)

    def test_empty_owned_successor_verifies_without_environment_or_network(self):
        runner.verify(self.out,self.anchor)
        self.environment.assert_not_called(); self.opener.assert_not_called(); self.identity.assert_not_called()

    def test_native_incomplete_refused_or_malformed_terminals_stop_globally(self):
        events = [terminal(unknown(),'incomplete'), terminal(unknown(),'failed'),
                  terminal(unknown(),refusal=True), terminal(unknown())]
        events[-1]['response']['output'][0]['content'][0]['text'] = '{'
        for event in events:
            self.setUp()
            self.opener.return_value.open.side_effect = lambda *a,**k:Stream(event)
            with self.subTest(status=event['response']['status']), self.assertRaises(EvaluationStopped):
                runner.run(self.out,self.anchor)
            self.assertEqual(self.opener.return_value.open.call_count,1)
            self.assertEqual(runner.load(self.out/'terminal-01.json'),event)
            self.assertFalse((self.out/'attempt-02.json').exists())

    def test_atomic_cap_denies_request_without_refund_or_new_allowance(self):
        with patch.object(runner,'CEILING',.1001), self.assertRaises(EvaluationStopped):
            runner.run(self.out,self.anchor)
        self.opener.assert_not_called()
        self.assertEqual(self.original.ai_reserved(runner.ALLOWANCE),.10)
        self.assertEqual(legacy.snapshot(self.before)['allowance_rows'],self.before['allowance_rows'])
        self.assertEqual(runner.journal(self.out),[])

    def test_unowned_accounting_or_active_jobs_block_before_environment(self):
        self.original.reserve_ai_allowance(runner.ALLOWANCE,'foreign',.01,10)
        with self.assertRaises(EvaluationStopped): runner.run(self.out,self.anchor)
        self.environment.assert_not_called(); self.opener.assert_not_called()

    def test_cancellation_consumes_run_without_reservation_or_next_attempt(self):
        (self.out.parent/(self.out.name+'.cancel')).write_text('cancel')
        with self.assertRaises(EvaluationStopped): runner.run(self.out,self.anchor)
        self.assertTrue((self.out/'started.json').exists())
        self.assertFalse((self.out/'attempt-02.json').exists())
        self.opener.assert_not_called()
        self.assertEqual(self.original.ai_reserved(runner.ALLOWANCE),.10)

    def test_prepare_requires_merged_main_before_offline_freeze(self):
        fresh = self.root/'new-successor'
        with patch.object(runner,'git',side_effect=lambda *a:'feature' if a == ('branch','--show-current') else ''), \
                self.assertRaises(EvaluationStopped):
            runner.prepare(fresh,'a'*40)
        self.assertFalse(fresh.exists())
        self.environment.assert_not_called(); self.opener.assert_not_called()

    def test_active_original_job_blocks_before_provider_lookup(self):
        self.original.put('jobs','active',{'id':'active','status':'running'})
        with self.assertRaises(EvaluationStopped): runner.run(self.out,self.anchor)
        self.environment.assert_not_called(); self.opener.assert_not_called()

    def test_omitted_adapter_or_changed_reviewed_tree_is_rejected(self):
        for change in ('code','tree'):
            manifest = copy.deepcopy(self.owned)
            if change == 'code': manifest['code_sha256_canonical_lf'] = {}
            else: manifest['reviewed_tree'] = 'b'*40
            (self.out/'prepared.json').write_text(json.dumps(manifest))
            with self.subTest(change=change), self.assertRaises(EvaluationStopped):
                runner.run(self.out,legacy.sha(self.out/'prepared.json'))
        self.environment.assert_not_called(); self.opener.assert_not_called()

    def test_prepare_freezes_reviewed_code_and_baseline_without_credentials_or_payment(self):
        # Authored historical ledger only; never touch the actual account DB.
        with self.original.connection() as db:
            db.executemany('INSERT INTO ml_ai_reservations (allowance_id,job_id,cost,created) VALUES (?,?,?,?)',
                [(runner.ALLOWANCE,f'authored-prior-{n}',(8.0266132-.1)/554,0) for n in range(554)])
            db.execute('UPDATE ml_ai_allowances SET reserved=? WHERE id=?',(8.0266132,runner.ALLOWANCE))
        baseline = legacy.snapshot({'artifacts':{'code.txt':legacy.sha(self.root/'code.txt')}})
        (self.prep/'baseline.json').write_text(json.dumps(baseline))
        source = copy.deepcopy(self.source)
        source['owned_files_sha256']['baseline.json'] = legacy.sha(self.prep/'baseline.json')
        (self.prep/'prepared.json').write_text(json.dumps(source))
        fresh = self.root/'fresh-successor'
        with patch.object(runner,'PREP_SHA',legacy.sha(self.prep/'prepared.json')):
            runner.prepare(fresh,'a'*40)
            prepared = runner.load(fresh/'prepared.json')
            self.assertEqual(prepared['reviewed_head'],'a'*40)
            self.assertEqual(prepared['new_calls'],0)
            runner.verify(fresh,legacy.sha(fresh/'prepared.json'))
        self.assertEqual(legacy.snapshot({'artifacts':baseline['artifacts']}),baseline)
        self.environment.assert_not_called(); self.opener.assert_not_called(); self.identity.assert_not_called()


if __name__ == '__main__':
    unittest.main()
