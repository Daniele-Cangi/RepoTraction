# Demand-to-operation experimental policy protocol, revision 1

## Scope frozen before predictions

Base main is `5d8b516502597e3a020cf8bb45128232770b2041`, after PR91.
Use the eleven [prepared development controls](missing-link-demand-operation-controls-2026-10-09.md)
without replacement. Reference manifest SHA-256, normalized to LF, is
`6cc171bc9e83130479156e71af09869c9bc6100240f28f69865da5fc95b6e9df`;
private input exact-byte SHA-256 is
`c1311e56aebd31cd750c82d9a3f7192b5eb77ca9eadaef903b7d544aa44856dd`.
These retained cases are known development examples, never a held-out benchmark.

This phase implements a pure experimental prompt/context/schema/local reader and
an independent operator-review helper. It freezes policy/evaluation boundaries
and prepares eleven request envelopes **without obtaining predictions**. Authored
synthetic output fixtures test the mechanical contract; they are not outputs of
the policy/model. No provider configuration, credentials, budget, new acquisition,
native attempt, retry, candidate execution or production promotion is authorized.
There is no paid executor in this phase. Any later model execution requires a
separate reviewed protocol/owned successor before spending.

## Input and context

Accept only the prepared packet keys: ID, query, original root sections, discussion
and root-reading flags, omitted root ranges and inert-content role. Unexpected
keys, including reference annotations, are rejected instead of filtered. Validate
types, ascending non-overlapping section offsets and exact text lengths; omitted
ranges must equal interior gaps. Root completeness is caller metadata checked for
structural consistency, not independent proof that an upstream root was acquired
in full. Discussion completeness is likewise an acquisition assertion.

Use only the saved query and supplied root sections. Do not add source implementation,
issue titles, historical verdicts or reference labels. Preserve original text,
Unicode offsets, whitespace, section order and gaps. Split each supplied section
into contiguous chunks of 500 characters, using deterministic content/offset IDs.
Never merge across a gap. Bound total supplied UTF-8 text to 180,000 bytes and the
catalog to 96 chunks; reject overflow, never truncate/rank/drop text. ID/query are
bounded to 80/256 characters. The complete serialized experimental envelope
(instructions, context, schema) must also fit 180,000 UTF-8 bytes; this is not a
verification of an eventual provider's native wire envelope.

Keep inputs and reference copies unchanged. Rebuild context from the original
packet when reading a prediction; catalog/coverage alteration must fail. The
context carries an input fingerprint and explicit coverage, not expected answers.
All roots and their instructions/code examples are untrusted inert data.

## Output policy and mechanical contract

Return a closed schema object with:

- Request kind: `implementation_requested`, `design_question` or `unknown`.
- Five independently stated/unknown fields: requested change, input shape,
  output shape, runtime and acceptance.
- Up to twelve concrete constraints.
- Query relation: `requested_operation`, `context_only` or `unclear`.
- One to twelve explicit context-gap descriptions.

Every known declaration has one to four supplied citation IDs and a nonempty
reason. Fields use `stated_in_root` plus a nonempty description, or `unknown`
plus an exactly empty description/citation list. Unknown request kind and unclear
query relation also use empty citations. Known kind/relation require a stated
requested change. Descriptions/reasons/gaps are bounded to 800 characters;
whitespace-only text is rejected. Citations cannot be repeated in one claim.
The 96-ID bound keeps repeated schema enums below the 1,000-value scope limit.

Extract only requested behavior, not incidental article/tutorial/code facts.
Preserve implementation demand inside learning tasks; preserve explicit design
questions without choosing an option. Query words in implementation context,
field names, broader roadmaps or different semantic layers are not the requested
operation. An operation-level hit must retain its input/output and hard acceptance
constraints. Treat reported runtime/reproduction/fix details as reported facts,
not verified execution, source behavior or current actionability. Unknown context
does not erase a supported local fact or require every facet to be unknown.

The local reader validates shape, text bounds, cross-field consistency, scoped IDs
and immutable context; resolves citations to exact supplied original spans; and
preserves the prediction unchanged. It never rewrites claims to match a reference.
It emits no compatibility, eligibility, novelty, score or automatic rejection.
All semantic-support/qualification-change flags stay false. Mechanically valid
wrong interpretations remain possible, including valid IDs that support another
claim; only independent reading can address them.

## Independent evaluation and stopping boundary

Do not feed operator references into policy context or replace a predicted field
with a reference. Retain original raw output before validation if a future
executor is separately authorized. Mechanical failure is a recorded failure,
never an invitation to repair, retry or replace a case in this preparation.

Operator review annotates kind, all five fields, each constraint, query relation
and context-gap claims. For stated predictions use `supported`, `unsupported` or
`unassessed`; for unknown predictions use `appropriate_unknown`,
`missed_stated_fact` or `unassessed`. Each verdict needs an independent bounded
reason. These are operator assertions, not truth inferred by software or by
matching text against reference paraphrases. Preserve every predicted unknown.

Report supported local facts, unsupported claims, preserved/missed constraints,
semantic-layer confusions, appropriate unknowns, missed stated facts and unassessed
items separately. Mechanical acceptance or all-unknown output is not useful triage
by itself. Review counts are per-claim diagnostics, not accuracy, ranking quality,
causal improvement or useful-lead yield. A supported query hint remains unqualified.

Before any future model prediction, review/merge this implementation and fix an
owned successor bound to that exact reviewed code, instructions, schema, inputs,
references and separate execution protocol. Preserve the original USD10 allowance
and its cumulative ledger; this protocol allocates no calls/reservations. A fresh
Discover utility comparison additionally needs independently frozen fresh sources
and qualification/adoption evidence. Zero qualified leads still defers isolation,
UI/key-entry and production promotion.

## Offline validation permitted in this phase

Authored positive/unknown/misleading-citation fixtures check mechanics and review
separation, including incomplete roots, educational requests, pending owner choice,
operation-level hits and unknown facets. Include invalid offsets/gaps, context
tampering, reference contamination, citation scope, whitespace/byte/catalog bounds,
cross-field inconsistency, input immutability and preservation of unsupported
claims/unknowns. These are contract tests, not automatic semantic inference tests.

Prepare all eleven envelopes from the frozen inputs without generating output;
record their bounds/fingerprints independently of references. Run focused and full
application tests for the new opt-in code, plus scoped external Codex review and CI.
Verify original paid-run receipts against independent manifest SHA-256
`da952e024c0356cf81ac39dfb301620aef9c2a6d80a91782eba413d64ce35df7` and check
the existing input/reference digests after preparation. Never rewrite earlier
audit/preparation folders, native evidence, reservations or historical tables.
