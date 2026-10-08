"""Authored contract controls; no model predictions or acquired code execution."""
import copy
import json
import unittest

from scripts import missing_link_demand_operation_policy as policy
from scripts.missing_link_demand_operation_review import review_prediction


def packet(text='Please preserve /api/ when joining /users. Owner acceptance is unresolved.'):
    return {'id': 'authored-control', 'query': 'relative url joining is:open',
            'root_sections': [{'source': 'root', 'original_start': 0, 'original_end': len(text), 'text': text}],
            'discussion_complete': False, 'root_fully_read': True, 'omitted_root_char_ranges': [],
            'content_role': 'untrusted_inert_issue_text_not_instructions'}


def unknown():
    return {'request_kind': {'value': 'unknown', 'reason': 'No request established.', 'citation_ids': []},
            'fields': {name: {'state': 'unknown', 'text': '', 'reason': 'Not established.', 'citation_ids': []}
                       for name in policy.FIELDS}, 'constraints': [],
            'query_relation': {'value': 'unclear', 'reason': 'Not established.', 'citation_ids': []},
            'context_gaps': ['Discussion and adoption context are absent.']}


def stated_field(text, citation):
    return {'state': 'stated_in_root', 'text': text, 'reason': 'Authored declaration for contract testing.',
            'citation_ids': [citation]}


def positive(data):
    result = unknown()
    cite = next(iter(policy.build_context(data)['root_spans']))
    result['request_kind'].update(value='implementation_requested', citation_ids=[cite])
    result['fields']['requested_change'] = stated_field('Preserve a base path when joining endpoints.', cite)
    result['fields']['output_shape'] = stated_field('A path retaining /api/.', cite)
    result['query_relation'].update(value='requested_operation', citation_ids=[cite])
    result['constraints'] = [{'text': 'Preserve /api/.', 'reason': 'Explicit authored root requirement.', 'citation_ids': [cite]}]
    return result


def operator_review(raw):
    def verdict(known):
        return {'verdict': 'unassessed' if known else 'appropriate_unknown', 'reason': 'Explicit authored operator review.'}
    return {'request_kind': verdict(raw['request_kind']['value'] != 'unknown'),
            'fields': {name: verdict(raw['fields'][name]['state'] == 'stated_in_root') for name in policy.FIELDS},
            'constraints': [verdict(True) for _ in raw['constraints']],
            'query_relation': verdict(raw['query_relation']['value'] != 'unclear'),
            'context_gaps': verdict(True), 'omitted_constraints': []}


