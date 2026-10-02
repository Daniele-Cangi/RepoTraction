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


def disposition_record(index, request, *, collected_at, ai_calls_used, cost_reserved_usd, analysis_source="model"):
    """Public review summary; raw completed output stays in the private checkpoint."""
    return {"index": index, "url": request["url"], "at": collected_at,
        "status": NON_DEMAND_STATUS, "reason": request["status_reason"],
        "status_evidence": request["status_evidence"], "fingerprint": request["fingerprint"],
        "context_complete": request["context_complete"], "analysis_source": analysis_source,
        "ai_calls_used": ai_calls_used, "cost_reserved_usd": cost_reserved_usd,
        "compatibility_evaluated": False,
        "note": ("Coding-agent" if analysis_source == "coding_agent_import" else "Model") +
            " interpretation of supplied discussion, not a compatibility rejection or proof that demand is absent elsewhere."}


def record_disposition(job, index, request, record):
    """Replace one discussion's outcome, without rewriting charged attempt history."""
    key = str(index)
    checkpoint = job["checkpoint"]
    checkpoint.setdefault("requests", {})[key] = request
    checkpoint.setdefault("non_demands", {})[key] = record
    # Reimports are idempotent per selected discussion, not repeated UI entries.
    job["result"]["non_demands"] = [item for item in job["result"].get("non_demands", [])
        if str(item["index"]) != key] + [record]


def clear_disposition(job, index, request):
    """A later reviewed demand import must not leave a contradictory outcome."""
    key = str(index)
    checkpoint = job["checkpoint"]
    if key not in checkpoint.get("non_demands", {}):
        return False
    checkpoint["non_demands"].pop(key)
    checkpoint.setdefault("requests", {})[key] = request
    job["result"]["non_demands"] = [item for item in job["result"].get("non_demands", [])
        if str(item["index"]) != key]
    # This explicitly imported discussion is already reviewed; a resume must not
    # resurrect the old non-demand or spend on an implicit reevaluation.
    if key not in checkpoint.setdefault("evaluated", []):
        checkpoint["evaluated"].append(key)
    return True
