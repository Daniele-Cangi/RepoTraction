"""Separate opt-in policy-v3 stream execution; explicit gates, no import IO."""
import copy
import time

from missing_link.service import Budget, Cancelled
from scripts import missing_link_demand_operation_policy_v3_executor as v3
from scripts.missing_link_repository_only_evaluator import configuration, require
from scripts.missing_link_stream_successor_receipts import complete_with_receipt

same_slot_structure = v3.same_slot_structure
JOB_PREFIX = "demand-operation-policy-v3-stream-owned-2026-10-09-"
STREAM_SETTINGS = {"active_stream_deadline_seconds": 240, "wall_stream_deadline_seconds": 600,
    "full_checkpoint_nonterminal_lines": 128, "full_checkpoint_wall_interval_seconds": 30}


def verify_requests(provider, packets, manifest, read, *, readiness=True):
    """Use the unchanged v3 builder/body verifier; rebind only private job IDs."""
    require(type(manifest.get("semantic_policy_revision")) is int
            and manifest["semantic_policy_revision"] == 3
            and manifest.get("transport_revision") == "stream_successor_1",
            "Stream successor preparation required")
    require(same_slot_structure({key: manifest.get(key) for key in STREAM_SETTINGS}, STREAM_SETTINGS),
            "Frozen stream settings changed")
    require(same_slot_structure(configuration(provider), manifest["config_without_key"]),
            "Concrete public provider configuration changed")
    legacy = copy.deepcopy(manifest)
    legacy["policy_revision"] = 3
    require(len(legacy["requests"]) == 11, "Frozen cohort needs eleven slots")
    for number, metadata in enumerate(legacy["requests"], 1):
        require(metadata["job_id"] == JOB_PREFIX + f"{number:02}", "New accounting ID/order changed")
        metadata["job_id"] = f"demand-operation-policy-v3-owned-2026-10-09-{number:02}"
    verified = v3.verify_requests(provider, packets, legacy, read, readiness=readiness)
    for number, slot in enumerate(verified, 1):
        slot["metadata"]["job_id"] = JOB_PREFIX + f"{number:02}"
    require(same_slot_structure([s["metadata"] for s in verified], manifest["requests"]),
            "Concrete request metadata changed")
    return verified


def execute_cases(provider, slots, *, manifest, read, gate, light_gate, identity,
                  claim, reserve, reservation_observed, persist, retain_terminal,
                  retain_telemetry, record, cancelled, clock=time.monotonic):
    gate()
    verified = verify_requests(provider, [s["packet"] for s in slots], manifest, read)
    require(same_slot_structure(slots, verified), "Execution slots differ from frozen manifest")
    original, results = copy.deepcopy(slots), []

    def guard(full=True):
        (gate if full else light_gate)()
        require(same_slot_structure(slots, original), "Execution inputs changed")
        require(same_slot_structure(configuration(provider), manifest["config_without_key"]),
                "Provider configuration changed during execution")

    for slot in slots:
        guard()
        identity(force=True)
        guard()
        claim(copy.deepcopy(slot))
        guard()
        number, job_id = slot["metadata"]["slot"], slot["metadata"]["job_id"]
        job = {"id": job_id, "ai_calls_used": 0, "cost_reserved_usd": 0, "checkpoint": {}}

        def reserve_one(cost):
            guard()
            require(cost == slot["metadata"]["reservation_usd"], "Reservation differs from frozen body")
            reserve(job_id, cost)
            guard()

        def persist_job():
            guard()
            persist(number, copy.deepcopy(job))
            guard()

        def full_checkpoint():
            guard()
            identity()
            guard()

        def light_checkpoint():
            if cancelled():
                raise Cancelled("Owned stream cancelled.")
            guard(False)
            identity()
            guard(False)
            if cancelled():
                raise Cancelled("Owned stream cancelled.")

        def receipt(event):
            guard(False)
            retain_terminal(number, event)
            guard(False)

        def telemetry(value):
            # Failure evidence may be retained when a DB/history guard failed.
            # It never permits acceptance or a complete seal without full gates.
            guard(False)
            retain_telemetry(number, value)
            guard(False)

        budget = Budget(job, persist_job, cancelled, full_checkpoint, reserve_one)
        envelope = slot["envelope"]
        raw = complete_with_receipt(provider, envelope["instructions"], envelope["context"], budget,
            schema=envelope["schema"], retain_terminal=receipt, retain_telemetry=telemetry,
            light_checkpoint=light_checkpoint, clock=clock,
            reservation_observed=lambda: reservation_observed(job_id, slot["metadata"]["reservation_usd"]))
        guard()
        result = v3.check_prediction(raw, slot, guard)
        guard()
        result.update(slot=number, job_id=job_id)
        record(copy.deepcopy(result))
        guard()
        results.append(result)
    return results
