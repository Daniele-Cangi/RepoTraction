"""D3-shaped citation regression, not execution or a repaired live comparison.

The synthetic 65-line fixture retains the observed 4--6 delegation wrapper and
mixed 1--60/61--65 excerpt boundaries. It neither imports nor runs acquired code.
"""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from missing_link.analysis import evidence_catalog, resolve_evidence, validate_matches, validate_request
from missing_link.context import normalize_references, supplied_reference
from missing_link.operation_evidence import cites_operation_body, operation_regions
from missing_link.proofs import export_handoff
from missing_link.provider import CandidateValidationError, Provider
from missing_link.sources import extract_structure
from missing_link.store import Store
import test_missing_link_partial_support as partial_fixtures


def group_case():
    repo, issue, _, raw = partial_fixtures.PartialSupportTests().case()
    lines = [
        'import { nest } from "./nest.js";',
        'import { identity } from "./identity.js";',
        '',
        'export default function group(values, ...keys) {',
        '  return nest(values, identity, identity, keys);',
        '}',
        '',
        'export function sibling(values) {',
        '  return values.length;',
        '}',
    ]
    lines.extend([''] * (60 - len(lines)))
    lines.extend(['function unrelated(values) {', '  return values.slice();', '}', '', '// End of synthetic fixture.'])
    repo['files'] = [{'path': 'src/group.js', 'kind': 'source', 'text': '\n'.join(lines),
        'url': 'https://github.com/example/fixture/blob/' + 'a' * 40 + '/src/group.js'}]
    repo['capabilities'] = extract_structure(repo)
    raw['capability_id'] = next(cap['id'] for cap in repo['capabilities'] if cap['entrypoint'].endswith(':group'))
    issue.update(body='Delegate grouping inputs to a supplied grouping helper. Integrate the result into the consumer.', comments=[])
    demand = {'outcome': 'Consumer grouping integration', 'status': 'unresolved', 'status_reason': 'Synthetic fixture only',
        'status_source_ids': ['q0'], 'requirements': [{'text': issue['body'], 'quote': issue['body'],
            'source_id': 'q0', 'mandatory': True, 'explicit': True, 'inference': ''}]}
    request = validate_request(demand, issue)
    raw['checks'][0]['reason'] = 'The wrapper delegates inputs; consumer integration remains unverified.'
    raw['partial_support'][0].update(operation='Delegate grouping inputs to nest',
        requirement_part='Forward values and keys', remaining_work='Consumer integration and helper semantics remain unverified')
    return repo, issue, request, raw


