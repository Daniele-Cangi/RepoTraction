# Luna explicit-scope comparison protocol

This is an isolated, **preparation-only** revision after the merged
[scope regressions](missing-link-triage-scope-regressions-2026-10-04.md).
No paid request has run in this phase. Production prompts, provider configuration,
source acquisition, ranking, qualification, HTTP contracts and UI are unchanged.
Base commit: `49a8d59c41846cce5a126ea0093891b8d3db8c47` (PR60, green CI;
Copilot reported no findings on its reviewed head).

The next experiment asks whether explicit comparison properties and interface
layers reduce the overclaims observed in the
[retained span responses](missing-link-triage-span-result-2026-10-04.md).
That question remains unanswered until new responses are independently assessed.
The synthetic controls below test software contracts, not Luna's reasoning.

## Changed task, unchanged evidence

`scripts/missing_link_triage_explicit_scope.py` adds a separate prompt/schema and
normalizer. It reuses the frozen span helper without editing it. Every original
body/comment, revision, discussion fingerprint, selected entrypoint, operation
span, 500-character demand chunk and offset-based ID stays unchanged. No summary,
relevance filtering, new acquisition, target-specific example or historical label
is added to the outbound context. All original characters remain available;
character coverage still does not establish complete requirements.

Each facet now has five required comparison declarations:

| Field | Contract | What it does not prove |
| --- | --- | --- |
| `axis` | Fixed question: runtime/environment, input/values, output/values or outcome/behavior | That the model actually compared that property |
| `comparison_scope` | Known relations require `requested_operation`; unknown requires empty | That a product-level claim has not been mislabeled |
| `operation_layer` | Known relations name `selected_entrypoint`, `returned_callable` or `returned_method`; unknown requires empty | That the named layer exists or its implementation is visible |
| `demand_property` | Concrete model-written property, nonempty and at most 400 characters for known relations; empty for unknown | That the selected demand chunk supports it |
| `operation_property` | Concrete model-written property with the same bounds | That the selected body proves it without unseen helpers |

The schema includes `project_deliverable` as a declared scope; a known claim using
it fails local normalization. It is not silently rewritten to operation scope.
The layer declaration distinguishes a factory's own arguments/result from the
arguments/result of its returned callable or methods. Runtime and outcome identify
the visible implementation layer, not proof of its execution environment. Different
facets may assess different layers only where independently justified.

Runtime asks about execution constraints, not behavioral differences, source
language alone, missing integration or an unsupported build-time assumption.
Input/output compare the same requested operation rather than whole-project ingest
or reports against a primitive. Generic parameters cannot exclude specific values;
an unseen delegate cannot establish a positively different output contract.

The prior exact-ID, original-source, selected-body span, acquisition-completeness,
reason and slice-description guards remain delegated to the unchanged helper.
Unknown requires empty declarations except its fixed axis, empty references and
empty slice descriptions. Outcome alone permits `slice`, with all three bounded
descriptions: requested part, visible behavior and remaining work. No invalid raw
response is repaired; the original projection and new declarations are retained
separately. Every result explicitly leaves comparison and slice semantics unverified.

