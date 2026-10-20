"""Offline authored responses over pinned blockCV documentation, not AI-quality evidence."""
import copy
import gzip
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from github_cli import ActiveAccountChangedError
from missing_link.analysis import validate_request
from missing_link.provider import Provider, CandidateValidationError
from missing_link.service import Budget, Cancelled, Paused, Service
from missing_link.sources import extract_structure
from missing_link.strategies import VERSION, INSTRUCTION
from test_missing_link import wire_request


def blockcv():
    path = Path(__file__).resolve().parents[1] / 'docs/experiments/prediction-error-operation-2026-10-20/source-sample.json.gz'
    repo = json.loads(gzip.decompress(path.read_bytes()))['repository']
    repo['capabilities'] = extract_structure(repo)
    return repo


def demand():
    body = ('Validate prediction errors after withholding groups of dependent observations. '
            'Report unobservable outputs rather than inventing values.')
    issue = dict(id=701, url='https://github.com/example/inverse-model/issues/1', title='Excluded prediction errors',
        body=body, comments=[], context_complete=True, fingerprint='independent-authored-demand', public=True)
    raw = dict(outcome='Construct excluded-prediction errors', status='unresolved', status_source_ids=['q0'],
        status_reason='Authored open requirement', optional_field_dispositions=[], environment=[], prior_attempts=[],
        missing_information=[], requirements=[dict(text=text, mandatory=True, explicit=True, source_id='q0', quote=text, inference='')
            for text in ('Validate prediction errors after withholding groups of dependent observations.',
                         'Report unobservable outputs rather than inventing values.')])
    return issue, raw


def response(data, relevance='pertinent'):
    # Cite the supplied first README chunk containing blockCV's grouped-CV description.
    ref = next(key for key in data['sources'] if key.startswith('file:README.md#L1-'))
    return dict(strategies=[dict(title='Grouped validation matched to prediction conditions', relevance=relevance,
        reason='A documented grouping mechanism may inform excluded-prediction examples; native value remains unknown.',
        mechanism='Separate dependent training and testing groups and check separation against prediction conditions.',
        requirement_ids=['r0'], source_ids=[ref],
        adaptation=['Map dependence to shared references and continuity segments; do not transplant spatial distances blindly.'],
        assumptions=['A suitable dependence measure can be estimated from admitted data.'],
        limitations=['Does not recover an unrestricted unobserved clock.', 'No new RF benefit is demonstrated.'],
        direct_alternative='Explicit mask-consistent refits with the existing primitives.',
        expected_advantage='Possibly more representative examples, not an established advantage over the direct alternative.',
        probe=dict(baseline='Existing explicit refits with fixed groups.', change='Change only the group design.',
            success_criterion='Improve an independent comparison on identical supported outputs without regressions.',
            failure_criterion='No gain over direct refits, lost estimability, or changed acceptance criteria.'))])


