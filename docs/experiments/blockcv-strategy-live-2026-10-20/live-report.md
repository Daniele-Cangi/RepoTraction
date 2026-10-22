# Live blockCV assessment: no strategy proposed, second call out of protocol

Two provider calls completed on RepoTraction revision
`813bdfc1f42888b01d4c69559a3d1afa0aa99ce7`, after PR #135 was merged with
all four Windows/Linux CI jobs green and its two preparation review findings
resolved. The reviewed preparation is `d64525cb687e1f6b56897566ad3d3416b1f99a2a`.
The existing `Provider.suggest_strategies` returned `{"strategies": []}` for
**both** supplied cases. There was no retry, prompt repair or replacement.
However, the second call violated the frozen advancement condition. This is
**not a fully protocol-compliant cohort**; only the first response is an
in-protocol result. The second is retained as supplemental, out-of-protocol data.

| Case | Native completed JSON | Local outcome | Provider-call wall time |
| --- | --- | --- | ---: |
| `excluded-errors` | `{"strategies": []}` | Valid empty result; no added strategy | 31.234 s |
| `unobserved-clock` | `{"strategies": []}` | Valid JSON, but out-of-protocol supplemental result | 30.195 s |

These are original parseable model outputs, retained before local strategy
resolution. The empty lists were not produced by filtering or rejecting proposed
ideas. Both response traces have status `completed`; neither call exhausted the
configured output cap. All 18 acquired documentation excerpts and the full
operator-authored discussion were in each packed request. The wider repository
sample still excludes implementation files and does not represent all blockCV
documentation or the complete target software.

## Protocol deviation: second call should not have run

The frozen [README](README.md) says that "only a candidate-local rejection"
permits advancing to the second case. The [machine-readable protocol](experiment.json)
also says to proceed to the fixed next case "only for candidate-local rejection".
Call 1 was a valid empty response, not a candidate-local rejection. Under that
written rule, execution should have stopped after call 1. The invocation instead
continued unconditionally after a valid empty result and performed call 2.

The preparation also describes two ordered cases, but that does not override its
explicit advancement restriction. We do not reinterpret the restriction after
seeing the results or change the frozen preparation to make this run compliant.
The two-call ceiling, cost ceiling and no-retry limits were respected; that does
not cure the stop-rule violation. The extra conservative reservation attributable
to call 2 is 0.0153834 USD, with reported usage estimated at 0.0022378 USD at the
configured prices.

The native [receipt](live-results.json) remains unchanged. Its job status
`completed` describes technical execution, not protocol compliance. The first
empty result remains an observation from the prepared primary assessment. The
second response must not count as a compliant negative control or contribute to
a compliant two-case success/failure rate. No compensating rerun is performed.

## What this establishes and what remains unknown

The new documentation path was exercised with a real model and accepted valid
empty results without inventing implementation evidence or benefit. It did not
produce a technical strategy beyond the existing grouped masked-refit baseline.
There is no new useful transfer, implementation, receiving-agent advancement or
RF improvement demonstrated by this cohort.

The supplemental G31 response emitted no claim to reconstruct an unrestricted
clock without observations. It is excluded from the protocol-compliant control
assessment. Independently of that exclusion, an unexplained empty list does
**not** show that the model understood observability or reasoned correctly about
the physical information. Indiscriminate abstention could produce empty lists too.

No rationale accompanies either empty list in the existing response contract.
We therefore cannot determine whether the primary abstention reflects appropriate
comparison with an already strong baseline, a missed documented partial method,
or an effect of the prompt/context. The documentation's known fold-design ideas
do not become native model discoveries merely because the operator can name
them. This was an explicit-source assessment of exposed diagnostic cases, not
autonomous discovery, blind evaluation or a held-out estimate of usefulness.

The absence of proposals was not caused by a transport error, malformed JSON,
local prose rejection, prompt truncation of the acquired excerpts or an exhausted
allowance. It also does not establish that documentation-based transfer is
generally ineffective, that blockCV has no relevant mechanism, or that the
requested operation has no external solution.

## Execution, retention and cost

The invocation used the existing Provider, Budget, Service/Store account verifier,
worker lease, atomic allowance and redacted completed-output persistence. It
loaded only the already conserved blockCV snapshot and the reviewed operator
requests. An experiment-local Store under ignored
`data/blockcv-strategy-live-2026-10-20/` keeps the ledger and job; the exclusive
new run directory prevents replaying this invocation over its results. No new
runner or transport was added. No source acquisition, donor execution, target
read, Satellite modification/command/message/PR action or historical evidence
rewrite occurred.

The public [receipt](live-results.json) contains the original completed JSON,
resolved outcomes, request hashes/byte counts, source revision and snapshot hash,
provider identity, response IDs, reported usage and reserved allowance. The
preparation files remain unchanged by this results commit.

- Reserved attempts: **2**; recorded completed responses: **2**.
- New allowance ceiling: **0.05 USD**; conservative reservation: **0.0307304 USD**.
- Provider-reported usage: **42,735 input / 397 output tokens** in total.
- Usage estimate at the configured prices: **0.004472 USD**; this is not a
  verified invoice. Conservative reservations remain retained in the Store.
- Measured two-call loop: **61.454 s**, including local packing, account checks,
  persistence, transport and resolution. The per-case durations are nested within
  that total; do not add them to it. Preflight, CI, operator work and assessment
  are excluded. Transport-only latency and callback time were not measured.

## Decision

Close this cohort with its empty primary outcome and recorded protocol deviation.
Do not present it as a compliant two-case comparison. Do not spend the
remaining ceiling on retries, revised prompts or additional blockCV cases, and
do not change the response contract or infrastructure just to recover a positive.
More budget was not needed to complete this test.

The remaining functional question is still whether Missing Link can select a
source and produce a concrete idea that changes a recipient's approach beyond
its direct baseline. A subsequent test should exercise the existing request-led
strategy path on an independently specified unresolved operation, rather than
preselecting blockCV again. A source-grounded proposal would then need a recipient
comparison before any benefit claim. No such follow-up is started or authorized
by this receipt; benefit stays `not_tested`, execution `not_executed` and
qualification false.
