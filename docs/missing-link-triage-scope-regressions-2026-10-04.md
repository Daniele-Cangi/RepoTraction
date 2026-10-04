# Offline triage scope regressions

This phase records the semantic and interface errors found in the
[completed Luna span comparison](missing-link-triage-span-result-2026-10-04.md)
as **no-spend, independently annotated controls**. Twenty-two new synthetic tests
pass, together with all 83 focused triage tests. A read-only replay preserves the
nine real responses and all 463 earlier artifacts. No model request, reservation,
production change or historical correction is made.

These tests do not teach or retest Luna. They verify how the experimental audit
reports a human review of a supplied prediction. Passing them does not establish
automatic semantic detection, relevance, model accuracy or an eligible lead.

## Independent review categories

The existing pure helper `scripts/missing_link_triage_evidence.py` adds five
review bases without changing its input shape or the existing relation checks.
Every base requires the same bounded independent reason. Exact original spans
must still pass validation before a review can be reported.

| Reviewer supplied basis | Reported issue | What the reviewer must inspect |
| --- | --- | --- |
| `facet_mismatch` | `reviewed_property_is_not_requested_facet` | Whether the cited property answers the facet, such as execution environment rather than computation. |
| `broader_scope` | `project_scope_is_not_suboperation_contract` | Whether inputs/outputs of a requested suboperation are being compared with whole-project deliverables. |
| `unseen_delegate` | `delegate_contract_not_established` | Whether the claimed input or output contract requires an uninspected helper. |
| `irrelevant_citation` | `citation_does_not_support_claim` | Whether the exact selected passage, not merely some other part of the full body, supports the claim. |
| `unresolved_interface_layer` | `interface_layer_not_established` | Whether the factory entrypoint, returned callable or returned method is actually the interface being compared. |

The helper does not infer these bases from code, keywords, language names, model
reasons or quotation validity. The reviewer can still be wrong. Interface-layer
issues can require a qualification rather than prove a false relation. The
existing `semantic_consistent_with_review` field means consistency with supplied
annotations only; it is not independent proof, a model-quality score or a gate.

Unknown predictions remain abstentions even when a reviewer supplies a negative
basis. Their lack of a reported disagreement is not counted as correctness,
agreement or rejection. Original `aligned`, `different` and `slice` relations,
unknown facets and partial hints are preserved; no card is silently repaired.

## Paired controls

The new public fixtures are authored examples, not historical cases relabeled
as held-out model outputs. Positive and negative controls limit over-filtering:

- Encoding or external anchoring behavior does not answer the runtime facet.
  A positively established in-process environment distinction can still be
  reported, while a shared environment does not imply shared behavior.
- A JavaScript callable is not excluded from build-time use merely because it
  is an ordinary function. Missing build integration is not a runtime conflict.
- A factory's direct arguments/result cannot silently be replaced by those of
  the callable or methods it returns. Explicitly selecting the returned-callable
  layer can support alignment, and a directly shown factory output can support
  a genuine difference.
- File-ingest formats versus a mean's values, or study reports versus a codec's
  bytes, do not establish the suboperation's contract. Explicit numeric values
  or serialized-byte suboperation requirements can support narrow alignment.
- Generic `values` arguments and an unseen delegate do not establish exclusion
  of schema keys or a positively different result shape. A directly shown
  output can support a difference.
- A scoped ID can select a genuine original passage that lacks the claimed
  property. The paired fixture passes the same mechanical normalizer with an
  irrelevant chunk and with a relevant chunk; only independent review supplies
  the relevance distinction. A separately supported average slice remains intact.

Additional checks preserve inputs, reject invalid original spans, retain unknown
abstentions for every new basis and prevent the model's reason from choosing its
own independent review. No code from acquired repositories is executed.

## Retained response replay

The owned private replay applies the previous post-response human review to all
22 known facets in the nine frozen responses. It first reproduces each original
normalization exactly, then maps the retained review categories explicitly to
audit bases. No new label is inferred from wording or written back into the
model response or application database.

The replay reports **14 review items**: four facet mismatches, three broader-scope
comparisons, two unseen-delegate claims, one irrelevant citation, three unresolved
interface layers and one missing-integration contrast. These include qualification
requests: **14 is not an incorrect-prediction count or an error rate**. The retained
independent review also supports eight narrow known facets. No accuracy percentage
is computed, and unknown facets are not credited as correct negatives.

The original case-9 mean retains its partial hint while its input/output review
items remain visible. In particular, the wrong output chunk is reported separately
from the explicitly requested average. The outcome relation, raw descriptions,
receipt, source inputs and original `context_required` state remain unchanged.

The private replay and evidence are retained under
`data/missing-link-triage-scope-regressions-2026-10-04/`:

- `replay.py`: SHA256 `8f7797edcd78e58cb7796a8b8245a59fbb0121403593dc7b1f29a5817a11b0df`.
- `reviewed-replay.json`: SHA256 `a64b6588c76f1709c8ff5024c3891f398612032e518554b3b3b5c385f7897571`.

The replay verifies **all 12 table hashes**, every reservation/allowance row,
the original nine inputs and **463 prior artifact hashes** unchanged. These
include the 435 artifacts previously protected plus 28 files from the completed
span execution, including its raw responses and independent review. No active
job is introduced. The original allowance remains **480 reservations /
USD7.3363205**; combined triage reservations remain **USD0.1240139**. Earlier
failed native usage is still unknown; no refund or new budget reset occurs.

The complete local suite passes **1,063 tests**, including the 22 new controls.
Production does not import this experimental audit helper; the span prompt,
provider schema, source catalog and actual application behavior remain unchanged.

## Next experimental revision

After reviewing these controls, define any new experimental prompt/context or
schema revision against execution environment, explicit interface layer and
requested suboperation scope. Citation provenance and citation support remain
separate questions; another model assertion cannot certify relevance.

Freeze a new pre-response comparison protocol before paid calls, retaining the
same cumulative caps, all previous failures and independent semantic assessment.
Do not hard-code these nine outcomes or treat synthetic audit agreement as model
improvement. Production discovery/selection, UI and key-entry work remain deferred
until an independently grounded eligible lead exists.
