"""Experimental layer-accurate explanations, including abstentions.

No production wiring, IO, semantic certification or historical-card repair.
Keep the predecessor and its schema/normalization delegates unchanged.
"""
from scripts import missing_link_triage_branch_prompt as previous


_LAYER_ANCHOR = "where it runs. An unsupported layer or property requires unknown.\n"
_LAYER_GUIDANCE = """
Keep source-layer attribution accurate in reason even for unknown. Keep its axis;
set only comparison_scope, operation_layer, demand_property, operation_property,
demand_span_id, operation_id and all slice fields to empty strings as required below.
A factory receiving
a callback and returning a callable does not itself consume that callable's later
arguments or return its later result. Describe any visible nested behavior at its
own layer; do not attribute it to the selected factory's interface. If a delegate
is unseen, name the specific evidence gap without guessing its return contract,
clock policy, external service or publication behavior from its name.
A delegate gap does not erase a separately visible local composition, but a known
comparison still needs the explicitly requested property and cited behavior at
the same layer. Do not impose a direct-call mechanism unless the demand requires
it, or force a known relation merely because a composition is visible. Unknown
remains appropriate when that bounded comparison is not established.
"""
_INSERTIONS = ((_LAYER_ANCHOR, _LAYER_GUIDANCE),)


def _revise_prompt(prompt):
    """Reject anchor drift rather than silently losing predecessor safeguards."""
    if any(prompt.count(anchor) != 1 for anchor, _ in _INSERTIONS):
        raise ValueError("Frozen layer anchor is missing or duplicated")
    for anchor, guidance in _INSERTIONS:
        prompt = prompt.replace(anchor, anchor + guidance, 1)
    return prompt


PROMPT = _revise_prompt(previous.PROMPT)
schema_for_context = previous.schema_for_context
normalize_prediction = previous.normalize_prediction
