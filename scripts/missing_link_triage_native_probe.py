"""One authored native-schema probe, explicitly invoked after caller preflight.

No CLI, provider configuration, IO, reservation or code execution on import.
Caller owns frozen request/code/config hashes, account/lease checks, exclusive
start marker, atomic original-allowance cap and private terminal storage.
This is mechanical schema acceptance, not Discover or model-quality evaluation.
"""
import copy

from missing_link.service import Budget
from scripts.missing_link_triage_prompt import build_context
from scripts.missing_link_triage_declaration_schema import PROMPT, schema_for_context, normalize_prediction
from scripts.missing_link_triage_receipts import complete_with_receipt

BODY = "def sum_values(values):\n    return sum(values)\n"
DEMAND = ("Provide numeric summary statistics for a nonempty collection, including its sum and count. "
          "Acceptance and integration details are not supplied.")
SEGMENT = "missing-link-native-schema-2026-10-05"


def build_case():
    """Fresh full-text fixture, no imported prediction, labels or expected relation."""
    sources = {"q0": DEMAND}
    context = build_context({"repository": "authored/native-schema-probe", "revision": "authored-fixture-v1",
        "selected_entrypoint": "authored_native_schema.py:sum_values", "demand_sources": sources,
        "operation_evidence": {"e0": {"path": "authored_native_schema.py", "line": 1, "end_line": 2, "quote": BODY}},
        "acquisition_complete": False,
        "acquisition_limitations": ["Authored contract probe only; acceptance and adoption context not supplied"]})
    return {"case": 1, "source": "authored_fixture_not_external_issue", "data": context,
        "demand_sources": sources, "operation_body": BODY,
        "operation_spans": {"e0": {"start": 0, "end": len(BODY), "quote": BODY}}}


def execute_probe(provider, *, identity, reserve, persist, retain_terminal, record):
    """Exactly one attempt, no retry/salvage; caller must enforce prepared preflight.

Transport, receipt and generic-shape failures propagate. Post-response final
local normalization errors retain the parsed card/error as the sole result.
No relation is forced; a mechanically valid all-unknown card is permissible.
    """
    case = build_case()
    identity(force=True)
    job = {"id": SEGMENT + "-01", "ai_calls_used": 0, "cost_reserved_usd": 0, "checkpoint": {}}
    budget = Budget(job, lambda: persist(copy.deepcopy(job)), lambda: False, identity,
                    reserve_total=lambda cost: reserve(job["id"], cost))
    parsed = complete_with_receipt(provider, PROMPT, case["data"], budget,
        schema=schema_for_context(case["data"]), phase="analysis", retain_terminal=retain_terminal)
    try:
        checked = normalize_prediction(parsed, case["data"], demand_sources=case["demand_sources"],
            operation_body=case["operation_body"], operation_spans=case["operation_spans"])
    except (ValueError, TypeError, KeyError) as exc:
        checked = {"validation_error": str(exc) if isinstance(exc, ValueError) else "invalid_reference_shape"}
    result = {"case": 1, "source": case["source"], "parsed": parsed, "checked": checked}
    record(result)
    return result