class StrategyProviderTests(unittest.TestCase):
    def setUp(self):
        self.repo = blockcv()
        self.issue, self.raw_request = demand()
        self.request = validate_request(self.raw_request, self.issue)
        self.provider = Provider({'REPOTRACTION_AI_URL': 'http://localhost/v1', 'REPOTRACTION_AI_MODEL': 'fixture'})
        self.job = dict(id='fixture', input={'max_requests': 20}, ai_calls_used=0, cost_reserved_usd=0., checkpoint={})
        self.budget = Budget(self.job, lambda: None, lambda: False, lambda: None)
        self.wires = []

    def run_response(self, change=lambda raw: raw, budget=None):
        def send(req, **kwargs):
            wire = json.loads(req.data)
            data = json.loads(wire['messages'][1]['content'].split('\nUNTRUSTED_DATA_JSON:\n')[-1])
            self.wires.append(data)
            raw = change(response(data))
            return io.BytesIO(json.dumps({'choices': [{'message': {'content': json.dumps(raw)}}]}).encode())
        with mock.patch('urllib.request.build_opener') as opener:
            opener.return_value.open.side_effect = send
            return self.provider.suggest_strategies(self.repo, self.issue, self.request, budget or self.budget)

    def test_pinned_documentation_can_support_an_untested_strategy_without_code(self):
        original = copy.deepcopy(self.repo)
        item = self.run_response()[0]
        self.assertEqual(item['kind'], 'documented_strategy')
        self.assertEqual(item['relevance'], 'pertinent')
        self.assertEqual(item['relevance_status'], 'unverified_assessment')
        self.assertEqual(item['benefit_status'], 'not_tested')
        self.assertEqual(item['verification']['status'], 'not_executed')
        self.assertFalse(item['qualified'])
        self.assertEqual(item['request']['requirements'], self.request['requirements'])
        self.assertEqual(item['revision'], '51e6903fe652411248aa20937c80b122e5e12e09')
        self.assertIn('training and testing folds', item['evidence'][0]['quote'])
        self.assertIn('/blob/' + item['revision'] + '/README.md#L', item['evidence'][0]['url'])
        self.assertEqual(item['evidence'][0]['sha'], '0d72d4ca070d3afbdddfb86d02454aa33f90df48')
        self.assertTrue(item['analysis_context']['implementation_context_missing'])
        self.assertEqual(self.job['ai_calls_used'], 1)
        self.assertEqual(self.job['checkpoint']['ai_outputs'][0]['phase'], 'strategies')
        self.assertEqual(self.repo, original)

    def test_documentation_also_remains_available_when_the_sample_contains_code(self):
        self.repo['files'].append(dict(path='unrelated.py', kind='source', text='print("unrelated marker")'))
        self.run_response()
        supplied = json.dumps(self.wires[-1])
        self.assertNotIn('unrelated marker', supplied)
        self.assertFalse(self.wires[-1]['repository']['capabilities'])

    def test_non_readme_design_note_and_different_operation_use_the_same_path(self):
        issue = dict(self.issue, title='Undo without repeated copies', body='Undo edits without copying the whole document.',
                     fingerprint='independent-undo-fixture')
        raw_request = copy.deepcopy(self.raw_request)
        raw_request['requirements'] = [dict(text=issue['body'], mandatory=True, explicit=True,
            source_id='q0', quote=issue['body'], inference='')]
        request = validate_request(raw_request, issue)
        repo = dict(self.repo, id=802, full_name='example/edit-journal', revision='c'*40, capabilities=[],
            files=[dict(path='docs/design.md', kind='documentation', sha='d'*40,
                url='https://github.com/example/edit-journal/blob/'+'c'*40+'/docs/design.md',
                text='Store the inverse of each edit in a journal.\nUndo by applying inverse edits in reverse order.')])
        def authored(instruction, data, budget, schema, phase):
            raw = response({'sources': {'file:README.md#L1-L60': {}}})
            item = raw['strategies'][0]
            item.update(title='Inverse edit journal', mechanism='Store inverse operations and replay them in reverse.',
                reason='An inverse journal may avoid full copies for undo.',
                source_ids=[next(key for key in data['sources'] if key.startswith('file:docs/design.md#'))],
                adaptation=['Define inverses for the target edit operations.'], assumptions=['Edits admit safe inverses.'],
                limitations=['Not all operations are reversible.'], direct_alternative='Full document snapshots.',
                expected_advantage='Possibly less memory; not measured.',
                probe=dict(baseline='Snapshot-based undo.', change='Use inverse edits for the same sequence.',
                    success_criterion='Same restored content with less memory and no regressions.',
                    failure_criterion='An edit cannot be reversed or memory does not improve.'))
            return raw
        with mock.patch.object(self.provider, 'complete', side_effect=authored):
            item = self.provider.suggest_strategies(repo, issue, request, self.budget)[0]
        self.assertEqual(item['evidence'][0]['path'], 'docs/design.md')
        self.assertEqual(item['benefit_status'], 'not_tested')
        self.assertEqual(item['request']['requirements'][0]['text'], issue['body'])

    def test_irrelevance_unknown_and_empty_results_remain_legitimate_outcomes(self):
        for relevance in ('not_pertinent', 'undetermined'):
            def change(raw):
                raw['strategies'][0]['relevance'] = relevance
                return raw
            item = self.run_response(change)[0]
            self.assertEqual(item['relevance'], relevance)
            self.assertEqual(item['benefit_status'], 'not_tested')
        self.assertEqual(self.run_response(lambda raw: {'strategies': []}), [])

    def test_claimed_benefit_execution_or_qualification_cannot_enter_result(self):
        for field, value in (('benefit_status', 'demonstrated'), ('qualified', True), ('verification', {'status': 'passed'})):
            def change(raw):
                raw['strategies'][0][field] = value
                return raw
            with self.subTest(field=field), self.assertRaises(CandidateValidationError):
                self.run_response(change)

    def test_discussion_target_or_omitted_lines_cannot_substitute_for_documentation(self):
        for ref in ('q0', 'target:README.md#L1-L60', 'file:README.md#L900-L901', 'file:absent.py#L1-L2'):
            def change(raw):
                raw['strategies'][0]['source_ids'] = [ref]
                return raw
            with self.subTest(ref=ref), self.assertRaises(CandidateValidationError):
                self.run_response(change)

    def test_a_pertinent_label_needs_an_adaptation_and_a_discriminating_comparison(self):
        for field, value in (('adaptation', []), ('direct_alternative', ''), ('probe',
                dict(baseline='', change='', success_criterion='', failure_criterion=''))):
            def change(raw):
                raw['strategies'][0][field] = value
                return raw
            with self.subTest(field=field), self.assertRaises(CandidateValidationError):
                self.run_response(change)

    def test_no_documentation_or_resolved_demand_makes_no_call(self):
        for repo, request in ((dict(self.repo, files=[]), self.request),
                              (self.repo, dict(self.request, status='resolved'))):
            with mock.patch.object(self.provider, 'complete') as complete:
                self.assertEqual(self.provider.suggest_strategies(repo, self.issue, request, self.budget), [])
            complete.assert_not_called()

    def test_implementation_only_guards_are_not_weakened_for_reuse(self):
        for phase in ('capabilities', 'matches'):
            with self.subTest(phase=phase), self.assertRaises(CandidateValidationError):
                self.provider._bounded_context(self.repo, self.issue, phase, INSTRUCTION, self.request)
        self.assertEqual(self.job['ai_calls_used'], 0)

    def test_cancellation_identity_and_budget_checks_still_precede_transmission(self):
        budgets = [Budget(self.job, lambda: None, lambda: True, lambda: None),
            Budget(self.job, lambda: None, lambda: False, mock.Mock(side_effect=ActiveAccountChangedError('changed')))]
        self.job['ai_calls_used'] = self.provider.max_calls
        budgets.append(self.budget)
        for budget in budgets:
            with mock.patch('urllib.request.build_opener') as opener, self.assertRaises((Cancelled, ActiveAccountChangedError, Paused)):
                self.provider.suggest_strategies(self.repo, self.issue, self.request, budget)
            opener.assert_not_called()

    def test_atomic_allowance_rejection_prevents_the_new_phase_from_transmitting(self):
        reserve = mock.Mock(side_effect=Paused('allowance exhausted'))
        budget = Budget(self.job, lambda: None, lambda: False, lambda: None, reserve_total=reserve)
        with mock.patch('urllib.request.build_opener') as opener, self.assertRaises(Paused):
            self.provider.suggest_strategies(self.repo, self.issue, self.request, budget)
        reserve.assert_called_once()
        opener.assert_not_called()
        self.assertEqual(self.job['ai_calls_used'], 0)


class StrategyServiceTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.provider = Provider({'REPOTRACTION_AI_URL': 'http://localhost/v1', 'REPOTRACTION_AI_MODEL': 'fixture'})
        self.service = Service(Path(temp.name)/'db.sqlite3', 'alice', mock.Mock(), lambda: 'alice', self.provider)
        self.issue, self.request = demand()
        self.source = mock.Mock()
        self.source.fetch_repository.return_value = blockcv()
        self.source.fetch_issue.return_value = self.issue
        self.source.fetch_reference_context.return_value = dict(id=801, full_name='example/inverse-model',
            revision='b'*40, public=True, files=[], fingerprint='target-context')
        self.phases = []
        self.invalid = False

    def send(self, req, **kwargs):
        wire = json.loads(req.data)
        data = json.loads(wire['messages'][1]['content'].split('\nUNTRUSTED_DATA_JSON:\n')[-1])
        if 'strategy_version' in data:
            self.phases.append('strategies')
            raw = response(data)
            if self.invalid:
                raw['strategies'][0]['benefit_status'] = 'demonstrated'
        elif 'discovery_goal' in data:
            from test_missing_link_request_discovery import decision
            self.phases.append('plan')
            raw = decision()
            raw['direct_alternative']['description'] = 'Explicit masked refits.'
            raw['benefit_hypothesis'] = 'A documented grouping strategy may improve representativeness.'
            raw['benefit_test'] = 'Compare on unchanged supported outputs with native refits.'
            raw['operations'][0].update(operation='Construct excluded-prediction errors', input='Grouped observations',
                output='Excluded prediction errors', rationale='Training residuals are not excluded errors.',
                search_terms='grouped validation prediction errors')
        elif 'plan' in data:
            self.assertEqual(data['plan']['discovery_goal'], 'documented_strategy')
            self.phases.append('select')
            raw = dict(decision='inspect', candidate_id='source0', operation_ids=['op0'],
                reason='Examine its documented grouping mechanism, not its implementation language.',
                source_check='Check the README explanation and its assumptions.', risks=['RF adaptation untested'])
        else:
            self.phases.append('request')
            raw = wire_request(data, self.request)
        return io.BytesIO(json.dumps({'choices': [{'message': {'content': json.dumps(raw)}}]}).encode())

    def test_explicit_discover_persists_strategy_and_never_creates_a_reuse_match(self):
        with mock.patch('missing_link.service.PublicGitHub', return_value=self.source), \
                mock.patch('urllib.request.build_opener') as opener, \
                mock.patch.object(self.provider, 'interpret_capabilities') as capabilities, \
                mock.patch.object(self.provider, 'evaluate') as evaluate:
            opener.return_value.open.side_effect = self.send
            started = self.service.start(dict(repo='rvalavi/blockCV', action='discover', strategies=True,
                issue_url=self.issue['url'], use_ai=True), background=False)
        job = self.service.store.get('jobs', started['job_id'])
        self.assertEqual(job['status'], 'completed', job.get('error'))
        self.assertEqual(job['checkpoint']['strategy_version'], VERSION)
        self.assertEqual(job['ai_calls_used'], 2)
        self.assertEqual(self.phases, ['request', 'strategies'])
        self.assertEqual(job['result']['match_ids'], [])
        self.assertEqual(len(job['result']['strategies']['0']['items']), 1)
        self.assertEqual(self.service.store.list('matches'), [])
        capabilities.assert_not_called()
        evaluate.assert_not_called()
        self.assertIn('strategies', self.service.state()['jobs'][0]['result'])

    def test_request_led_discovery_selects_documentation_without_capability_or_match_calls(self):
        self.source.search_repositories.return_value = dict(query='bounded query', items=[dict(full_name='rvalavi/blockCV',
            upstream_rank=1, description='Spatially separated validation groups')], complete=False)
        with mock.patch('missing_link.service.PublicGitHub', return_value=self.source), \
                mock.patch('urllib.request.build_opener') as opener:
            opener.return_value.open.side_effect = self.send
            started = self.service.start(dict(action='discover_from_request', strategies=True,
                issue_url=self.issue['url'], use_ai=True), background=False)
        job = self.service.store.get('jobs', started['job_id'])
        self.assertEqual(job['status'], 'completed', job.get('error'))
        self.assertEqual(self.phases, ['request', 'plan', 'select', 'strategies'])
        self.assertEqual(job['ai_calls_used'], 4)
        self.assertEqual(job['result']['match_ids'], [])
        self.assertEqual(job['result']['strategies']['0']['items'][0]['benefit_status'], 'not_tested')
        self.source.fetch_repository.assert_called_once_with('rvalavi/blockCV')
        self.source.search_repositories.assert_called_once_with('grouped validation prediction errors')

    def test_invalid_benefit_claim_is_retained_as_a_failed_attempt_without_retry_or_strategy(self):
        self.invalid = True
        with mock.patch('missing_link.service.PublicGitHub', return_value=self.source), \
                mock.patch('urllib.request.build_opener') as opener:
            opener.return_value.open.side_effect = self.send
            started = self.service.start(dict(repo='rvalavi/blockCV', strategies=True,
                issue_url=self.issue['url'], use_ai=True), background=False)
        job = self.service.store.get('jobs', started['job_id'])
        self.assertTrue(job['result']['partial'])
        self.assertEqual(job['ai_calls_used'], 2)
        self.assertEqual(len(job['checkpoint']['ai_outputs']), 2)
        self.assertEqual(job['result']['match_ids'], [])
        self.assertNotIn('strategies', job['result'])
        self.assertEqual(self.phases, ['request', 'strategies'])

    def test_new_mode_is_explicit_and_cannot_be_used_for_execution_or_structural_jobs(self):
        base = dict(repo='rvalavi/blockCV', action='discover', strategies=True, issue_url=self.issue['url'], use_ai=True)
        for change in ({'use_ai': False}, {'action': 'analyze'}, {'issue_url': ''},
                       {'strategies': 'true'}, {'behavioral_examples': True}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.service.start(dict(base, **change), background=False)
        self.assertEqual(self.service.store.list('jobs'), [])
