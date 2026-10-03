# Contract 25: repository-only Luna test result

## Outcome

All three frozen inputs completed through the production CLI and localhost API:
**21 real calls / 21 receipts, nine autonomously retrieved discussions, and 12
stored comparisons**. No candidate errors, partial jobs, retries, manual issue/query
inputs, imported analyses, provider substitution, or acquired/generated code execution occurred.

The normalized result is **eight non-fits, three grounded partial contributions,
one similarity-only comparison, and zero eligible leads**. The four model-proposed
partials must not be confused with the three retained partials: D3 grouping lost
its proposed support because its citations crossed operation boundaries.

This establishes autonomous retrieval, several correct rejections and limited
source-backed primitives, **not an adoptable integration, verified novelty or an
accuracy improvement over different earlier cohorts**. No bridge was executed.
The paid/API/export checks passed; the browser did not confirm the new results,
so the complete UI flow is **not** an unconditional clean pass.

## Frozen procedure and accounting

The [protocol](missing-link-contract25-three-repo-protocol-2026-10-03.md) was pushed
in `9a01d5b` before generation. Executable code stayed at merged
`123fe347d2436e4a448fdb7e4144148fec70ecd2`, contract 25. The source baseline had
951 passing local tests and four successful Ubuntu/Windows CI jobs; this
documentation-only experiment did not change production code or rerun that suite.
Seven owned offline harness checks passed before baseline registration.

OpenAI `gpt-6-luna`, Responses/streaming/JSON schema, medium reasoning, eight
calls/job, USD 2/job, 180,000 prompt bytes, 12,000 output tokens and the original
USD 10 cumulative allowance remained unchanged. Each repository-only job used
three maximum candidates and 80 maximum GitHub requests. The rejected unpaid
source-freshness preparation is preserved; no failed live input was replaced.

| Source | Calls / receipts | GitHub requests | Conservative USD reservation | Reported-token estimate, USD |
| --- | ---: | ---: | ---: | ---: |
| `jaraco/path` | 7 / 7 | 54 | 0.1240982 | 0.0325612 |
| `pallets/itsdangerous` | 7 / 7 | 57 | 0.1197059 | 0.0313899 |
| `d3/d3-array` | 7 / 7 | 57 | 0.1216642 | 0.0322644 |
| Total | 21 / 21 | 168 | **0.3654683** | **0.0962155** |

The segment is below its USD 0.60 reservation cap. Original allowance
`missing-link-verification-2026-09-30` is now **461 reservations / USD 7.2123066**,
leaving **USD 2.7876934** unreserved. Unknown earlier attempts stay charged; there
is no refund/reset. Reservations and token estimates at the unchanged configured
rates are **not the provider invoice**. Attempt IDs, ordered reservation rows,
cost formulas and all 21 retained outputs reconcile. Maximum wire sizes were
170,595 / 174,990 / 176,850 bytes, below the unchanged bound.

Pinned source revisions and jobs:

- Path: `67319bba24b0986abcf6c5a749a1b8ab6359bb22`, job `204b0927ed064962ad60adc02141c7fc`.
- ItsDangerous: `672971d66a2ef9f85151e53283113f33d642dabd`, job `be788aea813e4b8a99c840bbcb54b10e`.
- D3-array: `be0ae0d2b36ab91b833294ad2cfc5d5905acbd0f`, job `417f802199a64c7584dda29aeb2cc63a`.

## What is actually grounded

