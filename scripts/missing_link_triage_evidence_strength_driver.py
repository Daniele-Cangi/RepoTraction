"""Fresh evidence-strength gates/execution, never production or import-time IO.

Accounting delegates unchanged to the frozen prospective driver. Only the prompt
binding differs in exact-request checking and execution; old drivers stay frozen.

Caller owns frozen source/config/request fingerprints, merged revision, identity,
exclusive markers/private storage, worker lease and atomic original-allowance cap.
No semantic scoring, retries, acquired-code execution or provider construction.
"""
import copy
import hashlib
import json
import math

from missing_link.service import Budget
from scripts.missing_link_triage_native_driver import ACCOUNTING_TABLES, configuration
from scripts.missing_link_triage_evidence_strength_prompt import PROMPT, schema_for_context, normalize_prediction
from scripts.missing_link_triage_prospective_driver import verify_increment
from scripts.missing_link_triage_receipts import complete_with_receipt


def verify_requests(provider, *, cases, payloads, metadata, config, segment):
    """Check all six exact requests and public settings before any reservation.

Frozen case ownership and independently stored reference/code hashes are checked
by the caller. Readiness rejects without encoding or echoing provider diagnostics.
    """
    if provider.describe().get("configured") is not True:
        raise ValueError("Prospective provider is not ready")
    if configuration(provider) != config:
        raise ValueError("Prospective provider configuration changed")
    if not len(cases) == len(payloads) == len(metadata) == 6:
        raise ValueError("Prospective cohort needs six frozen requests")
    costs = []
    for number, (case, payload, expected) in enumerate(zip(cases, payloads, metadata), 1):
        if type(case["case"]) is not int or case["case"] != number:
            raise ValueError("Prospective case order changed")
        schema = schema_for_context(case["data"])
        endpoint, actual_payload, body = provider._encode_prompt(PROMPT, case["data"], schema, "analysis")
        cost = ((len(body) + 2048) * provider.input_price + provider.max_tokens * provider.output_price) / 1e6
        actual = {"case": number, "request_bytes": len(body),
            "request_sha256": hashlib.sha256(body).hexdigest(),
            "schema_sha256": hashlib.sha256(json.dumps(schema, sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
            "reservation_usd": cost, "job_id": f"{segment}-{number:02}"}
        if endpoint != "/responses" or actual != expected or actual_payload != payload or len(body) > provider.max_bytes:
            raise ValueError("Prospective frozen request changed")
        if not math.isfinite(cost) or not 0 < cost <= provider.max_cost:
            raise ValueError("Prospective per-case reservation exceeds cap")
        costs.append(cost)
    return sum(costs)


def execute_cases(provider, cases, *, segment, identity, before_case, after_case,
                  reserve, persist, retain_terminal, record):
    """One attempt per ordered case; transport/terminal/persistence errors stop.

Only the explicit post-response branch/provenance normalizer is candidate-local.
Keep its rejected raw card, never repair or retry. The caller's before_case gate
checks fingerprints/exact prior prefix both before and after fresh identity.
    """
    if len(cases) != 6 or any(type(case["case"]) is not int or case["case"] != number
            for number, case in enumerate(cases, 1)):
        raise ValueError("Prospective case order changed")
    results = []
    for case in cases:
        current = case["case"]
        before_case(current)
        identity(force=True)
        before_case(current)
        job = {"id": f"{segment}-{current:02}", "ai_calls_used": 0,
               "cost_reserved_usd": 0, "checkpoint": {}}
        budget = Budget(job, lambda: persist(current, copy.deepcopy(job)), lambda: False, identity,
                        reserve_total=lambda cost: reserve(job["id"], cost))
        parsed = complete_with_receipt(provider, PROMPT, case["data"], budget,
            schema=schema_for_context(case["data"]), phase="analysis",
            retain_terminal=lambda receipt: retain_terminal(current, receipt))
        try:
            checked = normalize_prediction(parsed, case["data"], demand_sources=case["demand_sources"],
                operation_body=case["operation_body"], operation_spans=case["operation_spans"])
        except (ValueError, TypeError, KeyError) as exc:
            checked = {"validation_error": str(exc) if isinstance(exc, ValueError) else "invalid_reference_shape"}
        result = {"case": current, "source_url": case["source_url"], "parsed": parsed, "checked": checked}
        record(result)
        after_case(current)
        results.append(result)
    return results
