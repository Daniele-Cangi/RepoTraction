# Luna span context comparison protocol

This protocol prepares an experimental revision of demand-to-mechanism triage
after the [offline evidence regressions](missing-link-triage-evidence-regressions-2026-10-04.md).
It is a preparation-only phase: **no paid requests have run**, and production
prompts, provider settings, discovery, selection and qualification are unchanged.
Review the isolated prompt/context helper before executing the bounded comparison.

## Changed prompt and citation task

`scripts/missing_link_triage_prompt.py` replaces freely rewritten demand quotations
with scoped identifiers for original text spans. Each body/comment is split into
contiguous 500-character chunks in original source/offset order. All original
characters, including whitespace and empty sources, are preserved; no ranking,
labeling, omission or relevance filtering chooses the spans. The operation
catalog remains the existing selected-body evidence.

For known relations the model selects one demand span ID and one operation ID;
unknown requires empty references. The strict schema restricts both identifiers
to the supplied catalog. Resolution reconstructs original character offsets and
checks the original text, selected-body spans and unchanged acquisition state.
Repeated text has distinct offset-based IDs, rather than ambiguous free quotations.
Each catalog is bounded at 220 spans and schema construction checks the total
enum-value limit described in [OpenAI Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs).
Overflow fails locally without truncating evidence or reserving money.

This changes the citation task: correct IDs eliminate paraphrase spelling, not
semantic errors. A selected 500-character chunk can be overly broad, irrelevant
or chosen from the wrong comment. Assess those errors independently. Do not
describe a lower mechanical citation-failure count as improved model accuracy.
Chunks may cut across clauses; full context is retained, but a one-span citation
cannot express every cross-boundary relationship. Preserve this limitation.

The revised prompt distinguishes requested runtime/input/output properties from
missing integration, broad project scope and remaining adoption work. An outcome
slice must identify an explicitly requested suboperation directly implemented
by the selected body, with `requested_part`, `existing_behavior` and `remaining_work`.
Non-slice relations require empty description fields. Descriptions are bounded
model assertions, **not independent semantic verification or new eligibility gates**.
No target-specific examples, previous verdicts or human reference labels enter
the outbound prompt/context. Its wording is nevertheless informed by previous
errors, so this is a retrospective development comparison, not held-out testing.

## Frozen comparison and acceptance

Use the same nine source-operation/discussion pairs in the same order as the
[completed retry](missing-link-luna-triage-retry-result-2026-10-04.md). Preserve
repository revisions, discussion fingerprints, original full bodies/comments and
the operation ownership guard. Compare with the retained original responses,
never by editing or replacing them. No new issue acquisition or code execution.

Record all raw model relations, descriptions, exact-ID validation and independent
semantic reading separately. For every known relation, inspect whether the
selected demand chunk and operation actually support that specific facet.
Unknown is abstention, not agreement, incompatibility or success by default.
Keep all failed cases, missing receipts and unexpected outcomes in the report.

The following controls are declared before any response:

- Local time/signature alone must not gain slice credit for independently
  controlled external anchoring. Sorted-array positions must not gain slice
  credit for help search based only on hypothetical data representation.
- Explicitly requested average profiling should retain a defensible narrow
  mean primitive where the original source supports it; rejecting all slices
  is not evidence of improvement. Compression and traversal primitives need
  equally bounded descriptions and remaining work, not whole-request claims.
- A forwarding wrapper cannot prove unseen helper behavior. Main-only CI versus
  a Python method is not by itself a demonstrated runtime incompatibility.
- Context coverage cannot make missing acquisition, acceptance details or
  adoption constraints complete. The comparison cannot qualify a new lead.

These are human assessment controls, withheld from the model as case labels.
Do not turn retrospective label agreement into accuracy, infer ranking gains,
or promote the helper to production from a single nine-case comparison.

## Provider and cumulative spending

Retain configured `gpt-6-luna`, Responses, streaming, strict schema, medium
reasoning and the experimental 6,000-token output bound. Keep endpoint, prices,
credentials, identity guards and the provider's 240-second stream deadline
unchanged. Require fresh account verification before each actual request and
bounded successful-check reuse during streaming. One call per case, nine maximum,
no automatic retry, substitution, resumption or refund of unknown failed usage.

