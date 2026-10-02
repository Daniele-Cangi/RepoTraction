"""Source-bound non-demand dispositions, separate from compatibility verdicts."""

NON_DEMAND_STATUS = "not_a_request"


def is_non_demand(request):
    return request.get("status") == NON_DEMAND_STATUS


def validate_non_demand(raw, issue, catalog):
    """Validate provenance/coverage, not the truth of the model's interpretation."""
    if not is_non_demand(raw):
        return
    if raw.get("requirements") != []:
        raise ValueError("A non-demand disposition must have an empty requirements list.")
    reason = raw.get("status_reason")
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("A non-demand disposition needs a source-grounded reason.")
    references = raw.get("status_source_ids")
    if not isinstance(references, list) or not references or any(
        not isinstance(ref, str) or ref not in catalog for ref in references
    ):
        raise ValueError("A non-demand disposition needs known discussion source IDs.")
    if not any(catalog[ref].get("kind") in {"request", "discussion"} for ref in references):
        raise ValueError("Timeline state alone cannot establish a non-demand disposition.")
    if not issue.get("context_complete"):
        raise ValueError("Incomplete discussion cannot establish a non-demand disposition; needs review.")


def disposition_record(index, request, *, collected_at, ai_calls_used, cost_reserved_usd):
    """Public review summary; raw completed output stays in the private checkpoint."""
    return {"index": index, "url": request["url"], "at": collected_at,
        "status": NON_DEMAND_STATUS, "reason": request["status_reason"],
        "status_evidence": request["status_evidence"], "fingerprint": request["fingerprint"],
        "context_complete": request["context_complete"], "analysis_source": "model",
        "ai_calls_used": ai_calls_used, "cost_reserved_usd": cost_reserved_usd,
        "compatibility_evaluated": False,
        "note": "Model interpretation of supplied discussion, not a compatibility rejection or proof that demand is absent elsewhere."}
