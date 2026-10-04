# Offline property comparison and abstention controls

Sixteen authored tests define a bounded comparison contract after the
[explicit-scope Luna result](missing-link-triage-explicit-result-2026-10-04.md).
A requested property can be contrasted with a candidate's visible property without
first proving that the candidate implements the request. That permission must not
turn missing evidence, adoption work or broad product differences into positive
incompatibility claims.

This phase adds **tests and documentation only**. The frozen prompt, schema,
normalizers, source catalogs, provider configuration and production behavior stay
unchanged. No model is queried or key loaded, no source is acquired or executed,
no historical result is rewritten and no new reservation is made. These controls
do not yet fix Luna's excessive abstention or establish its cause.

## What the new tests establish

`tests/test_missing_link_triage_properties.py` constructs synthetic source/body
fixtures, explicit-scope cards and separately supplied reviewer bases. The tests
exercise the actual unchanged normalizer and review audit, not mocked assertions
about what a live model would choose. Source code in fixtures is text, never executed.

| Comparison control | Permitted narrow assertion | Limit that stays explicit |
| --- | --- | --- |
| Text-result requirement versus a boolean predicate | Direct result-contract difference | Does not exclude every possible use of the predicate elsewhere. |
| Mixed-collection requirement versus an annotated scalar interface | Declared input-contract contrast | An annotation alone cannot prove runtime rejection; the example returns non-string inputs unchanged. |
| Requested averaging versus a body that directly returns false | Visible behavioral contrast | This is outcome evidence, not a runtime-environment judgment. |
| Numeric result requirement versus a factory returning methods | Difference at the selected entrypoint | Returned-method results must not be substituted for the factory result. |
| Numeric returned-method result requirement versus a boolean method | Difference at the explicit returned-method layer | A correct layer declaration still requires independently reviewed body support. |
| Numeric output requirement versus a constant numeric result | Output-property alignment | Returning a number does not prove averaging or justify a slice. |
| Explicit average in broader profiling versus visible sum/count | Bounded requested-suboperation slice | Numeric edge cases, other statistics, adoption and eligibility remain untested. |

Incomplete acquisition leaves the whole card `context_required`; it does not erase
an independently supported local property contrast. The normalizer neither requires
nor accepts a model-written `implementation_verified` field. Raw cards and original
source/context inputs are preserved, and semantic-verification flags remain false.

For paired controls, both the authored contrast and an authored all-unknown response
pass the mechanical contract. The unknown card is not repaired to the reviewer label,
scored as incorrect or credited as a correct rejection. The existing audit can report
`semantic_consistent_with_review=true` for both: that means no inconsistent known
claim was flagged, **not that abstention is useful, correct or complete**.

Negative controls preserve the other side of the boundary. Unseen delegates and
generic parameters cannot prove an excluded input/output shape; absent wiring alone
cannot establish a difference. A product report is not a primitive's output. A false
`requested_operation` label or a valid ID selecting an irrelevant chunk can still
pass mechanical validation, then be flagged by an explicitly supplied independent
review. Declared project scope fails locally. These checks are not an automatic
semantic classifier, forced-rejection policy or implementation/adoption gate.

Reviewer bases are authored fixture annotations, not truth inferred from the
normalizer, model reason or passing test. The tests establish software acceptance
and preservation behavior; they do not measure whether the frozen prompt produces
the bounded contrast, or whether a reviewer label is generally accurate.

## Retained response replay and preservation

The private replay first reproduces all nine original normalizations and raw receipt
outputs exactly. It then applies the retained independent review to the same three
known facets: two factory-interface differences and the average slice. It retains
all **33 unknown facets**, including the prior reviewer commentary about lost narrow
contrasts in cases 2, 4 and 8. Commentary is not converted into predicted relations,
new error labels, automatic scores or gold targets. The mean slice stays intact;
every raw card keeps its original verification flags and `context_required` state.

Read-only baseline/final checks preserve **all 12 table hashes**, every
allowance/reservation row, the nine original inputs and **502 prior artifact hashes**.
Those artifacts include the earlier 474 plus all 28 files from the completed
explicit-scope execution, including raw receipts and its independent review.
The original allowance stays **489 reservations / USD7.4039320**; combined triage
reservations stay **USD0.1916254**. No paid request, new reservation, active job,
provider lookup, production import or history repair occurs. Earlier failed native
usage remains unknown, without refund or budget reset.

Private evidence lives under `data/missing-link-triage-property-controls-2026-10-04/`:

- `replay.py`: SHA256 `7e7abdf52aa95920634e6ec447d98067a5e6904cfc6d89ad0e119e96b5206442`.
- `reviewed-replay.json`: SHA256 `ff7044eecf4181b46838b339c4c0cbc8131202d0f1b1ba56524f15ef9f13668e`.

All **122 focused triage tests**, including the 16 new controls, and the full
**1,102-test suite** pass on the final test revision. The post-test integrity check
again verifies all 12 table hashes, accounting rows and 502 protected artifacts
unchanged, along with the frozen prompt/schema/normalizer fingerprints.

## Next bounded revision

The unchanged validator already permits these narrow contrasts. The next task is
to clarify the experimental prompt's intended comparison scope, not to weaken
provenance, require proof of an implementation relationship or force all unknowns
to a relation. Review any revised wording against both direct contrasts and genuine
evidence gaps, retaining operation layers, relevant citations and the narrow mean.

Keep the frozen helper and prior artifacts immutable; prepare any new prompt as a
separate revision. Do not claim that these tests reduce the observed 33 abstentions.
Before another paid test, freeze a new protocol and explicitly authorize its spending
segment inside the original cumulative allowance. The existing combined test cap
has only USD0.0083746 remaining and is not reset by this no-spend work. Production,
ranking, isolation, UI and key-entry work remain deferred.

The preceding result report is in PR62; these controls are a separate stacked
change so their diff does not obscure or duplicate that report. No merge is inferred
from its green CI.
