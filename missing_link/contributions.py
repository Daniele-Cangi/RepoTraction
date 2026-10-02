"""Keep reusable primitives separate from fulfillment of target requirements."""
from .sources import source_role

CONTRIBUTION_KINDS = ("existing_behavior", "partial_behavior", "scope_compatible", "not_demonstrated")


def normalize_support(status, contribution, evidence, *, passive, reason, runtime_entrypoints=()):
    """Provenance gates, not semantic proof or permission to run/adopt source code."""
    if status not in {"satisfied", "incompatible", "undetermined"}:
        raise ValueError("Unknown requirement verdict.")
    if contribution not in CONTRIBUTION_KINDS:
        raise ValueError("Unknown requirement contribution kind.")
    if status in {"satisfied", "incompatible"} and not any(entry.get("path") for entry in evidence):
        status = "undetermined"
    implemented = any(entry.get("path") and source_role(entry["path"], runtime_entrypoints=runtime_entrypoints)
                      == "implementation" for entry in evidence)
    if contribution == "partial_behavior":
        # A primitive cannot certify a compound/end-to-end requirement. Require
        # an explicit bounded claim citing implementation, not only docs/tests.
        if status == "satisfied":
            status = "undetermined"
        return status, ("partial_behavior" if status == "undetermined" and implemented and not passive and reason
                        else "not_demonstrated")
    if status == "satisfied" and (contribution == "not_demonstrated"
                                   or (contribution == "existing_behavior" and not implemented)):
        status = "undetermined"
    if status != "satisfied":
        contribution = "not_demonstrated"
    elif passive:
        contribution = "scope_compatible"
    return status, contribution
