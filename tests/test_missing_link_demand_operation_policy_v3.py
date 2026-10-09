"""Authored offline mechanics; no generated predictions or adherence claims."""
import copy
import json
import unittest
from unittest.mock import patch

from missing_link.provider import Provider
from scripts import missing_link_demand_operation_policy as original
from scripts import missing_link_demand_operation_policy_v2 as prior
from scripts import missing_link_demand_operation_policy_v3 as revised
from scripts.missing_link_demand_operation_review import review_prediction
from scripts.missing_link_repository_only_run import knobs
from test_missing_link_demand_operation_policy import (
    packet, unknown, stated_field, operator_review)


class DemandOperationPolicyV3Tests(unittest.TestCase):
    def test_explicit_successor_preserves_both_prior_envelopes_and_packet(self):
        data = packet('Implement a record export with a required fallback.')
        data['id'] = 'private-reference-hint-not-for-model'
        before = copy.deepcopy(data)
        old, v2 = original.build_request(data), prior.build_request(data)
        new = revised.build_request(data)
        self.assertEqual(set(new), {'instructions', 'context', 'schema'})
        self.assertEqual(new['instructions'], revised.PROMPT)
        for retained in (old, v2):
            self.assertEqual(new['context'], retained['context'])
            self.assertEqual(new['schema'], retained['schema'])
            self.assertNotEqual(new['instructions'], retained['instructions'])
        self.assertNotIn(data['id'], json.dumps(new))
        self.assertEqual(data, before)
        self.assertEqual(original.build_request(data), old)
        self.assertEqual(prior.build_request(data), v2)

    def test_native_encoding_changes_only_the_instruction_content(self):
        data = packet('Required fallback; preferred resumable export if available.')
        provider = Provider(knobs())  # Public encoder; no key or request.
        def encode(envelope):
            return provider._encode_prompt(envelope['instructions'], envelope['context'],
                                          envelope['schema'], 'request')
        endpoint, payload, body = encode(revised.build_request(data))
        for policy in (original, prior):
            retained = policy.build_request(data)
            old_endpoint, old_payload, old_body = encode(retained)
            expected = copy.deepcopy(old_payload)
            expected['input'][1]['content'] = expected['input'][1]['content'].replace(
                retained['instructions'], revised.PROMPT, 1)
            self.assertEqual(endpoint, old_endpoint)
            self.assertEqual(payload, expected)
            self.assertNotEqual(body, old_body)
        self.assertEqual(endpoint, '/responses')
        self.assertTrue(payload['text']['format']['strict'])
        self.assertEqual(payload['text']['format']['name'], 'missing_link_request')
        self.assertTrue(payload['stream'])
        self.assertFalse(payload['store'])

    def test_complete_utf8_bound_includes_instructions_context_and_schema(self):
        data = packet('Export α records. Preserve 終.')
        envelope = revised.build_request(data)
        bound = len(original._bytes(envelope))
        self.assertGreater(bound, len(original._bytes(envelope['context'])))
        with patch.object(revised, 'MAX_ENVELOPE_BYTES', bound):
            self.assertEqual(revised.build_request(data), envelope)
        with patch.object(revised, 'MAX_ENVELOPE_BYTES', bound - 1):
            with self.assertRaisesRegex(ValueError, 'envelope'):
                revised.build_request(data)

    def test_exact_partial_coverage_and_citations_are_not_repaired(self):
        data = packet('α' * 501)
        data['root_sections'].append({'source': 'root', 'original_start': 900,
            'original_end': 903, 'text': 'β\r\n'})
        data.update(root_fully_read=False, omitted_root_char_ranges=[[501, 900]])
        context = revised.build_request(data)['context']
        self.assertEqual(context, original.build_context(data))
        self.assertEqual(list(context['root_spans'].values())[-1]['quote'], 'β\r\n')
        altered = copy.deepcopy(context)
        altered['coverage']['omitted_root_char_ranges'] = []
        with self.assertRaisesRegex(ValueError, 'immutable original'):
            revised.normalize_prediction(unknown(), altered, packet=data)
        raw = unknown()
        raw['fields']['runtime'] = stated_field('Declared target only.', 'not-a-span')
        with self.assertRaises(ValueError):
            revised.normalize_prediction(raw, context, packet=data)

    def test_operator_reference_metadata_cannot_enter_the_request(self):
        for key in ('reference', 'expected_relation', 'title', 'operator_reason'):
            data = packet()
            data[key] = 'An authored answer must remain separate.'
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'references must stay separate'):
                revised.build_request(data)

    def test_authored_minimum_and_open_choice_keep_distinct_card_states(self):
        # These cards are authored, not inferred by the builder or normalizer.
        for open_choice in (False, True):
            data = packet('Owner chooses export form; all options preserve order.' if open_choice else
                'Export must fail clearly at minimum; prefer resumption. All exports preserve order.')
            cite = next(iter(revised.build_context(data)['root_spans']))
            raw = unknown()
            raw['request_kind'].update(value='design_question' if open_choice else
                'implementation_requested', citation_ids=[cite])
            raw['fields']['requested_change'] = stated_field('Determine export behavior.', cite)
            raw['query_relation'].update(value='context_only', citation_ids=[cite])
            raw['constraints'] = [{'text': 'All options preserve order.',
                'reason': 'Authored explicit local obligation.', 'citation_ids': [cite]}]
            if not open_choice:
                raw['fields']['output_shape'] = stated_field(
                    'Clear failure at minimum; resumption preferred but not selected.', cite)
                raw['fields']['acceptance'] = stated_field('All exports preserve order.', cite)
            before = copy.deepcopy(raw)
            checked = revised.normalize_prediction(raw, revised.build_context(data), packet=data)
            with self.subTest(open_choice=open_choice):
                self.assertEqual(checked, original.normalize_prediction(raw, original.build_context(data), packet=data))
                self.assertEqual(checked['prediction'], before)
                self.assertEqual('output_shape' in checked['mechanical_summary']['unknown_fields'], open_choice)
                self.assertEqual('acceptance' in checked['mechanical_summary']['unknown_fields'], open_choice)
                self.assertFalse(checked['semantic_support_verified'])

    def test_reported_fact_as_requirement_remains_visible_to_operator_review(self):
        data = packet('A prior probe reportedly passed. Future exports must preserve order.')
        cite = next(iter(revised.build_context(data)['root_spans']))
        raw = unknown()
        raw['fields']['acceptance'] = stated_field('Future exports preserve order.', cite)
        raw['constraints'] = [{'text': 'The prior probe passed.',
            'reason': 'Wrongly categorized observation.', 'citation_ids': [cite]}]
        checked = revised.normalize_prediction(raw, revised.build_context(data), packet=data)
        review = operator_review(raw)
        review['constraints'][0] = {'verdict': 'unsupported',
            'reason': 'Reported outcome is not an imposed requirement.'}
        audited = review_prediction(checked, review)
        self.assertEqual(audited['checked']['prediction'], raw)
        self.assertEqual(audited['claim_paths']['unsupported'], ['constraints.0'])
        self.assertFalse(audited['semantic_support_verified'])
        self.assertFalse(audited['changes_qualification'])

    def test_wrong_relation_identifiers_and_broad_gap_are_not_semantically_rejected(self):
        data = packet('Relink a record. Source and destination examples conflict; conditional order preservation is required.')
        cite = next(iter(revised.build_context(data)['root_spans']))
        raw = unknown()
        raw['request_kind'].update(value='implementation_requested', citation_ids=[cite])
        raw['fields']['requested_change'] = stated_field('Relink a record.', cite)
        raw['fields']['output_shape'] = stated_field('Invented source urn:new:A and destination urn:new:B.', cite)
        raw['query_relation'].update(value='requested_operation', reason='Shared vocabulary alone.', citation_ids=[cite])
        raw['context_gaps'] = ['No conditional criterion is given.', 'Source and destination identifiers conflict.']
        before = copy.deepcopy(raw)
        checked = revised.normalize_prediction(raw, revised.build_context(data), packet=data)
        review = operator_review(raw)
        review['fields']['output_shape'] = {'verdict': 'unsupported', 'reason': 'Both literals are authored inventions.'}
        review['query_relation'] = {'verdict': 'unsupported', 'reason': 'Shared words do not establish the operation.'}
        review['context_gaps'] = [
            {'verdict': 'unsupported', 'reason': 'The root supplies a conditional criterion.'},
            {'verdict': 'supported', 'reason': 'Both affected roles are explicitly discrepant.'}]
        audited = review_prediction(checked, review)
        self.assertEqual(raw, before)
        self.assertEqual(audited['checked']['prediction'], before)
        self.assertEqual(audited['claim_counts']['unsupported'], 3)
        self.assertIn('context_gaps.0', audited['claim_paths']['unsupported'])
        self.assertFalse(audited['changes_selection'])
        self.assertFalse(audited['changes_qualification'])


if __name__ == '__main__':
    unittest.main()
