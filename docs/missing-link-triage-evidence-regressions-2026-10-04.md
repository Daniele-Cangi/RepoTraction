# Offline triage evidence regressions

The [completed Luna retry](missing-link-luna-triage-retry-result-2026-10-04.md)
exposed two separate limitations: non-verbatim quotations and partial-value
claims supported only by analogy. This follow-up records mechanical citation
checks and independently reviewed semantic controls, without another model call
or a change to production discovery. It does not claim that Luna now makes
better predictions or that an automatic semantic filter has been implemented.

## Exact demand quotations

The experimental `scripts/missing_link_triage_evidence.py` resolver checks one
quotation against its declared original body or comment. It returns original
character offsets in the joined source bodies; Unicode, Markdown and whitespace
are preserved. A paraphrase, undeclared source, cross-source quotation or
ambiguous occurrence is rejected, not repaired or searched elsewhere.

Nine synthetic quotation tests cover source/comment offsets, paraphrases,
formatting, legal substrings inside Markdown, duplicates, overlapping duplicates,
source ownership, malformed input and bounds. Original demand bodies are limited
to 180,000 UTF-8 bytes and quotations to 500 characters, without truncation.
Overlapping duplicates are explicitly ambiguous: `aa` in `aaa` is not uniquely
located, even though a non-overlapping substring count returns one.

The old paid harness and its saved results remain frozen. This resolver is
available for a future experimental harness; production evidence validation is
unchanged. Nothing silently replaces the earlier normalizer or its outputs.

## Reviewed semantic consistency

The second helper compares supplied predictions with **independent reviewer
annotations**, not with an automatically inferred meaning of the text. An
annotation must state its basis and reason. A reviewed outcome slice must also
name the requested suboperation, existing behavior and remaining work.

Eleven synthetic semantic checks exercise the following distinctions:

- Local timestamp/signature versus independently controlled external anchoring:
  an analogy does not establish an outcome slice.
- Sorted-array insertion versus hosted-help search with an unspecified data
  representation: hypothetical utility is not an established contribution.
- Ordered-array boundaries explicitly requested as part of an index: the same
  primitive can have narrow partial value under different reviewed requirements.
- Arithmetic mean as one explicitly requested profiling measure: partial value
  remains visible without qualifying the full request.
- A main-only CI step versus a Python method: missing integration is not an
  observed runtime difference. A genuinely reviewed interface/runtime difference
  remains only a hint, not proof that interoperation is impossible.
- Unknown predictions remain abstentions even when a reviewer knows more.
  Invalid citations, missing reviews or incomplete slice descriptions cannot be
  laundered into a positive audit result. Inputs are not rewritten.

These tests validate consistency with supplied judgments, **not the correctness
of those judgments**. A reviewer can still annotate incorrectly. The helper does
not determine semantic relevance, operation ownership, adoptability or accuracy;
its result cannot select or qualify a lead. The syntactic summary and semantic
issues are separate so a valid source span cannot masquerade as semantic proof.

## Replay of retained responses

A private read-only replay inspected all nine original completed responses. It
reproduces three citation-invalid cards and seven absent quotations, with the
original six validated annotations unchanged. Original raw output is preserved.

Two cards receive explicit independent semantic annotations in this replay.
The timestamp card produces two consistency warnings: the runtime difference is
missing integration, and the claimed outcome slice is analogy. The mean card
retains its reviewed average suboperation and stays context-required. The other
seven cards are not automatically semantically classified by this replay; the
invalid JLS/help-search response is covered by a synthetic negative control.

All **12 table hashes**, all reservation/allowance rows and **426 earlier private
artifacts** match the pre/post baseline. No acquisition, execution, job import,
history repair or paid call occurs. The original allowance remains
**471 reservations / USD7.2717195**. The earlier failed call's native usage remains
unknown. Forty-one focused triage tests pass, including the 20 new regressions.
The full local suite passes **1,021 tests**; production behavior and provider
configuration are unchanged.

## Next step

Specify a small experimental prompt/context revision against these controls,
keeping exact quotations and an explicit requested suboperation distinct from
analogy, scope mismatch or missing integration. Freeze its protocol and withheld
evaluation before any paid test. Do not loosen citation guards, relabel the
stored results or introduce this reviewed checklist into production selection.
