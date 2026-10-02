# Contract-21 VPN-off retry — 2 October 2026

## Explicit amendment before the new paid attempt

After the [first stopped contract-21 attempt](missing-link-live-discovery-contract21-2026-10-02.md),
the user reported disabling the VPN and explicitly requested another test **before
implementing fixes**. This authorizes one fresh repository-only Discover job for
`more-itertools/more-itertools`, not an automatic retry, resume, allowance reset
or removal of the failed job from the report. The VPN hypothesis is plausible but
unconfirmed; neither local connectivity nor a successful retry proves its cause.

Freeze production code at merged `77bcea37887c7c1cc6082c7d61ff2243c603cce2`,
analysis contract 21. Reuse the unmodified HTTP investigation driver, provider,
payload packing, timeouts and selection. Keep Luna, Responses/strict JSON schema,
streaming/medium reasoning, 180,000 prompt bytes, 12,000 output tokens,
three candidates, 80 GitHub requests, eight AI calls and USD 2 per job.
No issue, query, analysis import, host execution or public outreach is supplied.

The original cumulative USD 10 allowance starts this retry at **303 reservations /
USD 4.6946065**, including the unknown first outcome. At most eight new calls
reserve USD 0.1936384 at the fixed configured limits, for a cumulative maximum
USD 4.8882449. These are conservative reservations, not billed usage. Retain any
unknown or invalid outcome without assuming a refund.

Before paid execution, check the local state, active GitHub account and public
repository metadata, plus an authenticated **read-only model metadata GET** to
OpenAI. That connectivity check does not generate a response or consume an
analysis reservation. Verify no active job and unchanged code/settings; preserve
hashes of previous jobs/matches/snapshots/reports and all prior reservation rows.
Never log the key or raw provider error body. Preserve new observations in the
separate ignored `data/luna-discovery-contract21-2026-10-02/vpn-off-retry-01/`.

Only this one job is launched in the connectivity gate. On success, inspect its
actual source-backed answers and receipts before deciding how to continue the
12 unstarted repositories. On another driver/provider/account/budget failure,
stop, locate the known backend job, and observe its terminal state without
starting a replacement. Do not implement fixes or silently increase timeouts
during this retry. A successful repeated input is not new independent validation
data, causal evidence of a VPN problem or a held-out discovery.

## Results

