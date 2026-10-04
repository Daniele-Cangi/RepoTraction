"""Experimental offline contract for reviewed facets, not a semantic classifier.

No production imports this module. Callers supply human-reviewed relations and
original body spans; substring validation does not establish their semantics or
operation ownership. Nothing here selects candidates or qualifies a connection.
"""

FACETS = ("runtime", "input", "output", "outcome")
MAX_BODY_BYTES = 180_000


def _span(span, body):
    if not isinstance(span, dict) or set(span) != {"start", "end", "quote"}:
        raise ValueError("Evidence needs an exact body span")
    start, end, quote = span["start"], span["end"], span["quote"]
    if (type(start) is not int or type(end) is not int or not isinstance(quote, str)
            or not quote.strip() or len(quote) > 1600
            or not 0 <= start < end <= len(body) or body[start:end] != quote):
        raise ValueError("Evidence is not the supplied original body span")


def summarize_review(review, *, demand_body, operation_body):
    """Summarize explicit annotations only; unknown never means compatible.

    Body bounds reject oversized inputs, rather than silently truncating evidence.
    Runtime differences are review hints, not proof that interoperation is absent.
    Full-demand completeness includes missing references and acceptance details.
    """
    for body in (demand_body, operation_body):
        if not isinstance(body, str) or len(body.encode("utf-8")) > MAX_BODY_BYTES:
            raise ValueError("Body missing or over the offline contract bound")
    if (not isinstance(review, dict) or set(review) != {"demand_complete", "facets"}
            or type(review["demand_complete"]) is not bool
            or not isinstance(review["facets"], dict) or set(review["facets"]) != set(FACETS)):
        raise ValueError("Review needs explicit completeness and all four facets")
    relations = {}
    for name in FACETS:
        facet = review["facets"][name]
        if not isinstance(facet, dict) or set(facet) != {"relation", "reason", "demand", "operation"}:
            raise ValueError("Facet needs relation, reason and both evidence sides")
        relation = facet["relation"]
        if relation not in ("aligned", "different", "unknown", "slice"):
            raise ValueError("Invalid reviewed relation")
        if relation == "slice" and name != "outcome":
            raise ValueError("A slice denotes a limited outcome, not a runtime or data shape")
        if not isinstance(facet["reason"], str) or not facet["reason"].strip() or len(facet["reason"]) > 1600:
            raise ValueError("An explicit bounded review reason is required")
        if relation == "unknown":
            if facet["demand"] is not None or facet["operation"] is not None:
                raise ValueError("Unknown must not pretend to be an established relation")
        else:
            _span(facet["demand"], demand_body)
            _span(facet["operation"], operation_body)
        relations[name] = relation
    different = [name for name in FACETS if relations[name] == "different"]
    unknown = [name for name in FACETS if relations[name] == "unknown"]
    partial = relations["outcome"] == "slice"
    if not review["demand_complete"] or unknown:
        status = "context_required"
    elif different:
        status = "mismatch_hint"
    elif partial:
        status = "partial_candidate"
    else:
        status = "candidate_for_review"
    return {"status": status, "different_facets": different, "unknown_facets": unknown,
            "partial_outcome_hint": partial, "demand_complete": review["demand_complete"],
            "annotation_origin": "reviewed_not_automatically_inferred",
            "changes_qualification": False, "changes_selection": False}