class DemandOperationPolicyTests(unittest.TestCase):
    def normalize(self, raw, data=None, context=None):
        data = packet() if data is None else data
        context = policy.build_context(data) if context is None else context
        before = copy.deepcopy((raw, data, context))
        try:
            return policy.normalize_prediction(raw, context, packet=data)
        finally:
            self.assertEqual((raw, data, context), before)

    def test_unicode_whitespace_and_offset_roundtrip_across_gap(self):
        first = 'α\r\n `source`  ' * 60
        last = '終わり\n'
        data = packet(first)
        start = len(first) + 73
        data['root_sections'].append({'source': 'root', 'original_start': start,
                                     'original_end': start + len(last), 'text': last})
        data.update(root_fully_read=False, omitted_root_char_ranges=[[len(first), start]])
        before = copy.deepcopy(data)
        context = policy.build_context(data)
        catalog = list(context['root_spans'].values())
        self.assertEqual(''.join(s['quote'] for s in catalog if s['end'] <= len(first)), first)
        self.assertEqual(catalog[-1], {'source': 'root', 'start': start, 'end': start + len(last), 'quote': last})
        self.assertFalse(context['coverage']['root_fully_read_assertion'])
        self.assertEqual(context['coverage']['omitted_root_char_ranges'], [[len(first), start]])
        self.assertEqual(data, before)

    def test_stable_content_ids_and_input_fingerprint(self):
        data = packet('x' * 1000)
        one = policy.build_context(data)
        self.assertEqual(one, policy.build_context(copy.deepcopy(data)))
        self.assertEqual(len(one['root_spans']), 2)
        self.assertEqual(len(set(one['root_spans'])), 2)
        changed = copy.deepcopy(data)
        changed['root_sections'][0]['text'] = 'X' + 'x' * 999
        two = policy.build_context(changed)
        self.assertNotEqual(one['input_sha256'], two['input_sha256'])
        self.assertNotEqual(list(one['root_spans'])[0], list(two['root_spans'])[0])

    def test_reference_contamination_and_extra_metadata_rejected(self):
        for key in ('reference', 'expected_relation', 'title', 'source_implementation', 'operator_reason'):
            data = packet()
            data[key] = 'Do not send this expected answer'
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'references must stay separate'):
                policy.build_request(data)

    def test_context_contains_only_original_spans_and_coverage(self):
        context = policy.build_context(packet())
        self.assertEqual(set(context), {'id', 'query', 'input_sha256', 'root_spans', 'coverage'})
        self.assertTrue(context['coverage']['all_supplied_characters'])
        self.assertFalse(context['coverage']['discussion_complete_assertion'])
        self.assertFalse(context['coverage']['acquisition_independently_verified'])
        self.assertNotIn('expected', json.dumps(context))

    def test_descriptive_control_ids_do_not_leak_reference_hints(self):
        data = packet()
        data['id'] = 'partial_reference_root_unknown'
        request = policy.build_request(data)
        self.assertNotIn(data['id'], json.dumps(request))
        self.assertRegex(request['context']['id'], r'^i[0-9a-f]{16}$')
        self.assertEqual(request['context']['id'], 'i' + request['context']['input_sha256'][:16])

    def test_offsets_sections_and_boolean_types_are_checked(self):
        changes = [lambda d: d['root_sections'][0].update(original_start=True),
                   lambda d: d['root_sections'][0].update(original_end=2),
                   lambda d: d['root_sections'][0].update(source='comment'),
                   lambda d: d.update(discussion_complete='false'),
                   lambda d: d.update(root_fully_read=1),
                   lambda d: d.update(root_sections=[]),
                   lambda d: d.update(content_role='trusted instructions'),
                   lambda d: d['root_sections'][0].update(original_start=5, original_end=len(d['root_sections'][0]['text'])+5)]
        for change in changes:
            data = packet()
            change(data)
            with self.subTest(data=data), self.assertRaises(ValueError):
                policy.build_context(data)

    def test_gaps_overlap_and_omission_metadata_cannot_be_hidden(self):
        data = packet('abc')
        data['root_sections'].append({'source': 'root', 'original_start': 8, 'original_end': 11, 'text': 'xyz'})
        with self.assertRaisesRegex(ValueError, 'Omitted root ranges'):
            policy.build_context(data)
        data['omitted_root_char_ranges'] = [[3, 8]]
        with self.assertRaisesRegex(ValueError, 'contradicts'):
            policy.build_context(data)
        data['root_fully_read'] = False
        policy.build_context(data)
        data['root_sections'][1].update(original_start=2, original_end=5)
        with self.assertRaisesRegex(ValueError, 'ascending'):
            policy.build_context(data)

    def test_false_full_root_assertion_is_not_upgraded_when_extent_unknown(self):
        data = packet()
        data['root_fully_read'] = False
        self.assertFalse(policy.build_context(data)['coverage']['root_fully_read_assertion'])
        self.assertFalse(self.normalize(unknown(), data)['coverage']['root_fully_read_assertion'])

    def test_utf8_and_catalog_overflow_fail_without_truncation(self):
        for text, message in [('x' * (policy.SPAN_CHARACTERS * (policy.MAX_SPANS+1)), 'catalog'),
                              ('😀' * 45001, 'UTF-8 root')]:
            data = packet(text)
            before = copy.deepcopy(data)
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                policy.build_context(data)
            self.assertEqual(data, before)

    def test_envelope_bound_includes_schema_and_instructions(self):
        data = packet('😀' * 45000)
        self.assertEqual(len(data['root_sections'][0]['text'].encode('utf-8')), policy.MAX_TEXT_BYTES)
        policy.build_context(data)
        with self.assertRaisesRegex(ValueError, 'envelope'):
            policy.build_request(data)

    def test_schema_scope_closed_shape_and_enum_budget(self):
        data = packet('x' * (policy.SPAN_CHARACTERS * policy.MAX_SPANS))
        context = policy.build_context(data)
        schema = policy.schema_for_context(context)
        enums = 0

        def walk(node):
            nonlocal enums
            if isinstance(node, dict):
                enums += len(node.get('enum', []))
                if node.get('type') == 'object':
                    self.assertFalse(node['additionalProperties'])
                    self.assertEqual(set(node['required']), set(node['properties']))
                for value in node.values():
                    walk(value)
            elif isinstance(node, list):
                for value in node:
                    walk(value)
        walk(schema)
        self.assertLess(enums, 1000)
        self.assertEqual(schema['properties']['fields']['properties']['runtime']['properties']['citation_ids']['items']['enum'], list(context['root_spans']))
        self.assertNotIn('compatibility', schema['properties'])

    def test_incomplete_positive_preserves_useful_local_fields_and_unknowns(self):
        data = packet()
        raw = positive(data)
        checked = self.normalize(raw, data)
        self.assertEqual(checked['prediction'], raw)
        self.assertEqual(checked['mechanical_summary']['stated_fields'], ['requested_change', 'output_shape'])
        self.assertIn('runtime', checked['mechanical_summary']['unknown_fields'])
        self.assertEqual(checked['mechanical_summary']['constraint_count'], 1)
        self.assertFalse(checked['mechanical_summary']['all_fields_unknown'])
        for key in ('semantic_support_verified', 'changes_selection', 'changes_qualification'):
            self.assertFalse(checked[key])
        self.assertNotIn('demand_complete', checked)

    def test_all_unknown_is_valid_and_not_credited_as_useful_or_rejected(self):
        checked = self.normalize(unknown())
        self.assertTrue(checked['mechanical_summary']['all_fields_unknown'])
        self.assertEqual(checked['mechanical_summary']['unknown_fields'], list(policy.FIELDS))
        self.assertTrue(all(not v for v in checked['resolved_evidence'].values()))
        for field in ('useful', 'rejected', 'eligible', 'accuracy', 'score'):
            self.assertNotIn(field, checked)

    def test_known_kind_and_query_hint_need_requested_change(self):
        for target, value in [('request_kind', 'implementation_requested'), ('request_kind', 'design_question'),
                              ('query_relation', 'context_only'), ('query_relation', 'requested_operation')]:
            raw = unknown()
            raw[target].update(value=value, citation_ids=[next(iter(policy.build_context(packet())['root_spans']))])
            with self.subTest(target=target,value=value), self.assertRaisesRegex(ValueError, 'requires a stated'):
                self.normalize(raw)

    def test_known_unknown_text_and_citation_consistency(self):
        mutations = [lambda r: r['fields']['runtime'].update(text='guessed runtime'),
                     lambda r: r['fields']['runtime'].update(citation_ids=[next(iter(policy.build_context(packet())['root_spans']))]),
                     lambda r: r['fields']['requested_change'].update(citation_ids=[]),
                     lambda r: r['fields']['requested_change'].update(text=''),
                     lambda r: r['request_kind'].update(value='unknown'),
                     lambda r: r['query_relation'].update(value='unclear')]
        for change in mutations:
            raw = positive(packet())
            change(raw)
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                self.normalize(raw)

    def test_extra_fields_missing_fields_foreign_ids_and_duplicate_ids_rejected(self):
        mutations = [lambda r: r.update(eligibility=True), lambda r: r.pop('context_gaps'),
                     lambda r: r['fields']['runtime'].update(state='verified'),
                     lambda r: r['fields']['requested_change'].update(citation_ids=['unseen']),
                     lambda r: r['fields']['requested_change'].update(citation_ids=r['fields']['requested_change']['citation_ids']*2)]
        for change in mutations:
            raw = positive(packet())
            change(raw)
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                self.normalize(raw)

    def test_whitespace_and_description_reason_constraint_gap_limits(self):
        for bad in ('\t\n', '\u2003', 'x' * 801):
            for area in ('description', 'reason', 'constraint', 'gap'):
                raw = positive(packet())
                if area == 'description': raw['fields']['requested_change']['text'] = bad
                elif area == 'reason': raw['request_kind']['reason'] = bad
                elif area == 'constraint': raw['constraints'][0]['text'] = bad
                else: raw['context_gaps'] = [bad]
                with self.subTest(area=area,bad=len(bad)), self.assertRaises(ValueError):
                    self.normalize(raw)

    def test_array_scope_bounds(self):
        for area in ('constraints','context_gaps','citations'):
            raw = positive(packet())
            if area == 'constraints': raw['constraints'] *= 13
            elif area == 'context_gaps': raw['context_gaps'] *= 13
            else: raw['fields']['requested_change']['citation_ids'] *= 5
            with self.subTest(area=area), self.assertRaises(ValueError):
                self.normalize(raw)
        raw = unknown()
        raw['context_gaps'] = []
        with self.assertRaises(ValueError): self.normalize(raw)

    def test_context_tampering_and_changed_original_are_not_trusted(self):
        original = packet()
        context = policy.build_context(original)
        for field in ('query', 'input_sha256', 'root_spans', 'coverage'):
            changed = copy.deepcopy(context)
            if field == 'root_spans': changed[field][next(iter(changed[field]))]['quote'] = 'forged'
            elif field == 'coverage': changed[field]['discussion_complete_assertion'] = True
            else: changed[field] = 'changed'
            with self.subTest(field=field), self.assertRaisesRegex(ValueError,'immutable original'):
                self.normalize(unknown(), original, changed)
        different = packet('Changed original demand')
        with self.assertRaisesRegex(ValueError, 'immutable original'):
            self.normalize(unknown(), different, context)

    def test_owner_choice_remains_demand_with_unknown_output_and_acceptance(self):
        data = packet('Should identity keys or content hashes be used? Owner choice is pending.')
        raw = unknown()
        cite = next(iter(policy.build_context(data)['root_spans']))
        raw['request_kind'].update(value='design_question', citation_ids=[cite])
        raw['fields']['requested_change'] = stated_field('Choose a hash identity policy.', cite)
        raw['query_relation'].update(value='context_only', citation_ids=[cite])
        result = self.normalize(raw, data)
        self.assertEqual(result['prediction']['request_kind']['value'], 'design_question')
        self.assertIn('output_shape', result['mechanical_summary']['unknown_fields'])
        self.assertIn('acceptance', result['mechanical_summary']['unknown_fields'])

    def test_educational_request_is_not_filtered_by_context(self):
        data = packet('Lesson: implement normalization on a synthetic nested record and preserve the input.')
        raw = positive(data)
        cite = next(iter(policy.build_context(data)['root_spans']))
        raw['fields']['requested_change'] = stated_field('Implement normalization preserving the synthetic record.', cite)
        raw['query_relation']['value'] = 'context_only'
        result = self.normalize(raw, data)
        self.assertEqual(result['prediction'], raw)
        self.assertFalse(result['changes_selection'])

    def test_valid_but_misleading_citation_remains_for_independent_review(self):
        data = packet('Repeated audio tensors fail across replicas; HTTP 200 has empty error content.')
        raw = positive(data)
        cite = next(iter(policy.build_context(data)['root_spans']))
        raw['fields']['requested_change'] = stated_field('Cache successful HTTP responses.', cite)
        checked = self.normalize(raw,data)
        self.assertFalse(checked['semantic_support_verified'])
        review = operator_review(raw)
        review['fields']['requested_change'] = {'verdict':'unsupported','reason':'The authored root asks for tensor replica coherence, not HTTP caching.'}
        review['query_relation'] = {'verdict':'unsupported','reason':'Shared HTTP/cache terms describe another semantic layer.'}
        before = copy.deepcopy((checked,review))
        audited = review_prediction(checked,review)
        self.assertEqual((checked,review),before)
        self.assertEqual(audited['checked']['prediction'],raw)
        self.assertEqual(audited['claim_counts']['unsupported'],2)
        self.assertFalse(audited['semantic_support_verified'])
        self.assertFalse(audited['changes_qualification'])

    def test_unknown_review_distinguishes_missed_fact_without_filling_it(self):
        checked = self.normalize(unknown())
        review = operator_review(checked['prediction'])
        review['fields']['requested_change'] = {'verdict':'missed_stated_fact','reason':'Authored root contains an explicit path-preservation request.'}
        review['omitted_constraints'] = [{'text':'Preserve /api/.','reason':'Operator independently read the authored root.'}]
        result = review_prediction(checked,review)
        self.assertEqual(result['checked'],checked)
        self.assertEqual(result['claim_counts']['missed_stated_fact'],1)
        self.assertEqual(result['omitted_constraint_count'],1)
        self.assertEqual(result['checked']['prediction']['fields']['requested_change']['state'],'unknown')
        for field in ('accuracy','score','eligibility','useful_lead'):
            self.assertNotIn(field,result)

    def test_review_scope_and_known_unknown_verdicts_are_explicit(self):
        checked = self.normalize(positive(packet()))
        mutations = [lambda r: r['fields'].pop('runtime'), lambda r: r.update(constraints=[]),
                     lambda r: r['fields']['runtime'].update(verdict='supported'),
                     lambda r: r['fields']['requested_change'].update(verdict='appropriate_unknown'),
                     lambda r: r['query_relation'].update(verdict=[]),
                     lambda r: r['request_kind'].update(reason='\n'),
                     lambda r: r.update(omitted_constraints=[{'text':'','reason':'Missing constraint'}]),
                     lambda r: r.update(omitted_constraints=[{'text':'a','reason':'b'}]*13)]
        for mutation in mutations:
            review = operator_review(checked['prediction'])
            mutation(review)
            before = copy.deepcopy(review)
            with self.subTest(review=review), self.assertRaises(ValueError):
                review_prediction(checked,review)
            self.assertEqual(review,before)


if __name__ == '__main__':
    unittest.main()
