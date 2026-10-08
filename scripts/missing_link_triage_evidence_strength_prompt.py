"""Experimental evidence-strength instructions, not production or semantic proof.

Keep all predecessor prompts, native declaration schema and provenance guards
frozen. No provider, history, budget, source acquisition or execution on import.
"""
from scripts import missing_link_triage_declaration_schema as previous


_DECLARATION_ANCHOR = "Do not silently restate an observed-return claim as a declared-type comparison.\n"
_DIFFERENCE_ANCHOR = "A primitive cannot certify the whole task.\n"

_DECLARATION_GUIDANCE = """
Distinguish a textual declaration from behavior demonstrated by the supplied body.
Docstrings, examples, annotations and callable names do not demonstrate an unseen
delegate's actual result or behavior. Repeating a declaration in both cited
passages is not independent implementation evidence. If the requested property
concerns actual results or behavior, do not satisfy it by comparing declarations
with themselves. A declaration-only comparison remains permitted when the
requested property itself concerns a declared contract; explicitly state that
scope in demand_property, operation_property and reason, without certifying
runtime enforcement. When the needed delegate contract is unseen, keep the
actual-result property unknown unless a separately visible local composition
establishes the bounded property being compared. A visible dispatch or validation
step can support its own requested property without establishing the delegate's
contents, output type or complete behavior. Do not force a known relation or slice.
"""

_DIFFERENCE_GUIDANCE = """
A conditional possibility is not an established counterexample. Before choosing
different, identify a positively supported differing property in the supplied
evidence at the stated input, branch and implementation layer. A conditional
helper call with unseen values may preserve or change a result; its presence
alone proves neither difference nor unconditional alignment. Missing proof of
alignment is not proof of difference. Unknown remains appropriate when that
comparable result cannot be established. Runtime execution is not required for
a source-supported contrast: explicit literal behavior can establish a bounded
difference. State input/branch restrictions in operation_property and reason;
do not generalize one changing input to all inputs or one default branch to all
branches. Keep separately supported local behavior even when another delegate
is unseen. A visible requested validation suboperation may support a bounded
slice, with remaining producer/integration work explicit; it does not certify
the producer's results or the complete requested task. Do not manufacture a slice
or repair unknown to claim complete coverage.
"""

_INSERTIONS = ((_DECLARATION_ANCHOR, _DECLARATION_GUIDANCE),
               (_DIFFERENCE_ANCHOR, _DIFFERENCE_GUIDANCE))


def _revise_prompt(prompt):
    """Reject predecessor anchor drift rather than silently losing safeguards."""
    if any(prompt.count(anchor) != 1 for anchor, _ in _INSERTIONS):
        raise ValueError("Frozen evidence-strength anchor is missing or duplicated")
    for anchor, guidance in _INSERTIONS:
        prompt = prompt.replace(anchor, anchor + guidance, 1)
    return prompt


PROMPT = _revise_prompt(previous.PROMPT)
schema_for_context = previous.schema_for_context
normalize_prediction = previous.normalize_prediction
