"""Explicitly invoked experimental execution; no IO or credential lookup on import.

Caller owns the frozen preflight, exclusive one-shot marker, worker lease, account
checks, atomic original-allowance cap and raw receipts. No production job imports.
"""
from missing_link.service import Budget
from scripts.missing_link_triage_layer_prompt import PROMPT, schema_for_context, normalize_prediction
from scripts.missing_link_triage_receipts import complete_with_receipt


def execute_cases(provider, cases, *, segment, identity, reserve, persist, retain_terminal, record):
    """One request per supplied case; transport/account/budget errors stop the run.

Only post-response local shape/provenance validation is candidate-local. Preserve
its parsed card and error, never repair it or retry. The required retain_terminal
callback saves full terminal JSON privately before output parsing or acceptance.
Other callbacks handle job persistence and original-allowance reservations.
"""
    results = []
    for case in cases:
        current = case["case"]
        identity(force=True)
        job = {"id": f"{segment}-{current:02}", "ai_calls_used": 0,
               "cost_reserved_usd": 0, "checkpoint": {}}
        budget = Budget(job, lambda: persist(current, job), lambda: False, identity,
                        reserve_total=lambda cost: reserve(job["id"], cost))
        parsed = complete_with_receipt(provider, PROMPT, case["data"], budget,
            schema=schema_for_context(case["data"]), phase="analysis",
            retain_terminal=lambda receipt: retain_terminal(current, receipt))
        try:
            checked = normalize_prediction(parsed, case["data"], demand_sources=case["demand_sources"],
                operation_body=case["operation_body"], operation_spans=case["operation_spans"])
        except (ValueError, TypeError, KeyError) as exc:
            checked = {"validation_error": str(exc) if isinstance(exc, ValueError) else "invalid_reference_shape"}
        result = {"case": current, "issue": case["issue"], "parsed": parsed, "checked": checked}
        record(result)
        results.append(result)
    return results
