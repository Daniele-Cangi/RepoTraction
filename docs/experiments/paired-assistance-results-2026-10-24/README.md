# Result: no Missing Link contribution demonstrated

The authorized pair completed within both frozen 20-minute ceilings. **Missing
Link failed on its first request-interpretation call, before searching any source.**
The native error is `ai_stream_deadline_exceeded`, with no terminal receipt or
reported token usage. After 246.76 seconds including packet handling, B continued
normally with its remaining budget, as required by the frozen protocol. No packet
was delivered, no source was manually substituted, and no retry was made.

This is an **interruption before the treatment**, not a negative semantic result
about a discovered mechanism. It does not establish whether a useful external
idea would help. It also supplies no incremental benefit or new discovery
capability attributable to Missing Link. No qualified connection is claimed.

## Native behavior and fixed timing comparison

Independent post-freeze checks confirm both patches pass the same **63 unchanged
native tests plus 14 frozen acceptance groups**, with no failures/skips, and all
seven native doctest groups. Their own additional regression counts (A 18, B 15)
are different tests and are not a between-arm quality score. All eight exact cycle
counts/digests match the immutable reference, and timed calls preserve their input.

Both implement inclusive minimum bounds, retain closure/unblocking bookkeeping,
skip undersized SCCs/BCCs, and apply undirected biconnected decomposition to directed
long-cycle search. Neither received model-generated notes or a Missing Link idea.
A inspected disclosed proposals and a paper through ordinary research; B reports
reasoning from pinned local code/public context. These reports do not establish
novelty or prove the timing/order of an agent's internal reasoning.

Nine sequential batches rotated reference/A/B order on the same Windows host,
using exactly the original graph generators and baseline iteration counts.
Times below are medians per API invocation, not end-to-end development time.
Ranges and all raw batches are preserved; no weights/workloads/thresholds changed.
No benchmark feedback was delivered to either agent and no patch was repaired.

| Workload | Reference ms | A ms | B ms | A/reference speedup | B/reference speedup |
| --- | ---: | ---: | ---: | ---: | ---: |
| dense-directed | 293.714 | 270.554 | 284.739 | 1.09x | 1.03x |
| dense-undirected | 226.177 | 202.541 | 209.209 | 1.12x | 1.08x |
| short-heavy-directed | 53.289 | 2.071 | 2.365 | 25.73x | 22.53x |
| short-heavy-undirected | 123.972 | 2.243 | 2.389 | 55.27x | 51.90x |
| output-rich-directed | 38.394 | 35.549 | 37.724 | 1.08x | 1.02x |
| output-rich-undirected | 17.537 | 16.254 | 16.923 | 1.08x | 1.04x |
| sparse-directed | 0.178 | 0.155 | 0.169 | 1.15x | 1.05x |
| acyclic | 12.300 | 9.692 | 10.106 | 1.27x | 1.22x |

On the four positive workloads, geometric-mean speedup over enumerate/filter is
**6.44x for A and 6.01x for B**.
Both meet the frozen 1.25x aggregate threshold without a control regression above
20%. Gains are concentrated in the two synthetic short-heavy families (roughly
22–55x); dense-family improvements are only about 1.03–1.12x. These are deliberately
constructed probes, not production workloads or evidence of universal improvement.

B/A geometric-mean speedup is **0.933x**, below 1.25x;
**0/9** paired aggregates exceed 1.10x. There is no additional efficiency
advantage for B under the fixed criterion. More fundamentally, the absence of a
packet prevents attribution to Missing Link regardless of that timing comparison.
The shorter reported B development time is not an assistance effect: no assistance
arrived and implementation choices/agent variability differ.

## Resources and evidence

| Observation | A: direct | B: assigned assistance, no packet |
| --- | ---: | ---: |
| Solver-reported total arm time | 963.50 s | 611.67 s, including discovery |
| Operator frozen snapshot upper bound | 1038.11 s | 644.26 s |
| Authorized wall ceiling | 1200 s | 1200 s |
| Provider calls | 1 | 1 (native interpretation) |
| Metered content HTTP reads | 6 | 2 (ordinary solver only) |
| Conservative retained reservation | USD 0.0064492 | USD 0.0100593 |
| Missing Link searches / sources / packet | — | 0 / 0 / none |

Total retained reservation: **USD 0.0165085 of USD 0.30 authorized**. This is not
an invoice or measured token spend: neither call supplied terminal usage receipts.
A's stream-timeout/no-notes outcome is recorded by its solver report and absence
of outputs; B's failure has a native structured transport diagnostic. Reservations
were retained, not refunded. Unused time, calls and allowance were not transferred
or repurposed. After completion, ordinary cancellation flags close helper access.

The preparation #141 CI was green before dispatch. The case-specific binding had
10 passing offline checks and clean exact-head review (`7ac2e51`) before A started;
its supplemental Windows CI was still running at A dispatch and all four jobs
were green before B discovery. This distinction is retained in execution-freeze,
rather than claiming every supplemental job had finished at the first dispatch.
The product modules and historical cohorts are unchanged. Exact backend model
snapshots and hidden subscription inference cost remain unavailable; the two
solvers used the same inherited model/effort settings and equal resource access.

