# Missing Link contract-19 live retest — 2 October 2026

## Frozen protocol (before any paid call)

This is an explicitly authorized fresh model test, not an offline replay or a
feature change. Implementation is frozen at merged commit
`12e9c300aa10f69d5e08889a13673b71a1cd8dca`, analysis contract 19. Documentation
commits may follow, but application/provider/acquisition/selection code must not
change during the cohort. Historical reports remain immutable.

Repeat all 13 repository-only inputs from the earlier 2 October contract-16
evaluation, in the same order. Neither group is now held out. Do not provide
issues, custom queries, coding-agent interpretations, imported analyses or
replacement repositories. Repository revisions and discovered issues may change;
this is not a controlled causal accuracy comparison.

1. `more-itertools/more-itertools`
2. `tkem/cachetools`
3. `marshmallow-code/marshmallow`
4. `python-babel/babel`
5. `lepture/mistune`
6. `sindresorhus/p-retry`
7. `sindresorhus/strip-ansi` (canonical repository may be `chalk/strip-ansi`)
8. `colinhacks/zod`
9. `jquast/wcwidth`
10. `python-humanize/humanize`
11. `theskumar/python-dotenv`
12. `sindresorhus/escape-string-regexp`
13. `caolan/async`

Each input uses `Discover`, AI enabled, at most three candidates and 80 retrieval
requests. Eligibility preflight reads repository metadata only: public,
non-archived, issues enabled. Keep source acquisition failures in the denominator;
do not substitute a more successful input.

Provider configuration stays `gpt-6-luna`, Responses API, JSON schema, streaming,
medium reasoning, 180,000 prompt bytes, 12,000 output tokens, at most eight calls
and USD 2 reserved per job. Configured prices remain USD 0.10/M input and USD
0.50/M output; usage estimates are not bills. The original cumulative allowance
`missing-link-verification-2026-09-30` stays capped at USD 10, with 251 existing
reservations totaling USD 3.844534 (remaining conservative allowance USD 6.155466).
Do not reset or replace the allowance. Keys stay local and are never recorded.

There are no automatic paid retries or resumes. Completed partial jobs retain
their candidate errors and charged outputs. A paid/transport/account/budget
failure or a non-completed paid job stops the cohort for explicit inspection;
only a source-acquisition failure with zero paid calls may be recorded and passed
over. Do not change code or provider settings to force a successful outcome.

## Prespecified inspection

- Were primary product APIs supplied and recognized rather than lower-level
  helpers alone?
- Are source-grounded partial primitives retained separately from full request
  fulfillment, especially when an overall request has a real conflict?
- Are descriptive current gaps distinguished from actual prohibitions without
  weakening ambiguous or authoritative constraints?
- Are references/articles handled as non-demands without fabricated requirements?
- Are actual requests within 1..30 requirements, quotations/source IDs valid,
  omissions visible and invalid charged outputs retained?
- Did autonomous retrieval produce a useful external contribution and a
  defensible false-positive rejection? Distinguish existing behavior, partial
  behavior, uncertainty, novelty and adoption; no invented success percentages.

Reconcile real calls, traces, usage and SQLite allowance reservations. Check pinned
match exports and earlier model results remain intact, including after a restart.
Audit the model's answers against acquired source/discussion, not their summaries
alone. Preserve raw public-source evidence locally; commit only the reproducible
protocol and a non-secret aggregate report.

Isolation is conditional on a source-grounded eligible candidate and explicit
testable success criteria. Use the existing deny-network WASI runner, not Docker
or host execution; otherwise report why no safe experiment is warranted. UI/key
entry work and new parser features remain deferred.

## Initial interrupted segment

**Interrupted on the first source; the 13-source evaluation is not complete.**
Protocol commit `35d47ec` was pushed before any paid job. All 13 inputs passed
metadata-only preflight. The initial More Itertools job
`0e9003dd7b314f1cbcebf6b39c6dcf2a` stopped at 17:58:47 UTC on 2 October with
`status=paused`, during comparison of its second selected issue. The error was
`Active GitHub account could not be verified. Switch back or restart for separate history.`
No paid retry, resume, replacement input, import or isolation run followed within
this initial segment. The remaining 12 sources were not started, and none of the
13 jobs completed at that point. The separately approved continuation is recorded
below without replacing this interrupted report.

### Interruption and accounting

Read-only checks immediately afterward confirmed GitHub CLI's active keyring
account was still `Daniele-Cangi` with `state=success`; `gh api user` returned the
same login. Core API capacity was 4,671/5,000 remaining, and search capacity was
30/30. This is not evidence of an expired token, a changed account or exhausted
rate limits. The precise probe failure/timeout is not captured: the worker stores
a generic account-verification error. Do not weaken the identity safety check or
claim a definitive upstream root cause without further evidence.

