"""Experimental wording revision only; no production wiring or IO on import.

The prior prompt stays frozen. Its schema, provenance validation, context and
normalization are reused unchanged; a declared contrast is not semantic proof.
"""
from scripts import missing_link_triage_explicit_scope as previous


_PREVIOUS_COMPARISON = """For a known relation, use comparison_scope=requested_operation and describe concrete
demand_property and operation_property, each nonempty and at most 400 characters.
Compare the same requested operation, not whole-product deliverables against a
primitive's arguments/result. Project reports, file ingest or final exports are not
automatically the inputs/outputs of every nested operation. Missing wiring does not
establish incompatible shapes. Generic parameters do not exclude specific values;
an unseen delegate's return contract is unknown, not a positively different output.
"""

_PROPERTY_COMPARISON = """This is a property comparison, not an implementation or adoption assessment.
For each facet, identify the property explicitly required of the requested operation
and the candidate property actually visible at the declared operation layer. Compare
the same property dimension at that layer; you do not need proof that the candidate
already implements, belongs to or is integrated with the requested operation.
comparison_scope=requested_operation names the scope of the demand property; it
does not assert that the candidate implements that demand. If a property or the
corresponding interface cannot be established, use unknown and explain that gap.

For a known relation, use comparison_scope=requested_operation and describe concrete
demand_property and operation_property, each nonempty and at most 400 characters.
A positively supported local property contrast permits different even when adoption
or complete acceptance context is unavailable. Missing acceptance/adoption context
keeps demand_complete false; it alone does not erase an evidenced local comparison.
Property alignment is not proof of the requested behavior or a supported slice.

Do not compare whole-product deliverables against a primitive's arguments/result.
Project reports, file ingest or final exports are not automatically the inputs/outputs
of every nested operation. Missing wiring does not establish incompatible shapes.
Distinguish a declared interface contract from observed runtime enforcement. Type
annotations can support a declared interface contrast, not runtime rejection of
other values; state which property is compared and do not switch between them.
Generic parameters do not exclude specific values; an unseen delegate's return
contract is unknown, not a positively different output. A lack of implementation
proof is not itself a property difference. Do not invent a requested property from
project goals or force a relation when comparable evidence is missing.
"""


def _revise_prompt(prompt):
    """Fail on predecessor drift rather than silently removing other safeguards."""
    if prompt.count(_PREVIOUS_COMPARISON) != 1:
        raise ValueError("Frozen comparison paragraph is missing or duplicated")
    return prompt.replace(_PREVIOUS_COMPARISON, _PROPERTY_COMPARISON, 1)


PROMPT = _revise_prompt(previous.PROMPT)
schema_for_context = previous.schema_for_context
normalize_prediction = previous.normalize_prediction