- [Native checks](independent-checks.json), [complete logs](independent-native-logs.json.gz).
- [Timing medians/ranges/decision](timing-summary.json), [27 raw batch records](nine-batch-timings.json.gz), [assessment caller](native_measurement.py).
- [Resource receipt](resource-receipt.json), [authorization/preflight](authorization-and-preflight.json), [execution freeze](execution-freeze.json).
- A: [target patch](A/target.patch), [solver report](A/solver-report.json), [effective task](A/effective-task.md), [public job context](A/private-job-public-context.json.gz).
- B: [target patch](B/target.patch), [solver report](B/solver-report.json), [effective task](B/effective-task.md), [discovery outcome](B/discovery-outcome.json), [public job context](B/private-job-public-context.json.gz).

Public artifacts replace the absolute workspace root with `<REPOTRACTION>` and
use canonical UTF-8/LF. Original private hashes and public Git-blob hashes have
separate scopes. Native patches are byte-for-byte exports; their context contains
intentional unified-diff whitespace. Target code attribution/license is retained
in [target-LICENSE.txt](target-LICENSE.txt). No target dependency or upstream
repository was modified outside the ignored local RepoTraction copies.

## Decision after this cohort

Close this pair without retries, timeout increases, extra sources or another
problem. The useful cycle-search changes belong to ordinary solver work and the
public target context. Discover never reached retrieval or source qualification;
this run cannot justify tuning those stages or selecting another harder problem.

The next concrete prerequisite is an offline diagnosis of the existing SSE
receive deadline, using these retained inputs and current transport code, before
another paid cohort. Both a small advisory call and native interpretation failed
on that route. Network latency, model latency and time in synchronous callbacks
are not separated by these receipts, so a root-cause claim would be premature.
This warrants a bounded check of that specific failure, not a new runner, audit
system, larger budget or general infrastructure phase. No such fix/extra API
experiment is included here.

## Reproduce native results without API calls

Use the exact pinned target and environment from #141. Apply either `A/target.patch`
or `B/target.patch` to a separate pristine copy inside ignored RepoTraction data.
Set `ML_CYCLE_TARGET` and `PYTHONPATH` to that copy,
`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, and `ML_CYCLE_MODE=candidate`. Run the original
frozen `native_acceptance.py`, the unchanged native `test_cycles.py`, and the new
separate `test_cycles_min_length.py`. Run `--doctest-modules` on `cycles.py` too.
For the reference use the unchanged target and `ML_CYCLE_MODE=reference`.

Run `native_measurement.py BATCH ARM` with the isolated native interpreter for
each version, rotating reference/A/B by batch index modulo three for nine batches.
It verifies exact output digests before timing, uses only frozen baseline
iterations, and checks non-mutation/counts/length totals. Save fresh observations
under ignored data; do not overwrite committed evidence or re-tune the thresholds.

## Pre-launch contract and binding record

The user authorized the proposed two development agents and USD 0.30 aggregate
on 2026-10-24 (Europe/Rome), conditional on readiness. Preparation #141 is merged
at `c52ca49`; its exact head `771205b` has a clean Codex review and all four
Windows/Linux Python 3.10/3.13 CI jobs passed (run `40027748982`).

This follow-up retains the same request, tests, prompts, limits, source policy
and acceptance. Historical files are unchanged. `execution_bindings.py` is the
small case binding anticipated in the protocol: the previous frozen-read pattern,
ordinary Service/Provider/Budget/Store and identical metered notes/GitHub access
for both solvers. It adds no product mode, transport or agent runner. The existing
worker lease serializes helper use. Operator-created clocks cannot be reset by
the helper CLI. B's discovery and later helper calls consume one shared ledger.

Official [GPT-6 Luna documentation](https://developers.openai.com/api/docs/models/gpt-6-luna)
was fetched on 2026-10-24: Standard short-context input USD 0.10 and output USD
0.50 per million tokens. Both arms explicitly request `service_tier=default`;
the existing serialized-byte reservation and persisted USD 0.15 ceilings remain.
There are no hosted model tools or extra tool charges in these provider calls.
Six worst-size calls reserve USD 0.1452288 per arm, not a predicted invoice.

Offline preflight (`python test_bindings.py`, ten checks) uses temporary ledgers, mocked
identity and no provider requests. It checks expiry, no restart, shared call and
request counters, atomic allowance protection, provider settings and frozen
reads. The native discovery integration test exercises the actual Service start
path, reserves one call without transport, then checks that helpers see that same
call/allowance and that the bound native verification callback stops at five
minutes. `discovery_service` and `run_discovery` freeze B's construction/start
options, rather than leaving these connections to later operator commands.
Effective solver prompts will be the original common/arm text plus only
operational paths, remaining resources and any native strategy packet. The
existing native pipeline retains its own prompts, recorded in private job data.

The two solver dispatches will both use `fork_turns=none`, with model and effort
overrides omitted. Tool semantics guarantee inheritance of the same parent
settings. The runtime does not expose an exact backend model snapshot or hidden
reasoning token use; record that limitation rather than inventing identifiers or
claiming proven identical compute. Run A then B, as frozen. No outcome is assumed.

This initial execution commit precedes both clocks, agents, donor searches and
paid calls. Review this binding/effective-prompt contract before dispatch. Results,
ledgers, patches, native checks and timing observations are retained here;
no old evidence is rewritten. All target copies stay in ignored RepoTraction data.
