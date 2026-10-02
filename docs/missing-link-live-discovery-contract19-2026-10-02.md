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

## Results

**Interrupted on the first source; the 13-source evaluation is not complete.**
Protocol commit `35d47ec` was pushed before any paid job. All 13 inputs passed
metadata-only preflight. The initial More Itertools job
`0e9003dd7b314f1cbcebf6b39c6dcf2a` stopped at 17:58:47 UTC on 2 October with
`status=paused`, during comparison of its second selected issue. The error was
`Active GitHub account could not be verified. Switch back or restart for separate history.`
No paid retry, resume, replacement input, import or isolation run followed. The
remaining 12 sources were not started, and none of the 13 jobs completed.

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
forced from this incomplete sample. Explicit approval is needed to resume the
checkpoint/retry the unreceipted comparison and then start the remaining 12 inputs,
while retaining this interrupted segment and its charges separately. No product
code, prompts, provider settings or selection policy changed during the run.