| Measurement | Observed value |
| --- | --- |
| Initial source jobs started / completed / paused | 1 / 0 / 1 |
| Selected issues / completed issue comparisons | 3 / 1 |
| Retained capability-to-issue comparisons | 2 |
| Application AI reservations | 5 |
| Completed response traces, reported usage entries, retained JSON outputs | 4 each |
| Reservation without a completed response receipt | 1 |
| GitHub acquisition/search requests charged to the job | 24 |
| Additional conservative reserved cost | USD 0.0874559 |
| Token estimate for the four known responses only | USD 0.0183797 |
| Cumulative reservations / reserved cost | 256 / USD 3.9319899 |
| Remaining conservative allowance under USD 10 | USD 6.0680101 |

The fifth attempt has a reservation but no completed trace, usage or JSON output.
It is not certified as a fifth completed model response, a zero-cost request or
a refundable reservation. Its provider-side outcome/cost is unknown. All original
charges remain counted, and no allowance is reset. The maximum request size among
the four completed traces is 160,324 bytes; the unknown attempt is not assigned
an invented trace size. Request extraction returned 10 and 30 requirements;
the latter is at the bound and still needs a coverage audit.

### Independent source inspection of the saved comparison

Autonomous retrieval selected [ml-pipes issue 42](https://github.com/trained-by-humans/ml-pipes/issues/42),
which requests a pipeline chunking operator with list-valued groups and explicit
validation, documentation and test work. Neither the issue nor a tailored query
was supplied. All three selected issue URLs also appeared in the earlier cohort;
there is no new-target or novelty claim from this interrupted sample.

- **Useful partial contribution:** the pinned
  [`chunked` implementation](https://github.com/more-itertools/more-itertools/blob/1ea82a711c69f590054987b5cb194157f8ce8ac4/more_itertools/more.py#L215-L250)
  returns an iterator yielding lists, retains a short final list by default and
  explicitly rejects negative sizes. These source claims are supported. The
  normalized match keeps two satisfied behaviors and three implementation-cited
  partial checks; target operator registration, validation, docs and project tests
  are not presented as existing implementation. It is `investigate / needs_review`,
  not a qualified external lead. A missing documentation example is now unknown
  new work rather than the hard incompatibility assigned in the earlier answer.
- **Defensible as-is rejection:** the pinned
  [`grouper` implementation](https://github.com/more-itertools/more-itertools/blob/1ea82a711c69f590054987b5cb194157f8ce8ac4/more_itertools/recipes.py#L351-L389)
  yields tuples and fills, drops or rejects incomplete groups instead of preserving
  a short list. It remains rejected for that requested output shape/edge behavior.
  This is rejection of the existing operation as-is, not proof that no newly written
  adapter could ever work. Its lazy grouping contribution is retained separately.
- **Remaining questionable partial credit:** `grouper` check `r9` credits rejection
  of an invalid `incomplete` option toward the request's invalid-*size* tests.
  Those are different properties; the cited source does not establish size validation
  or the required tests. This is a semantic over-credit in the model answer, despite
  an overall correct rejection and valid citations. It needs further evaluation,
  not a parser expansion or a claim that every partial label is trustworthy.
- **Safety normalization still holds:** proposed partial credit backed only by
  test references becomes `not_demonstrated`. Test presence is not executed
  coverage. Generated example files are retained as unexecuted proposals only.

The earlier and current answers split the request into nine and ten requirements,
respectively; do not compare raw check counts as a measured improvement rate. One
completed issue comparison cannot establish cohort-level gains, public-API recall
for python-dotenv, non-demand handling, extraction coverage or discovery accuracy.

### Persistence and next step

Read-only integrity checks before and after a server restart confirm both pinned
HTTP exports are identical to their saved reports, four completed JSON outputs
remain retained, and all earlier job payloads, model matches, pinned snapshots
and 13 frozen reports remain byte-identical. The job stays paused after restart:
there is no implicit resume. The server remains available on loopback port 8765.
Browser verification found meaningful Missing Link content and no captured console
errors; missing `agent-browser` CLI was handled with the in-app browser.

Neither saved match is eligible for follow-up execution. No isolated proof is
forced from this incomplete sample. Explicit approval was needed to resume the
checkpoint/retry the unreceipted comparison and then start the remaining 12 inputs,
while retaining this interrupted segment and its charges separately. No product
code, prompts, provider settings or selection policy changed during the run.

## Explicit continuation amendment (before further paid calls)

On 2 October, after inspecting the interruption, the user explicitly approved
one checkpoint resume of job `0e9003dd7b314f1cbcebf6b39c6dcf2a`, retrying its
unreceipted comparison, then starting the remaining 12 frozen repository inputs.
This is a separately authorized continuation, not an automatic retry policy.

The original paused report and its accounting remain immutable in the initial
segment. Continuation reports are saved separately. Existing completed outputs
and all five original reservations are retained; the unknown fifth attempt is
not refunded or treated as a completed response. The continuation starts at
256 reservations / USD 3.9319899, keeping the same allowance and USD 10 ceiling.
The original job's eight-call limit includes its existing five reservations.

Implementation stays frozen at `12e9c30`, contract 19, with identical provider,
discovery inputs and selection limits. No issue, custom query or manual analysis
is supplied. Another non-completed paid/account/transport/budget outcome stops
the cohort for inspection, without further automatic resume or code changes.
Approval itself is not evidence of a completed cohort, improved discovery or an
eligible isolated experiment. Amendment commit `4967485` was pushed before the
continuation's paid calls.

## Continuation results: stopped on input 8

**Seven jobs completed, including one partial completion; Zod failed and five
inputs remain unstarted. The 13-input cohort is still incomplete.** The one
approved More Itertools checkpoint resume completed with its original history and
unknown attempt preserved. Subsequent jobs used only the frozen repository inputs.
No supplied issues, custom queries, manual analysis imports, replacement inputs,
automatic retries or product changes were introduced.

The following totals include the initial interrupted segment once, not twice.
"Attempts" means allowance reservations, not necessarily completed responses.

| Input | Status | Attempts / response receipts | Issue evaluations / saved matches | Reserved USD |
| --- | --- | --- | --- | --- |
| More Itertools | Completed after explicit resume | 8 / 7 | 3 / 5 | 0.1433778 |
| Cachetools | Completed; one deterministic reference skip | 5 / 5 | 2 / 3 | 0.0825219 |
| Marshmallow | Completed | 7 / 7 | 3 / 4 | 0.1147507 |
| Babel | Completed partial; one invalid extraction retained | 6 / 6 | 2 / 2 | 0.0965691 |
| Mistune | Completed | 7 / 7 | 3 / 5 | 0.1195725 |
| p-retry | Completed | 7 / 7 | 3 / 6 | 0.1155229 |
| strip-ansi (canonical `chalk/strip-ansi`) | Completed | 7 / 7 | 3 / 5 | 0.0850816 |
| Zod | Failed at second comparison transport preflight | 4 / 4 | 1 / 1 | 0.0718236 |
| **Total** | **8 started / 7 completed / 1 failed** | **51 / 50** | **20 / 31** | **0.8292201** |

`wcwidth`, `humanize`, `python-dotenv`, `escape-string-regexp` and `async` were not
started. Zod's second request was extracted but not compared; its third candidate
was not acquired. Twenty-four distinct issues were selected across the eight
started jobs, using 269 charged GitHub retrieval/search requests. Four selected
URLs overlap the earlier contract-16 cohort. Neither issue selection nor source
revisions are controlled, and there is no held-out, novelty or causal accuracy
claim.

### Accounting and retained evidence

- The continuation added 46 reservations / USD 0.7417642 to its starting ledger.
  Including the original segment, this cohort has 51 reservations / USD 0.8292201.
- Fifty completed response traces, reported usage entries and completed JSON
  outputs are retained: eight capability responses, 22 request responses and 20
  comparison responses. One request output was rejected by validation but retained
  and charged. The original unknown fifth attempt remains the only unreceipted
  reservation; the explicit retry is a separate sixth attempt, not a refund.
- Cumulative allowance: **302 reservations / USD 4.6737541**, leaving
  **USD 5.3262459** under the unchanged USD 10 ceiling. This is conservative
  reserved cost, not an OpenAI invoice. The estimate from the 50 known token-usage
  receipts is USD 0.2176745; the unknown attempt has no invented usage estimate.
- All started jobs remain within eight attempts / USD 2 per job. The largest
  completed transport receipt is 175,319 bytes under the 180,000-byte bound.
  Zod's rejected oversized comparison added no reservation or HTTP request.
- Local raw reports are in the ignored
  `data/luna-discovery-contract19-2026-10-02/continuation-01/` directory. The initial
  reports and earlier 13-source contract-16 reports remain immutable. No keys,
  credentials, private repository data or environment contents are committed.

The 31 saved matches are 22 `investigate` and nine `rejected`. Discovery assessments
are three `needs_review`, 18 `partial_contribution`, two `not_actionable`, six
`similarity_only` and two `reference_review`. **None is eligible for follow-up.**
The 75 `partial_behavior` check labels are model labels, not 75 verified useful
contributions: independent inspection below finds attribution and semantic
over-credit. Ten checks have `existing_behavior`; 337 are `not_demonstrated`.

### Finding 1: final transport is not budgeted during context packing

Zod's second discovered target is
[Rosetta issue 1461](https://github.com/Entif-AI/Rosetta/issues/1461). Its extracted
request has 27 requirements, within the declared bound. Comparison failed locally
with `Source context exceeds AI prompt bound. Select a smaller source subset or
use a coding-agent handoff.` This is not evidence of a GitHub/OpenAI outage or
exhausted call allowance.

Offline replay of this exact retained input through the frozen provider serializes
**185,562 bytes**, 5,562 over the existing 180,000-byte limit. It makes zero HTTP
calls and zero reservations. The data object is 164,570 bytes, including a
29,992-byte interpreted request (16,347 bytes of requirements and 9,019 bytes of
constraint review), 69,886 bytes of supplied sources, 31,411 bytes of repository
metadata and 21,720 bytes of coverage reporting. Component sizes are independent
JSON measurements, not additive wire-accounting claims.

`missing_link/context.py:build_context` packs to a 60% target and checks its final
data against `byte_limit - 16000`. `missing_link/provider.py:evaluate` then appends
the full interpreted request and match schema. `complete` serializes those into
the actual Responses framing, including further JSON escaping and the wire schema.
That late overhead defeats the fixed packing margin. The final preflight correctly
fails closed **before** reservation/network; packing feasibility is what failed.
The prior 78-context offline replay was valid for those retained inputs, not a
universal feasibility guarantee.

Necessary follow-up: pack against the actual final transport, including request,
schema, instructions, framing and escaping. Preserve the byte cap, implementation
ownership and explicit omission reporting. Add this acquired context as a bounded
offline regression; do not raise limits, silently truncate requirements or retry
paid calls to hide the failure.

### Finding 2: root-report citations starve an actual later request

Babel selected
[QuantEcon issue 676](https://github.com/QuantEcon/lecture-python-intro/issues/676),
a long generated translation onboarding report followed by a human request for
feedback/suggestions and later clarification. This is not a pure non-demand.
The discussion is incomplete, so `not_a_request` would also be inappropriate.

Luna's fourth response explicitly identifies the later request but returns zero
requirements with `status=unclear`, explaining that the offered demand spans omit
the relevant comments. Validation rejects it with `Extract at least one
source-grounded requirement.` The completed JSON/receipt and USD 0.0125237
reservation are retained; Babel finishes partial without a retry or replacement.

Offline inspection confirms `q1`'s actual comment is in supplied context, alongside
`q2` and `q3`. However, `missing_link/demand.py:citation_spans` consumes its global
18 KB serialized span budget in source order: **all 153 offered spans belong to
the long root report `q0`; none belongs to `q1`**. It reports 131 omitted visible
spans. Valid verbatim-citation enforcement cannot extract the later request when
no citation ID is available for it.

Necessary follow-up: share the citation budget across supplied discussion sources
so a long root report cannot monopolize it. Preserve exact original text, bounded
IDs/bytes and visible incompleteness; do not fabricate requirements, bypass quote
validation or relabel the actual feedback request as a reference-only outcome.
There are zero typed model `not_a_request` outcomes in this incomplete cohort;
Cachetools' reference-body skip is deterministic and is not a live validation of
that new model disposition.

### Finding 3: implementation citations do not establish a relevant contribution

Two inspected answers illustrate why a syntactically valid source link is not
sufficient proof of useful partial support:

- **Target-side work attributed to Zod.** For
  [Lightspeed issue 2760](https://github.com/lightspeedwp/.github/issues/2760),
  match `df02b35d71af32b4143498b9b209e567` assigns eight `partial_behavior` checks
  to Jest/ESLint/TypeScript/CI configuration. Its reasons acknowledge that the
  useful files are the *target project's* configuration and that Zod does not
  implement the requested tooling work. Each also cites an unrelated
  [Zod global configuration definition](https://github.com/colinhacks/zod/blob/0b216ef674e297ebe41d8bf902262e56f8755822/packages/zod/src/v4/core/core.ts#L227-L227).
  The citation exists but does not justify candidate-owned contribution. The
  summary admits non-fit; the saved partial labels are nevertheless misleading.
- **Analogy credited as implementation.** For
  [Ruff issue 16436](https://github.com/astral-sh/ruff/issues/16436), match
  `eec45bd3bb3bd5df5323e3dfd1e6c203` credits Cachetools runtime `cachedmethod`
  behavior toward static B019 checking of other caching libraries. The answer
  itself calls the relationship an analogy and acknowledges missing AST checking
  and Ruff diagnostics. Genuine runtime implementation does not make that analogy
  an existing contribution to the requested analyzer behavior.

Together with the initial `grouper` invalid-option/invalid-size over-credit, these
are failures relative to the declared partial-support meaning, not requests for
universal parser completeness. Necessary follow-up: require a candidate-owned,
concretely reusable operation relevant to the specific requested behavior. Separate
target-side context, conceptual analogy and adaptation/new work. Keep real partial
primitives, whole-request conflicts, unknown integration and execution gates intact.
Neither inspected false partial attribution passed the eligible-lead gate.

### What was independently supported, and what remains uncertain

Useful mechanisms remain narrower than a completed external integration:

- More Itertools' `chunked` support and `grouper` as-is rejection are source-backed
  as detailed above. Cachetools' bounded LRU storage is also a real partial primitive
  for [Asqueel issue 3](https://github.com/asqueel-org/asqueel/issues/3), while its
  memoization decorator's direct cached return does not rebuild current query
  parameters/environment. Neither case is a qualified new lead.
- p-retry's public
  [`makeRetriable`](https://github.com/sindresorhus/p-retry/blob/1472907affe8d6107aba5884abc36d6361b3042e/index.js#L267-L270)
  forwards arguments/`this` and delegates retry orchestration to `pRetry`. These
  primary APIs were recognized for
  [a fetch-wrapper request](https://github.com/vision72/eight-weeks-to-full-stack/issues/7),
  while project integration, HTTP policy and tests stay new work. Private delay
  helpers were not substituted for the public wrapper.
- Mistune's full parse pipeline is defensibly rejected for
  [Larch's byte-preserving extraction](https://github.com/zhupanov/larch/issues/6085):
  its [normalization](https://github.com/lepture/mistune/blob/a1b50bc12e066e5707ff797f821829bfcdab03b5/src/mistune/markdown.py#L82-L86)
  changes line endings/adds a newline. Its fence extraction can help other parsing
  work but is not certified raw-byte preservation. strip-ansi's ANSI removal is
  likewise not filename encoding repair or OS filename policy for
  [Fetchflow issue 6](https://github.com/Mayanktaker/fetchflow/issues/6).
- In [OpenTelemetry demo issue 1947](https://github.com/LGU-SE-Internal/opentelemetry-demo/issues/1947),
  "No external dependencies required" is not unambiguous proof of a dependency
  ban; that inferred hard conflict deserves review, not blanket acceptance.
  Independently, p-retry's
  [randomized delay](https://github.com/sindresorhus/p-retry/blob/1472907affe8d6107aba5884abc36d6361b3042e/index.js#L66-L73)
  is not the requested full-jitter range. Real explicit constraints must retain
  priority while ambiguous wording remains reviewable.

Accepted request extractions remain within 1..30 requirements. This incomplete
sample does not establish exhaustive extraction, trustworthy partial-label counts,
fresh python-dotenv public-API recall or successful typed non-demand handling.
No acquired/generated code was executed on the host. No isolated experiment was
forced: there is no eligible match with a demonstrated complete integration and
safe reproducible acceptance criteria.

### Persistence, browser verification and stop boundary

Read-only integrity checks before and after a second server restart produce
identical reports: all 31 pinned HTTP exports match the saved reports by hash,
the 50 completed outputs and original four receipts are retained, and historical
jobs/matches/snapshots plus initial/prior frozen reports are unchanged. No job
resumed implicitly and the ledger remains 302 / USD 4.6737541.

The verification workflow checked saved results through API/export and browser
after restart. Missing Link renders meaningful content, current provider/budget
and the completed/partial/failed jobs, including Zod's local packing error; no
captured console warnings/errors were present. The unavailable `agent-browser`
CLI was replaced by the in-app browser. The default source still showed correctly
marked historical results, not a claim that new results replaced earlier history.
No Discover/Resume control was pressed. The server remains on loopback port 8765.

Product/provider/acquisition/prompts/selection remain frozen at `12e9c30`; this
report and plan are documentation only. The next step is the three narrow offline
corrections above, separately committed and tested. Another paid resume or the
five pending inputs require a new explicit continuation decision and a frozen
protocol retaining this run's failures and charges. UI/key-entry work, new language
coverage and broader parser/resolver extensions remain deferred.
