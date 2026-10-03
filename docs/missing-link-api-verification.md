# Missing Link: real API and isolated example verification

Checked on **2026-09-30**. These are real public GitHub acquisitions and OpenAI
`gpt-6-luna` Responses calls, through RepoTraction's local HTTP API. No analysis
was manually imported. The older [coding-agent cases](missing-link-cases.md) and
fictional unit/browser fixtures are different evidence classes.

## Review and implementation checks

Codex's [PR review finding](https://github.com/Daniele-Cangi/RepoTraction/pull/7#discussion_r4141605545)
was reproduced: refreshing a deterministic match could erase feedback and revive
superseded structural results. Atomic persistence now preserves both, and each
match has its own pinned reproduction snapshot. Regression tests cover refresh,
stale writers, supersession, restart and export independent of recent-job scans.

The provider now uses closed strict schemas with actual enums, independently
extracts demand before seeing a repository, checks citations against supplied
lines, and rejects refused/incomplete output. Context is bounded with explicit
omissions; recent discussion evidence is retained. Shared cost reservations
persist across jobs and restarts. Checkpoints cannot silently resume with a
different provider/model/contract.

## Actual investigations

Source: [un33k/python-slugify](https://github.com/un33k/python-slugify/tree/866401ea6b346d7575cf941bc73ad32a362e34aa),
pinned commit `866401ea6b346d7575cf941bc73ad32a362e34aa`. Source acquisition covered
23 files; prompt coverage was smaller and recorded separately. Code presence and
tests referenced in the source are not themselves execution results.

| Public need | API result | What it establishes / does not establish |
| --- | --- | --- |
| [LessWrong #519: whole-word meta descriptions](https://github.com/bellroy/lesswrong/issues/519) | Useful `smart_truncate` mechanism and generated narrow adapter; final classification **investigate** | The existing helper can preserve plain prose, but its hard-slice fallback needs a guard. Caller budget and no-word-fits policy remain assumptions; runtime/adoption/current demand are not established. |
| Same LessWrong request, full `slugify` API | **rejected** | Similar word-boundary options are insufficient: slugification changes prose into identifiers. |
| [CSSWG #4406: CSS text-overflow clipping](https://github.com/w3c/csswg-drafts/issues/4406) | Two candidates **rejected** | Python string shortening does not implement browser CSS layout/painting/ellipsis. A hard runtime/behavior conflict cannot be offset by similar terminology. Discussion cross-references remain uncollected. |
| [Manuskript #1006: readable Cyrillic filenames](https://github.com/olivierkes/manuskript/issues/1006) | **investigate** | Unicode/transliteration is a plausible mechanism, but exact Cyrillic output, target runtime, compatibility and migration policy were not established. No target integration was executed. |

Final positive investigation job: `5b3caba003814f0092c37f25b337af10` (3 AI calls).
Useful candidate: `3640f45126beeee67724cd8efa2269fc`.
CSS rejection job: `c69da03ae9db4359b9501719d7e13cba` (4 reservations including a
failed attempt). Manuskript job: `73d7ad0ae4614824b3a19894df9f13d2`.
Job traces retain response IDs, request SHA256, exact model and context coverage.
The report does not claim these old issues demonstrate fresh commercial demand.

## First isolated bridge, without Docker

Execution used **Wasmtime 49.0.1 / CPython WASI 3.14.7**, not host Python.
The explicit optional bootstrap verified release archive SHA256; the runner
verified engine/module hashes. Only copied stdlib, pinned public Python files,
generated bridge files and reviewed test fixtures entered a fresh temporary
directory. No host account/configuration/database directory was mounted.

Fixed boundary probes passed: guest platform `wasi`, only three explicit Python
environment variables, host-path reads denied, network/native subprocesses
unavailable, fuel exhaustion on an infinite loop, `MemoryError` above the guest
limit, and output termination at the configured cap. See
[runner setup and limits](missing-link.md#optional-isolated-python-examples-without-docker-windows-x64).
This is a capability sandbox, not a VM or a guarantee against runtime bugs.

The initial generated example passed its one ordinary-word test. Independent
checks then exposed an oversized-first-word failure: `encyclopedia next` with
assumed budget 5 produced `encyc`. That failed receipt is retained; it is not
hidden by a later successful run. It exposed an over-broad initial `direct`
assessment. After strengthening edge-case assessment, a **new API investigation**
produced a guarded adapter and downgraded the claim to **investigate**. No corrected
analysis or bridge was imported manually.

The final generated adapter's **2 tests passed**. The same independent controlled
fixtures also passed **4/4**, compared with ordinary slicing:

| Assumed input / limit | Slice baseline | Guarded existing mechanism |
| --- | --- | --- |
| `red fox jumps` / 10 | `red fox ju` | `red fox` |
| `A Quick, brown fox jumps` / 16 | `A Quick, brown f` | `A Quick, brown` |
| `alpha encyclopedia cat` / 12 | `alpha encycl` | `alpha` |
| `encyclopedia next` / 5 | `encyc` | empty string (explicit adapter policy) |

Final independent runner receipt: `f3892628a3e94490b7304643a7a79075`.
Generated-test receipt: `4d7c3946efb945788c2fdab71c6eb429`.
Receipts persist separately from importable model claims, include artifact hashes,
and become historical when bridge/criteria/revision/fingerprint changes.
`request_criteria_verified` remains **false**: fixture inputs, budget, spaces-only
normalization and the empty-output policy are not the original application's
accepted production contract. The package declares a base transliteration
dependency; this isolated helper path did not use it. No dependency install,
native extension, target application or live service was exercised.

## Budget and reproducibility

The user-authorized shared ceiling was **$2**, unchanged during verification.
Across all 17 reservations, including failed/debug attempts, the conservative
allowance ledger reserved **$0.2943555**. Fifteen responses reported token usage,
estimated at configured standard prices as **$0.0611546**. Usage for two interrupted
attempts was unknown and was **not** called zero; their full reservations remain.
These figures are not an OpenAI invoice. No additional paid call is required to
view the saved results.

Local regression verification: **144 tests passed**, including optional browser
fixtures. A read-only desktop/mobile smoke check against the real acquired
results reported no JavaScript errors, no mutation requests and no mobile overflow.
Windows installation/update preserved both SQLite history and local `.env`,
included the optional tools, and kept runtime downloads disabled. Local tests
do not substitute for the pull request's CI result.

Commands used (paid investigation is explicit):

```sh
python scripts/investigate_missing_link.py --repo un33k/python-slugify --issue https://github.com/bellroy/lesswrong/issues/519 --use-ai --report data/positive.json
python scripts/investigate_missing_link.py --repo un33k/python-slugify --issue https://github.com/w3c/csswg-drafts/issues/4406 --use-ai --report data/rejection.json
python scripts/run_missing_link_example.py --match-id 3640f45126beeee67724cd8efa2269fc --entrypoint bridge/tests/test_meta_description_adapter.py --approve --report data/example.json
python scripts/run_missing_link_example.py --match-id 3640f45126beeee67724cd8efa2269fc --entrypoint reviewed_tests/check_meta_description.py --reviewed-test examples/missing-link/check_meta_description.py --approve --report data/ablation.json
```

IDs and model outputs can differ on a new run. The independent test script expects
the recorded initial/refined example module names; inspect any new bridge before
selecting its entry point. Runtime downloads, local reports, credentials and the
account database are ignored by Git. Nothing was published to third-party projects.

## Post-merge acceptance check — 2026-09-30

PR #7 was merged, and the local checkout was fast-forwarded to `main` commit
`bf04cd4`. Its reviewed head passed all four Windows/Linux, Python 3.10/3.13 CI
jobs. The server was restarted without interrupting an active investigation.

- Read-only browser verification of the real saved results: 15 cards, 15 ZIP
  export links, no JavaScript errors, no mutation requests and no mobile overflow.
- Local suite: **171 tests passed**, including an additional browser-to-HTTP-to-
  service-to-SQLite acceptance test. This uses fictional public source fixtures
  and a temporary account database, not new AI analysis or the user's database.
  It covers source review, discovery, correction, invalidation, stale execution
  rejection, a distinct reevaluation and persistence after service restart.
- The acceptance test's fixed example also ran through the actual WASI endpoint;
  its receipt survived restart and appeared in the browser. Its successful exit
  does not establish the original request's criteria or any target integration.
- Repeated WASI boundary probes passed after startup hardening: only
  `PYTHONHOME` and `PYTHONDONTWRITEBYTECODE` are supplied, no project startup
  `PYTHONPATH`, no inherited credentials, host filesystem/network/native
  process access, and enforced fuel/memory/output bounds. Separate regression
  coverage verifies that project startup hooks and stdlib shadows do not run.
- Effective capability changes now invalidate previous matches and block old
  examples. The UI explains interpretation changes as well as source/discussion
  changes; immutable issue IDs preserve freshness across repository renames.

No additional paid API calls were made for these acceptance checks. The
[README screenshot](screenshots/missing-link.png) uses the built-in synthetic
demo and deliberately shows no fabricated positive result. The live account
screenshot stays in ignored local data, not the repository.

Release preparation is documented in the 3.1.0 development changelog. Publishing
a tag/release and testing a real application's integration are separate next
steps; neither is implied by this local acceptance pass.

## Identity-stop diagnostics — 2026-10-03 (offline)

This is a no-spend fix following the [stopped contract-21 continuation](missing-link-contract21-continuation-2026-10-02.md),
not another live AI evaluation. The older recorded Babel error cannot be
retrospectively classified; its unknown charged call stays unknown.

The CLI guard still executes one `gh auth status --json hosts` read with a
ten-second timeout. `app.py` retains the same five-second success cache, forced
checks, account-selected history and lock. The runner is injected into the new
standalone `github_cli.py`; imports do not contact GitHub, select an account,
open a database, start a thread or load an AI provider.

Paused jobs now expose the optional `error_diagnostic` object alongside the
existing readable `error` string. Its category is `github_identity`:

| Code | What the current failure establishes |
| --- | --- |
| `github_identity_cli_missing` | The CLI executable is unavailable. |
| `github_identity_cli_timeout` | The ten-second CLI check timed out; `timeout_seconds` is 10. |
| `github_identity_cli_error` | The identity subprocess could not run because of an OS error. |
| `github_identity_cli_failed` | The CLI returned a nonzero exit, without proof of token expiration or account change. |
| `github_identity_invalid_response` | JSON or active-login structure is invalid; identity remains unverified. |
| `github_identity_unavailable` | No verified active GitHub login was supplied. |
| `github_identity_ambiguous` | Multiple verified active GitHub logins were supplied. |
| `github_identity_changed` | Exactly one verified active login differs from the expected identity. |
| `github_identity_unclassified` | A legacy/injected verifier raised an account-related error without a typed cause. |

The fields use fixed bounded values, not CLI stdout/stderr, credentials, response
bodies or arbitrary exception details. A failed check does not advance the
success cache or authorize further processing. A typed mismatch cannot become
a candidate-local validation failure or a malformed-provider-output error.
Existing `app.GitHubCLIError`, `app.ActiveAccountChangedError` and
`app.GitHubRateLimitError` names remain aliases for compatibility. The service's
own mismatch now raises the shared runtime exception instead of `ValueError`;
HTTP handling and account isolation remain intact.

The current diagnostic persists through restart; explicit resume or
cancellation clears it, just as it clears/replaces the current error. This is
not a new immutable per-attempt history. Existing job JSON needs no migration,
and old records without diagnostics are not rewritten. No automatic retry,
resume, reservation refund, budget reset or credentials change is introduced.
Incomplete streams retain their reserved unknown outcome; completed receipts
and JSON remain auditable without being accepted as analysis after an identity
failure.

### Polling while identity remains unavailable

The PR review found that the blanket API identity guard returned HTTP 409 before
the saved stop could be read. `missing_link/polling.py` now handles just
`GET /api/missing-link`: a typed identity-verification outage can return HTTP 200
with `diagnostic_only: true`, `identity_verified: false` and
`actions_available: false`. The current poll's `identity_diagnostic` is distinct
from each job's persisted `error_diagnostic`.

This view requires a service already bound to the expected account and database
during verified operation in this process. It checks the database's identity in
the same read-only SQLite transaction as the job read. It exposes only opaque
job IDs, paused status and fixed, allowlisted identity-stop messages/codes, plus
the previously bound account and current verification failure. It never creates
a Store/service/provider or reconciles worker leases. Source, input, results,
provider configuration, checkpoints, receipts and arbitrary stored error text
are not returned. Old untyped stops are not retroactively classified.

No existing binding, missing/mismatched storage, confirmed account changes,
ambiguous identities and unclassified failures still deny the poll. Cold startup
does not use this view to bypass identity verification. All mutations, exports,
packages, source-context downloads and other APIs keep their original guard.

The UI replaces full evidence, including focused edit forms, with a clearly
restricted diagnostic view; actions/downloads are unavailable. It polls every
15 seconds while this view is active and restores full state only after the
normal checks succeed. Capability review and AI opt-in are cleared; recovery
does not resume a job or make a provider request.

### Identity failures are not endpoint failures

The second PR review found another P1: introducing a separate typed identity
exception left six existing endpoint-fallback catches unaware of that type.
An unavailable/ambiguous identity or CLI timeout could therefore become a
failed repository lookup and persist a false `inactive` alias. That alias could
then suppress resolution after recovery. These were reproducible regressions,
not an extension of the discovery/parser contract.

All six catches now propagate `GitHubAccountVerificationError` before the
generic `GitHubCLIError` fallback: registry reconciliation, safe traffic reads,
parallel traffic/event collection and both automatic-collector stages. The
same exception instance/code reaches the caller; no new exception hierarchy or
retry policy is introduced. Identity failure cannot become empty/partial
endpoint data, cached traffic, a newly written event or a failed-lookup alias.
The collector does not count the failed repository as completed or advance to
another repository/stage; it retains its existing failed-run diagnostic.

Already submitted bounded requests may finish. Previously committed, verified
registry/history work is not rolled back. Ordinary endpoint errors still have
the existing defaults/partial-result behavior, and rate-limit handling remains
unchanged. Historical aliases/errors are not retroactively repaired or relabeled.

Validation: **848 tests passed** with fake HTTP/CLI replies and owned temporary
databases. Target-error, partial-stream, post-terminal-response, restart, explicit
fixture resume/cancellation, cache and malformed-output regressions pass. Ten
real-handler HTTP regressions additionally cover persistent failed checks,
binding/identity mismatch, mutation/download denial, recovery, redaction and
byte-identical DB/unchanged reservations. Two browser regressions cover evidence
replacement, disabled actions, continued polling and recovery without POSTs.
A separate browser smoke used the actual HTTP route with a fictional account,
temporary database and injected failed verifier; no live credentials/provider.
Nine additional regressions cover all seven typed identity categories across
the six fallback boundaries, unchanged owned history, resolution after recovery,
prior successful alias commits, stopped collection, retained exception identity,
no endpoint subprocess after guard failure and ordinary-error compatibility.
The alias regression first failed on the reviewed HEAD for all seven categories
and passed after the localized catch correction.
Windows installation includes the standalone module; isolated installed imports and a
simulated identity check passed. These startup/installation checks did not start
a production server or invoke a paid provider.

A read-only audit of the unchanged running server and saved live cohort passed:
old job/match/snapshot/report hashes, pinned exports and reservation rows remain
unchanged, with no queued/running job. The real allowance remains **328
reservations / USD 5.1150975 of USD 10**. This improves future diagnostic evidence;
it does not identify the earlier outage's cause, improve connection resilience,
complete the remaining cohort or prove better discovery quality.

## Provider transport and HTTP observer diagnostics — 3 October 2026

This separate no-spend correction follows merged PR #38. It does not resume any
live job, replace an old report or explain either historical unknown outcome.

`missing_link/provider_errors.py` defines fixed global transport stops. The job's
additive `error_diagnostic` contains category `ai_transport`, a bounded code,
interpretation phase, captured call/attempt identity, `reservation_retained=true`
and `response_receipt=unavailable` (no complete model response receipt, not a
claim that the HTTP request never reached the provider). An observed HTTP error
adds only its numeric status. Raw exception reasons, headers, bodies, SSE content,
prompts and keys are not copied into diagnostics.

| Codes | Meaning |
| --- | --- |
| `ai_transport_timeout` | Direct or wrapped socket timeout. |
| `ai_transport_network_error`, `ai_transport_io_error` | Network failure versus other transport I/O failure; no invented DNS/VPN cause. |
| `ai_transport_http_error`, `ai_transport_redirect` | Numeric HTTP failure or locally denied redirect. |
| `ai_transport_invalid_json`, `ai_transport_invalid_response`, `ai_transport_protocol_error` | Invalid transport JSON, non-object envelope or another bounded protocol failure. |
| `ai_transport_size_exceeded`, `ai_stream_deadline_exceeded` | Existing response/stream size or time bound reached. |
| `ai_stream_invalid_event`, `ai_stream_missing_terminal` | Malformed SSE event or stream without a terminal response. |

These failures stop the job before another candidate/call, keep charged unknown
attempts and do not fabricate usage, terminal traces or accepted JSON. They are
not `CandidateValidationError`: a received completed model answer still follows
the existing refusal/shape/semantic validation and output-audit contracts.
Cancellation and typed GitHub identity failures retain priority at partial-frame
checkpoints; completed JSON remains auditable before a post-terminal stop.
Limits remain 55 seconds per provider socket, 240 seconds per stream,
512,000 bytes per response/frame and 8,000,000 aggregate SSE bytes. Model,
schema, packing, budgets, automatic-retry policy and analysis contract 21 do not
change. This is observability, not a network-resilience guarantee.

`scripts/investigate_missing_link.py` remains explicitly opt-in and delegates
observation to `missing_link/investigation.py`. Its report path must be new; it
is created before mutation and updated atomically. On GET failure it retains
the known job ID and last observed state, returns nonzero and does not cancel,
resume or start a replacement. A failed start acknowledgement is also unknown:
the request may have started a backend job, so it is never repeated implicitly.
An explicit resume's original ID is retained even if its acknowledgement fails.
Observer diagnostics distinguish timeout, network/I/O, HTTP status, protocol,
identity-only polling, missing job, report-write failure and the job deadline.
No raw HTTP/exception body is added to the failure record. If report persistence
itself fails, the known ID and safe diagnostic remain in stdout.

The existing 30-second socket and 15-minute job deadline are not increased. On
the deadline only, cancellation is requested once. `acknowledged` means the local
API returned the correct cancelled job, **not** that an in-flight worker/provider
call has exited or that its reservation was refunded. Failure/unconfirmed reply
is not called successful cancellation. Export failure retains terminal job state
and already received exports without re-running analysis. The cohort wrapper must
stop on a nonzero driver result and separately inspect the known backend job.

Fixtures use mocked provider HTTP, fictional owned stores and one actual
loopback HTTP test server; no paid model, real account job or acquired-code
execution is invoked. Provider failures were reproduced as untyped diagnostics
before the fix. Regression coverage includes per-call reservation retention,
restart, no later candidate, safe messages, partial-stream cancellation/identity
priority, report ownership, persisted IDs, ambiguous POST outcome, GET failure,
deadline cancellation and partial exports. Historical live samples are still
incomplete; the nine unstarted repositories require a separately frozen segment.

Final local validation: **871 tests pass**, including the 23 new provider,
observer and cancellation regressions and the existing browser/account/history
suite. Source and installed driver `--help` and isolated installed imports pass.
A read-only before/after check preserves all 12 real Missing Link table hashes
and all 64 frozen JSON report hashes. The ledger remains **328 reservations /
USD 5.1150975 of USD 10**, with zero queued/running jobs. No production server was
started, and no real job was resumed/cancelled or model call made by this work.