The starting original allowance is **471 reservations / USD7.2717195**. Earlier
test reservations total USD0.0594129, including the failed request. The same
combined USD0.20 test cap therefore leaves **USD0.1405871**. Keep the atomic
ceiling at **USD7.4123066**, inside the original USD10 allowance; do not reset it
to the new baseline plus USD0.20.

The nine actual serialized requests total **357,578 bytes**, individually
9,806–145,458 bytes, all within 180,000 bytes. Their conservative future reservation
is **USD0.0646010**; together with prior attempts it would be **USD0.1240139**.
These are preflight upper bounds, not usage or invoice estimates. No reservation
was made in this preparation phase. Earlier failed native usage remains unknown.

## Frozen request fingerprints

Prompt SHA256: `49803933da54ac0273edbe4b060abdc5c65158af1d9ec1c8db554eab3c4a7219`.
Helper SHA256 with canonical LF: `642699c0b84cfce1b78be13ee7efdcfcf1f636a1694338b81e7012d0d59d37d5`.
Private preparer SHA256 with canonical LF: `b6f860733e7ef0cabf6051321e8b674f48edee4296755f70259a100102fd71c7`.
Canonical LF avoids treating Git's Windows line-ending conversion as a code change.
Serialized request hashes still refer to exact outbound payloads.

| Case | Span count | Bytes | Request SHA256 |
| --- | ---: | ---: | --- |
| 1 | 9 | 13105 | `4eacbb647d9275bec69230d1ad9583071c339f7460ac0503987ae736de0281a7` |
| 2 | 14 | 15947 | `cab949c9c9fa0655e7339adfe4ab41d3cab1a7ff73039b56fdff8af9284142e6` |
| 3 | 198 | 145458 | `4f53171a9f061589f824cce075bc187b4595b2558e0ab8dc87c2d4c0ea8b2d58` |
| 4 | 5 | 9806 | `9cd91b6b664500fd785e40b61ff52753a51686e645012b534624d98178a215e7` |
| 5 | 49 | 39531 | `307e007c9f2d2c8a6cdefcdf4cc1ce392faf917150acc7a55e75af4cc020497b` |
| 6 | 7 | 11492 | `593f97f2869b77269b6eea73d799e0476cf5257cee7508f1c06da788a44e26b8` |
| 7 | 9 | 12566 | `731cf29289be8d02b763a636ed5e0df393fff149bf18557526bd8b0c4edd7624` |
| 8 | 118 | 89387 | `d656ae9f3c6b67efb210f13707a3e1dde82d873a42dda9e19fa306fd52d95755` |
| 9 | 19 | 20286 | `64029d8223f74fff5681a1f890ddb321b089c3784fe32415b548b65bdfba6124` |

Per-case schema fingerprints and original inputs are retained privately. Local
preparation verifies complete text reconstruction, selected-operation ownership,
all nine unknown fixture normalizations and exact payload packing. Twenty new
synthetic tests cover catalogs, scoped schemas, invalid identifiers, descriptions,
completeness, non-mutation and a simulated `Provider.complete` receipt.
Sixty-one focused triage tests pass without network requests or paid calls.
The full local suite passes **1,041 tests**. A second read-only preflight confirms
all nine packed request hashes, source inputs and complete history unchanged.
All **12 table hashes**, reservation/allowance rows and **430 prior artifacts**
remain unchanged during preparation.

## Execution prerequisite

After reviewing this helper, freeze a one-shot driver under the existing worker
lease and verify that all nine payload hashes still match before any paid call.
The preparer intentionally has no paid execution entry point. The driver must
preserve old artifacts and non-accounting tables, append only this segment's
allowance reservations and private receipts, and recheck integrity after release.
Stop for identity, allowance, transport, incomplete/refused response or wire-schema
failure; retain typed diagnostics and unknown usage without retrying. Preserve
completed reference/description-invalid cards as failures, then continue once to
the next case. Publish execution receipts and semantic conclusions separately
from this pre-response protocol.
