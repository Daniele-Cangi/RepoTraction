# Discover: source-independent executable examples

Discover can now optionally ask its existing Provider to translate a public
discussion into cited input/output examples, then prepare the existing behavioral
prototype against the saved source snapshot. Previously those example contracts
had to be written by the operator. This closes a functional handoff; it does not
yet demonstrate better autonomous discovery.

## Use and boundaries

The existing start-investigation API accepts `behavioral_examples: true` together
with `use_ai: true` and `action: "discover"`. It is off by default. There is no
new dashboard toggle, runner, transport, database, scheduler or forensic audit.
Use the existing API client or `Service.start(...)`; enabling AI still requires
the existing explicit provider configuration and authorized budget.

For each candidate that survives demand disposition, Discover makes at most one
additional proposal call before compatibility evaluation. It is **not supplied
candidate source, repository identity, function lists, adapters or source-derived
contracts**. It sees the bounded discussion, citation spans and coverage report;
the discussion itself can of course mention a particular library.
Its output contains at most three operations with up to four examples and four
checks each, explicit/inferred case labels, constraints, assumptions, gaps and
an unknown runtime when the discussion does not establish one.

The closed output schema and local validator reject invented citation IDs,
duplicate example/check inputs, malformed or non-finite JSON, changed/redacted
example values, invalid boolean masks and oversized output. Citations establish
where text came from, **not whether the proposed operation correctly interprets
that text**. The model's explicit/inferred labels and runtime claims still require
semantic review. Repeated checks from that same model are not an independent
oracle. An `undetermined` response produces no executable plan.

The existing Budget reserves the call before dispatch and enforces account,
per-job call/cost caps and the atomic persisted allowance. The existing transport
records response, request hash, usage and attempt identity. The trace uses phase
`request` with `context_coverage.interpretation_contract = behavioral-demand-v1`.
No limits are raised: with the default eight-call cap, three fully evaluated AI
candidates may pause because the opt-in path can need ten calls (one source
interpretation plus three calls per candidate). Costs depend on configured prices
and actual request sizes; no old allowance authorizes a new paid pilot.

Successful proposals are saved in the existing job checkpoint before downstream
evaluation. Resume reuses them. Invalid proposals become candidate-local failures,
with fixed public diagnostics and no automatic retry. Job state exposes only a
summary; `Service.context(job_id)` exposes the retained proposal and provenance.

After reviewing a proposal, a local caller can prepare an inspectable plan:

```python
# service is the existing account-bound Service; job_id is a saved investigation.
prepared = service.behavioral_plan(job_id, 0)
proposal = prepared["proposal"]
plan = prepared["plan"]  # None for an undetermined operation
```

This method checks account and discussion snapshot identity and performs no
network or execution. It uses `prepare_behavior_search` from PR #114. Only an
explicit invocation of the existing `WasiRunner.run(plan["files"],
plan["entrypoint"])` executes acquired code; `assess_behavior_search` then attaches
observations. Do not execute artifact files with host Python. This remains an
opt-in Python prototype API, not an automatic sandbox step in ordinary Discover.
Every result remains unqualified and unintegrated. A behavioral witness does not
alter the existing compatibility classification or prove all issue requirements.

## Fixed new-family comparison

The [protocol](missing-link-independent-contracts-protocol.md) was committed as
`19f5deb` before acquisition. New immutable inputs and preparation observations are
in `tests/fixtures/independent_behavior_contracts/`; the old experiment is untouched.

Three fixed queries returned 12 distinct issues with 301 visible comments. The
first-100 limit omitted 47 comments from SymPy #3461. Timelines, linked issues and
attachments were not acquired, so all discussion-completeness flags remain false.
One bounded prompt also omitted 13 acquired source entries. These are unknowns,
not evidence that additional requirements do not exist. No cases were replaced
because they were irrelevant, old or difficult to interpret.

| Source family / fixed file | Prepared functions | Omitted top-level functions | AST preparation |
| --- | ---: | ---: | ---: |
| more-itertools / recipes.py | 40 | 27 | 0.047 s |
| boltons / mathutils.py | 1 | 2 | 0.008 s |
| NetworkX / dag.py | 0 | 20 | 0.029 s |

The existing 40-function cap, selected standard-library allowlist and unresolved
package bindings account for omissions. Graph package dependencies remain a
coverage limitation; no new extractor or adapter was added to rescue the sample.
Class methods are outside this prototype's scope and outside the omission counts.

Preparing all 12 proposal prompts took 1.340 seconds on the local Windows host.
Serialized chat/JSON-mode requests ranged from 12,199 to 140,541 bytes with the
documented default 180,000-byte cap. These are one-shot local measurements,
excluding acquisition and model time, not paid-call latency predictions.

The baseline selector still takes the same first three issues for each source:
CPython #42255, ghettoq #2, SymPy #4238. The opt-in proposal stage does not modify
ranking: **zero top-three changes**. Retrieval, diversity and the candidate cap
remain a bottleneck that this feature does not claim to solve. A separate isolated
comparison may interpret all 12 fixed discussions to measure missed opportunities;
that is not an increase in ordinary Discover selections.

## Free execution controls and what they establish

The authored synthetic protocol fixture asks for stable first-occurrence
deduplication: `[3, 1, 3] -> [3, 1]`, plus an empty-input check. It exercises the
new proposal decoder before using the existing behavioral plan. Runtime variants
are explicitly synthetic overrides, not interpretations of real issue text.

Three actual executions used the already-installed, pinned WASI runtime:

| Source family | Bindings attempted | Unobserved | Guest duration |
| --- | ---: | ---: | ---: |
| more-itertools | 72 | 0 | 3.125 s |
| boltons | 3 | 0 | 2.396 s |
| NetworkX | 0 | 0 | 2.250 s |

Only `unique_everseen` produced a witness for the Python control. The same output
was `runtime_blocked` for JavaScript and `runtime_unknown` for an unspecified
runtime. All three remained unqualified. Boltons had no match; NetworkX's empty
candidate set demonstrates missing coverage, not absence of applicable behavior.
`unique` and `unique_justseen` failed because their returned iterator objects are
outside the current JSON normalizer, so those failures do **not** demonstrate
their algorithms' semantic incompatibility. Full failures and omissions are saved.

There were **zero paid calls and zero qualified leads**. The mock Provider response
is authored test data, not a model interpretation. These controls demonstrate
protocol-to-execution continuity and compatibility gates, not autonomous discovery
or useful relations added/lost. That quality comparison is still unmeasured.

The baseline selector, extractor, example evaluator, WASI runner and Store are
unchanged from `c1d2d67`. Thus the saved contracts use the same baseline execution
logic; a second historical run was not rewritten or presented as fresh evidence.

## Decision after this PR

Keep the infrastructure phase closed. The next functional decision needs a fixed
model pilot on this pool, separately authorized, followed by source-blind technical
judgment of demand interpretation and independent challenge examples. Measure
useful relations and false positives against the fixed baseline, including the
effort and advantage of reuse. Do not tune on these new families or count synthetic
controls as quality successes. If interpretive proposals are accurate but useful
matches remain absent, distinguish retrieval, extraction coverage and genuine
non-applicability before selecting the next intervention.

Regression coverage includes source blindness, cited/unknown interpretation,
JSON and text preservation, existing budget/cancellation/account boundaries,
optional/default behavior, persisted resume, invalid candidates and read-only plan
identity. Windows/Linux complete CI remains a merge requirement.
