"""Experimental branch/property wording; no production wiring or IO on import.

Keep the predecessor and all schema/provenance/normalization delegates frozen.
Instructions are not semantic verification, model-quality evidence or a gate.
"""
from scripts import missing_link_triage_property_prompt as previous


_CONTRAST_ANCHOR = "Property alignment is not proof of the requested behavior or a supported slice.\n"
_BRANCH_ANCHOR = "other values; state which property is compared and do not switch between them.\n"

_CONTRAST_GUIDANCE = """
Separate comparability of properties from identity of implementations. First
establish the explicitly requested property and the visible candidate property
in their cited passages at the stated layer. For example, a demand for command
text and a body visibly returning booleans may support a local output contrast
without proving that the candidate already implements the command generator.
That contrast does not establish whole-task rejection or a runtime ban. Do not
infer a comparable interface from a project deliverable, a guessed nested layer
or an unseen delegate. Keep unknown when either comparable property is missing;
do not force a contrast merely because the operations have different names.
"""

_BRANCH_GUIDANCE = """
Before an observed-return or behavior claim, check the supplied return paths and
their conditions. Separate a declared return type from the actual behavior visible
on each branch. If one branch encodes strings and another returns non-strings
unchanged, describe that conditional behavior; a bytes annotation does not prove
an unconditional bytes result. State any input or branch restriction explicitly
in operation_property and reason. A single branch cannot certify all inputs.
Do not silently restate an observed-return claim as a declared-type comparison.
When a return path or delegate is unseen, its behavior remains unknown; a cited
declared contract or an explicitly bounded visible branch may still support its
own local property comparison. Passing through a collection does not establish
the requested collection detection or transformation policy.
"""

_INSERTIONS = ((_CONTRAST_ANCHOR, _CONTRAST_GUIDANCE), (_BRANCH_ANCHOR, _BRANCH_GUIDANCE))


def _revise_prompt(prompt):
    """Reject missing/duplicated anchors, rather than dropping frozen safeguards."""
    if any(prompt.count(anchor) != 1 for anchor, _ in _INSERTIONS):
        raise ValueError("Frozen branch/property anchor is missing or duplicated")
    for anchor, guidance in _INSERTIONS:
        prompt = prompt.replace(anchor, anchor + guidance, 1)
    return prompt


PROMPT = _revise_prompt(previous.PROMPT)
schema_for_context = previous.schema_for_context
normalize_prediction = previous.normalize_prediction
