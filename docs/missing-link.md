# Missing Link

Missing Link connects a publicly expressed problem to a product, subsystem or
mechanism in a selected **public** repository. Traffic and popularity are not
compatibility inputs. It produces an inspectable proposal, not an adoption forecast.

## Use it

1. Start RepoTraction normally and open **Missing Link** (not synthetic demo).
2. Enter `OWNER/REPO` or choose a public repository from your account.
3. Select **Analyze repository**. Read the pinned revision, source coverage,
   candidate mechanisms, dependencies and test references. “Referenced” does
   not mean those tests have run. Correct interpretations where necessary.
4. Explicitly check the capability-review box. Supply a public issue URL or
   leave it empty to discover candidates. A problem-oriented query is optional;
   otherwise searches derive from reviewed/enriched capability terms.
5. With a configured provider, opt in to AI interpretation. Without one, expect
   retrieval candidates marked **Needs investigation**, not alleged matches.
6. Inspect the problem, selected capability, hard constraints, obstacles and
   bridge. Download a handoff JSON or reproducible inspection ZIP. Record human
   feedback separately from source evidence.

The UI's review checkbox is a workflow aid, not a security permission. Backend
public-source enforcement, identity checks, budgets and package safety do not
depend on trusting that checkbox.

## Coding-agent mode without a provider

After evaluating a selected issue, expand **Use a coding agent without configuring
a provider** in the jobs section. Download that job's source context. It includes
the acquired source/discussion, coverage, source IDs and the analysis contract.

Ask the agent to extract the request **before considering the repository**, then
assess compatibility and the smallest bridge. Import the resulting JSON for that
job (maximum 480 KB). Source IDs and verbatim demand quotes are checked; missing
mandatory assessments become unknown, hard conflicts become rejection. Imported
reasoning is attributed to the coding agent, not to original source authors.
An importer cannot verify semantic truth merely because a citation exists.

Each context lists discussion indexes. The UI imports the first (`"0"`) discussion;
for another, use the API envelope `{job_id, discussion_index, analysis}`. Returned
requirement IDs are normalized to `r0`, `r1`, etc. Compatibility checks refer to
these IDs. Evidence IDs are `q0` (title/body), `q1…` (comments), `t0…` (timeline),
`file:PATH` (acquired source), and `cINDEX:OFFSET` (capability references).
Use `file:PATH#LSTART-LEND` for precise source spans of up to 60 lines. These
validated spans enter the proof package; a whole-file reference is a bounded
excerpt plus a pinned link, not an offline copy of the entire implementation.

The [reviewed examples](../examples/missing-link/README.md) demonstrate this on
real public discussions. They are not auto-loaded or a hardcoded discovery engine.
The provider can enrich structural capabilities; coding-agent imports currently
evaluate existing candidates rather than inventing additional capability IDs.

## Optional interpretation provider

Only standard-library HTTP is used. Configure an OpenAI-compatible chat completion
endpoint and model **before starting the server**. For a local server, for example:

```powershell
$env:REPOTRACTION_AI_URL = "http://127.0.0.1:11434/v1"
$env:REPOTRACTION_AI_MODEL = "YOUR_INSTALLED_MODEL"
$env:REPOTRACTION_AI_MAX_CALLS = "8"
python app.py --no-open
```

These settings do not install/download a model or start a model service. The
endpoint must support JSON chat responses, `max_tokens` and `response_format`.
The UI checkbox must still be enabled for each AI-backed job. Configure the model's
context size to accommodate the bounded sources, or choose a smaller repository.

For a remote HTTPS endpoint, these **additional** settings are mandatory:

| Variable | Meaning |
| --- | --- |
| `REPOTRACTION_AI_ALLOW_REMOTE=1` | Explicitly permit public context to leave the machine. |
| `REPOTRACTION_AI_KEY` | Optional provider credential. Kept in process memory; never sent to the frontend or stored with evidence. |
| `REPOTRACTION_AI_MAX_COST_USD` | Per-job conservative reservation ceiling. |
| `REPOTRACTION_AI_INPUT_USD_PER_MILLION` | User-configured conservative price for input tokens. |
| `REPOTRACTION_AI_OUTPUT_USD_PER_MILLION` | User-configured conservative price for output tokens. |
| `REPOTRACTION_AI_MAX_CALLS` | Per-job call ceiling (default 8). |

Use your provider's current prices/limits, not example guesses. Prompts reserve
a conservative byte-per-token input bound plus framing allowance and the output
token cap. Failed calls retain their reservation. When token usage is reported,
it is recorded separately at configured prices. This is **not** a provider invoice
or a substitute for provider-side billing limits. Unknown usage is not called zero.
Redirects and credentials embedded in endpoint URLs are rejected.

Outbound context is displayed in the UI: selected public source snippets and
signatures, public issue/comments/timeline, requirements, and compatibility
results. No GitHub tokens, private sources or traffic/account history enter prompts.
API keys must not be pasted into capability corrections or issue text. Credential
shape redaction is defense in depth, not a universal secret detector.

Without a configured provider the rest of RepoTraction works normally. No paid
provider call was made during this implementation's verification; local HTTP
protocol tests use explicitly fictional responses.

## Jobs, persistence and updates