For [zedBSD #2](https://github.com/awemorris/zedBSD/issues/2), Path's
`Traversal.__call__` yields items from a supplied generator and sends back a
predicate callback (acquired lines 140–151). This can be a traversal design
primitive, but it does not walk the filesystem itself, implement POSIX `find`,
address the wider compliance workstream or establish a zedBSD integration. The
toy generator example tests its own fixture contract, not the target request.

For [mcp-skill-hub #163](https://github.com/ccancellieri/mcp-skill-hub/issues/163),
ItsDangerous's `URLSafeSerializerMixin.dump_payload` conditionally zlib-compresses
serialized bytes, base64-encodes them and marks compressed output (lines 55–69).
The two retained partial checks describe **one** candidate transport primitive,
not two independent discoveries. They do not establish model comprehension,
full-request token savings, native measurements or the requested research
harness. The synthetic round-trip example does not even require the compression
branch to fire; it is not evidence for the study's desired outcome.

For [Timeline #440](https://github.com/xtreemze/timeline/issues/440), D3's `mean`
computes the arithmetic-average component of a requested profiling suite
(lines 1–19). Other metrics, data policies, ingestion, canonical data-model
integration and the graph/renderer roadmap remain new work. A `[2, 4, 6]` fixture
does not demonstrate meaningful adoption utility or roadmap completion.

These three primitives cover three discussions. All remain undetermined partial
checks and ineligible for follow-up. Grounding is not a utility score, and a
generated example is not an observed execution.

## Correct rejections and a citation failure

- Path's modification-time copy wrapper is not the failure-safe atomic
  publication requested in [Hermes #123354](https://github.com/NousResearch/hermes-agent/issues/123354).
  Its filename glob matcher is not Caro's Rust grep-command generator
  ([#961](https://github.com/wildcard/caro/issues/961)).
- ItsDangerous's scalar bytes normalizer and serializer-output type guard do not
  detect mixed NumPy array inputs ([#32765](https://github.com/numpy/numpy/issues/32765)).
  Locally timestamped signing and generic signature comparison do not implement
  independent release-tag timestamp anchoring
  ([#10](https://github.com/thecolab-ai/nz-election-evidence/issues/10)).
- D3's ordered-array insertion-point bisector is not hosted-help text search,
  URL resolution or CI link checking ([JLS #795](https://github.com/anadon/JLS/issues/795)).
  `groupSort` is not a TypeScript key-tree generator
  ([SvelteKit i18n #299](https://github.com/sveltekit-i18n/lib/issues/299)).

For that last issue, the model's separate `group` proposal cites `src/group.js`
lines 1–60 and 61–65: the export wrapper, siblings and recursive helper together.
The selected operation is only **lines 4–6**. Both proposed partial checks are
correctly downgraded to `not_demonstrated` with `selected_operation_body_missing`;
the discovery assessment is `similarity_only`, not a fourth grounded partial.

A pure retained-input fixture confirms that the precise 4–6 span was available
in the actual supplied context and passes the named-function ownership gate.
It establishes the wrapper's **delegation**, not the whole recursive helper's
behavior or target integration. The broad citation fails. This is a model
citation-precision failure, not proof of a missing JS named-function parser.
No stored comparison was upgraded, rewritten or paid-retried.

## Retrieval and context limits

Sanitized unchanged-selector pools contain 78 / 120 / 79 distinct hints; all
selected candidates equal their persisted checkpoints. These are lexical search
hints, not measured relevance labels or a recall denominator. The examples show
out-of-domain retrieval and broad program/roadmap requests. No ranking change or
unselected-candidate utility assessment was made during the frozen segment.

Source acquisition was 16/16 eligible files for Path, 23/33 for ItsDangerous and
24/132 for D3. Each enrichment call was offered 30 capability IDs and interpreted
eight; 70 / 50 / 18 IDs were omitted from that enrichment context. Path reached
the 100-capability scanner bound. Python AST coverage and partial JS scanning
are not equivalent, and eligible-file coverage is not whole-repository coverage.

Eight of nine independently interpreted discussions remain context-incomplete,
including missing cross-referenced issues or shortened demand spans. Caro's
discussion is marked complete but still has unresolved acceptance details.
Timeline explicitly reports requirements omitted by the 30-requirement bound.
No completed job status certifies complete demand, later resolution, novelty or
adoption. These limits independently preclude strong positive conclusions.

## Exports, history and operational qualification

All **12** CLI JSON handoffs equal fresh HTTP exports from their pinned snapshots.
All 12 HTTP ZIPs equal deterministic pinned packages and verify manifest, fragment
and whole-document hashes/sizes. Five use lossless multipart indexes (two or three
parts); seven are inline. Reconstructed handoffs span 72,981–315,694 bytes, with
a largest individual file of 128,000 bytes and largest uncompressed package of
332,078 bytes, inside the existing bounds. Every package remains not executed.

The identified temporary loopback server was replaced with the normal production
handler on the same frozen code, without the selection observer, analytics
scheduler or automatic job resumption. **All 12 JSON/ZIP comparisons also pass
after that restart.** Safe identity observations are retained before verification
assertions. They establish healthy checks in this new segment, not the cause or
retroactive repair of the previous contract-24 transient identity failure.

All **84 prior jobs, 294 prior matches, 272 prior snapshots, 440 prior reservation
rows and 157 protected JSON artifacts** remain byte/value-identical. Startup,
read-only exports and the normal restart preserve all 12 table hashes. The old
Freezegun/Babel jobs remain paused; no new investigation is active.

Browser/verification skill checks loaded Missing Link and Overview without initial
page errors. However, selecting D3 still showed the old job list and zero results;
one Refresh results click had a pending fetch. The wait for the new four results
returned a Windows socket read timeout (`10060`) from the browser tool. The failed
wait was not rerun and no production fix was made. **Rendering the new cohort in
the UI is unconfirmed**; this observation alone does not establish a frontend,
server or browser-transport root cause. Screenshots and failure evidence remain
private, not README assets.

## Next decision

Prioritize a bounded no-spend citation-precision regression using the retained
`group` case, plus a separate read-only diagnosis of the browser refresh boundary.
Do not expand the universal parser or relax operation ownership. Then evaluate
retrieval utility and demand granularity under a separately stated contract;
simple primitives and large roadmaps are not yet valuable adoptable connections.

No further paid test is automatic. Keep the original allowance, unknown attempts,
and this completed segment immutable. An eligible grounded lead is still needed
before isolated connection execution; UI/key-entry features remain deferred.
