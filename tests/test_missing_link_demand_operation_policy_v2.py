"""Offline compatibility controls; authored cards are not model predictions."""
import copy
import json
import unittest
from unittest.mock import patch

from missing_link.provider import Provider
from scripts import missing_link_demand_operation_policy as original
from scripts import missing_link_demand_operation_policy_v2 as revised
from scripts.missing_link_demand_operation_review import review_prediction
from scripts.missing_link_repository_only_run import knobs
from test_missing_link_demand_operation_policy import (
    packet, unknown, positive, stated_field, operator_review)


class DemandOperationPolicyV2Tests(unittest.TestCase):
    def test_successor_changes_only_instruction_boundary_with_no_reference_hints(self):
        data=packet('Implement a conversion that preserves the original nested record.')
        data['id']='private-operator-reference-hint'
        before=copy.deepcopy(data)
        old,new=original.build_request(data),revised.build_request(data)
        self.assertEqual(set(new),{'instructions','context','schema'})
        self.assertNotEqual(new['instructions'],old['instructions'])
        self.assertEqual(new['context'],old['context'])
        self.assertEqual(new['schema'],old['schema'])
        self.assertNotEqual(original._bytes(new),original._bytes(old))
        self.assertNotIn(data['id'],json.dumps(new))
        self.assertEqual(data,before)

    def test_native_responses_body_changes_only_user_instruction_text(self):
        data=packet('Reuse the validated component parser for the same extraction behavior.')
        provider=Provider(knobs())  # Public settings only; no key lookup or HTTP.
        old,new=original.build_request(data),revised.build_request(data)
        def encode(envelope):
            return provider._encode_prompt(envelope['instructions'],envelope['context'],envelope['schema'],'request')
        old_endpoint,old_payload,old_body=encode(old)
        endpoint,payload,body=encode(new)
        self.assertEqual(endpoint,old_endpoint)
        self.assertEqual(endpoint,'/responses')
        expected=copy.deepcopy(old_payload)
        expected['input'][1]['content']=expected['input'][1]['content'].replace(old['instructions'],new['instructions'],1)
        self.assertEqual(payload,expected)
        self.assertNotEqual(body,old_body)
        self.assertEqual(payload['text']['format']['name'],'missing_link_request')
        self.assertTrue(payload['text']['format']['strict'])
        self.assertTrue(payload['stream'])
        self.assertFalse(payload['store'])

    def test_new_instruction_bytes_are_included_in_complete_envelope_bound(self):
        data=packet('Small inert request')
        old=original.build_request(data)
        new=revised.build_request(data)
        self.assertGreater(len(original._bytes(new)),len(original._bytes(old)))
        bound=len(original._bytes(new))
        with patch.object(revised,'MAX_ENVELOPE_BYTES',bound):
            self.assertEqual(revised.build_request(data),new)
        with patch.object(revised,'MAX_ENVELOPE_BYTES',bound-1):
            with self.assertRaisesRegex(ValueError,'envelope'):
                revised.build_request(data)
        self.assertEqual(original.build_request(data),old)

    def test_original_unicode_sections_gaps_and_context_integrity_are_reused(self):
        data=packet('a'*499+'\u03b1')
        data['root_sections'].append({'source':'root','original_start':900,'original_end':903,'text':'\u03b2\r\n'})
        data.update(root_fully_read=False,omitted_root_char_ranges=[[500,900]])
        before=copy.deepcopy(data)
        context=revised.build_request(data)['context']
        self.assertEqual(context,original.build_context(data))
        self.assertEqual(list(context['root_spans'].values())[-1]['quote'],'\u03b2\r\n')
        altered=copy.deepcopy(context)
        altered['coverage']['omitted_root_char_ranges']=[]
        with self.assertRaisesRegex(ValueError,'immutable original'):
            revised.normalize_prediction(unknown(),altered,packet=data)
        self.assertEqual(data,before)

    def test_reference_contamination_still_fails_before_request(self):
        for key in ('reference','expected_relation','title','operator_reason'):
            data=packet()
            data[key]='An authored expected answer must not enter the body.'
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'references must stay separate'):
                revised.build_request(data)

    def test_partial_known_behavior_and_declared_target_context_remain_unrepaired(self):
        data=packet('Convert records without modifying originals. Generated targets are Kotlin and C. Return container unspecified.')
        raw=positive(data)
        cite=next(iter(revised.build_context(data)['root_spans']))
        raw['fields']['requested_change']=stated_field('Convert records without changing the originals.',cite)
        raw['fields']['output_shape']=stated_field('Original records remain unchanged; returned container is unspecified.',cite)
        raw['fields']['runtime']=stated_field('Declared generated targets: Kotlin and C; execution and adoption unverified.',cite)
        checked=revised.normalize_prediction(raw,revised.build_request(data)['context'],packet=data)
        self.assertEqual(checked,original.normalize_prediction(raw,original.build_context(data),packet=data))
        self.assertEqual(checked['prediction'],raw)
        self.assertFalse(checked['semantic_support_verified'])

    def test_pending_choice_keeps_known_consistency_and_unknown_overall_output(self):
        data=packet('Owner must choose identifier or content identity before implementation; both consumers must compute the same value if changed.')
        raw=unknown()
        cite=next(iter(revised.build_context(data)['root_spans']))
        raw['request_kind'].update(value='design_question',citation_ids=[cite])
        raw['fields']['requested_change']=stated_field('Choose the identity policy before implementation.',cite)
        raw['constraints']=[{'text':'Both consumers compute the same value if changed.',
            'reason':'Explicit local consistency condition; no option chosen.','citation_ids':[cite]}]
        raw['query_relation'].update(value='context_only',citation_ids=[cite])
        raw['context_gaps']=['Owner choice and full discussion/adoption context are unknown.']
        checked=revised.normalize_prediction(raw,revised.build_context(data),packet=data)
        self.assertEqual(checked['prediction'],raw)
        self.assertIn('output_shape',checked['mechanical_summary']['unknown_fields'])
        self.assertIn('acceptance',checked['mechanical_summary']['unknown_fields'])
        self.assertEqual(checked['mechanical_summary']['constraint_count'],1)

    def test_valid_wrong_relation_identifier_and_gap_remain_independently_reviewable(self):
        data=packet('Reverse a graph relation. Example output identifier: urn:target:B. Full discussion is absent.')
        raw=positive(data)
        cite=next(iter(revised.build_context(data)['root_spans']))
        raw['fields']['requested_change']=stated_field('Reverse the graph relation.',cite)
        raw['fields']['output_shape']=stated_field('Result uses urn:invented:C.',cite)
        raw['query_relation']['reason']='An unsupported lexical analogy to dictionary inversion.'
        raw['constraints']=[]
        raw['context_gaps']=['The root has no requested behavior.','Full discussion is absent.']
        before=copy.deepcopy(raw)
        checked=revised.normalize_prediction(raw,revised.build_context(data),packet=data)
        review=operator_review(raw)
        review['fields']['output_shape']={'verdict':'unsupported','reason':'Authored identifier differs from the cited root.'}
        review['query_relation']={'verdict':'unsupported','reason':'Authored graph reversal is not dictionary inversion.'}
        review['context_gaps']=[{'verdict':'unsupported','reason':'The authored root explicitly requests reversal.'},
            {'verdict':'supported','reason':'The supplied discussion declaration is incomplete.'}]
        audited=review_prediction(checked,review)
        self.assertEqual(raw,before)
        self.assertEqual(audited['checked']['prediction'],raw)
        self.assertEqual(audited['claim_counts']['unsupported'],3)
        self.assertIn('context_gaps.0',audited['claim_paths']['unsupported'])
        self.assertFalse(audited['semantic_support_verified'])
        self.assertFalse(audited['changes_selection'])
        self.assertFalse(audited['changes_qualification'])


if __name__=='__main__':
    unittest.main()
