"""Keep reusable primitives separate from fulfillment of target requirements."""
from .sources import source_role
from .operation_evidence import cites_operation_body, in_operation

CONTRIBUTION_KINDS = ("existing_behavior", "partial_behavior", "scope_compatible", "not_demonstrated")
PARTIAL_BASES = ("candidate_implementation", "target_context", "analogy", "not_established")

SUPPORT_MESSAGES = {
    "repository_evidence_missing": "No acquired repository evidence establishes the asserted verdict.",
    "partial_requirement_unfulfilled": "A partial primitive does not establish fulfillment of the whole requirement.",
    "partial_attribution_not_established": "Candidate-owned partial behavior was not established by a complete attribution review.",
    "selected_operation_body_missing": "The citations do not establish the selected operation's own implementation body. A class or sibling citation cannot borrow a method's behavior; select an available method ID and cite its body for method-level claims.",
    "selected_operation_attribution_missing": "Partial citations are not bound to this check and the selected operation's implementation region.",
    "partial_behavior_not_supported": "This check does not establish a reusable partial behavior; passive constraints, conflicts and unexplained claims cannot receive partial credit.",
    "behavior_not_demonstrated": "The claimed requirement fulfillment has no demonstrated existing behavior.",
}


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


def normalize_support(status, contribution, evidence, *, capability, passive, reason, runtime_entrypoints=(), partial=None, operation_regions=(), diagnostics=None):
    """Provenance gates, not semantic proof or permission to run/adopt source code."""
    if status not in {"satisfied", "incompatible", "undetermined"}:
        raise ValueError("Unknown requirement verdict.")
    if contribution not in CONTRIBUTION_KINDS:
        raise ValueError("Unknown requirement contribution kind.")
    def note(code):
        if diagnostics is not None and code not in diagnostics:
            diagnostics.append(code)
    if status in {"satisfied", "incompatible"} and not any(entry.get("path") for entry in evidence):
        status = "undetermined"
        note("repository_evidence_missing")
    implemented = any(entry.get("path") and source_role(entry["path"], runtime_entrypoints=runtime_entrypoints)
                      == "implementation" for entry in evidence)
    selected_body = any(entry.get("path") and source_role(entry["path"], runtime_entrypoints=runtime_entrypoints)
        == "implementation" and cites_operation_body(entry, operation_regions) for entry in evidence)
    if contribution == "partial_behavior":
        # A primitive cannot certify a compound/end-to-end requirement. Require
        # an explicit bounded claim citing implementation, not only docs/tests.
        if status == "satisfied":
            status = "undetermined"
            note("partial_requirement_unfulfilled")
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
        accepted = status == "undetermined" and implemented and attributed and cited_body and not passive and reason
        if not accepted:
            if not partial or partial["basis"] != "candidate_implementation" or not all(
                    partial[key] for key in ("operation", "requirement_part", "remaining_work")):
                note("partial_attribution_not_established")
            elif not cited_body:
                note("selected_operation_body_missing")
            elif not attributed:
                note("selected_operation_attribution_missing")
            else:
                note("partial_behavior_not_supported")
        return status, ("partial_behavior" if accepted else "not_demonstrated")
    if status == "satisfied" and (contribution == "not_demonstrated"
                                   or (contribution == "existing_behavior" and not passive and not selected_body)):
        status = "undetermined"
        note("behavior_not_demonstrated" if contribution == "not_demonstrated" else "selected_operation_body_missing")
    if status != "satisfied":
        contribution = "not_demonstrated"
    elif passive:
        contribution = "scope_compatible"
    return status, contribution
