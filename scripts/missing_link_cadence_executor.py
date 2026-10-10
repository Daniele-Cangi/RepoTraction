"""One-shot cadence executor. Frozen bodies, dedicated accounting IDs, no import IO."""
import copy
from dataclasses import dataclass
import json
import time

from missing_link.service import Budget, Cancelled
from scripts import missing_link_demand_operation_policy_v3_executor as v3
from scripts import missing_link_stream_successor_executor as predecessor
from scripts.missing_link_repository_only_evaluator import configuration, require
from scripts.missing_link_cadence_checks import Checks
from scripts.missing_link_cadence_reader import complete_with_receipt

JOB_PREFIX = 'demand-operation-policy-v3-cadence-owned-2026-10-10-'
SETTINGS = {'transport_revision': 'checkpoint_cadence_1',
            'critical_interval_seconds': 1, 'history_interval_seconds': 30,
            'active_stream_deadline_seconds': 240, 'wall_stream_deadline_seconds': 600}


@dataclass(frozen=True)
class BoundRequest:
    slot_json: bytes
    body: bytes

    def slot(self):
        return json.loads(self.slot_json)


def successor_manifest(source):
    """Pure prospective binding; it is neither a retained freeze nor authorization."""
    result = copy.deepcopy(source)
    for key in ('full_checkpoint_nonterminal_lines', 'full_checkpoint_wall_interval_seconds'):
        result.pop(key, None)
    result.update(SETTINGS)
    for number, row in enumerate(result['requests'], 1):
        row['job_id'] = JOB_PREFIX + f'{number:02}'
    return result


def bind_requests(provider, packets, manifest, read, *, readiness=True):
    require(v3.same_slot_structure({k: manifest.get(k) for k in SETTINGS}, SETTINGS), 'Cadence settings changed')
    require(not any(k in manifest for k in ('full_checkpoint_nonterminal_lines',
            'full_checkpoint_wall_interval_seconds')), 'Consumed line cadence is not this contract')
    legacy = copy.deepcopy(manifest)
    legacy.update(predecessor.STREAM_SETTINGS, transport_revision='stream_successor_1')
    for number, row in enumerate(legacy['requests'], 1):
        require(row['job_id'] == JOB_PREFIX + f'{number:02}', 'Cadence accounting ID/order changed')
        row['job_id'] = predecessor.JOB_PREFIX + f'{number:02}'
    verified = predecessor.verify_requests(provider, packets, legacy, read, readiness=readiness)
    bound = []
    for number, slot in enumerate(verified, 1):
        slot['metadata']['job_id'] = JOB_PREFIX + f'{number:02}'
        body = read(slot['metadata']['native_body'])
        require(type(body) is bytes and v3.digest(body) == slot['metadata']['native_sha256'], 'Native body changed while binding')
        bound.append(BoundRequest(json.dumps(slot, ensure_ascii=False).encode(), body))
    return tuple(bound)


def execute_cases(provider, packets, *, manifest, read, fast, critical, history, identity,
                  claim, reserve, reservation_observed, persist, retain_terminal,
                  retain_telemetry, record, cancelled, finish, opener_factory=None,
                  clock=time.monotonic, case_limit=11):
    """All mutation callbacks receive copies; request bytes remain immutable.

    Only v3.check_prediction's explicit normalization refusal is local. Every
    other failure unwinds the cohort; the owned caller consumes its start marker.
    """
    requests = bind_requests(provider, packets, manifest, read)
    require(type(case_limit) is int and 1 <= case_limit <= 11, 'Invalid offline case limit')
    require(case_limit == 11 or opener_factory is not None, 'Partial probes require an authored transport')
    config, key = copy.deepcopy(configuration(provider)), provider.key

    def immediate():
        if cancelled():
            raise Cancelled('Owned cadence stream cancelled.')
        fast()
        require(v3.same_slot_structure(configuration(provider), config) and provider.key == key,
                'Provider configuration changed')
        identity()
        if cancelled():
            raise Cancelled('Owned cadence stream cancelled.')

    checks = Checks(fast=immediate, critical=critical, history=history, clock=clock)
    checks.start()
    results = []
    for request in requests[:case_limit]:
        slot = request.slot()
        checks.barrier()
        identity(force=True)
        checks.write(lambda: claim(copy.deepcopy(slot)))
        number, job_id = slot['metadata']['slot'], slot['metadata']['job_id']
        cost = slot['metadata']['reservation_usd']
        job = {'id': job_id, 'ai_calls_used': 0, 'cost_reserved_usd': 0, 'checkpoint': {}}

        def reserve_one(value):
            require(type(value) is float and value == cost, 'Reservation differs from frozen body')
            checks.write(lambda: reserve(job_id, value))

        def persist_job():
            checks.write(lambda: persist(number, copy.deepcopy(job)))

        def telemetry(value):
            # Failure evidence cannot grant acceptance or a success seal. On a
            # broken integrity gate retain only diagnostics, without clearing it.
            if value['failure'] is None:
                checks.write(lambda: retain_telemetry(number, value))
            else:
                fast()
                retain_telemetry(number, value)
                fast()

        budget = Budget(job, persist_job, cancelled, checks.barrier, reserve_one)
        raw = complete_with_receipt(provider, slot, request.body, budget, checks=checks,
            retain_terminal=lambda event: retain_terminal(number, event), retain_telemetry=telemetry,
            reservation_observed=lambda: reservation_observed(job_id, cost),
            before_open=lambda: identity(force=True), opener_factory=opener_factory, clock=clock)
        # Thaw again: the parser gets a private value, never the authoritative
        # binding or another slot. Its own before/after guards detect mutation.
        result = v3.check_prediction(raw, request.slot(), checks.barrier)
        result.update(slot=number, job_id=job_id)
        checks.write(lambda: record(copy.deepcopy(result)))
        results.append(result)
    checks.write(lambda: finish(copy.deepcopy(results)))
    checks.finish()
    return results