**Completed without production changes.** The amendment was committed and pushed
as `460c4c3` before the new job. Connectivity checks passed: the local state GET
took 6.91 seconds, GitHub authentication 5.30 seconds with `Daniele-Cangi` active,
and the authenticated Luna model metadata GET 5.79 seconds. OpenAI Docs was used
to preserve the requested model and existing Responses/streaming configuration,
not to select another model or change limits. See the official
[Luna model documentation](https://developers.openai.com/api/docs/models/gpt-6-luna)
and [streaming guide](https://developers.openai.com/api/docs/guides/streaming-responses).

Job `cc37ec5069574f12aa9fb01e6fd354d9` ran from `2026-10-02T21:06:40Z` to
`2026-10-02T21:21:02Z` (14 minutes 22 seconds), using only the repository input.
It was completed through the unchanged HTTP driver, with no polling failure,
transport error, candidate validation failure, paid retry or resume inside the
job. The 12 other repositories were not started by this one-job gate.

| Measure | Result |
| --- | --- |
| Fresh retry jobs / completed / partial | 1 / 1 / 0 |
| GitHub retrieval requests / cache hits | 32 / 24 |
| AI reservations / terminal receipts / retained JSON outputs | 7 / 7 / 7 |
| Unknown response receipts in this retry | 0 |
| Actual largest serialized request | 172,204 / 180,000 bytes |
| New reserved amount | USD 0.1244633 |
| Token-based estimate from reported usage, not an invoice | USD 0.0359222 |
| Cumulative reservations / reserved amount | 310 / USD 4.8190698 |
| Remaining cumulative allowance | USD 5.1809302 |
| Automatically selected issues / stored evaluations | 3 / 4 |
| Follow-up-eligible matches / isolated examples | 0 / 0 |

All seven responses have completed receipts, usage and retained JSON. The phases
were one capabilities enrichment followed by three independent request
extractions and three comparisons. Interpreted request sizes were 10, 30 and 22
requirements; no final transport exceeded the byte bound, and each comparison
included implementation context. The two larger discussions remain explicitly
incomplete rather than being certified as exhaustive.

### What the answers actually demonstrate

The acquired source revision remained
`1ea82a711c69f590054987b5cb194157f8ce8ac4`. Discover selected the following issues;
none was supplied as an input to the job:

| Selected request and candidate | Audited result |
| --- | --- |
| [ml-pipes #42](https://github.com/trained-by-humans/ml-pipes/issues/42), `chunked` | A useful source-backed core operation: iterable input, bounded groups and iterable-of-lists output are supported. The target `Chunk` operator, boundary validation, integration docs and target tests remain undetermined. |
| [pyplantuml-bundled #1](https://github.com/HansBug/pyplantuml-bundled/issues/1), `with_iter` | Resource-lifecycle similarity is not credited as rendering, subprocess/JVM management or the requested API. No supported/partial requirement and no eligible lead. |
| [pruebas #44](https://github.com/GPTFY-biz/pruebas/issues/44), `strictly_n` | One narrowly useful partial: count exactly 29 items **after full consumption**. It does not validate document identities/upload status, enforce public-project finalization or implement the platform. |
| The same `pruebas` request, `roundrobin` | A deceptive crew-allocation resemblance is explicitly identified as `similarity_only`. Interleaving inputs does not implement one work order per available crew or geographic planning; no contribution is credited. |

These conclusions were checked against the acquired implementation, request
requirements and normalized stored checks, not just the model summaries. The
`strictly_n` partial cites its own implementation path and remains undetermined,
with remaining integration work explicit. No existing invalid-option guard was
credited as invalid-size handling.

One model partial review for the target `Chunk` API included the helper `take`
in another file, as well as the selected `chunked` implementation. The existing
contract-21 anchor/ownership gate downgraded that particular partial claim to
`not_demonstrated`; the independently supported core-operation checks remain.
This is a visible model attribution limitation caught by the current validator,
not a reason to expand ownership to arbitrary repository files during this test.

The PlantUML request's Python 3.6 rule was extracted. Its comparison omitted the
candidate packaging manifest from the bounded context and kept runtime
compatibility undetermined. The acquired manifest elsewhere states Python >=3.10;
do not turn the model's lack-of-conflict statement into package-installation
compatibility or assume that an extracted primitive has the same deployment
contract. This sample did not establish complete runtime or dependency closure.

The false positives are **not promoted as leads**, but their technical
classification remains `investigate`, not a proved `incompatible`/`reject`.
Likewise a useful operation or partial contribution is not an eligible complete
connection: all four evaluations have `eligible_for_followup=false`. No isolated
execution or outreach was forced to make a successful test look like adoption.

### Integrity and interpretation

Read-only reconciliation passed: previous jobs, matches, pinned match snapshots,
report artifacts and reservation rows—including the first failed contract-21
job—are unchanged. All four API exports agree with their stored handoff projection;
the known successful driver report and separate terminal observation are retained
locally. There are no active jobs, imports, host executions or allowance resets.

The completed retry shows that this configuration can traverse the real provider
and Discover workflow after the reported VPN change. It does **not** establish
that the VPN caused the first failure: network conditions, cached acquisitions
and stochastic answers can differ. The first unknown reservation remains counted.
Across contract-21 attempts so far, one source has two jobs (one failed, one
completed); the remaining 12 prescribed sources are still unstarted. Do not
report this as a completed 13-repository cohort or independent novel discovery.

The planned diagnostic/polling fixes were not implemented, as requested. Continue
the unstarted inputs under the frozen settings next; preserve failures and stop
on another non-completed paid/transport/account/budget job. This successful job
finished only 38 seconds inside the existing 15-minute driver deadline, an
operational limitation to keep visible rather than silently changing mid-test.