Strict schema adherence is not semantic accuracy: OpenAI documents both schema
constraints and the possibility of incorrect values in
[Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs).
The total 1,000-enum-value bound now includes the added scope/layer/axis choices,
not just citation IDs. Overflow fails before transport, without truncating text.
The old 220-demand-span bound also remains. The largest prepared schema has 849
enum values. These are API compatibility checks, not a claim that a longer prompt
will improve Luna. The configured model remains
[gpt-6-luna](https://developers.openai.com/api/docs/models/gpt-6-luna).

## Frozen comparison and independent assessment

Use the same nine original source-operation/discussion pairs and order as the
span execution. Reconstruct inputs from retained jobs and compare them exactly
with the prior frozen inputs before packing requests. Review the helper before
freezing a new execution driver. No earlier driver or artifact is reused for a
second execution or modified to accommodate this task.

Record raw outputs, mechanical validation and independent semantic review
separately. For every known facet, examine the claimed property, declared scope
and interface layer against the actual cited demand chunk and visible operation.
A valid ID, plausible reason or correct declaration is not independent proof.
A false operation-scope label, unsupported returned-method claim or irrelevant
valid chunk can still pass normalization and must remain visible in the review.

Assessment controls are withheld as case labels from the model:

- Distinguish behavior from execution environment, and missing wiring from an
  established environment difference. Retain genuine narrow differences rather
  than forcing all runtime answers to unknown.
- Distinguish entrypoint arguments/results from a returned callable or methods;
  do not silently substitute layers. Assess same-operation input/output rather
  than ingest formats, final exports or research reports belonging to the product.
- Unseen delegates and generic parameters cannot prove exclusion. Citation support
  must come from the selected chunk, not another part of the full discussion.
- Keep local signing/external anchoring and sorted positions/help-search analogies
  from receiving unsupported slice credit. Unknown is abstention, not a correct
  negative by default.
- Preserve independently defensible narrow value, including explicitly requested
  arithmetic mean. Inspect numeric suitability, missing integration and remaining
  work separately; do not infer eligibility. Traversal and compression may remain
  unknown where policy, decoding or adoption evidence is missing. Their older
  slice labels are not compulsory ground truth.

This is a retrospective development comparison informed by prior errors, not
held-out accuracy testing. The output task has changed again: compare supported
properties and explicit gaps, not merely fewer validator failures or agreement
with old labels. All-unknown responses do not demonstrate improvement. Preserve
failures, qualifiers, abstentions and unexpected outcomes; do not alter historical
predictions, discovery selection or qualification from this experiment.

## Provider, budget and stop conditions

Keep `gpt-6-luna`, Responses, streaming, strict schema and medium reasoning;
6,000 maximum output tokens and 180,000 maximum serialized request bytes.
Keep existing credentials, endpoint, price configuration, account isolation and
240-second stream deadline. No `.env` mutation or credential publication.
Fresh account verification precedes every future request, with the existing
bounded successful-check reuse during streaming and worker lease.

The original allowance remains **480 reservations / USD7.3363205**.
Combined triage reservations remain **USD0.1240139**, including the failed call
whose native usage is unknown. The unchanged combined USD0.20 cap leaves
**USD0.0759861**, with the atomic ceiling still **USD7.4123066**, inside the
original USD10 allowance. No allowance reset, unknown-usage refund or new cap.

The nine prepared requests total **387,683 bytes**, individually
13,151–148,803 bytes. The conservative future reservation is **USD0.0676115**;
if all nine are reserved, combined triage reaches **USD0.1916254**, leaving
USD0.0083746 inside this test cap. This is a preflight reservation bound, not
native usage or an invoice. This phase creates **zero reservations and zero
paid calls**. Larger output, extra calls or retries are not implicitly authorized.

Future execution is one call per case, nine maximum, in order. No automatic retry,
resumption, substitution, supplementary acquisition or acquired-code execution.
Stop on identity/allowance/transport, refusal, incomplete response or wire-schema
failure; retain typed diagnostics and unknown usage. Preserve terminal,
locally-invalid declaration/citation/description cards as failures and continue
only once to the next case. Append only this segment's reservations and private
receipts; never import experimental verdicts into jobs. Recheck history on release.

## Request fingerprints and verification

Prompt SHA256: `d659de7d06f83cf072c67722e91dc48de4e128ee405f263ee299930599546b9b`.
New helper SHA256 (canonical LF): `649f7b8f48c64334dcb04af115900e5b7a6ec3f67cf672c9851d93aac3daa0f2`.
Private preparer SHA256 (canonical LF): `66a4cf7dfbc40700f7cc41f87adfbf81fc44ff973fcd7734560914ba7656ea3d`.
Old helper remains `642699c0b84cfce1b78be13ee7efdcfcf1f636a1694338b81e7012d0d59d37d5`.
Canonical LF permits Git's Windows line-ending conversion without a false code
change. Exact serialized payload and per-case schema fingerprints are frozen
separately. Original bodies, local receipts and accounting rows remain private.

| Case | Demand spans | Bytes | Request SHA256 |
| --- | ---: | ---: | --- |
| 1 | 9 | 16450 | `0b9d0c62c709396feecd91c5df0bd13a91aca347ee3feb063a0c5e7cd1949ba2` |
| 2 | 14 | 19292 | `749f8bb5f19b57ea2abaed1dc5515d39a8d20f8c8a53ec0b9676245c47bdde50` |
| 3 | 198 | 148803 | `7b0a27d1391c45c921da4c4f3fa0eeed64e74e76ffed17330bc5f3eeaf14d240` |
| 4 | 5 | 13151 | `4503af48f66bab7a24dfe22e6f790d9ab13fb61b2b0d8e4bf5abba6908d715a7` |
| 5 | 49 | 42876 | `533f417c800631ff38b4feda03e4d536d1466e3b67683a87c522a27648f70029` |
| 6 | 7 | 14837 | `0cfdb1af96333c88ac2d88927a9607531a3875ad5d6a5c193eb0a764cb7cf1c3` |
| 7 | 9 | 15911 | `551f81f1776eb12d6ccdec5223992edeff361013dfe0480018223d68eb495d46` |
| 8 | 118 | 92732 | `ef8e044b42742f4eee43e56f59d4128fa5a6a83b88dbba51e45d7ed9cb3c9008` |
| 9 | 19 | 23631 | `4c603904ca790d2b0783bf3dd4ad454f4f8793d93fa29fbc37faba347ce6019a` |

Preparation evidence is retained under
`data/luna-triage-explicit-context-2026-10-04/`: a preparation-only driver,
baseline, unchanged-input copy, packed-request fingerprints and integrity record.
There is no paid execution entry point. A read-only `verify` repeats input/body
ownership checks, code hashes, all nine packed hashes and budget arithmetic.

Twenty-three new authored tests cover declarations, abstention, inherited
provenance/completeness, raw preservation, the additional enum budget and the real
provider contract through a mocked stream. Negative controls deliberately show
that a fixed runtime axis, false layer or irrelevant valid citation can still pass
mechanical validation, then be flagged by an independently supplied review.
The requested mean slice survives the wrong-chunk control. No automatic semantic
classifier or model-written self-verification is introduced.

All **106 focused triage tests** and **1,086 full-suite tests** pass. A second
read-only preflight after the suite reproduces all nine request hashes and
unchanged original inputs, and verifies **12 table hashes**, every
allowance/reservation row and **468 historical artifacts** unchanged (463
previously protected artifacts plus the five scope-replay files). No active job
or paid execution is introduced. The post-test integrity snapshot is retained
separately from the preparation baseline.

## Next gate

Request a scoped review of the new helper/schema and inherited guards, not a
parser/resolver completeness expansion. After that review, freeze and publish a
fresh leased, one-shot execution addendum before any paid request, requiring
matching fingerprints and the unchanged cumulative ceiling. Publish actual
response receipts and independent semantic conclusions in a separate report.
Production promotion, new selection rules, UI/key entry and isolation remain
deferred until an independently grounded eligible lead exists.
