"""Offline successor with explicit protected-unit ownership and unused job IDs."""
import copy
import json
import time

from missing_link.service import Budget, Cancelled
from scripts import missing_link_cadence_executor as predecessor
from scripts import missing_link_demand_operation_policy_v3_executor as v3
from scripts.missing_link_cadence_reader import complete_with_receipt
from scripts.missing_link_repository_only_evaluator import configuration, require
from scripts.missing_link_protected_operations import ProtectedOperations

JOB_PREFIX = 'demand-operation-policy-v3-operation-owned-2026-10-10-'
SETTINGS = dict(predecessor.SETTINGS, transport_revision='checkpoint_operations_1',
                protected_operation_revision=1)


def successor_manifest(source):
    result = predecessor.successor_manifest(source)
    result.update(SETTINGS)
    for number, row in enumerate(result['requests'], 1):
        row['job_id'] = JOB_PREFIX + f'{number:02}'
    return result


def bind_requests(provider, packets, manifest, read):
    require(v3.same_slot_structure({k: manifest.get(k) for k in SETTINGS}, SETTINGS),
            'Protected operation settings changed')
    legacy = copy.deepcopy(manifest)
    legacy.pop('protected_operation_revision')
    legacy.update(predecessor.SETTINGS)
    for number, row in enumerate(legacy['requests'], 1):
        require(row['job_id'] == JOB_PREFIX + f'{number:02}', 'Protected operation accounting ID changed')
        row['job_id'] = predecessor.JOB_PREFIX + f'{number:02}'
    verified = predecessor.bind_requests(provider, packets, legacy, read)
    bound = []
    for number, request in enumerate(verified, 1):
        slot = request.slot()
        slot['metadata']['job_id'] = JOB_PREFIX + f'{number:02}'
        bound.append(predecessor.BoundRequest(json.dumps(slot, ensure_ascii=False).encode(), request.body))
    return tuple(bound)


def execute_cases(provider, packets, *, manifest, read, fast, critical, history, identity,
                  claim, reserve, reservation_observed, persist, retain_terminal,
                  retain_telemetry, record, cancelled, finish, opener_factory=None,
                  clock=time.monotonic, case_limit=11):
    config, key = copy.deepcopy(manifest['config_without_key']), provider.key
    requests = bind_requests(provider, packets, manifest, read)
    require(type(case_limit) is int and 1 <= case_limit <= 11, 'Invalid offline case limit')
    require(opener_factory is not None, 'Protected operations currently require an authored transport')

    def immediate():
        if cancelled(): raise Cancelled('Owned operation stream cancelled.')
        identity()
        fast()
        require(v3.same_slot_structure(configuration(provider), config) and provider.key == key,
                'Provider configuration changed')
        if cancelled(): raise Cancelled('Owned operation stream cancelled.')

    checks = ProtectedOperations(fast=immediate, critical=critical, history=history, clock=clock)
    checks.start()
    results = []
    for request in requests[:case_limit]:
        slot = request.slot()
        def claim_one():
            identity(force=True)
            checks.commit('claim', lambda: claim(copy.deepcopy(slot)))
        checks.operation('claim', claim_one)
        number, job_id = slot['metadata']['slot'], slot['metadata']['job_id']
        cost = slot['metadata']['reservation_usd']
        job = {'id': job_id, 'ai_calls_used': 0, 'cost_reserved_usd': 0, 'checkpoint': {}}

        def reserve_one(value):
            require(type(value) is float and value == cost, 'Reservation differs from frozen body')
            checks.commit('reservation', lambda: reserve(job_id, value))

        def persist_job():
            checks.commit('checkpoint', lambda: persist(number, copy.deepcopy(job)))

        def telemetry(value):
            if value['failure'] is None:
                checks.operation('telemetry', lambda: checks.commit('telemetry',
                    lambda: retain_telemetry(number, value)))
            else:
                fast()
                retain_telemetry(number, value)
                fast()

        budget = Budget(job, persist_job, cancelled, checks.guard, reserve_one)
        raw = complete_with_receipt(provider, slot, request.body, budget, checks=checks,
            operations=checks, retain_terminal=lambda event: retain_terminal(number, event),
            retain_telemetry=telemetry, reservation_observed=lambda: reservation_observed(job_id, cost),
            before_open=lambda: identity(force=True), opener_factory=opener_factory, clock=clock)
        def validate_and_record():
            result = v3.check_prediction(raw, request.slot(), checks.guard)
            result.update(slot=number, job_id=job_id)
            checks.commit('result', lambda: record(copy.deepcopy(result)))
            return result
        result = checks.operation('validate', validate_and_record)
        results.append(result)
    checks.operation('finish', lambda: checks.commit('finish', lambda: finish(copy.deepcopy(results))))
    checks.finish()
    return results
