# End-to-end discovery: one frozen cohort

Baseline: `5598fe17f6ad74b0d61c591b4e6fe383e376d6fb` (merged PR #119).
Status: prepared; **no paid execution or target search performed**.

The question is whether ordinary Discover can find a previously unconsidered,
advantageous use of existing software. Better retrieval labels, valid contracts,
correct rejection and exact citations are diagnostic results, not the primary
success measure. Finish this cohort before deciding on any functional changes.

## Fixed inputs and execution

The three source identities were chosen before reading their implementation or
searching for external demands in this experiment. Only public repository
metadata was checked during preparation. These are purposive, familiar Python
projects from different application domains, not a random or fully blind sample.
Their names are absent from the checked historical experiment documents/fixtures.
No source is replaced because it is difficult to extract or produces no matches.

| Order | Public source | GitHub repository ID | Selection reason |
| --- | --- | ---: | --- |
| 1 | [pallets/jinja](https://github.com/pallets/jinja) | 994551 | Template processing |
| 2 | [psf/black](https://github.com/psf/black) | 125266328 | Source formatting |
| 3 | [scrapy/scrapy](https://github.com/scrapy/scrapy) | 529502 | Web crawling |

Use **`Service.start(..., background=False)`**, once per source in this order,
with the exact inputs in [manifest.json](experiments/end-to-end-discovery-2026-10-11/manifest.json).
Use a fresh account-scoped experiment database and the existing authenticated
GitHub read/account-verification functions, Provider, Store, Budget and lease.
This is the ordinary full Discover path; no custom request-only runner,
prepopulated repository/issue checkpoints, hand-selected files or replacement
queries. Do not change the local `.env` or historical stores.

Each job uses `action=discover`, `use_ai=true`, `behavioral_examples=true`, empty
`issue_url` and `query`, five selected candidates and 200 GitHub requests maximum.
Keep existing deduplication, diversity, screening, source sampling, three-query
limit and two search pages per query. Screening does not refill rejected slots.
The ordinary acquisition pins the default-branch commit when each job begins;
record its revision and repository ID before evaluating results. The protocol
fixes repository identities, not a future default-branch SHA. A rename/identity
mismatch invalidates that source's result without substitution. Sequential live searches are
time-dependent; preserve their returned order and actual acquisition times.

Run all three jobs before diagnosing or repairing any stage. Persist the native
capability/request/behavioral/match outputs, normalized results and existing
traces. A non-demand, invalid proposal, zero extracted functions or candidate
failure remains part of the denominator. Candidate-local failures follow the
existing Service continuation policy. Do not restart/resume jobs, retry paid
attempts, refill candidates or change model/prompt/configuration. Account,
credential, cancellation or budget failures stop the cohort; other job failures
are recorded before proceeding to the next fixed source. Reconcile the final
saved counters, not repeated global audits during streaming.

## Review and concrete verification after the cohort

Freeze all three outputs before inspection intended to improve the system.
The proposing model's `checks` remain model-generated, not an independent oracle.

1. Reuse the authorized separate-context reviewer workflow. Supply retained
   discussions and model-proposed demand contracts, excluding source names/code,
   retrieval terms and matching results. Review every selected candidate,
   including abstentions and skips. Record real unmet demand, requested operation,
   status changes, inferred assumptions, incompatible and unknown cases. Freeze
   independently authored challenge cases (at most four per supported contract)
   and the simplest credible direct-solution strategy before source behavior is
   inspected. Uncertain expected outputs stay unknown;
   do not rewrite the original contracts to make them pass.
2. For each candidate with a saved executable proposal, use existing
   `Service.behavioral_plan`, `prepare_behavior_search`, `WasiRunner.run` and
   `assess_behavior_search`. Preserve the existing maximum of 40 extracted
   callables and fixed adapter repertoire. Evaluate original examples/checks and
   independently supported challenge cases as separate, attributed observations.
   Independent cases may test an existing proposed operation; they may not add a
   new operation or a source binding absent from the autonomous proposals/search.
   Any such suggestion is an assisted result, excluded from autonomous successes.
3. Inspect surviving source bindings for preconditions, actual contribution,
   input mutation, target runtime, dependencies, licensing and deployment fit.
   Use the existing ablation observations to distinguish source computation from
   work performed by the adapter. Missing target evidence remains unknown; no
   additional searches, target-source acquisition or bespoke adapter vocabulary
   are introduced to rescue a case during this cohort.
4. Export surviving partial bridges through `prepare_behavior_bridge`. Compare
   each with the simplest credible direct implementation or already-available
   target solution. Record existing source versus new glue, dependencies and
   maintenance burden, and the specific advantage claimed. Independent expected
   values must not be adjusted to either implementation. At most one original
   and one challenge search per selected candidate, followed by at most one
   representative bridge and one direct-baseline check: at most 60 isolated
   executions. Choose a representative by least adapter complexity, then source
   ID; alternative bindings remain in the report. No external code runs on host
   Python, and no network/service/native target integration is implied.

The existing Windows WASI runtime is available at preparation. Its pure-Python,
top-level-function, JSON-value and adapter limits are part of the configuration
under test. Unsupported coupling or runtime is a limitation, not an invitation
to build a runner or proof framework. Agent-authored challenge/baseline code is
evaluation assistance and must be attributed; agent-authored connections do not
count as autonomous discovery. If the direct alternative cannot be established
from retained evidence, advantage remains unknown.

## Primary outcome, novelty and advantage

Count a **verified partial-reuse opportunity** only when all of these hold:

- Discover retrieved the demand from the source repository alone and proposed
  the operation/binding without an operator supplying an issue, query or link.
- Independent demand review establishes a real current need for that operation.
- Pinned implementation and isolated original/independent cases support the
  contribution, with no known blocking precondition or target incompatibility.
- The source supplies the useful computation; the adapter does not replace it.
- The bridge has a concrete adoption route and a documented advantage over the
  credible simpler alternative. Possible advantages include required measured
  behavior/performance or a substantive implementation avoided; similarity,
  source size, novelty alone and hypothetical time savings do not suffice.
- The source/target relation is absent from previous experiment cases and no
  existing adoption is established in retained target evidence. Report this as
  observed novelty within the checked evidence, never universal novelty.

Report incomplete adoption evidence or an unmeasured claimed benefit as unknown,
not as success. Count a source/target/operation once, irrespective of how many
bindings pass. Report per-source outcomes as well as unique opportunities.
Keep **target-integrated results** separate: isolated extracted-slice behavior
does not establish them. Never set the product's `qualified` flag merely because
this experimental rubric passes; existing product qualification remains intact.

Primary table: sources attempted/completed; candidates selected, skipped,
interpreted and assessed; autonomous opportunities surviving the entire chain;
assisted suggestions; incompatible/rejected/unknown cases; target integrations.
For every claimed opportunity include the exact source, external need, binding,
adapter, independent check, advantage evidence and remaining limitations.
Report model calls, reserved/usage-estimated cost, job time, isolated-execution
time and manual evaluation time separately. Rejection quality and span counts
are secondary diagnostics and cannot offset zero useful discoveries.

One verified opportunity is a case demonstration, not an estimate of general
success rate. Zero means this frozen configuration did not demonstrate the
desired capability on this cohort. With no demonstrated benefit, do not start
automatic repairs to the first failed stage. First decide whether the overall
functional strategy warrants another experiment. No weights, representations,
sample replacements or infrastructure changes are tuned on this cohort.

## Budget and authorization boundary

Freeze the current configured `gpt-6-luna`, Responses JSON schema, medium
reasoning, streaming, 12,000 output tokens and 180,000 request bytes. Configured
prices are USD 0.10/input and USD 0.50/output per million tokens; these are the
local accounting assumptions, not a newly verified provider price quote.

Each source needs at most one capability call and three calls for each of five
candidates (request, behavioral proposal, matching): **16 calls per job, 48 total**.
Non-demands/skips/failures may reduce this total. Existing reservation arithmetic:

`((180000 + 2048) * 0.10 + 12000 * 0.50) / 1000000 = USD 0.0242048/call`

Thus the maximum conservative reservation is **USD 1.1618304**. Propose a fresh
**USD 1.20** persisted allowance shared by the three jobs and USD 0.40 per job.
Do not reuse any previous allowance. Keep the new configuration scoped to this
invocation; no credentials appear in this manifest or exported evidence.

The 48-call count is bounded by exactly three jobs with the existing 16-call
per-job cap; the dollar ceiling is enforced atomically across jobs by Store.
It is not a forecast of actual billed usage. No paid dispatch occurs until the
user explicitly authorizes this cohort and ceiling. This preparation changes no
product code. Any future implementation change still requires regressions and
complete Windows/Linux CI before merge.

Preparation verification: the manifest's bounds and Decimal reservation arithmetic
pass; the proposed database does not exist; the existing WASI runtime is available;
all 51 existing behavioral/proposal tests pass. No new tests or runner were added.