One investigation runs at a time per account. Defaults are 80 GitHub requests,
5 evaluated candidates and 24 source files; the UI can choose up to 200 requests
and 10 candidates. Broad retrieval and deeper full-context evaluation are separate.
GitHub's [search API](https://docs.github.com/en/rest/search/search) limits result
sets to 1,000 and can report incomplete results. Missing Link also limits pages
and records queries, counts and incompleteness. No-results is not no-demand.
An OS-released worker lease also enforces this across two RepoTraction processes
sharing the same account database. Opening another instance does not pause a
healthy job. Cancellation is persisted so the other instance can request it too.

**Cancel** stops new calls at checkpoints; an in-flight GitHub/provider read may
finish first. **Resume** retains completed checkpoints and used budgets; increasing
the GitHub cap requires an explicit higher selection. An upstream rate limit
pauses the job without automatic retry. Server restarts pause unfinished jobs,
not restart them silently. AI-budget exhaustion requires an explicit configuration
change/restart or another reviewed workflow, not a hidden unlimited retry.

Tables prefixed `ml_` live in the existing per-account SQLite database. A service
captures that account/database path; account switches stop the old account's work.
Numeric GitHub repository IDs and stable source-path/symbol capability IDs support
renames/revision changes. Sources/permalinks remain pinned to exact commits.
Screened unchanged blobs are reused; the default branch head is checked anew on
a new job. Old discussion snapshots and rejection reasons remain available.

Updates are **operator-triggered**: start a new analysis/evaluation when you want
to refresh. A changed revision or newly acquired discussion fingerprint marks old
results stale, including before a replacement evaluation is completed. There is
no background Missing Link crawler. Old capability corrections require review
at a new revision. Maintainer feedback does not overwrite original evidence.

Independent unresolved requests blocked by the same normalized requirement text
can be grouped as extension leads. This first grouping is deliberately narrow;
it does not claim semantic clustering or predict adoption. Superseded/historical
results are not current opportunities.

## Coverage and trust boundaries

- Python functions/classes are parsed with `ast`; source snippets, signatures,
  imports/calls and test references are structural evidence, not behavior proofs.
- JS/TS uses a partial declaration scan, not a parser/typechecker. Other languages
  currently contribute documentation/manifests only. There is no universal code
  understanding claim. Large/sensitive/binary/generated/unsupported files are
  excluded and coverage/truncated-tree flags stay visible.
- Issue comments and timeline are paginated within bounds. Cross-referenced
  discussions are **not** followed: their presence marks context incomplete.
  Open/closed state alone cannot establish resolution; bots, duplicates and
  resolved needs must not become qualified opportunities.
- AI interprets; ordinary code enforces identities, budgets, source references,
  mandatory-constraint rules, storage and safe packages. Neither citations nor
  a high lexical overlap establish successful integration.
- Public files/discussions/model outputs are untrusted data and cannot authorize
  execution, credentials, network changes or publication. No third-party write
  endpoint exists in Missing Link.

## Proof packages and current limitations

ZIPs contain `HANDOFF.md`, `handoff.json`, a SHA256 manifest, bounded source
snippets, available license text and proposed bridge files. Revision agreement,
portable relative paths, case-insensitive collisions, symlinks and sizes are
checked. Criteria come from the original demand; new assumptions remain separate.
If acquired discussion context makes the ZIP exceed its bounds, the match is
retained with an explicit packaging obstacle; JSON handoff/source context remain
available. This is not an excuse to bypass path, public-source or credential checks.

All packages say **NOT EXECUTED**. A genuinely isolated proof backend is not yet
implemented/configured; a subprocess or the mere presence of Docker CLI is not
isolation. Do not run acquired/generated code in the account/credential environment.
The environment used for this change had Docker CLI but no reachable engine.
Installing/starting Docker is not performed automatically.

The three real cases test source-aware usefulness, not general discovery accuracy:
Unicode filename adaptation, independent prose truncation, and incompatible CSS
layout. The cases are old; maintainer interest/current deployment needs review.
No successful target integration, functional ablation run, paid-provider quality
evaluation or fresh user-demand volume has been established.

## Verification and development

```sh
python -m unittest discover -s tests -v
python app.py --help
```

Optional browser regressions run if Playwright and Chromium are available;
otherwise they skip. They use fixture APIs, never GitHub/AI. On a running local
server with acquired case results, the read-only browser smoke check is:

```sh
python scripts/verify_missing_link.py --repo un33k/python-slugify
```

Windows install/update can be tested without altering a real installation:

```powershell
.\install.ps1 -NoShortcut -Destination C:\PATH\TO\TEMP\RepoTraction
```

CI runs core tests on Linux/Windows, Python 3.10/3.13, checks startup help and
Windows install/update preservation. Optional browser dependencies are not added
to the application requirements. Local checks do not preempt the actual CI result.

## Local endpoints

```text
GET  /api/missing-link
POST /api/missing-link/jobs       {repo, action?, issue_url?, query?, max_requests?, max_candidates?, use_ai?}
POST /api/missing-link/cancel     {job_id}
POST /api/missing-link/resume     {job_id, max_requests?}
POST /api/missing-link/capability {repo, capability_id, correction}
POST /api/missing-link/feedback   {match_id, decision, note}
GET  /api/missing-link/context?job_id=ID
POST /api/missing-link/analysis   {job_id, discussion_index?, analysis}
GET  /api/missing-link/export?match_id=ID
GET  /api/missing-link/package?match_id=ID
```

POSTs require bounded JSON and the local same-origin header. Repository content,
models and imported analysis cannot expand these permissions. The analytics JSON
export is still not a complete/restorable backup; back up the SQLite database to
retain Missing Link jobs, corrections and history too.
