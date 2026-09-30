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
