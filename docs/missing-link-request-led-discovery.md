# Request-led discovery: bounded functional experiment

Status: implementation and offline verification; no authorized live model run yet.
Historical experiments and their claims are unchanged.

## Why this change

The #120 source-first cohort completed 46 AI calls and examined 15 discussions,
but demonstrated zero advantageous autonomous reuses. The #121 experiments added
real executable API search, with operator-supplied packages. Neither experiment
let the product decide which software to inspect from an independent need.
The separate #122 demand-first lexical baseline selected irrelevant sources;
its native audio-feeder comparison favored the direct standard-library solution.
These outcomes motivate a decision about whether reuse is worth searching for,
before source selection. They do not establish that a semantic decision will work.

## Implemented path

The existing Service accepts `action=discover_from_request`, one public issue URL,
`use_ai=true`, and no donor repository or query. The existing investigation CLI
exposes this as `--from-request --issue URL --use-ai`. AI configuration and an
explicit appropriate allowance remain required. The ordinary source-first mode
and its defaults remain unchanged.

1. Interpret the discussion with the existing source-independent request method.
   Non-demands and resolved requests stop before repository search.
2. Read the existing bounded, pinned target context (at most four files). Propose
   requested operations and the strongest direct alternative. Decide `search`,
   `use_direct`, or `defer`. A search requires a concrete benefit hypothesis and
   a falsifiable comparison against that alternative, linked to requirement IDs.
3. Only for `search`, use at most three model-selected behavior queries on public,
   unarchived, non-fork GitHub repositories; one page of at most 20 results each.
   Deduplicate repositories, exclude the target itself, preserve query provenance.
4. Assess the returned metadata semantically and select at most one supplied
   repository ID, or `none`. No operator replacement, automatic retry or new query.
5. The ordinary pinned acquisition, capability interpretation and compatibility
   evaluation examine that source against the original request, with every
   mandatory constraint preserved. Empty capability extraction remains empty.

This adds two Provider decisions and one source-search method, not a new runner,
transport, store, lease, cache or generalized orchestration framework. Atomic
allowances, cancellation, account/provider identity, native response retention,
redaction and result validation use the existing path. Successful checkpoints
are reused on explicit resume; a failed attempt is not automatically repeated.

Both decisions are explicitly unverified. Metadata is not code evidence; a model
claim about the direct alternative is not a tested baseline. `use_direct` and
`none` are revisable abstentions, not proof that no useful library exists.
Target coverage is incomplete; the planner sees at most 8,000 characters per
file and receives redaction/truncation/coverage flags. The source selection can
miss a good package outside its first pages or reject one with poor metadata.
The system chooses operations and repository queries within GitHub; it does not
yet choose among ecosystems/search services or demonstrate reliable economics.

## Frozen live comparison (before reading the new need)

This protocol fixes acquisition and assessment before inspecting the fresh issue
or any candidate package. No prompt or selector tuning during the cohort.

* Historical control: `https://github.com/pganssle/audio-feeder/issues/81` from
  #122. This is already known, not a held-out success opportunity. The direct
  standard-library correction passed native acceptance in that experiment.
  Test whether the new mode avoids the lexical baseline's irrelevant inspection;
  changed discussion/source state must be reported, not hidden.
* One fresh primary need: the **first result** from GitHub issue search
  `is:issue is:open is:public language:Python label:enhancement created:2025-01-01..2025-12-31 comments:>=2`,
  sorted by creation descending, page 1, one result. No reading other results,
  replacement, repository-name filter or fallback query. Save the returned issue
  identity before reading its full discussion. Empty search is an outcome.
  If the issue already names the eventual package, count selection as assisted.
  This single Python feature request is a purposive temporal sample, not an
  estimate of broad discovery quality.
* Before either model run, record acceptance criteria and the strongest direct
  alternative using only the demand and target context. Criteria may include
  non-code or ambiguous requirements; leave those unknown. Record when project
  context cannot support a native acceptance test. Do not look for donor packages
  while defining the criteria. The product does not receive this assessor's notes.
* Run the historical control first, then the fresh primary, once each through
  ordinary Service with no supplied donor, query, interpretation or corrections.
  At most 5 AI calls, 3 search requests and one source inspection per need; at
  most 10 AI calls for the cohort. Existing GitHub request bound: 120 per job.
  Each failure, pause, abstention or empty pool counts; no resume or retry in
  this cohort. The primary is not replaced if it is unsuitable for reuse.
* A new allowance is necessary; earlier authorizations covered other cohorts.
  No model calls may run before approval. Existing reports/experiments are not
  overwritten. Keep new public evidence compact and retain original job records.

## What counts as progress

Record calls, conservative reservations and reported usage separately, wall time,
queries, pools, selected package/revision, operation-to-requirement links, stops,
coverage gaps and failures. Authored offline responses only test wiring and
validation; they are not model-quality evidence.

For the control compare with #122's frozen lexical choices and already tested
direct solution. For the primary report whether the model chose a real requested
operation, whether its query plausibly seeks that behavior, whether the source
contains it, and whether any expected advantage survives comparison with the
strongest direct alternative. Do not score more matches as improvement. Report
incorrect abstentions and unnecessary searches as well as false positives.

A useful-reuse claim requires all acceptance criteria justified independently of
the selected donor; an implemented integration in the actual target at a pinned
revision; its native tests and relevant end-to-end behavior; and comparison with
the best direct alternative on the same inputs/environment. A sandbox-only
function success, compatible signature, citation, selected package or convincing
explanation is insufficient. Measure new integration logic/dependencies and the
specific benefit predicted before selection (e.g. correctness, supported cases,
maintenance work or performance). Avoid counting shorter glue code alone as
lower total cost. Native integration can fail, or show no advantage; report that
without selecting a replacement or enlarging the engine. Maintainer acceptance
and production benefit remain unknown without independent evidence.

The next decision is driven by this result, not by a presumption that another
retrieval, citation or infrastructure layer is needed.