class GroupCitationTests(unittest.TestCase):
    def provider_result(self, references, *, omitted_body=False):
        repo, issue, request, raw = group_case()
        raw['checks'][0]['source_ids'] = references
        raw['partial_support'][0]['source_ids'] = references
        before = copy.deepcopy((repo, issue, request, raw))
        provider = Provider({'REPOTRACTION_AI_URL': 'http://localhost/v1', 'REPOTRACTION_AI_MODEL': 'fixture'})
        budget = mock.Mock()
        original_pack = provider._bounded_context

        def pack(*args):
            data, report = original_pack(*args)
            if omitted_body:
                data['sources'] = {key: entry for key, entry in data['sources'].items() if not entry.get('path')}
                ref = 'file:src/group.js#L4-L4'
                data['sources'][ref] = resolve_evidence(ref, evidence_catalog(repo, issue))
            return data, report

        with mock.patch.object(provider, '_bounded_context', side_effect=pack), \
             mock.patch.object(provider, 'complete', return_value={'matches': [raw]}) as complete, \
             mock.patch('urllib.request.build_opener', side_effect=AssertionError('No provider HTTP')):
            result = provider.evaluate(repo, issue, request, budget)[0]
        budget.reserve_ai.assert_not_called()
        self.assertEqual((repo, issue, request, raw), before)
        instruction, data, _, schema, phase = complete.call_args.args
        self.assertLessEqual(len(provider._encode_prompt(instruction, data, schema, phase)[2]), 180000)
        return result, data, instruction, before

    def test_precise_wrapper_is_already_offered_and_only_establishes_delegation(self):
        reference = 'file:src/group.js#L4-L6'
        result, data, instruction, (repo, issue, _, _) = self.provider_result([reference])
        selected = next(cap for cap in data['repository']['capabilities'] if cap['entrypoint'].endswith(':group'))
        self.assertEqual(selected['implementation_bounds'], [{'line': 4, 'end_line': 6}])
        self.assertIn(reference, data['sources'])
        self.assertTrue(supplied_reference(reference, data['sources'], evidence_catalog(repo, issue)))
        self.assertIn('not every behavior of its callee', instruction)
        check = result['checks'][0]
        self.assertEqual(check['contribution'], 'partial_behavior')
        self.assertEqual(check['status'], 'undetermined')
        self.assertEqual(result['discovery_assessment']['status'], 'partial_contribution')
        self.assertFalse(result['discovery_assessment']['eligible_for_followup'])
        self.assertNotIn('support_normalization', check)
        self.assertIn('consumer integration remains unverified', check['reason'])
        self.assertEqual(check['evidence'][0]['quote'], data['sources'][reference]['quote'])

    def test_actual_broad_ranges_are_not_silently_cropped_to_the_available_wrapper(self):
        refs = ['file:src/group.js#L1-L60', 'file:src/group.js#L61-L65']
        result, data, _, _ = self.provider_result(refs)
        self.assertIn('file:src/group.js#L4-L6', data['sources'])
        check = result['checks'][0]
        self.assertEqual(check['contribution'], 'not_demonstrated')
        self.assertEqual(check['status'], 'undetermined')
        self.assertEqual(check['support_normalization']['codes'], ['selected_operation_body_missing'])
        self.assertEqual([entry['source_id'] for entry in check['evidence']], refs)
        self.assertTrue(all('quote_selection' not in entry for entry in check['evidence']))
        self.assertEqual(result['discovery_assessment']['status'], 'similarity_only')
        self.assertFalse(result['discovery_assessment']['eligible_for_followup'])

    def test_normalized_wide_range_still_does_not_grant_selected_body_credit(self):
        repo, issue, request, raw = group_case()
        _, data, _, _ = self.provider_result(['file:src/group.js#L4-L6'])
        refs = normalize_references(['file:src/group.js#L1-L65'], data['sources'], evidence_catalog(repo, issue))
        self.assertEqual(refs, ['file:src/group.js#L1-L60', 'file:src/group.js#L61-L65'])
        raw['checks'][0]['source_ids'] = refs
        raw['partial_support'][0]['source_ids'] = refs
        result = validate_matches([raw], repo, issue, request, 'model')[0]
        self.assertEqual(result['checks'][0]['contribution'], 'not_demonstrated')

    def test_helper_sibling_and_signature_cannot_certify_the_wrapper(self):
        for ref in ('file:src/group.js#L4-L4', 'file:src/group.js#L8-L10', 'file:src/group.js#L61-L63'):
            with self.subTest(ref=ref):
                result, _, _, (repo, _, _, _) = self.provider_result([ref])
                regions = operation_regions(result['capability'], repo['files'])
                self.assertFalse(cites_operation_body(result['checks'][0]['evidence'][0], regions))
                self.assertEqual(result['checks'][0]['contribution'], 'not_demonstrated')
                self.assertFalse(result['discovery_assessment']['eligible_for_followup'])

    def test_available_bounds_do_not_restore_body_omitted_from_the_call(self):
        with self.assertRaisesRegex(CandidateValidationError, 'not actually provided'):
            self.provider_result(['file:src/group.js#L4-L6'], omitted_body=True)
        result, _, _, _ = self.provider_result(['file:src/group.js#L4-L4'], omitted_body=True)
        self.assertEqual(result['checks'][0]['contribution'], 'not_demonstrated')

    def test_downgrade_survives_restart_and_handoff_without_replacing_original_claim(self):
        result, _, _, (repo, _, _, raw) = self.provider_result(
            ['file:src/group.js#L1-L60', 'file:src/group.js#L61-L65'])
        with tempfile.TemporaryDirectory() as directory:
            store = Store(Path(directory) / 'fixture.sqlite3', 'fixture')
            store.put('matches', result['id'], result)
            restored = Store(store.path, 'fixture').get('matches', result['id'])
        self.assertEqual(restored, result)
        handoff = json.loads(json.dumps(export_handoff(restored, repo)))
        check = handoff['match']['checks'][0]
        self.assertEqual(check['partial_support'], raw['partial_support'][0])
        self.assertEqual(check['support_normalization']['original_reason'], raw['checks'][0]['reason'])
        self.assertEqual(check['support_normalization']['original_contribution'], 'partial_behavior')
        self.assertEqual(check['contribution'], 'not_demonstrated')


if __name__ == '__main__':
    unittest.main()
