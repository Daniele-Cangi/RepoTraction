"""Keep reusable primitives separate from fulfillment of target requirements."""
from .sources import source_role
from .operation_evidence import cites_operation_body, in_operation

CONTRIBUTION_KINDS = ("existing_behavior", "partial_behavior", "scope_compatible", "not_demonstrated")
PARTIAL_BASES = ("candidate_implementation", "target_context", "analogy", "not_established")


def partial_reviews(values, requirement_ids):
    """Explicit model attribution, not an automatic semantic-truth certificate."""
    if not isinstance(values, list) or len(values) > 30:
        raise ValueError("Partial support reviews must be a bounded list.")
    reviews = {}
    fields = {"requirement_id", "basis", "operation", "requirement_part", "remaining_work", "source_ids"}
    for value in values:
        if not isinstance(value, dict) or set(value) != fields:
            raise ValueError("Partial support review has missing or unexpected fields.")
        rid = value["requirement_id"]
        if not isinstance(rid, str) or rid not in requirement_ids or rid in reviews:
            raise ValueError("Unknown or duplicate partial support requirement.")
        if value["basis"] not in PARTIAL_BASES:
            raise ValueError("Unknown partial support basis.")
        review = {"requirement_id": rid, "basis": value["basis"]}
        for key in ("operation", "requirement_part", "remaining_work"):
            if not isinstance(value[key], str) or len(value[key]) > 6000:
                raise ValueError("Partial support text exceeds contract bounds.")
            review[key] = value[key].strip()
        refs = value["source_ids"]
        if not isinstance(refs, list) or len(refs) > 100 or any(not isinstance(ref, str) or not ref for ref in refs):
            raise ValueError("Partial support citations must be a bounded list of source IDs.")
        review["source_ids"] = list(dict.fromkeys(refs))
        reviews[rid] = review
    return reviews


def normalize_support(status, contribution, evidence, *, capability, passive, reason, runtime_entrypoints=(), partial=None, operation_regions=()):
    """Provenance gates, not semantic proof or permission to run/adopt source code."""
    if status not in {"satisfied", "incompatible", "undetermined"}:
        raise ValueError("Unknown requirement verdict.")
    if contribution not in CONTRIBUTION_KINDS:
        raise ValueError("Unknown requirement contribution kind.")
    if status in {"satisfied", "incompatible"} and not any(entry.get("path") for entry in evidence):
        status = "undetermined"
    implemented = any(entry.get("path") and source_role(entry["path"], runtime_entrypoints=runtime_entrypoints)
                      == "implementation" for entry in evidence)
    selected_body = any(entry.get("path") and source_role(entry["path"], runtime_entrypoints=runtime_entrypoints)
        == "implementation" and cites_operation_body(entry, operation_regions) for entry in evidence)
    if contribution == "partial_behavior":
        # A primitive cannot certify a compound/end-to-end requirement. Require
        # an explicit bounded claim citing implementation, not only docs/tests.
        if status == "satisfied":
            status = "undetermined"
        anchors = {entry.get("source_id"): entry for entry in evidence}
        # Repository ownership is not ownership by this selected capability.
        # Only its pinned structural evidence/definition paths grant scope;
        # model interpretation citations cannot expand it to other subsystems.
        candidate_paths = {entry["path"] for entry in capability.get("evidence", []) if entry.get("path")}
        definition_path = capability.get("definition", {}).get("path")
        if definition_path:
            candidate_paths.add(definition_path)
        attributed = bool(partial and partial["basis"] == "candidate_implementation"
            and all(partial[key] for key in ("operation", "requirement_part", "remaining_work"))
            and partial["source_ids"] and all(ref in anchors and anchors[ref].get("path")
                and anchors[ref]["path"] in candidate_paths
                and source_role(anchors[ref]["path"], runtime_entrypoints=runtime_entrypoints) == "implementation"
                and in_operation(anchors[ref], operation_regions)
                for ref in partial["source_ids"]))
        cited_body = bool(partial and any(ref in anchors and cites_operation_body(anchors[ref], operation_regions)
            for ref in partial["source_ids"]))
        return status, ("partial_behavior" if status == "undetermined" and implemented and attributed and cited_body and not passive and reason
                        else "not_demonstrated")
    if status == "satisfied" and (contribution == "not_demonstrated"
                                   or (contribution == "existing_behavior" and not passive and not selected_body)):
        status = "undetermined"
    if status != "satisfied":
        contribution = "not_demonstrated"
    elif passive:
        contribution = "scope_compatible"
    return status, contribution
