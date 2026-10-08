"""Explicit operator annotations on mechanically checked demand predictions.

No semantic classifier, reference-text matching, eligibility, accuracy or scores.
"""
import copy
from collections import Counter

from scripts.missing_link_demand_operation_policy import FIELDS, MAX_DESCRIPTION, MAX_CONSTRAINTS, _text


def review_prediction(checked, review):
    """Retain every prediction, including unknowns; summarize supplied review only.

    The caller supplies normalize_prediction's result and independently reads all
    claims/evidence. A supported verdict is an assertion, never proof by software.
    """
    if not isinstance(review, dict) or set(review) != {
            'request_kind', 'fields', 'constraints', 'query_relation', 'context_gaps', 'omitted_constraints'}:
        raise ValueError('Operator review must cover every prediction area')
    raw = checked['prediction']
    if (not isinstance(review['fields'], dict) or set(review['fields']) != set(FIELDS)
            or not isinstance(review['constraints'], list)
            or len(review['constraints']) != len(raw['constraints'])):
        raise ValueError('Operator review fields/constraints do not match prediction scope')
    counts = Counter()
    groups = {'supported': [], 'unsupported': [], 'appropriate_unknown': [],
              'missed_stated_fact': [], 'unassessed': []}

    def verdict(item, path, known):
        if not isinstance(item, dict) or set(item) != {'verdict', 'reason'}:
            raise ValueError('Operator verdict requires a label and independent reason')
        allowed = {'supported', 'unsupported', 'unassessed'} if known else {
            'appropriate_unknown', 'missed_stated_fact', 'unassessed'}
        if not isinstance(item['verdict'], str) or item['verdict'] not in allowed:
            raise ValueError('Operator verdict conflicts with stated/unknown prediction state')
        _text(item['reason'], MAX_DESCRIPTION, 'operator reason')
        counts[item['verdict']] += 1
        groups[item['verdict']].append(path)

    verdict(review['request_kind'], 'request_kind', raw['request_kind']['value'] != 'unknown')
    for name in FIELDS:
        verdict(review['fields'][name], 'fields.' + name, raw['fields'][name]['state'] == 'stated_in_root')
    for i, item in enumerate(review['constraints']):
        verdict(item, f'constraints.{i}', True)
    verdict(review['query_relation'], 'query_relation', raw['query_relation']['value'] != 'unclear')
    verdict(review['context_gaps'], 'context_gaps', True)
    omissions = review['omitted_constraints']
    if not isinstance(omissions, list) or len(omissions) > MAX_CONSTRAINTS:
        raise ValueError('Operator omitted-constraint list is invalid or over bound')
    for omission in omissions:
        if not isinstance(omission, dict) or set(omission) != {'text', 'reason'}:
            raise ValueError('Operator omitted constraint needs text and independent reason')
        _text(omission['text'], MAX_DESCRIPTION, 'operator omitted constraint')
        _text(omission['reason'], MAX_DESCRIPTION, 'operator omission reason')
    return {'checked': copy.deepcopy(checked), 'operator_review': copy.deepcopy(review),
            'claim_counts': dict(counts), 'claim_paths': groups,
            'omitted_constraint_count': len(omissions),
            'review_origin': 'operator_assertions_not_automatically_inferred',
            'semantic_support_verified': False, 'changes_selection': False, 'changes_qualification': False}
