"""Offline triage regressions, not a semantic classifier or production gate.

Quotation checks are mechanical. Semantic bases must be independently reviewed:
validating a review's shape or label consistency does not prove its truth.
Nothing here repairs predictions, changes history or qualifies a connection.
"""
from scripts.missing_link_triage_contract import FACETS, MAX_BODY_BYTES, summarize_review


def resolve_demand_quote(sources, source_id, quote):
    """Resolve one unique exact quotation in its declared original source.

    No normalization, cross-source search, truncation or paraphrase repair.
    Offsets are characters in the bodies joined in insertion order with \n\n.
    """
    if (not isinstance(sources, dict) or not sources
            or any(not isinstance(key, str) or not key or not isinstance(text, str)
                   for key, text in sources.items())):
        raise ValueError("Invalid original demand sources")
    body = "\n\n".join(sources.values())
    if len(body.encode("utf-8")) > MAX_BODY_BYTES:
        raise ValueError("Original demand exceeds body bound")
    if (not isinstance(source_id, str) or source_id not in sources
            or not isinstance(quote, str) or not quote.strip() or len(quote) > 500):
        raise ValueError("Invalid demand quotation")
    text = sources[source_id]
    first = text.find(quote)
    # Search from the next character, so overlapping occurrences are ambiguous too.
    if first < 0 or text.find(quote, first + 1) >= 0:
        raise ValueError("Demand quotation must occur exactly once in its source")
    offset = 0
    for key, original in sources.items():
        if key == source_id:
            start = offset + first
            return {"start": start, "end": start + len(quote), "quote": quote}
        offset += len(original) + 2


BASES = ("observed_alignment", "observed_difference", "requested_suboperation",
         "analogy", "missing_integration", "not_established")


def audit_reviewed_prediction(prediction, reviews, *, demand_body, operation_body):
    """Compare a supplied prediction to independent reviewer annotations.

    This does NOT infer semantic support from quotes, code, labels or wording.
    A caller can still supply an incorrect review. Unknown predictions are
    abstentions, never errors merely for disagreeing with known reviewer labels.
    """
    summary = summarize_review(prediction, demand_body=demand_body, operation_body=operation_body)
    summary.pop("annotation_origin")
    if not isinstance(reviews, dict) or set(reviews) != set(FACETS):
        raise ValueError("Independent review required for all four facets")
    issues = []
    for facet in FACETS:
        review = reviews[facet]
        if not isinstance(review, dict) or set(review) != {
                "basis", "reason", "requested_part", "existing_behavior", "remaining_work"}:
            raise ValueError("Invalid independent semantic review")
        basis = review["basis"]
        if not isinstance(basis, str) or basis not in BASES:
            raise ValueError("Unknown semantic basis")
        if (not isinstance(review["reason"], str) or not review["reason"].strip()
                or len(review["reason"]) > 1600):
            raise ValueError("Explicit bounded review reason required")
        for key in ("requested_part", "existing_behavior", "remaining_work"):
            value = review[key]
            if basis == "requested_suboperation":
                if facet != "outcome" or not isinstance(value, str) or not value.strip() or len(value) > 1600:
                    raise ValueError("A reviewed slice needs the requested part, existing behavior and remaining work")
            elif value is not None:
                raise ValueError("Non-slice bases must not claim a reviewed suboperation")
        relation = prediction["facets"][facet]["relation"]
        expected = {"aligned": "observed_alignment", "different": "observed_difference",
                    "slice": "requested_suboperation"}.get(relation)
        if relation != "unknown" and basis != expected:
            kind = ("analogy_is_not_suboperation" if relation == "slice" and basis == "analogy"
                    else "missing_integration_is_not_difference" if relation == "different" and basis == "missing_integration"
                    else "relation_not_established_by_review")
            issues.append({"facet": facet, "kind": kind})
    return {"syntactic_summary": summary, "semantic_consistent_with_review": not issues,
            "issues": issues, "review_origin": "independent_review_not_automatically_inferred",
            "changes_selection": False, "changes_qualification": False}
