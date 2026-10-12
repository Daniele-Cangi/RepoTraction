# Independent blind review — frozen before candidate behavior

This is an independent **AI review, not a human oracle**. The only cohort evidence consulted was `blind-review-packet.json`, SHA-256 `605d0ae0329980628cc2c32537ce5ab09e063910b9b2d4216f1d73dd8b802cad`. All 15 retained bodies, all retained comments and timelines, interpretations and proposal decisions were reviewed. No candidate implementation, mapping, behavior result, linked page or external acquisition was consulted. Exact evidence, coverage and freeze time are in `independent-review.json`.

Four cases support a pending need in the retained discussion; one is a completed incident note without a further request; ten have uncertain residual status. These are snapshot judgments, not assertions about live repository status. All twelve abstentions from executable proposals are legitimate. Two proposed contracts support narrow suboperations, with eight new challenges frozen below. **No candidate reuse advantage is established.**

| Case | Remaining demand and interpretation | Abstention/proposal and simplest credible direct solution |
|---|---|---|
| 01 | Completed parser/query mismatch repair; no new request. `not_a_request` is appropriate. | No contract. Reinstall the matching parser and run the reported smoke test. No further reusable-component need established. |
| 02 | Real updater preflight/pin-preservation request; bot reports PR review in progress, not completion. | Membership predicate is defensible but excludes receipt selection, markers, mutation order and verification. Use the explicitly requested standard packaging dependency directly, with those caller prerequisites. |
| 03 | Real CA-trust failure; latest comment asks diagnostic topology questions, without a fix. | Abstention justified. Share working S3 client trust configuration or expose the missing CA setting; requires topology, CA and actual client wiring. |
| 04 | Two real reports: unsafe read-only evaluation and sync/pending-job mismatch. Resolution unknown. | Abstention justified. Restrict the evaluation surface and align dispatch metadata with intended behavior; requires host trust and lifecycle decisions. Removing builtins alone does not prove containment. |
| 05 | Explicit shared dispatch refactor; no visible completion. | Abstention justified. Extract local shared action policy while preserving sync/async IO; action semantics and shutdown lifecycle are prerequisites. |
| 06 | Broad typed HTTP route integration request; linked dependencies/resolution unavailable. Interpretation largely faithful; r29's selected citation only partially supports its combined statement. | Abstention justified. Extend existing router/middleware with adapters and codecs; schemas, stream/cancellation and security integration are prerequisites. A generic codec cannot establish completion. |
| 07 | Initial shape-lint proposal is challenged by measurements and an existing runtime warning; requester acknowledges the alternative. Remaining new-cop demand is unsettled. | Abstention justified. Try the cited built-in performance warning on representative workloads. Static tooling needs demonstrated additional utility and acceptable false positives. |
| 08 | Shared container recipe setup requested; baseline audit is completed work, not completed refactor. Dependencies unknown. | Abstention justified, although build/runtime context is visible. Extract a focused local build fragment; retain different launchers until behavior is agreed and tested. |
| 09 | Real shared HTTP transport request; linked resolution unknown. No cryptographic JSON canonicalization requirement follows. | Abstention justified. Use a thin injectable shared client with standard JSON serialization and centralized policy; concrete method/body/error semantics remain prerequisites. |
| 10 | Upstream adoption/integration need remains after a reported successful local fix. Interpretation misses the visible stale-RawPath/path-rewrite constraint. | Preservation contract is narrow and identity-shaped. Go context is explicit despite `runtime: unknown`; no callable binding follows. The credible direct repair is already described in the issue: wire-path conversion at a shared seam plus call-site updates. |
| 11 | Extra docstring delimiter is a real bug; later “Duplicate of Issue #10” is an unverified report, not a demonstrated fix. | Abstention justified. Fix existing docstring boundary/selection handling; requires width, selection fixtures and duplicate context. |
| 12 | Tentative proposal to consider a larger PO wrapping default, partly an upstream pointer. No decided width or exact gettext-parity mandate. | Abstention justified. Agree formatting policy, then change existing serializer configuration or upstream behavior. |
| 13 | Real project-scaffold request, explicitly blocked by #1; linked resolution unknown. Some interpretation requirements repeat the same quality-check acceptance criteria. | Abstention justified. Minimal src-layout, CLI, lock/check tooling, CI and exclusions. Tool choices/blocker resolution are prerequisites; ML vocabulary does not imply a finite ML computation. |
| 14 | Real chat trust-boundary/scope problem. Interpretation reasonably separates proposed mechanisms from acceptance criteria. | Abstention justified. Server-owned grounding/history plus explicit lab policy and deterministic refusals. Corpus, thresholds, template, storage and no-overblocking tests remain prerequisites. |
| 15 | Owner ruling supersedes initial undecided semantics; later owner update blocks enforcement/recovery/restart claims on #1146. Subsequent cross-references do not prove resolution. | Abstention justified for content decisions, though mode/copy boundaries are settled. Use existing bounded-copy/truncation seam and measured built-in profiles; enforcement additionally needs framework restart safety. No private transaction system or general policy DSL is justified. |

The practical advantage bar is improvement over these small direct solutions: lower integration/maintenance cost with the requested behavior demonstrated. Broad topical overlap, successful toy outputs or a component's existence do not meet it. For security cases, actual corpus outcomes and lifecycle/trust boundaries matter; for refactors, preserved local behavior matters.

## Frozen independent challenges

Only the two already proposed operations are reviewed; no contract is rewritten and no operation added. All eight inputs differ from original examples/checks. Expected values are conservative AI semantic inferences, not independently executed results.

`demand-5958e7a5e9f0a93f5b85` — valid active root PEP 440 constraint permits a valid final target version:

| Args | Expected |
|---|---|
| `[">=2.0,!=2.4.1,<3.0", "2.4.1"]` | `false` |
| `[">=2.4,<2.5", "2.5"]` | `false` |
| `["==2.4.*", "2.4.9"]` | `true` |
| `["==2.4.1", "2.4.1"]` | `true` |

These exercise explicit exclusion, exclusive boundary, wildcard and equality semantics. They assume root selection and active-marker evaluation have already occurred. They do not cover invalid inputs, prereleases, receipt handling or the updater's side effects. Direct standard specifier membership is the credible baseline; reuse needs a concrete benefit over that already requested dependency.

`demand-eb97596b6b64e856972c` — preserve an unchanged valid origin-form raw request target:

| Protocol | Target and expected identical string |
|---|---|
| `HTTP/1.1` | `/a%2Fb%3Fc?x=%2F&y=%3F` |
| `HTTP/2` | `/a%2fb%3fc?x=%3a&x=%3A` |
| `HTTP/1.1` | `/percent%252Fvalue?literal=%2525` |
| `HTTP/2` | `/plain/path?a=1&a=2&empty=` |

The issue's “wire bytes unchanged,” exact corrected table cells and unaffected query support preserving delimiters, escape case, encoded percent signs and duplicate/empty query values. **A literal identity function passes all four.** These cases therefore cannot prove actual recording/storage/resend, stale-RawPath handling, protocol integration or reuse advantage. The stronger direct baseline is the author's described local helper and call-site repair; claims beyond preservation require separate lifecycle evidence.

This freeze preserves uncertainty: linked discussions, candidate code, dependencies, runtime verification and exact domain policies remain unavailable. No challenge was invented for abstained operations with undefined expected outputs.
