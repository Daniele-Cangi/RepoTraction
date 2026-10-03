# Missing Link: contract-24 remaining-input Luna result

## Outcome

**All three prescribed repository-only jobs completed: 21 real calls, 21 completed
receipts, nine discovered discussions and 15 stored comparisons.** There were no
candidate acquisition/validation failures, partial jobs, paid retries, manual
issue/query inputs, imported analyses or acquired/generated code execution.

Four comparisons retain source-grounded partial primitives, seven are non-fits,
two are similarity-only and two are already-known references. Those four partials
cover only **two discussions**, not four independent opportunities. **None is
eligible for follow-up or isolated execution.** The experiment demonstrates
autonomous retrieval and bounded technical contributions, not a new adoptable
integration, verified novelty or general discovery accuracy.

The final operational confirmation after restoring the normal server did fail
at the verified-state assertion. Browser checks had passed, and a later read-only
observation recovered full state, but the failed confirmation was not rerun.
Thus the paid segment completed; the entire post-restart verification is **not**
an unconditional clean pass. See the separate operational limitation below.

## Frozen procedure and accounting

The [protocol](missing-link-contract24-remaining-protocol-2026-10-03.md) was pushed
before spending in `b1d1a0a16b51478790d703495312f75a0313e171`. Executable code
remained merged `1ea99416c01ecd4ade19203c9ce640fd3951e0ef` (PR #47), contract 24.
The merged baseline had 938 passing offline tests and four green Ubuntu/Windows
Python 3.10/3.13 CI jobs; this documentation-only experiment did not change
production code or rerun that full suite.

The actual production CLI/local HTTP job API, GitHub acquisition, configured
OpenAI `gpt-6-luna` Responses/streaming/strict schema, persistence and exports
were used. Medium reasoning, eight calls/job, USD2/job, 180,000 request bytes,
12,000 output tokens and the original USD10 cumulative allowance stayed frozen.
Three maximum candidates and 80 GitHub requests were supplied per job. No
Freezegun/Babel resume, source replacement or mid-run fix occurred.

| Source | Calls / receipts | GitHub requests | Conservative USD reservation | Reported-token estimate, USD |
| --- | ---: | ---: | ---: | ---: |
| `tox-dev/filelock` | 7 / 7 | 61 | 0.1224116 | 0.0320937 |
| `giampaolo/psutil` | 7 / 7 | 55 | 0.1175816 | 0.0310184 |
| `websockets/ws` | 7 / 7 | 57 | 0.1153705 | 0.0278321 |
| Total | 21 / 21 | 173 | **0.3553637** | **0.0909442** |

The segment remains below USD0.60. Allowance
`missing-link-verification-2026-09-30` is now **440 reservations / USD6.8468383**,
with **USD3.1531617** headroom. All earlier unknown attempts remain reserved;
there is no budget reset or refund. Reservations and estimates at the unchanged
configured USD0.10/USD0.50 per-million rates are **not the provider invoice**.
All 21 outputs, logical attempt IDs, ordered SQL reservation rows, exact reserved
cost formulas and reported-usage entries reconcile. Maximum recorded wire sizes
are 177,867 / 174,679 / 163,543 bytes respectively, below the unchanged bound.

Pinned sources and job IDs:

- Filelock: `bc2405b882657b649fff86fe86ddd7883510393f`,
  job `f3066bae296744ae945c3283ca405c43`.
- Psutil: `7ef91833c2f852f8ad5e121e654562c23bb46ec0`,
  job `62866b33ca7343be836b46f294d12cb0`.
- Ws: `297202cdae9b0590629821373b3b679c407f3431`,
  job `528e9370594e40739923b0439823b948`.

## Useful mechanisms versus adoptable connections

For [hq-cli #21](https://github.com/ryannmicua/hq-cli/issues/21), Psutil's
`_psposix.pid_exists` probes a PID with signal zero, returning false for a missing
process and true for permission denial. Its cited body, lines 29–48 of the pinned
`psutil/_psposix.py`, supports the liveness primitive that the stale-lock policy
needs. The two accepted partial checks remain **undetermined**: owner-PID parsing,
lock policy, conservative errors and integration with the target's **Go** runtime
are absent. Porting an algorithm is not a demonstrated reusable Python adapter.
The process-iteration alternative is correctly rejected as the requested solution.

For [homebridge-ratgdo-forceclose #47](https://github.com/Haglerd/homebridge-ratgdo-forceclose/issues/47),
Ws offers three bounded, implementation-cited pieces: buffer-list concatenation,
chunk collection/length tracking and conversion of individual values to Buffers.
All stay partial; none implements the target HTTP response lifecycle, preserves
the caller contract or satisfies the requested smoke tests.

In particular, Ws's custom allocation/copy routine is **not** the expressly
requested `Buffer.concat(chunks)` call. The compression callback's chunk push is
not an HTTP handler, and `toBuffer` does not collect a response. The model names
these limitations correctly. However, three small implementation primitives
for one issue must not be marketed as three valuable connections: the target
already asks for a standard Buffer API, and borrowing Ws code has not been shown
to reduce integration work. Groundedness is not a utility score.

For [Harbor #2348](https://github.com/harbor-framework/harbor/issues/2348), the model
recognizes task-scoped asynchronous deadlock handling and explicitly leaves
the target's dependency version/adoption unknown. The source is already referenced
in the acquired discussion and target manifest, so both comparisons are labeled
`known_reference`, not new discovery. The broader class attribution still has the
evidence weakness described next; do not treat its satisfied check as executed proof.

## Two attribution weaknesses reproduced without spending

1. **An unrelated class assignment can satisfy body presence for a method claim.**
   Match `e72f5f6d33154cd84350a7591c8a7968` selects `BaseAsyncFileLock` but explains
   `_deadlock_scope()` returning the current task. The class's owned body consists
   only of assignments at lines 126–127. Its broad citation contains those assignments
   and the nested method, so the structural presence gate passes. Reciting the same
   acquired method excerpt without those class assignments makes the class gate
   fail. The source contains the described method; the problem is that **the selected
   class evidence does not establish that method's behavior**. Its method ID is not
   available in the bounded 100-capability snapshot, so prompt guidance alone cannot
   select it. This is a reproducible attribution weakness, not semantic proof from
   a successful structural check.
2. **A quoted prefix can omit the useful body despite a wider declared range.**
   Match `dff2a683d6a07b845c6dce9c666196b6` proposes Filelock's native descriptor-lock
   primitive for [Open WebUI #122](https://github.com/DankerMu/open-webui/issues/122).
   Its 1,600-character citation declares lines 16–50 but actually stops at line 38;
   the executable body starts at line 43. The existing gate correctly discards that
   partial claim, records `selected_operation_body_missing` and exposes an explanatory
   check reason. This is under-supported attribution, not evidence that the acquired
   function lacks useful behavior. Body-focused bounded citations need separate
   fixtures; weakening the gate would recreate false credit.

These pure retained-snapshot spot checks made no calls and did not rewrite any
stored result. Fix them separately with positive/negative offline regressions,
preserving ownership, request bounds, transport limits and unknown results. Do
not broaden every class to its methods or expand universal parser/resolver scope.

## Rejections and retrieval limits

Filelock's expiring soft lease is rejected for Open WebUI's mandatory serialization:
its documented possible overlap of live holders defeats that guarantee. A generic
shared-filesystem reader/writer lock is also not a Runnable agent implementation.
Ws's extension-header parser is correctly rejected as a Node compatibility-survey
reviewer or SIP display-name sanitizer. These are useful false-positive controls,
not proof that all unselected retrieval candidates are correctly classified.

Psutil correctly separates OS **process IDs** from Actor-TS **persistence IDs**.
The whole candidate is a non-fit. Its raw output nevertheless labels many absent
target deliverables as `incompatible`; that conflict count must not be treated
as independently verified runtime prohibitions. Scope mismatch and lack of
implementation are not automatically hard environmental contradictions.

The transparent wrapper preserved the unchanged selector return and sanitized
query batches: Filelock 88 rows / 87 distinct hints, Psutil 80 / 80 and Ws 76 / 76.
Each selected pool exactly matches the persisted checkpoint. Search remains
lexical: process/persistence IDs and general parsing collide; Harbor is a known
dependency, and several retrieved requests are broad product programs. Unselected
titles are not a measured missed-opportunity or recall denominator.

Source sampling was bounded to 24 files: 24/91 eligible files for Filelock,
24/179 for Psutil and 24/47 for Ws. Enrichment was offered 30, 30 and 27 capability
IDs and interpreted 8, 8 and 7. Python samples hit the 100-capability limit; the
enrichment bound omitted 70 IDs each. Psutil native backends are not equivalent
to acquired Python implementation coverage; JS scanning remains partial. No
parser expansion or changed search ranking occurred during this experiment.

## Exports, preserved history and restart limitation

Before restoring the normal handler, **all 15 CLI JSON exports equal fresh HTTP
exports from their pinned match snapshots**. All 15 HTTP ZIPs equal the deterministic
pinned package; manifest/part/total hashes and sizes verify. Five use the multipart
index (two or three fragments), ten are inline. Reconstructed handoffs span
56,206–280,696 bytes; largest individual file is 128,000 bytes and largest total
uncompressed package is 309,615, below the unchanged 2,000,000-byte bound. No
evidence is lost, and every package remains **not executed**.

All **81 prior job payloads, 279 prior matches, 257 prior snapshots, 419 old
reservation rows and 133 protected JSON artifacts** retain exact values/hashes.
Pre-spending startup/browser checks preserved all 12 table hashes. Post-run
exports did not alter tables, and all 12 hashes remained identical across the
normal-handler restart. Both old paused investigations stay paused; no new job
is active and analytics collection was not started.

The temporary selection wrapper was removed by restarting only the identified
owned loopback server on the same frozen code. Browser verification using the
verification/agent-browser skills passed Missing Link, repository-result filtering
and Overview without browser errors; screenshots are private, not published.

**A later read-only restart-confirmation helper stopped at its verified-state
assertion, before its planned second JSON/ZIP comparison loop.** It observed a
state that failed `account == Daniele-Cangi and not diagnostic_only`; the diagnostic
subtype was not retained before that assertion. Do not infer a confirmed switch,
expired token, proven timeout or VPN cause. The failure and unused helper remain
preserved; no repair or rerun of that confirmation occurred.

One subsequent read-only diagnostic observation returned normal full state for
Daniele-Cangi with the three completed jobs. Unrestricted `gh auth status --json hosts`
reported active success using Windows keyring. This establishes later recovery,
not the earlier cause. The account guard was not weakened, no `gh auth login`
was requested, and no further paid request/resume was made. The pre-restart export
checks remain valid; **post-restart export equality was not completed**.

## Next decision

The three unstarted source inputs have now been evaluated, but the older stopped
five-source experiment remains immutable and incomplete. No causal accuracy
improvement can be inferred from different retrieved discussions, and no isolated
connection should be forced from these partial primitives.

Prioritize the two reproduced evidence-attribution cases as bounded no-spend
work, then retain safe observations for transient identity diagnostics. Keep
retrieval utility, conflict semantics and optional typed-export coverage distinct
from regressions against declared contracts. UI/key-entry and broad language
coverage remain deferred; another paid verification needs a separately frozen
decision under the same allowance, not an automatic continuation.
