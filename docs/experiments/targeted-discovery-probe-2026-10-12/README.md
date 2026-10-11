# Targeted discovery inquiry: interrupted comparison

**The comparison is inconclusive.** Three jobs completed, the fourth paused on a
GitHub identity-verification timeout, and the two remaining jobs were not started.
There is no complete fresh A/B pair. No advantageous reuse or native target
integration was demonstrated. This is neither a successful discovery experiment
nor evidence that the targeted-inquiry idea fails.

Execution used `eeb6028c6eb817dd3c41f8e9b34943a790300ecd`, on 2026-10-11,
22:29:48--22:34:02 UTC, after review and all four Windows/Linux Python 3.10/3.13
jobs in [CI 38179652056](https://github.com/Daniele-Cangi/RepoTraction/actions/runs/38179652056)
passed. The preparation [protocol](protocol.md), [selection](selection.json),
[acceptance notes](acceptance-before-search.md) and
[acquisition index](acquisition-index.json) remain unchanged. Subsequent
[authorization](authorization.json), [readiness](readiness.json),
[measurements](run-result.json), [native outputs](evidence.json),
[match summaries](match-summaries.json) and [retained index](retained-index.json)
record what actually happened.

## Execution and accounting

A is the unchanged default request-led path; B enables one target-file inquiry.
The two historical controls ran B only; their #123 outputs are not live A arms.

| Case | Arm | Outcome | Reserved attempts / complete outputs | Wall seconds | Reserved USD |
| --- | --- | --- | ---: | ---: | ---: |
| audio-feeder #81, historical | B | `use_direct` | 3 / 3 | 28.786 | 0.0274802 |
| tunesynctool #21, historical | B | `search`, then select none | 4 / 4 | 45.467 | 0.0383358 |
| Agentic-AI-Pipeline #23, fresh | A | `search`, one donor inspected | 5 / 5 | 143.475 | 0.0655401 |
| Agentic-AI-Pipeline #23, fresh | B | Paused during request interpretation | 1 / 0 | 36.011 | 0.0083388 |
| PINA #761, fresh | B, then A | Neither started | 0 / 0 | — | 0 |
| Cohort | | Stopped, no retry or resume | 13 / 12 | 253.851 | 0.1396949 |

The fourth job recorded `github_identity_cli_timeout`: account verification
exceeded 10 seconds. No change of account was confirmed. It has no retained
terminal provider response, native output or usage. Reservation occurs before
dispatch, and identity checks also run during streaming; the retained record
does not establish whether that attempt reached or completed at the provider.
Its reservation remains charged. It must not be counted as a completed response,
zero-cost call or known provider failure. The underlying cause of the CLI timeout
is unknown. The frozen stopping rule ended the cohort; no timeout tuning, retries,
resumes, replacement cases or extra paid calls followed.

The twelve recorded responses report 155,871 input and 21,188 output tokens:
**USD 0.0261811** at the existing configured USD 0.10/0.50 per million tokens.
This estimate excludes any unreported usage from the paused attempt and is not
a bill. The conservative reservation is **USD 0.1396949**, within the new
**USD 1.00** authorization. Unused allowance does not cover another experiment.
A read-only reconciliation found 13 reservation rows and 12 unique completed
attempt/output records, with the ledger sum matching the four job records.

The Service charged 63 GitHub reads: 28 new network reads and 35 replayed reads;
two Store cache hits are separate and are not another two network requests.
The 33 unique preparation reads are also separate. There were two repository
search queries and one donor inspection. Identity-verification CLI calls are
not included in these repository-read counts. Wall time covers the invocation,
not preparation, CI or assessment. The job timers sum to 253.739 seconds; the
remaining 0.112 seconds are outside those timers. No model-versus-callback time
breakdown was measured. These different paths and the interrupted cohort do not
support a performance comparison with each other or with the forensic runner.

## What the completed jobs establish

**audio-feeder.** B selected `page_generator.py`, `pages.py` and
`test_page_generator.py` at the fixed revision. The selected `pages.py` is longer
than the unchanged 8,000-character prompt limit, and its supplied excerpt calls
`get_sorted_entries` without including its implementation. The model discloses
that gap and keeps `use_direct`, proposing Unicode normalization, numeric-token
handling and an original-value tie-break. This is an autonomously chosen code
inspection, not verified sorting behavior or proof that a package cannot help.
The historical direct test still does not establish numeric natural sorting.

**tunesynctool.** B selected the synchronous and asynchronous Subsonic drivers.
The acquired synchronous driver exposes `search_tracks` using `search2` and leaves
`get_track_by_isrc` unimplemented. The model changed the historical `defer` to a
bounded search for a specification-grounded lookup mechanism. It rejected all
four returned repositories because their metadata did not establish that mechanism
or a benefit over the current client. Exact matching and avoiding MusicBrainz
requests are explicit normalized requirements this time, whereas #123 did not
represent them separately. That extraction improvement happens **before** the
inquiry, with the same interpretation prompt hash: it cannot be credited to
reading the drivers. The later decision uses the new source evidence, but changed
model outputs and interpretation remain confounders. External protocol/server
support and the direct alternative's adequacy remain unknown.

For both historical controls, the recorded issue fingerprints, target revisions
and initial interpretation-prompt hashes match #123. There is no observed drift
in those identities. These historical comparisons still do not isolate causality.

**Agentic-AI-Pipeline, A only.** The baseline independently generated a behavioral
query, considered twenty metadata candidates and selected
[`Tejasdk04/agent-golden-harness`](https://github.com/Tejasdk04/agent-golden-harness/tree/46afde6e747fdaf503132f222f8af2fd8e529e9d).
This source was not supplied by the operator or named in the original discussion.
Thirteen source files were acquired; three other files were excluded for
credential-looking content. The bounded capability/match context has explicit
omissions. The final records classify `Cassette` as `similarity_only` and
`assert_golden` as `partial_contribution`, both `investigate` and ineligible for
qualified follow-up. The latter grounds snapshot comparison and mismatch failure,
while target record/replay, no-live-call behavior and integration remain unproved.
Neither example bridge was executed.

That is live evidence that the existing request-led baseline can choose an
operation, issue a query, choose an unprovided repository and inspect its code.
It is not evidence for the added inquiry, which never ran on this fresh case.
Nor is it a useful new opportunity: the pre-search assessor already established
that [target PR #24](https://github.com/hoangsonww/Agentic-AI-Pipeline/pull/24)
was merged and its integration files exist at the pinned revision. No residual
failure was established. The product's bounded discussion does not confirm the
merge, so its uncertainty is understandable; it nevertheless investigates an
alternative before establishing that an unmet need remains. Using the existing
integration is the stronger available direct alternative. A JSON snapshot example
would not demonstrate an improvement over it. We did not manufacture a residual
failure, run the real chat graph, or replace the selected donor to obtain a win.

**The missing comparison.** Fresh B stopped during its first request call,
before choosing an inquiry. PINA has no outputs in either arm. We therefore cannot
say that B avoids redundant search, improves source choice, loses fewer useful
opportunities or changes execution cost on new requests. Zero demonstrated useful
reuses is a count of observed results, not a measured zero success rate for B.

## Engineering disposition and next decision

The PR adds an opt-in functional action within the existing Service, Provider and
source acquisition functions: choose one question and up to three exact files at
the pinned target revision, then make the existing decision. Defaults preserve
the old path. It introduces no runner, transport, database, retrieval framework or
repeat investigation. Budget, identity, persistence, redaction and public provenance
stay on the ordinary path. Review found one incomplete-acquisition defect; the
executed commit requires the exact selected path/SHA set and count, with regressions
for total and partial omission. All 15 inquiry regressions pass; the full executed
commit passed the four-platform CI matrix (Linux 3.13 collected 1,949 tests).

Keep the code reviewable as an optional capability; this experiment does not
justify enabling it by default. Close **this execution** as interrupted and
inconclusive. Do not optimize its file selector, prompts or identity checks in
order to finish the comparison, and do not report the idea as disproved.

Given the agreed priority, the next useful experiment can instead test assistance
to a development agent: fix a real unresolved problem and native acceptance first;
record the agent's unaided attempt; then compare equal-budget continuation with
ordinary investigation against continuation receiving a source-grounded mechanism
from Missing Link. Credit a changed implemented approach and better native outcomes,
not a persuasive suggestion or a library-only demonstration. A positive must trace
the useful change to the supplied mechanism; a negative must retain the unchanged
baseline and failed attempts. This is a proposal, not a capability demonstrated by
this cohort, and no such second experiment or additional API expenditure has begun.

The isolated branch and current opt-in path already provide the separation needed
for that decision. No new infrastructure phase is warranted by this result. The
historical experiments and the frozen preparation files have not been rewritten.
