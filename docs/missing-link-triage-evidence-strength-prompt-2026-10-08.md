# Experimental instructions for evidence strength

This October 8 revision adds two instruction blocks to the experimental triage
prompt following the [authored evidence controls](missing-link-triage-evidence-strength-controls-2026-10-08.md).
It addresses declared versus demonstrated behavior and possible versus established
differences. It is not wired into production or the frozen paid driver, and has
not been tested with a new model response.

## Bounded instruction change

The new [prompt module](../scripts/missing_link_triage_evidence_strength_prompt.py)
wraps the native declaration-schema module. Removing its two insertions reproduces
the complete predecessor prompt. Missing or duplicated anchors fail explicitly.
Schema and normalizer remain the exact predecessor function objects, including
explicit native branch validation and source/provenance guards.

The first block instructs the model not to treat repeated docstrings, annotations
and callable names as proof of unseen delegate results. It permits declaration-only
comparisons when the requested property itself concerns a declared contract, with that scope
explicit in both properties and the reason. Actual-result demands cannot be
satisfied by silently comparing textual declarations with themselves. Separately
visible local composition or dispatch can still support its own bounded property.

The second block requires positive evidence for a differing property at the
stated input, branch and implementation layer. An unseen helper's conditional
policy may preserve or change a result; that possibility proves neither difference
nor unconditional alignment. Literal visible behavior can support a scoped
contrast without executing acquired code. Visible validation suboperations remain
available as bounded slices when explicitly requested, with producer/integration
work separate. Unknowns and branch restrictions must not be repaired or generalized.

## Offline checks and limits

The [new tests](../tests/test_missing_link_triage_evidence_strength_prompt.py)
replay all 18 authored controls through the unchanged delegates and add 11 checks
for instruction insertion, frozen predecessor hash, native schema/guard identity,
unknown declarations, import safety, transport encoding and absent production wiring.
For the authored encoding context, Responses and chat payloads differ only in the
instruction text; context, schema and other transport settings stay unchanged.
Encoding uses an explicit fictional
local provider configuration and makes no model request.

These checks verify instruction presence and software contracts, not that a model
obeys the wording or that grounding quality improves. Well-formed semantic
overclaims still require review; there is no automatic semantic classifier or new
eligibility gate. Earlier prompts, sources, native responses and reviewer notes
remain immutable. No historical card is repaired or relabeled.

All 403 focused triage tests and the complete 1,383-test suite pass; CLI help and
local documentation links are checked. Read-only integrity verification reproduces
the frozen source-review/response hashes and protects 741 earlier artifacts.
Accounting remains 523 reservations / USD7.6539126 reserved, not a provider
invoice. No new model call or allowance reservation is made.

## Next validation step

Review this wording against the two declared evidence distinctions, preserving
grounded local contrasts and honest abstention without parser/resolver expansion.
Only then prepare a separately frozen fresh model protocol with explicit source
coverage, exact requests and the original cumulative allowance. Do not rerun the
familiar paid cohort as evidence of improvement. Repository-only autonomous
discovery and isolated candidate execution remain separate, gated tasks.
