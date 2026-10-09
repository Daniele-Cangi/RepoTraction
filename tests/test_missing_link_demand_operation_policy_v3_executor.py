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
from scripts import missing_link_demand_operation_policy_v3_executor as executor
from scripts import missing_link_demand_operation_policy_v3_run as runner
from scripts import missing_link_repository_only_run as legacy
from scripts.missing_link_repository_only_evaluator import configuration, EvaluationStopped
from test_missing_link_demand_operation_policy import packet, unknown
from test_missing_link_repository_only_evaluator import Stream, terminal


class PolicyV3ExecutorTests(unittest.TestCase):
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
                'input_sha256':env['context']['input_sha256'],'phase':'request','endpoint':endpoint,'job_id':f'demand-operation-policy-v3-owned-2026-10-09-{n:02}',
                'policy_envelope':env_name,'envelope_sha256':executor.digest(self.files[env_name]),'envelope_bytes':len(self.files[env_name]),
                'native_body':native_name,'native_bytes':len(body),'native_sha256':executor.digest(body),'reservation_usd':cost})
            self.packets.append(item)
        self.source = {'config_without_key':configuration(self.provider),'requests':self.requests,
            'planned_reservations_usd':sum(r['reservation_usd'] for r in self.requests),'segment_cap_usd':.1,
            'policy_revision':3,'status':'offline_only_no_policy_v3_executor',
            'account':runner.ACCOUNT,'allowance':runner.ALLOWANCE,'configured_total_usd':10,
            'atomic_cumulative_ceiling_usd':runner.CEILING,'call_authorization_granted':False,'new_calls':0,'new_predictions':0,'new_reservations':0}
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
        # Authored historical native/assessment/preparation anchors, not real data.
        self.history_folders = []
        anchors = {}
        for relative, prepared_key, receipt_key in runner.HISTORIES:
            folder = self.root/relative
            folder.mkdir(parents=True)
            runner.save(folder,'prepared.json',{'authored':'consumed preparation'})
            runner.save(folder,'evidence.json',{'authored':'retained native or assessment'})
            runner.save(folder,'owned-artifacts.json',{p.name:legacy.sha(p) for p in folder.iterdir()})
            if prepared_key: anchors[prepared_key] = legacy.sha(folder/'prepared.json')
            anchors[receipt_key] = legacy.sha(folder/'owned-artifacts.json')
            self.history_folders.append(folder)
        older = self.root/runner.OLDER_PREP
        older.mkdir(parents=True)
        runner.save(older,'native.json',{'authored':'older immutable body'})
        runner.save(older,'prepared.json',{'owned_files_sha256':{'native.json':legacy.sha(older/'native.json')}})
        self.history_folders.append(older)
        prior = self.root/runner.LEGACY_PREP
        prior.mkdir(parents=True)
        runner.save(prior,'native.json',{'authored':'old immutable body'})
        runner.save(prior,'prepared.json',{'owned_files_sha256':{'native.json':legacy.sha(prior/'native.json')},
            'historical_anchors':{'v1_execution_preparation_sha256':legacy.sha(older/'prepared.json')}})
        anchors['v2_execution_preparation_sha256'] = legacy.sha(prior/'prepared.json')
        self.history_folders.append(prior)
        self.source['historical_anchors'] = anchors
        protected_history = {'code.txt':legacy.sha(self.root/'code.txt')}
        protected_history.update({p.relative_to(self.root).as_posix():legacy.sha(p)
            for folder in self.history_folders for p in folder.iterdir()})
        baseline = legacy.snapshot({'artifacts':protected_history})
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
        self.authorization = self.root/'authorization.json'
        runner.save(self.root,'authorization.json',runner.authorization_scope(self.anchor,self.source))
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
        runner.run(self.out,self.anchor,self.authorization)
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
        with self.assertRaises(EvaluationStopped): runner.run(self.out,self.anchor,self.authorization)
        self.assertEqual(self.opener.return_value.open.call_count,11)

    def test_local_rejection_retained_and_next_slots_attempted_once(self):
        invalid = unknown(); invalid['fields']['runtime']['text']='Invented'
        events = [terminal(invalid)] + [terminal(unknown())]*10
        self.opener.return_value.open.side_effect = [Stream(e) for e in events]
        runner.run(self.out,self.anchor,self.authorization)
        self.assertEqual(self.opener.return_value.open.call_count,11)
        result = runner.load(self.out/'result-01.json')
        self.assertEqual(result['disposition'],'local_rejection')
        self.assertEqual(result['prediction'],invalid)

    def test_schema_invalid_native_terminal_stops_after_one_and_is_preserved(self):
        event = terminal({'wrong':'shape'})
        self.opener.return_value.open.side_effect = lambda *a,**k:Stream(event)
        with self.assertRaises(EvaluationStopped): runner.run(self.out,self.anchor,self.authorization)
        self.assertEqual(self.opener.return_value.open.call_count,1)
        self.assertEqual(runner.load(self.out/'terminal-01.json'),event)
        self.assertFalse((self.out/'attempt-02.json').exists())
        runner.verify(self.out,self.anchor,legacy.sha(self.out/'owned-artifacts.json'))

    def test_transport_failure_keeps_charge_and_records_absent_terminal(self):
        self.opener.return_value.open.side_effect = TimeoutError()
        with self.assertRaises(EvaluationStopped): runner.run(self.out,self.anchor,self.authorization)
        self.assertEqual(self.opener.return_value.open.call_count,1)
        self.assertFalse((self.out/'terminal-01.json').exists())
        self.assertEqual(len(runner.journal(self.out)),1)
        self.assertEqual(len(runner.load(self.out/'summary.json')['unattempted']),10)

    def test_bad_independent_anchor_stops_before_credential_lookup(self):
        with self.assertRaises(EvaluationStopped): runner.run(self.out,'0'*64,self.authorization)
        self.environment.assert_not_called(); self.opener.assert_not_called()

    def test_account_failure_before_start_never_reserves(self):
        self.identity.side_effect = RuntimeError('Authored identity uncertainty')
        with self.assertRaises(EvaluationStopped): runner.run(self.out,self.anchor,self.authorization)
        self.assertFalse((self.out/'started.json').exists())
        self.assertEqual(self.original.ai_reserved(runner.ALLOWANCE),.10)
        self.opener.assert_not_called()

    def test_foreign_worker_lease_prevents_start_and_payment(self):
        from missing_link.lease import WorkerLease
        lease = WorkerLease(self.db)
        self.assertTrue(lease.acquire())
        try:
            with self.assertRaises(EvaluationStopped): runner.run(self.out,self.anchor,self.authorization)
        finally: lease.release()
        self.opener.assert_not_called()
        self.assertFalse((self.out/'started.json').exists())

    def test_atomic_reservation_journal_failure_keeps_charge_and_cannot_seal(self):
        original_save = runner.save
        def save(out,name,value):
            if name.startswith('reservation-'): raise OSError('Authored disk failure')
            original_save(out,name,value)
        with patch.object(runner,'save',side_effect=save), self.assertRaises(EvaluationStopped):
            runner.run(self.out,self.anchor,self.authorization)
        self.assertGreater(self.original.ai_reserved(runner.ALLOWANCE),.10)
        self.opener.assert_not_called()
        self.assertFalse((self.out/'owned-artifacts.json').exists())
        with self.assertRaises(EvaluationStopped): runner.run(self.out,self.anchor,self.authorization)

    def test_receipt_persistence_failure_is_global_and_no_second_attempt(self):
        original_save = runner.save
        def save(out,name,value):
            if name.startswith('terminal-'): raise OSError('Authored disk failure')
            original_save(out,name,value)
        with patch.object(runner,'save',side_effect=save), self.assertRaises(EvaluationStopped):
            runner.run(self.out,self.anchor,self.authorization)
        self.assertEqual(self.opener.return_value.open.call_count,1)
        self.assertFalse((self.out/'attempt-02.json').exists())

    def test_tampered_preparation_or_history_fails_before_network(self):
        (self.prep/self.requests[0]['native_body']).write_bytes(b'changed')
        with self.assertRaises(EvaluationStopped): runner.run(self.out,self.anchor,self.authorization)
        self.opener.assert_not_called(); self.environment.assert_not_called()

    def test_changed_pinned_code_after_receipt_stops_without_local_continuation(self):
        def receive(*a,**k):
            (self.root/'code.txt').write_text('Changed')
            return Stream(terminal(unknown()))
        self.opener.return_value.open.side_effect = receive
        with self.assertRaises(EvaluationStopped): runner.run(self.out,self.anchor,self.authorization)
        self.assertEqual(self.opener.return_value.open.call_count,1)
        self.assertFalse((self.out/'owned-artifacts.json').exists())
        self.assertFalse((self.out/'attempt-02.json').exists())

    def test_receipt_anchor_and_extra_file_are_rejected(self):
        runner.run(self.out,self.anchor,self.authorization)
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
                runner.run(self.out,self.anchor,self.authorization)
            self.assertEqual(self.opener.return_value.open.call_count,1)
            self.assertEqual(runner.load(self.out/'terminal-01.json'),event)
            self.assertFalse((self.out/'attempt-02.json').exists())

    def test_atomic_cap_denies_request_without_refund_or_new_allowance(self):
        self.source['atomic_cumulative_ceiling_usd'] = .1001
        self.reseal_source()
        self.reseal_owned()
        runner.save(self.root,'cap-authorization.json',dict(runner.authorization_scope(self.anchor,self.source),atomic_cumulative_ceiling_usd=.1001))
        self.authorization = self.root/'cap-authorization.json'
        with patch.object(runner,'CEILING',.1001), self.assertRaises(EvaluationStopped):
            runner.run(self.out,self.anchor,self.authorization)
        self.opener.assert_not_called()
        self.assertEqual(self.original.ai_reserved(runner.ALLOWANCE),.10)
        self.assertEqual(legacy.snapshot(self.before)['allowance_rows'],self.before['allowance_rows'])
        self.assertEqual(runner.journal(self.out),[])

    def test_unowned_accounting_or_active_jobs_block_before_environment(self):
        self.original.reserve_ai_allowance(runner.ALLOWANCE,'foreign',.01,10)
        with self.assertRaises(EvaluationStopped): runner.run(self.out,self.anchor,self.authorization)
        self.environment.assert_not_called(); self.opener.assert_not_called()

    def test_cancellation_consumes_run_without_reservation_or_next_attempt(self):
        (self.out.parent/(self.out.name+'.cancel')).write_text('cancel')
        with self.assertRaises(EvaluationStopped): runner.run(self.out,self.anchor,self.authorization)
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
        with self.assertRaises(EvaluationStopped): runner.run(self.out,self.anchor,self.authorization)
        self.environment.assert_not_called(); self.opener.assert_not_called()

    def test_omitted_adapter_or_changed_reviewed_tree_is_rejected(self):
        for change in ('code','tree'):
            manifest = copy.deepcopy(self.owned)
            if change == 'code': manifest['code_sha256_canonical_lf'] = {}
            else: manifest['reviewed_tree'] = 'b'*40
            (self.out/'prepared.json').write_text(json.dumps(manifest))
            with self.subTest(change=change), self.assertRaises(EvaluationStopped):
                runner.run(self.out,legacy.sha(self.out/'prepared.json'),self.authorization)
        self.environment.assert_not_called(); self.opener.assert_not_called()

    def reseal_source(self):
        self.source['owned_files_sha256'] = {p.name:legacy.sha(p) for p in self.prep.iterdir() if p.name != 'prepared.json'}
        (self.prep/'prepared.json').write_text(json.dumps(self.source))
        self.stack.enter_context(patch.object(runner,'PREP_SHA',legacy.sha(self.prep/'prepared.json')))

    def reseal_owned(self):
        baseline = runner.load(self.prep/'baseline.json')
        baseline['artifacts'].update({p.relative_to(self.root).as_posix():legacy.sha(p) for p in self.prep.iterdir()})
        (self.out/'baseline.json').write_text(json.dumps(baseline))
        self.before = baseline
        self.owned.update(baseline_sha256=legacy.sha(self.out/'baseline.json'),preparation_sha256=runner.PREP_SHA)
        (self.out/'prepared.json').write_text(json.dumps(self.owned))
        self.anchor = legacy.sha(self.out/'prepared.json')

    def test_prepare_freezes_577_row_baseline_without_credentials_or_payment(self):
        with self.original.connection() as db:
            db.executemany('INSERT INTO ml_ai_reservations (allowance_id,job_id,cost,created) VALUES (?,?,?,?)',
                [(runner.ALLOWANCE,f'authored-prior-{n}',(8.1314287-.1)/576,0) for n in range(576)])
            db.execute('UPDATE ml_ai_allowances SET reserved=? WHERE id=?',(8.1314287,runner.ALLOWANCE))
        baseline = legacy.snapshot(runner.load(self.prep/'baseline.json'))
        (self.prep/'baseline.json').write_text(json.dumps(baseline))
        self.reseal_source()
        fresh = self.root/'fresh-successor'
        with patch.object(runner,'HISTORY_ARTIFACTS',len(baseline['artifacts'])):
            runner.prepare(fresh,'a'*40)
            prepared = runner.load(fresh/'prepared.json')
            self.assertEqual(prepared['reviewed_head'],'a'*40)
            self.assertEqual(prepared['new_calls'],0)
            runner.verify(fresh,legacy.sha(fresh/'prepared.json'))
        self.assertEqual(legacy.snapshot(baseline),baseline)
        self.assertFalse((fresh/'authorization.json').exists())
        self.environment.assert_not_called(); self.opener.assert_not_called(); self.identity.assert_not_called()

    def test_policy_v1_bodies_cannot_enter_policy_v3_before_reservation(self):
        from scripts import missing_link_demand_operation_policy as v1
        modified = self.slots()
        for slot in modified:
            env = v1.build_request(slot['packet'])
            endpoint,payload,body = self.provider._encode_prompt(env['instructions'],env['context'],env['schema'],'request')
            slot.update(envelope=env,payload=payload)
            slot['metadata'].update(native_sha256=executor.digest(body))
        callbacks = {n:Mock() for n in ('gate','identity','claim','reserve','persist','retain_terminal','record','cancelled')}
        with self.assertRaises(EvaluationStopped):
            executor.execute_cases(self.provider,modified,manifest=self.source,read=lambda n:self.files[n],**callbacks)
        callbacks['reserve'].assert_not_called(); self.opener.assert_not_called()
        with self.assertRaises(EvaluationStopped): executor.check_prediction(unknown(),modified[0],lambda:None)

    def test_old_instruction_encoder_request_mismatch_is_global(self):
        from scripts import missing_link_demand_operation_policy as v1
        with patch.object(executor,'build_request',side_effect=v1.build_request), self.assertRaises(EvaluationStopped):
            self.slots()
        self.opener.assert_not_called()

    def test_original_frozen_source_revision_and_slot_namespace_rejected(self):
        for key,value in (('policy_revision',1),('job_id','demand-operation-owned-2026-10-09-01'),('envelope_bytes',0)):
            source = copy.deepcopy(self.source)
            if key == 'policy_revision': source[key] = value
            else: source['requests'][0][key] = value
            with self.subTest(key=key), self.assertRaises(EvaluationStopped):
                executor.verify_requests(self.provider,self.packets,source,lambda n:self.files[n])
        self.opener.assert_not_called()

    def test_missing_or_mismatched_call_scope_stops_before_key_identity_or_payment(self):
        with self.assertRaises(EvaluationStopped): runner.run(self.out,self.anchor)
        base = runner.authorization_scope(self.anchor,self.source)
        for key,value in (('prepared_manifest_sha256','0'*64),('calls',12),('account','other'),
                ('allowance','other'),('atomic_cumulative_ceiling_usd',20),('native_sha256',[]),('job_ids',[])):
            scope = dict(base,**{key:value})
            (self.authorization).write_text(json.dumps(scope))
            with self.subTest(key=key), self.assertRaises(EvaluationStopped):
                runner.run(self.out,self.anchor,self.authorization)
        self.environment.assert_not_called(); self.identity.assert_not_called(); self.opener.assert_not_called()
        self.assertFalse((self.out/'started.json').exists())
        self.assertEqual(self.original.ai_reserved(runner.ALLOWANCE),.10)

    def test_v1_sealed_inventory_addition_stops_before_credentials(self):
        (self.history_folders[0]/'extra.json').write_text('{}')
        with self.assertRaises(EvaluationStopped): runner.run(self.out,self.anchor,self.authorization)
        self.environment.assert_not_called(); self.opener.assert_not_called()

    def test_v1_assessment_mutation_during_stream_is_global_after_one_charge(self):
        def receive(*a,**k):
            (self.history_folders[1]/'evidence.json').write_text('changed')
            return Stream(terminal(unknown()))
        self.opener.return_value.open.side_effect = receive
        with self.assertRaises(EvaluationStopped): runner.run(self.out,self.anchor,self.authorization)
        self.assertEqual(self.opener.return_value.open.call_count,1)
        self.assertEqual(runner.load(self.out/'terminal-01.json'),terminal(unknown()))
        self.assertFalse((self.out/'attempt-02.json').exists())
        self.assertFalse((self.out/'owned-artifacts.json').exists())

    def test_history_static_checks_preserve_prior_seals_after_own_extension(self):
        before = [{p.name:legacy.sha(p) for p in f.iterdir()} for f in self.history_folders]
        runner.run(self.out,self.anchor,self.authorization)
        self.assertEqual(legacy.snapshot(self.before)['reservations'],self.before['reservations']+11)
        runner.historical_evidence(self.source,runner.load(self.prep/'baseline.json'))
        runner.verify(self.out,self.anchor,legacy.sha(self.out/'owned-artifacts.json'))
        after = [{p.name:legacy.sha(p) for p in f.iterdir()} for f in self.history_folders]
        self.assertEqual(after,before)

    def test_owned_baseline_cannot_drop_prior_assessment_even_with_fresh_owned_anchor(self):
        baseline = runner.load(self.out/'baseline.json')
        baseline['artifacts'].pop(next(n for n in baseline['artifacts'] if 'assessment' in n))
        (self.out/'baseline.json').write_text(json.dumps(baseline))
        self.owned['baseline_sha256'] = legacy.sha(self.out/'baseline.json')
        (self.out/'prepared.json').write_text(json.dumps(self.owned))
        with self.assertRaises(EvaluationStopped):
            runner.run(self.out,legacy.sha(self.out/'prepared.json'),self.authorization)
        self.environment.assert_not_called(); self.opener.assert_not_called()

    def test_validation_code_gate_value_error_cannot_be_absorbed_as_local(self):
        invalid = unknown(); invalid['fields']['runtime']['text'] = 'Unstated guess'
        gate = Mock(side_effect=[None,ValueError('Authored changed executable')])
        with self.assertRaises(ValueError): executor.check_prediction(invalid,self.slots()[0],gate)
        self.assertEqual(gate.call_count,2)

    def test_schema_failure_keeps_raw_checkpoint_before_rejection(self):
        raw = {'wrong':'shape'}
        self.opener.return_value.open.side_effect = lambda *a,**k:Stream(terminal(raw))
        with self.assertRaises(EvaluationStopped): runner.run(self.out,self.anchor,self.authorization)
        checkpoints = [runner.load(p) for p in self.out.glob('checkpoint-01-*.json')]
        self.assertTrue(any(o['phase'] == 'request' and o['output'] == raw
            for j in checkpoints for o in j['checkpoint'].get('ai_outputs',[])))
        self.assertFalse((self.out/'attempt-02.json').exists())

    def test_direct_execution_rejects_all_changed_frozen_metadata_before_claim_or_payment(self):
        # Every location is tested, including a late slot before an earlier call.
        changes = {'operator_id':'other', 'opaque_id':'other', 'input_sha256':'0'*64,
            'phase':'analysis', 'endpoint':'/other', 'native_bytes':1, 'envelope_bytes':1,
            'native_sha256':'0'*64, 'envelope_sha256':'0'*64, 'native_body':'other.json',
            'policy_envelope':'other.json', 'reservation_usd':0, 'job_id':'other'}
        original = self.slots()
        with patch.object(executor,'complete_with_receipt',side_effect=AssertionError('Receipt reached')) as receipt:
            for index in (0,5,10):
                for key,value in changes.items():
                    slots = copy.deepcopy(original)
                    slots[index]['metadata'][key] = value
                    callbacks = {n:Mock() for n in ('gate','identity','claim','reserve','persist','retain_terminal','record','cancelled')}
                    with self.subTest(slot=index+1,key=key), self.assertRaises(EvaluationStopped):
                        executor.execute_cases(self.provider,slots,manifest=self.source,read=lambda n:self.files[n],**callbacks)
                    callbacks['claim'].assert_not_called(); callbacks['reserve'].assert_not_called()
            receipt.assert_not_called()
        self.opener.assert_not_called()

    def test_descendant_main_cannot_execute_from_another_tree_before_credentials(self):
        def descendant(*args):
            if args == ('branch','--show-current'): return 'main'
            if args in (('rev-parse','HEAD'),('rev-parse','origin/main'),('rev-parse','HEAD^{tree}')): return 'b'*40
            if args and args[0] == 'rev-parse': return 'a'*40
            return ''
        self.environment.side_effect = AssertionError('Credential lookup reached')
        with patch.object(runner,'git',side_effect=descendant), self.assertRaises(EvaluationStopped):
            runner.run(self.out,self.anchor,self.authorization)
        self.environment.assert_not_called(); self.identity.assert_not_called(); self.opener.assert_not_called()
        self.assertFalse((self.out/'started.json').exists())
        self.assertEqual(self.original.ai_reserved(runner.ALLOWANCE),.10)

    def test_direct_execution_cannot_reanchor_changed_body_using_its_own_hash(self):
        slots = self.slots()
        slot = slots[-1]
        slot['packet']['query'] = 'Altered operation outside the frozen request'
        envelope = executor.build_request(slot['packet'])
        endpoint,payload,body = self.provider._encode_prompt(envelope['instructions'],envelope['context'],envelope['schema'],'request')
        slot.update(envelope=envelope,payload=payload)
        slot['metadata'].update(native_sha256=executor.digest(body),native_bytes=len(body),
            envelope_sha256=executor.digest(executor._bytes(envelope)),envelope_bytes=len(executor._bytes(envelope)),
            opaque_id=envelope['context']['id'],input_sha256=envelope['context']['input_sha256'],
            reservation_usd=((len(body)+2048)*self.provider.input_price+self.provider.max_tokens*self.provider.output_price)/1e6)
        callbacks = {n:Mock() for n in ('gate','identity','claim','reserve','persist','retain_terminal','record','cancelled')}
        with self.assertRaises(EvaluationStopped):
            executor.execute_cases(self.provider,slots,manifest=self.source,read=lambda n:self.files[n],**callbacks)
        callbacks['claim'].assert_not_called(); callbacks['reserve'].assert_not_called(); self.opener.assert_not_called()

    def test_reviewed_tree_change_during_receipt_stops_after_one_reservation(self):
        changed = False
        def git(*args):
            if args == ('branch','--show-current'): return 'main'
            if args in (('rev-parse','HEAD'),('rev-parse','origin/main'),('rev-parse','HEAD^{tree}')):
                return ('b' if changed else 'a')*40
            if args and args[0] == 'rev-parse': return 'a'*40
            return ''
        def receive(*a,**k):
            nonlocal changed
            changed = True
            return Stream(terminal(unknown()))
        self.opener.return_value.open.side_effect = receive
        with patch.object(runner,'git',side_effect=git), self.assertRaises(EvaluationStopped):
            runner.run(self.out,self.anchor,self.authorization)
        self.assertEqual(self.opener.return_value.open.call_count,1)
        self.assertEqual(len(runner.journal(self.out)),1)
        self.assertEqual(runner.load(self.out/'terminal-01.json'),terminal(unknown()))
        self.assertFalse((self.out/'attempt-02.json').exists())
        self.assertFalse((self.out/'owned-artifacts.json').exists())

    def test_direct_execution_rejects_json_equivalent_concrete_type_changes_before_claim(self):
        original = self.slots()
        def change(slots, index, target):
            slot = slots[index]
            if target == 'envelope_enum':
                schema = slot['envelope']['schema']['properties']['request_kind']['properties']['value']
                schema['enum'] = tuple(schema['enum'])
            elif target == 'payload_input':
                slot['payload']['input'] = tuple(slot['payload']['input'])
            elif target == 'envelope_metadata':
                slot['envelope']['context']['coverage']['omitted_root_char_ranges'] = tuple(
                    slot['envelope']['context']['coverage']['omitted_root_char_ranges'])
            else:
                slot['metadata']['slot'] = float(slot['metadata']['slot'])
        with patch.object(executor,'complete_with_receipt',side_effect=AssertionError('Receipt reached')) as receipt:
            for index in (0,5,10):
                for target in ('envelope_enum','payload_input','envelope_metadata','metadata_numeric_type'):
                    slots = copy.deepcopy(original)
                    change(slots,index,target)
                    callbacks = {n:Mock() for n in ('gate','identity','claim','reserve','persist','retain_terminal','record','cancelled')}
                    with self.subTest(slot=index+1,target=target), self.assertRaises(EvaluationStopped):
                        executor.execute_cases(self.provider,slots,manifest=self.source,read=lambda n:self.files[n],**callbacks)
                    callbacks['claim'].assert_not_called(); callbacks['reserve'].assert_not_called()
            receipt.assert_not_called()
        self.opener.assert_not_called()

    def test_v2_revision_and_namespace_cannot_dispatch_v3(self):
        for key, value in (('policy_revision', 2), ('job_id', 'demand-operation-policy-v2-owned-2026-10-09-01')):
            source = copy.deepcopy(self.source)
            if key == 'policy_revision':
                source[key] = value
            else:
                source['requests'][0][key] = value
            with self.subTest(key=key), self.assertRaises(EvaluationStopped):
                executor.verify_requests(self.provider, self.packets, source, lambda n: self.files[n])
        self.opener.assert_not_called()

    def test_v2_instruction_encoder_cannot_reproduce_v3_frozen_bodies(self):
        from scripts import missing_link_demand_operation_policy_v2 as v2
        with patch.object(executor, 'build_request', side_effect=v2.build_request), self.assertRaises(EvaluationStopped):
            self.slots()
        self.opener.assert_not_called()

    def test_v2_native_inventory_addition_stops_before_credentials(self):
        (self.history_folders[2]/'extra.json').write_text('{}')
        with self.assertRaises(EvaluationStopped):
            runner.run(self.out, self.anchor, self.authorization)
        self.environment.assert_not_called()
        self.opener.assert_not_called()
        self.assertFalse((self.out/'started.json').exists())

    def test_v2_assessment_mutation_retains_terminal_and_stops_after_one_charge(self):
        def receive(*args, **kwargs):
            (self.history_folders[3]/'evidence.json').write_text('changed')
            return Stream(terminal(unknown()))
        self.opener.return_value.open.side_effect = receive
        with self.assertRaises(EvaluationStopped):
            runner.run(self.out, self.anchor, self.authorization)
        self.assertEqual(self.opener.return_value.open.call_count, 1)
        self.assertEqual(runner.load(self.out/'terminal-01.json'), terminal(unknown()))
        self.assertEqual(len(runner.journal(self.out)), 1)
        self.assertFalse((self.out/'attempt-02.json').exists())
        self.assertFalse((self.out/'owned-artifacts.json').exists())

    def test_call_authorization_requires_concrete_json_types_before_credentials(self):
        scope = runner.authorization_scope(self.anchor, self.source)
        for key, value in (('authorized', 1), ('calls', 11.0), ('calls_per_slot', True), ('configured_total_usd', 10.0)):
            self.authorization.write_text(json.dumps(dict(scope, **{key: value})))
            with self.subTest(key=key), self.assertRaises(EvaluationStopped):
                runner.run(self.out, self.anchor, self.authorization)
        self.environment.assert_not_called()
        self.identity.assert_not_called()
        self.opener.assert_not_called()
        self.assertEqual(self.original.ai_reserved(runner.ALLOWANCE), .10)

    def test_identity_callback_cannot_change_late_slot_type_before_claim(self):
        slots = self.slots()
        callbacks = {name: Mock() for name in ('gate', 'identity', 'claim', 'reserve', 'persist', 'retain_terminal', 'record', 'cancelled')}
        def identity(**kwargs):
            slots[-1]['metadata']['slot'] = float(slots[-1]['metadata']['slot'])
        callbacks['identity'].side_effect = identity
        with self.assertRaises(EvaluationStopped):
            executor.execute_cases(self.provider, slots, manifest=self.source, read=lambda n: self.files[n], **callbacks)
        callbacks['claim'].assert_not_called()
        callbacks['reserve'].assert_not_called()
        self.opener.assert_not_called()

    def test_normalizer_cannot_hide_equal_numeric_slot_type_mutation(self):
        slot = self.slots()[0]
        def normalize(*args, **kwargs):
            slot['metadata']['slot'] = 1.0
            raise ValueError('Authored local-looking rejection')
        with patch.object(executor, 'normalize_prediction', side_effect=normalize), self.assertRaises(EvaluationStopped):
            executor.check_prediction(unknown(), slot, lambda: None)
        self.opener.assert_not_called()

    def test_slot_type_change_at_payment_boundary_cannot_reach_reservation(self):
        slots = self.slots()
        callbacks = {name: Mock() for name in ('gate', 'identity', 'claim', 'reserve', 'persist', 'retain_terminal', 'record')}
        callbacks['cancelled'] = Mock(return_value=False)
        def complete(provider, instruction, data, budget, **kwargs):
            slots[-1]['metadata']['slot'] = 11.0
            budget.reserve_ai(slots[0]['metadata']['reservation_usd'], 1, .02)
        with patch.object(executor, 'complete_with_receipt', side_effect=complete), self.assertRaises(EvaluationStopped):
            executor.execute_cases(self.provider, slots, manifest=self.source, read=lambda n: self.files[n], **callbacks)
        callbacks['claim'].assert_called_once()
        callbacks['reserve'].assert_not_called()
        callbacks['retain_terminal'].assert_not_called()
        self.opener.assert_not_called()

    def test_slot_change_after_commit_stops_before_native_transmission(self):
        slots = self.slots()
        callbacks = {name: Mock() for name in ('gate', 'identity', 'claim', 'reserve', 'persist', 'retain_terminal', 'record')}
        callbacks['cancelled'] = Mock(return_value=False)
        def reserve(*args):
            slots[-1]['metadata']['slot'] = 11.0
        callbacks['reserve'].side_effect = reserve
        def complete(provider, instruction, data, budget, **kwargs):
            budget.reserve_ai(slots[0]['metadata']['reservation_usd'], 1, .02)
            self.fail('Changed slot reached the transmission boundary')
        with patch.object(executor, 'complete_with_receipt', side_effect=complete), self.assertRaises(EvaluationStopped):
            executor.execute_cases(self.provider, slots, manifest=self.source, read=lambda n: self.files[n], **callbacks)
        callbacks['claim'].assert_called_once()
        callbacks['reserve'].assert_called_once()
        callbacks['retain_terminal'].assert_not_called()
        callbacks['record'].assert_not_called()
        self.opener.assert_not_called()

    def test_final_snapshot_foreign_reservation_cannot_be_sealed(self):
        snapshot = runner.snapshot
        finalization_snapshots = 0
        def changed_snapshot(before):
            nonlocal finalization_snapshots
            if (self.out/'summary.json').exists() and not (self.out/'final-integrity.json').exists():
                finalization_snapshots += 1
                if finalization_snapshots == 2:
                    self.original.reserve_ai_allowance(runner.ALLOWANCE, 'foreign-finalization', .01, 10)
            return snapshot(before)
        with patch.object(runner, 'snapshot', side_effect=changed_snapshot), self.assertRaises(EvaluationStopped):
            runner.run(self.out, self.anchor, self.authorization)
        self.assertEqual(self.opener.return_value.open.call_count, 11)
        self.assertTrue((self.out/'final-integrity.json').exists())
        self.assertFalse((self.out/'owned-artifacts.json').exists())

    def test_persistence_slot_mutation_after_charge_stops_before_transmission(self):
        slots = self.slots()
        callbacks = {name: Mock() for name in ('gate', 'identity', 'claim', 'reserve', 'persist', 'retain_terminal', 'record')}
        callbacks['cancelled'] = Mock(return_value=False)
        def persist(*args):
            slots[-1]['metadata']['slot'] = 11.0
        callbacks['persist'].side_effect = persist
        with self.assertRaises(EvaluationStopped):
            executor.execute_cases(self.provider, slots, manifest=self.source, read=lambda n: self.files[n], **callbacks)
        callbacks['reserve'].assert_called_once()
        self.opener.return_value.open.assert_not_called()
        callbacks['retain_terminal'].assert_not_called()
        callbacks['record'].assert_not_called()

    def test_retained_final_snapshot_must_match_prefix_even_if_live_db_is_valid(self):
        snapshot = runner.snapshot
        finalization_snapshots = 0
        def mismatched_snapshot(before):
            nonlocal finalization_snapshots
            result = snapshot(before)
            if (self.out/'summary.json').exists() and not (self.out/'final-integrity.json').exists():
                finalization_snapshots += 1
                if finalization_snapshots == 2:
                    result['tables']['ml_jobs'] = '0'*64
            return result
        with patch.object(runner, 'snapshot', side_effect=mismatched_snapshot), self.assertRaises(EvaluationStopped):
            runner.run(self.out, self.anchor, self.authorization)
        self.assertEqual(self.opener.return_value.open.call_count, 11)
        self.assertTrue((self.out/'final-integrity.json').exists())
        self.assertFalse((self.out/'owned-artifacts.json').exists())

    def test_owned_baseline_cannot_drop_v2_assessment_with_fresh_owned_anchor(self):
        baseline = runner.load(self.out/'baseline.json')
        baseline['artifacts'].pop(next(n for n in baseline['artifacts'] if 'policy-v2-owned-assessment' in n))
        (self.out/'baseline.json').write_text(json.dumps(baseline))
        self.owned['baseline_sha256'] = legacy.sha(self.out/'baseline.json')
        (self.out/'prepared.json').write_text(json.dumps(self.owned))
        with self.assertRaises(EvaluationStopped):
            runner.run(self.out, legacy.sha(self.out/'prepared.json'), self.authorization)
        self.environment.assert_not_called()
        self.opener.assert_not_called()


if __name__ == '__main__':
    unittest.main()
