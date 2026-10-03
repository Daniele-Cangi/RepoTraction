# Missing Link: frozen five-new-repository contract-23 experiment

This protocol follows the merge of PR #45 with a clean targeted review and all
four CI jobs green. Commit and push it before any paid call. Earlier stopped or
completed segments remain immutable and are not resumed or combined into this run.

## Question and prescribed inputs

Can repository-only discovery find a useful source-grounded contribution on
untried, domain-diverse repositories while correctly declining lexical false
positives? This is a small exploratory held-out-input experiment, not a blinded
benchmark, accuracy/recall measurement or proof of independent novelty.

The five inputs and order are fixed before inspecting their issues or search
results. They have not appeared as source inputs in retained jobs:

| Order | Input | Selection domain / coverage caveat |
| --- | --- | --- |
| 1 | `alexmojaki/asttokens` | AST-to-source token mapping; Python source analysis |
| 2 | `spulec/freezegun` | Clock/time simulation for testing; patching assumptions |
| 3 | `tox-dev/filelock` | Interprocess file locking; platform/locking semantics |
| 4 | `giampaolo/psutil` | Process/system observation; native implementations may be omitted |
| 5 | `websockets/ws` | WebSocket networking; partial JS declaration coverage |

Supply only each repository name through the production investigation CLI/local
HTTP job API: AI enabled, empty issue URL/query, three maximum candidates and
80 GitHub requests. No manual analysis import, selected issue, tailored query,
replacement input, source/bridge execution, security testing or external contact.
Public/non-archived metadata and free model availability may be checked first.
If any source is unavailable, stop preflight rather than replacing it.

## Executable/provider freeze and budget

Freeze executable code at merged **`edcef83db733703fd0138b359d7403d33cdbd3b8`**,
analysis contract **23**. Documentation commits may follow, but production code,
prompts, query/selection rules, settings and the owned harness must remain frozen
throughout the experiment. Restart only the owned local evaluation server with
the production HTTP handler, without enabling the analytics collector. Verify
browser, account, API and stored history before spending.

Keep configured OpenAI `gpt-6-luna` unchanged: Responses/streaming/strict schema,
medium reasoning, eight maximum calls and USD 2 per job, 180,000 encoded request
bytes and 12,000 maximum output tokens. Never print, publish or commit credentials.
Verify safe provider fingerprints agree with the running server before every job.

Retain original allowance `missing-link-verification-2026-09-30`, **USD 10**.
The starting ledger is **409 reservations / USD 6.3181696**. Unknown earlier
attempts stay charged: no replacement allowance, reset or refunds.
This segment adds at most **USD 1.00 in conservative reservations**. Using the
unchanged configured input/output rates (USD 0.10 / 0.50 per million):

```text
maximum per call = ((180000 + 2048) * 0.10 + 12000 * 0.50) / 1000000
                 = USD 0.0242048
five jobs, eight calls each = 40 * 0.0242048 = USD 0.968192
maximum cumulative envelope = USD 7.2863616 < original USD 10
```

Recheck the full next job's worst-case reservation against both caps before
starting it. Reservations and reported-token estimates are not the vendor invoice.

## Observation, pool retention and stop rules

Run sequentially. The owned server wrapper captures **only** sanitized bounded
retrieval metadata for these sources before compatibility analysis: public URL,
title, state, query index and upstream rank, plus the selector's actual returned
decision. No raw search body is retained. It delegates to the unchanged production
selector and returns the same result, without reranking or supplying extra issues.
Verify that transparency wrapper offline before spending; an artifact-save failure
is a stop, not permission to silently lose the pool.

Stop the whole segment on an observer failure, failed/paused/cancelled job, any
candidate acquisition/validation error, transport/provider error, missing terminal
receipt, budget failure, frozen-code/account/settings change or unexpected paid
job. **Completed partial jobs with CLI exit 1 also stop this segment.** Do not
retry, resume, replace, increase limits, repair code or reinterpret a failure to
continue. Preserve acknowledged IDs and uncertain charged attempts. The production
observer's existing deadline/cancellation behavior is not changed.

Before spending, protect historical job/match/snapshot payloads, all existing
reservation rows and prior frozen evaluation artifacts with read-only hashes;
verify no active job and keep Babel paused. Afterward reconcile those old records,
new DB jobs, raw model outputs, attempt receipts, reservations, pool decisions and
HTTP exports. Mutable acquisition caches may refresh normally; do not confuse
that with permission to rewrite old analyses. No record is deleted or relabeled.

## Assessment and follow-up

Inspect what the model was actually shown and what it answered, not merely job
completion. Distinguish acquisition/scanner omissions, query breadth, ranking
hints, source-local behavior, grounded partial contribution, technical conflict,
semantic non-fit and eligibility. Compare selected/unselected titles only as
retrieval hints; an uninspected issue is not a demonstrated better match.

Report all attempted inputs, unstarted inputs, errors and uncertainty, original
requirements versus bounded contribution, code/settings, receipts and spending.
Zero eligible leads is a valid result. Different source inputs/requests do not
provide a controlled before/after accuracy comparison for PR #45.

Do not force a positive result or isolated demonstration. An eligible grounded
lead can motivate a separately scoped isolated test; interface/key-entry work and
typed callable-export coverage remain separate follow-ups after reconciliation.

## Unpaid startup correction before the final harness freeze

The first owned startup preflight stopped before any job/paid request: its exact
provider-description equality check rejected the API's documented additive
`limits.total_reserved_usd` field. The configured provider itself was unchanged;
all 12 table hashes stayed identical across restart/browser checks. No backend job
was acknowledged, no allowance was reset and no live job was retried.

Preserve that initial setup and baseline in `five-new-01`. The final owned harness
in `five-new-02` compares every configured description/limit field and separately
checks the live reserved total against the ledger. Positive/additive-field and
negative model/limit tests cover this startup-only correction. Freeze its new
hashes and push this clarification before paid calls. This is not permission to
repair or continue after a failed live job: the original strict stop rules apply
unchanged once a source job is started.

The second unpaid preflight mistakenly required the *source* issue tracker to
be enabled. `alexmojaki/asttokens` has `has_issues=false`, but its public code is
available and production discovery searches external requests; the source loader
does not require its own tracker. Preserve the `five-new-02` preflight showing
that false exclusion. The final driver in `five-new-03` removes only that
unnecessary prerequisite, with positive/negative eligibility fixtures. Inputs
and all genuine access/safety gates stay unchanged; no issue was inspected or
source replaced. The verified `five-new-02` runtime and unchanged pool capture
stay loaded, with their hashes also frozen by the final driver. No further
restart or production correction is needed. Both startup corrections occur
before any source job is acknowledged or paid attempt is reserved.
