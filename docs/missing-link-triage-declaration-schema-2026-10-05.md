# Offline declaration schema constraints

This separate experiment addresses the empty properties in the rejected mean
card from the [layer comparison](missing-link-triage-layer-result-2026-10-05.md).
It makes known and unknown declarations distinct in the generation schema,
without changing the frozen prompt, existing normalizers or production wiring.
Offline checks preserve the previous accepted results and rejection. **No new
model response, improved explanation quality or live API acceptance is demonstrated.**

PR74 merged as `84f7710` after its no-findings Codex review and four green CI jobs.
PR75 merged as `0a53dae` with four green CI jobs after correcting two valid
documentation findings: only slice needs the three slice descriptions; populated
unknown declarations are rejected without being cleared.

## Generation constraints

`scripts/missing_link_triage_declaration_schema.py` reuses the exact layer prompt.
Each facet has closed, fully required nested `anyOf` branches:

- Unknown preserves its fixed axis and requires empty scope, layer, properties,
  citations and slice descriptions. A nonempty reason remains required.
- Aligned/different requires requested-operation scope, an explicit known layer,
  both nonempty properties and supplied nonempty citation IDs. Slice descriptions
  must be empty.
- Outcome alone has a slice branch requiring the same known declarations plus
  nonempty requested-part, existing-behavior and remaining-work descriptions.

The root remains an object, not a union. Citation enums live once in `$defs`
and branches use `$ref`, rather than multiplying full source catalogs. Original
context limits remain enforced; no source or ID is truncated. If either citation
catalog is empty, only unknown branches are emitted, without an empty enum or
fabricated citation.

The [OpenAI Structured Outputs guide](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses)
documents nested `anyOf`, references and string patterns, with all object fields
required and additional properties forbidden. This experiment uses the pattern
`[\s\S]` for at least one character. It does not introduce unsupported conditional
keywords or claim native whitespace/length enforcement. The existing local guards
still reject whitespace-only properties, properties over 400 characters and
reasons/slice descriptions over 800 characters. Nonempty text is not source truth.
Conformance to the documented subset and dummy encoding are not a successful
live API submission.

## Reader compatibility and mandatory local validation

The existing generic `validate_shape` understands typed objects, strings and enums,
not `anyOf`, `$ref` or `pattern`. Each facet therefore also has a typed outer
projection for that reader. Passing the generic reader is **not acceptance of
the experimental branch constraints**.

Call this module's `normalize_prediction` after receipt capture. Its narrow
`validate_prediction_shape` selects a branch, resolves flat string definitions
and checks the nonempty pattern, then delegates to the unchanged frozen normalizer.
It is not a general JSON Schema implementation. The frozen provenance, source
ownership, completeness, whitespace and length guards remain mandatory. The
eight retained accepted results still have context required. Semantic-verification
flags and selection/qualification gates remain unchanged. No executor, production
caller or paid driver
is switched to the experiment in this change.

A mocked stream control confirms that the existing reader preserves a complete
terminal event and parsed output before this final local guard. A schema-violating
empty property supplied by the mock is preserved, then rejected without repair,
salvage or retry. This tests local reader compatibility, not native model compliance.

## Offline verification and preservation

Seventeen authored controls cover valid slices, all facets' known/unknown
declarations, empty properties, closed shapes, exact citations, axis/scope/layer,
slice-only descriptions, frozen bounds and provenance, import safety, exact
Responses encoding and receipt preservation. Only authored fixtures and mocked
streams are used. Dummy providers have explicit loopback configuration, never
real credentials or ledger access. These controls do not execute acquired code.
All 297 focused triage tests and 1,277 full-suite tests pass; CLI help is unchanged.

A separately owned read-only check under
`data/missing-link-triage-declaration-schema-2026-10-05/` freezes **694 prior
artifact hashes**, all twelve table hashes and all accounting. Earlier raw cards,
terminal receipts, errors, reports and frozen executable fingerprints stay intact.
The original allowance remains **516 reservations / USD7.6143589 reserved**,
with zero new model calls or reservations.

All nine old cards are inspected without mutation. The eight accepted cards
normalize identically under the experiment; the raw mean card still fails, now
also at the experimental nonempty shape guard. Its historical error remains
unchanged. This is mechanical compatibility, not nine new observations or a
quality benchmark. Dummy encoded requests range from 24,685 to 148,178 bytes,
below the existing 180,000-byte limit; emitted schemas have 66 to 259 enum values,
below 1,000. The largest original context is retained in full.

## Next bounded decision

Review only the schema/reader contract and concrete regressions. Native schema
acceptance still needs a separately reviewed, frozen minimal protocol before any
paid call; do not rerun the nine familiar cases or silently replace their results.
First test the mechanical provider contract, not semantic improvements. Any later
quality or repository-only autonomous usefulness evaluation needs its own protocol.
Branch/delegate explanation accuracy remains a separate source-reading problem.
No parser expansion, semantic classifier, ranking, isolation or UI/key-entry change
is included here.
