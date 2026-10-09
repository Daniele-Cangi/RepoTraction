"""Opt-in one-shot policy-v3 execution; caller owns gates/storage/leases.

No provider construction, credentials, network or filesystem access on import.
Only the post-schema policy ValueError branch can reject locally; native wire,
identity, persistence and integrity errors escape and stop the owned runner.
"""
import copy
import hashlib
import math

from missing_link.contracts import validate_shape
from missing_link.service import Budget
from scripts.missing_link_demand_operation_policy_v3 import build_request, normalize_prediction, _bytes
from scripts.missing_link_repository_only_evaluator import configuration, require
from scripts.missing_link_triage_receipts import complete_with_receipt


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def verify_requests(provider, packets, manifest, read, *, readiness=True):
    """Reproduce ALL ordered bodies/costs before any attempt/reservation."""
    require(manifest['policy_revision'] == 3, 'Policy-v3 preparation required')
    if readiness:
        require(provider.describe().get('configured') is True, 'Owned provider is not ready')
    require(configuration(provider) == manifest['config_without_key'], 'Public provider settings changed')
    require(len(packets) == len(manifest['requests']) == 11, 'Frozen cohort needs eleven slots')
    slots, seen = [], set()
    for order, (packet, expected) in enumerate(zip(packets, manifest['requests']), 1):
        envelope = build_request(packet)
        endpoint, payload, body = provider._encode_prompt(
            envelope['instructions'], envelope['context'], envelope['schema'], 'request')
        cost = ((len(body)+2048)*provider.input_price + provider.max_tokens*provider.output_price)/1e6
        require(type(expected['slot']) is int and expected['slot'] == order
                and expected['operator_id'] == packet['id'] and expected['opaque_id'] == envelope['context']['id']
                and expected['phase'] == 'request' and expected['endpoint'] == endpoint == '/responses'
                and expected['input_sha256'] == envelope['context']['input_sha256'], 'Frozen slot identity changed')
        require(expected['job_id'] == f'demand-operation-policy-v3-owned-2026-10-09-{order:02}'
                and expected['job_id'] not in seen, 'Policy-v3 accounting ID/order changed')
        seen.add(expected['job_id'])
        require(_bytes(envelope) == read(expected['policy_envelope'])
                and digest(_bytes(envelope)) == expected['envelope_sha256']
                and body == read(expected['native_body']) and digest(body) == expected['native_sha256']
                and len(body) == expected['native_bytes'] <= provider.max_bytes
                and len(_bytes(envelope)) == expected['envelope_bytes'], 'Frozen request bytes changed')
        require(math.isfinite(cost) and 0 < cost == expected['reservation_usd'] <= provider.max_cost,
                'Frozen reservation changed')
        slots.append({'metadata':copy.deepcopy(expected), 'packet':copy.deepcopy(packet),
                      'envelope':envelope, 'payload':payload})
    require(abs(sum(s['metadata']['reservation_usd'] for s in slots)-manifest['planned_reservations_usd']) < 1e-12
            and manifest['planned_reservations_usd'] <= manifest['segment_cap_usd'], 'Frozen segment exceeds cap')
    return slots


def check_prediction(raw, slot, gate):
    """Schema/integrity before AND after narrowly caught policy normalization."""
    frozen = copy.deepcopy((raw, slot))

    def guards():
        gate()
        require(same_slot_structure([raw, slot], list(frozen)), 'Prediction or slot changed during validation')
        require(build_request(slot['packet']) == slot['envelope'], 'Context differs from pinned packet')
        validate_shape(raw, slot['envelope']['schema'])

    guards()
    error, checked = None, None
    try:
        checked = normalize_prediction(raw, slot['envelope']['context'], packet=slot['packet'])
    except ValueError:
        error = 'policy_local_validation_rejected'
    guards()
    return {'prediction':copy.deepcopy(raw), 'checked':checked,
            'disposition':'local_rejection' if error else 'mechanically_valid', 'validation_error':error}


def same_slot_structure(actual, expected):
    """Compare concrete JSON-domain types recursively, without serialization."""
    if type(actual) is not type(expected):
        return False
    if type(actual) is dict:
        return (actual.keys() == expected.keys()
                and all(type(key) is str for key in actual)
                and all(type(key) is str for key in expected)
                and all(same_slot_structure(actual[key], expected[key]) for key in expected))
    if type(actual) is list:
        return len(actual) == len(expected) and all(
            same_slot_structure(left, right) for left, right in zip(actual, expected))
    return type(actual) in (str, int, float, bool, type(None)) and actual == expected


def execute_cases(provider, slots, *, manifest, read, gate, identity, claim, reserve, persist,
                  retain_terminal, record, cancelled):
    """Caller supplies its anchored manifest/body reader; never trust slot metadata."""
    gate()
    verified = verify_requests(provider, [s['packet'] for s in slots], manifest, read)
    require(same_slot_structure(slots, verified), 'Execution slots differ from the frozen manifest')
    original = copy.deepcopy(slots)
    results = []

    def guard():
        gate()
        require(same_slot_structure(slots, original), 'Execution inputs changed')

    for slot in slots:
        require(same_slot_structure(slots, original), 'Execution inputs changed')
        guard()
        identity(force=True)
        guard()
        claim(copy.deepcopy(slot))
        guard()
        number, job_id = slot['metadata']['slot'], slot['metadata']['job_id']
        job = {'id':job_id, 'ai_calls_used':0, 'cost_reserved_usd':0, 'checkpoint':{}}

        def reserve_one(cost):
            guard()
            require(cost == slot['metadata']['reservation_usd'], 'Attempt reservation differs from frozen body')
            reserve(job_id, cost)
            guard()

        def persist_job():
            guard()
            persist(number, copy.deepcopy(job))
            guard()

        budget = Budget(job, persist_job, cancelled, identity, reserve_one)
        envelope = slot['envelope']
        raw = complete_with_receipt(provider, envelope['instructions'], envelope['context'], budget,
            schema=envelope['schema'], phase='request',
            retain_terminal=lambda event: retain_terminal(number, event))
        require(same_slot_structure(slots, original), 'Execution inputs changed during receipt handling')
        result = check_prediction(raw, slot, guard)
        require(same_slot_structure(slots, original), 'Execution inputs changed during normalization')
        result.update(slot=number, job_id=job_id)
        record(copy.deepcopy(result))
        guard()
        results.append(result)
    return results
