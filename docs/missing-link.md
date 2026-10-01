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

### How automatic discovery chooses its sample

Automatic queries use short mechanism/problem phrases, removing the source
package name rather than searching for existing references to it. Automatic
queries may also use specific single-word mechanisms such as `pagination` or
`backpressure`; a second word is not mandatory. Contextual phrases are preferred
when available, while package names and generic helpers such as `main`/`run`
cannot create queries on their own. Fragmented terms are checked again after
joining so they cannot reconstruct the canonical repository/package name.
Unreviewed README/manifest summaries do not create implementation queries. Up to three
queries cover distinct source modules within the same source/review priority
tier where possible; diversity cannot promote weaker docs over reviewed code.
Unreviewed declaration
filler is skipped rather than promoted for diversity; a bare API constructor
name does not establish problem-oriented terms. They target open issues
in title/body and exclude the source repository; a custom query or specific
issue still allows closed discussions and same-project work. Open issue state
is a retrieval hint, not proof that the request remains unresolved.

Within the existing two-page-per-query budget, selection favors external open
issues, then balances projects and queries before title-term overlap and GitHub
result position. A later relevant hit can displace an early hit; no popularity
metric enters this ranking. This deterministic lexical heuristic is not semantic
relevance, novelty, or a probability of adoption. Queries, page limits, canonical
candidate URLs, query attribution, upstream ranks and selection order are saved
in `job.result.search`. Resuming keeps the selected checkpoint batch unchanged.
Empty results and excluded candidates do not demonstrate absence of demand.

After reading each selected discussion, fully automatic discovery applies narrow
filename/code-dump, exam-preparation-manual, reference-only-body and automated-
author hints based on acquired bot metadata. Mentioning generated plans, automation
or a robot emoji does not establish bot authorship or trigger that early skip;
the same metadata-only bot distinction applies during downstream qualification.
Explicit generated-artifact labels/headings remain content/authority review hints,
not bot identity or maintainer approval. Neutral requests about generated content
do not trigger them.
A subsequent discussion keeps the candidate available for review.
Skipped candidates remain
in `job.result.candidate_skips`, with policy, reason, context completeness and
`proves_absence_of_demand=false`. They receive no request/match AI calls and are
**not compatibility rejections**. The selected sample is not refilled or reranked.
An explicit issue URL or custom query bypasses this screening. Request-like prose
keeps a non-automated prose candidate eligible; this is not a general demand
classifier. Language names such as JavaScript/TypeScript remain whole search terms.

Python source acquisition follows top-level imports in already acquired package
initializers to eligible local modules (including `src` layouts), within the same
file/read/byte limits. Dotted imports prioritize eligible intermediate package
initializers before the final module; missing namespace-package initializers are
not invented. These static hints are recorded with omitted targets; they
keep same-package absolute imports in the acquired initializer's flat or `src`
layout rather than following an unrelated same-name package in another tree, and
are not verified exports or dependency closure. Declaration sampling prioritizes
public top-level classes/functions before their nested mechanisms and balances
files within source-role tiers so an early
large helper class cannot consume all 100 capability slots. Dynamic imports,
conditional exports and oversized/excluded modules remain limitations. JS/TS
sampling follows literal relative re-exports and package entrypoint paths, including
eligible `.js` to `.ts` source counterparts. These hints only reorder safety-filtered
file attempts; cycles do not duplicate reads or increase the file/read/byte budget.
They are not full export resolution, dependency closure or a typecheck. Their
recorded paths, omissions and bounded-scan completeness remain visible in coverage.

Technical compatibility and useful partial contribution are separate. A rejected
request can retain supported requirement IDs alongside conflicts and unknowns;
**partial support does not satisfy the whole request or unblock a mandatory
conflict**. It is not follow-up-ready. Proposed adapter code is new work, not
evidence that the selected interface already implements that behavior.

Extraction asks for independently checkable mandatory and optional behaviors.
Constraint hints share the demand catalog's conservative sentence boundaries,
so a valid constraint sentence need not quote a following explanation. Separate
constraint sentences on one line remain independent review items; omitted,
truncated or uncertain-authority constraints still prevent qualification.
A bounded optional-field review flags omitted/bundled TypeScript-style fields
such as `strip_ansi?: boolean`. It never adds a requirement or awards support.
Provider hints are packed with the supplied discussion excerpts under the same
byte budget; omitted comments cannot reappear through these hints. Overflow is
explicit, and final validation still checks the full acquired discussion for
unrepresented fields, so a partial prompt cannot silently clear them.
The identifier must be represented separately, and uncertain source authority
still requires review. Longer identifiers such as `colorMode` do not also count
as `mode`; explicitly naming both still flags a bundled requirement. An optional
API argument does not by itself make the requested implementation optional.
A supported optional mechanism can be a
partial contribution while mandatory conflicts still reject the full request.

Each check also records `contribution`: `existing_behavior`, `scope_compatible`
or `not_demonstrated`. A compatible boundary (for example keeping capture APIs
unchanged) can satisfy a constraint but is not a reusable behavior. Qualification
counts it separately in `scope_compatible_requirement_ids`, not in supported
requirements. A scope-only candidate cannot qualify as a useful contribution.
Recurring gaps without any demonstrated reusable behavior cannot form extension
groups either; repeated passive scope compatibility is not an extension lead.
An `existing_behavior` check must cite a supplied implementation path, not merely
a README, test, fixture, benchmark or `.d.ts` declaration. Conventional standalone
`test`/`tests`/`spec`/`specs` filenames with supported Python/JS/TS extensions
remain test references even at the repository root; they cannot satisfy the
implementation preflight or independently substantiate existing behavior.
Path membership still does not validate the semantic reasoning or certify execution.
Old imported checks without this field default to unknown, not affirmative support.
The deterministic API-preservation override only recognizes whole, preservation-
only extracted requirements. Compound requirements such as "format bytes without
changing the public API" retain source-supported functional behavior. A passive
clause in a larger quotation cannot relabel a functional extracted requirement.

Independent demand extraction does not receive candidate source or target files.
After extraction, prior-reference review reads a pinned public target sample:
up to two root manifests and two discussion-cited Python/JS/TS paths, at most
four file attempts through the same safety filters. Target excerpts are capped at
32,768 characters per file; truncation is recorded. `target:PATH` evidence is
reference-only and cannot satisfy a source implementation check. Literal dependency
fields, static Python imports and package/import aliases provide review hints,
not adoption or endorsement evidence. Different discussions do not reuse each
other's cited-file sample. Revision, fingerprints, coverage and acquired files
are saved with matches and included in handoffs. No target code is executed.
Only numeric `qN`/`tN` IDs count as discussion/timeline. Reference-only target
files are not head/tail-shortened as comments and cannot make an otherwise complete
discussion appear incomplete. Actual discussion and selected source definitions
are supplied before target references; omitted target context is reported separately.
Paths in same-target GitHub blob links are sampled from the target's current
pinned default-branch tree, not automatically from the linked historical revision.

Missing target context and malformed/truncated acquired manifests block follow-up
qualification. An absence of references in this bounded sample never proves
novelty. Python 3.11+ uses the built-in [TOML parser](https://docs.python.org/3/library/tomllib.html).
On Python 3.10, [Tomli](https://github.com/hukkin/tomli) is an optional backport:
`python -m pip install tomli`. It is never installed implicitly; without it, TOML
review is explicitly incomplete, not negative evidence. Core analytics do not
require this optional dependency.

Python distribution dependency names treat runs of hyphens, dots and underscores
as equivalent when checking declarations and locating their original evidence.
For example, `zope-interface` also matches `zope_interface`; npm dependency names
retain exact separator spellings. These remain prior-reference hints, not proof
of adoption.

Requirements include/constraint directives (`-r`, `-c`, `--requirement`,
`--constraint`) mark dependency review incomplete: included files are not acquired
automatically. Poetry group dependency tables are inspected, including optional
groups; malformed group layouts block complete review. Same-target blob URLs
with slash-containing refs are matched against safe path suffixes in the current
pinned tree. Ambiguous suffixes may sample multiple files within the existing
two-cited-file limit; this is not historical ref resolution or complete coverage.

Poetry dependency values receive bounded structural validation in the main table
and groups, including scalar types, supported table fields and table alternatives.
Malformed or unsupported values block review instead of generating references.
This does not validate version expressions or prove installation. Supported shapes
follow the [Poetry dependency specification](https://python-poetry.org/docs/dependency-specification/).

Contract 14 marks earlier results as historical, preserving their original
interpretations and exports. There is no automatic migration or paid reevaluation.

An empty body or a body containing only example/reference links cannot establish
independent adoption demand from its title. Markdown link/image labels and HTML
anchor labels are references, not request prose; surrounding request prose is
retained. Extension groups also exclude demand with qualification blockers,
including old activity or unknown/invalid recency. Follow-up qualification requires
valid snapshot collection/update timestamps. Issue activity at least 365 days old
requires current-demand review; this conservative threshold is not proof of
resolution or project abandonment. Activity age is calculated against the saved
collection time, not today's clock, and is reproducible in historical exports.
An open/non-archived target alone does not verify runtime versions, acceptance
criteria, current demand, integration or adoption.

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

Only standard-library HTTP is used. Configure a provider **before starting the
server**, either in the process environment or by copying `.env.example` to the
ignored project-root `.env`. The reader accepts only `REPOTRACTION_AI_*`
assignments, never evaluates shell/interpolation, and never returns the key to
the browser. Process environment overrides the file. Never commit `.env`.
For a local OpenAI-compatible chat server, for example:

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
| `REPOTRACTION_AI_TOTAL_BUDGET_USD` | Positive allowance shared across jobs/restarts in this account database; required for paid remote calls. |
| `REPOTRACTION_AI_BUDGET_ID` | Stable allowance identifier; changing it starts a different allowance. |
| `REPOTRACTION_AI_API_KIND` | `chat` (compatible default) or `responses`. |
| `REPOTRACTION_AI_RESPONSE_FORMAT` | `json_schema` (closed strict schema) or `json_object` (locally validated). |
| `REPOTRACTION_AI_REASONING_EFFORT` | Responses reasoning setting, e.g. `medium`. |
| `REPOTRACTION_AI_STREAMING=1` | Responses SSE; only a complete terminal response is accepted, not partial deltas. |
| `REPOTRACTION_AI_MAX_PROMPT_BYTES` | Serialized request limit including framing/schema (default 180000). |
| `REPOTRACTION_AI_MAX_OUTPUT_TOKENS` | Output/reasoning cap (default 12000). |

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
call starts merely by opening the dashboard. Real API checks are separate from
fictional protocol fixtures in [the API verification report](missing-link-api-verification.md).

The sample `.env.example` selects OpenAI **gpt-6-luna**, Responses, strict JSON
schema and streaming. Budget defaults are zero (disabled): choose explicit
positive per-job and total ceilings before enabling paid calls. Sample prices
were checked against [the model documentation](https://developers.openai.com/api/docs/models/gpt-6-luna)
on 2026-09-30; verify them again for your model/account. Chat-server configuration
does not inherit the sample's Responses-only settings unless explicitly set.

Request extraction sees only the public discussion, not the candidate repository.
Context packing preserves recent comments/resolution evidence, selects actual
implementation spans, and records omitted/shortened sources. Incomplete
discussion coverage cannot qualify a positive match. Citations must refer to
lines actually supplied in that phase; fully visible long spans are normalized
into bounded evidence chunks. Refused, malformed, partial or incomplete output
does not become a match. Provider identity and request hashes stay in the job.

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

Invalid candidate analysis (for example an unavailable demand-span ID or
unsafe proposed artifact) is recorded in `result.candidate_errors`; other selected
candidates continue. `status=completed` means processing ended, **not** that all
candidates succeeded: `result.partial=true` and the visible warning identify
partial results. Reservations remain charged. Resume after a global pause skips
these invalid candidates rather than silently retrying them; a fresh explicit
investigation is needed after review. Authentication, transport errors, budget
exhaustion and cancellation still stop/pause the whole job. The investigation
script saves available matches but returns a nonzero exit code for partial jobs.

Tables prefixed `ml_` live in the existing per-account SQLite database. A service
captures that account/database path; account switches stop the old account's work.
Numeric GitHub repository IDs and stable source-path/symbol capability IDs support
renames/revision changes. The result filter uses the selected repository's numeric
ID, not the historical name: a rename retains its matches, and reusing an old name
for another repository cannot mix their histories. Sources/permalinks remain pinned to exact commits.
Screened unchanged blobs are reused; the default branch head is checked anew on
a new job. Old discussion snapshots and rejection reasons remain available.

Updates are **operator-triggered**: start a new analysis/evaluation when you want
to refresh. A changed revision, effective capability interpretation or newly acquired discussion fingerprint marks old
results stale, including before a replacement evaluation is completed. There is
no background Missing Link crawler. Old capability corrections require review
at a new revision. Maintainer feedback does not overwrite original evidence.
Refreshes atomically preserve feedback and supersession. Each result keeps its
exact reproduction snapshot, independent of the list of recent jobs. Resuming
with another provider/model/contract pauses rather than mixing interpretations.
Analysis contract changes also mark older assessments historical and block
their isolated examples until reevaluation; historical snapshots/exports remain
available and are not silently rewritten as current evidence.
Discussion freshness uses immutable GitHub issue IDs, including older URL-keyed
records after renames. Capability corrections invalidate previous results and
block their isolated examples; reevaluation produces a distinct result while
retaining the original interpretation and feedback. Recovery also runs when an
already-open dashboard discovers that the worker lease is free: abandoned jobs
become paused and require explicit resume, with checkpoints and budgets intact.

Independent unresolved requests blocked by the same normalized requirement text
can be grouped as extension leads. This first grouping is deliberately narrow;
it does not claim semantic clustering or predict adoption. Superseded/historical
results are not current opportunities. Same-project work, existing source
references and package-reference hints do not enter external extension groups.

### Compatibility is not a new discovery

Each result also has a source-derived `discovery_assessment`, separate from its
technical `classification`. It distinguishes same-project work, an existing
repository reference, a package-name hint needing identity/intent review,
empty-body reference notes, non-actionable demand, an incompatible contribution,
retrieval-only resemblance, incomplete qualification and a potential external
connection. Imported/model claims cannot set this assessment; it is recomputed
from acquired discussion and validated checks. Repository IDs preserve the
same-project distinction after a rename when available.

A source mention may be a prior attempt or an explicit refusal, never presumed
endorsement. Ordinary words such as “click” are not treated as package references;
repository URLs and bounded name/code-pattern hints are retained with exact
discussion excerpts. Reference detection scans all acquired discussion regardless
of the eight-excerpt presentation/export cap. Exact repository links take priority
over package-name hints in those excerpts, including links found in later comments;
within each kind the original discovery order is preserved. Total counts and
incomplete excerpt coverage remain explicit. URL detection accepts closing quotes,
Markdown delimiters and terminal sentence punctuation; dotted/extended repository
names such as `words.extra` are not treated as a link to `words`. These are text
heuristics rather than URL-resolution/identity verification, and are non-exhaustive
and can need review.
All-undetermined checks demonstrate no contribution, even if the model proposes
a bridge. Only complete unresolved external demand with supported mandatory
explicit requirements and a positive compatibility class becomes a follow-up lead;
inferred mandatory demand still needs confirmation.
Even then `novelty` stays `unverified`: no name found in bounded context is not
proof that an author has never considered it. Execution, target integration and
adoption need separate verification. The assessment and reference evidence are
visible in cards and preserved in JSON/ZIP handoffs; historical data is not
retroactively relabeled as new evidence.

## Coverage and trust boundaries

Prompt selection prioritizes implementation over documentation, tests and build
helpers (including `winbuild`, `ci_tools` and `_custom_build`). The 30-capability
sample distributes candidates across files; definition chunks are interleaved
before broad file coverage so one large module cannot monopolize the prompt.
Coverage records the selected capability roles and actually supplied source roles
and implementation paths, including an explicit missing-implementation flag.
These are path-based sampling hints, not verified exports or execution evidence.
Comparison packing keeps the root request, then selected implementation definitions
before later discussion. Comments cannot evict already supplied code; omitted later
resolution/constraints still make coverage incomplete and prevent qualification.
If no implementation is supplied, enrichment/comparison fails explicitly before
its provider call or reservation. Documentation, fixtures, benchmarks and `.d.ts`
declarations do not pass that implementation preflight. This is an unavailable
analysis, not a semantic rejection or evidence of absent useful functionality.

Provider schemas are scoped per call: source IDs must be exact keys actually
supplied, and capability/requirement IDs must belong to the selected candidates.
Context packing shares the schema's 400-ID bound, in addition to the byte bound;
ID-limited omissions are counted in coverage and make discussion incomplete.
Repository comparisons reserve ID slots for selected source/support excerpts.
Wider or fabricated line ranges are not offered as valid model outputs. This
scope is checked locally for JSON-mode providers too; inspection/import contracts
still accept precisely validated visible subspans. Provider request requirements
select `citation_id` from a bounded catalogue of exact original discussion spans,
rather than copying quotations. IDs bind source URL, offsets and text; synthetic
omission markers are never evidence. The application supplies the stored quote,
without altering the recorded provider attempt. Catalogue omissions are explicit
and prevent complete-discussion qualification. Its 400-span bound plus disposition
IDs stays below the [Structured Outputs enum limits](https://developers.openai.com/api/docs/guides/structured-outputs).
Oversized enum text is rejected before transport/reservation. Schema membership proves
availability, not semantic support for a claim. Invalid IDs remain failures with
no automatic paid retry. Human/coding-agent imports retain the exact-span validator,
including whitespace-only normalization. Improved real-model discovery success
still requires a separate fresh experiment; the frozen live report is unchanged.

An analysis with no structural capability candidates completes with an empty
list, without constructing an AI schema, calling the provider or reserving cost.
Compatibility comparison also returns no matches when there are no candidates.
This does not prove absence of useful functionality in unsupported/unsampled code;
discovery still needs established search terms or an explicit operator query.

- Source sampling uses a path heuristic to prioritize implementation over build,
  check, benchmark and example infrastructure within the existing file budget.
  Source-role counts and missing-implementation warnings are recorded in coverage.
  Package entrypoints and literal relative JS/TS re-exports, including multiline
  named clauses and multiple compact declarations on the same line, can
  prioritize eligible files without increasing file/read/byte
  budgets. A separate lexical scan excludes comments, quoted strings and template
  literals (including nested interpolations). Unterminated/depth/work-limited regions
  and ambiguous regexp/division contexts make the hint scan explicitly incomplete.
  A bounded delimiter-scope scan excludes nested declarations; malformed or
  depth-limited scopes make the scan incomplete rather than exposing their tail.
  Extensionless hints try eligible `.ts`, `.js`, `.tsx`, `.jsx`, `.mjs` and `.cjs`
  files before directory index variants, with TS/JS first in each tier. Excluded
  files and `.d.ts` declarations are not inferred as implementation targets.
  `export_hints_complete` describes the bounded hint scan, not complete
  JS/TS semantic coverage or verified exports.
  This is not exported-API discovery or proof that the sample represents the
  entire product. Unsupported/native source still remains outside the analyzer.
- Imported requirement quotations may differ only in whitespace; the stored quote is
  recovered from one contiguous original source span. Paraphrases, changed
  punctuation and quotes from omitted context are not accepted.
- A bounded, non-exhaustive English constraint-hint scan examines acquired
  discussion before prompt shortening. Selected middle excerpts preserve likely
  dependency/runtime prohibitions; omissions and truncation remain explicit.
  `request.constraint_review` retains authorship, exact spans, represented
  requirement IDs and qualification blockers. Unrepresented, truncated or
  authority-uncertain hints prevent a qualified positive. Generated plans are
  not maintainer approval, and the guard does not infer or execute their rules.
  Empty-body reference notes and archived targets also require demand review.
  Absence of a marker is not proof that all constraints were understood; false
  review flags and non-English constraints still require human assessment.
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

Packages still say **NOT EXECUTED**: model/imported claims cannot certify a run.
The optional isolated runner writes separate persistent receipts, shown in result
cards and JSON exports. Exit code zero never promotes compatibility, verifies
original criteria automatically, or claims target integration.

### Optional isolated Python examples without Docker (Windows x64)

```sh
python scripts/bootstrap_missing_link_wasi.py
python scripts/verify_missing_link_wasi.py --report data/wasi-boundary.json
```

Explicit bootstrap downloads pinned Wasmtime 49.0.1 and an
[unofficial CPython WASI 3.14.7 build](https://github.com/brettcannon/cpython-wasi-build),
validates archive SHA256 values and extraction, and never executes project code.
Each asset is staged and checked before publication. Completed installations are
verified against pinned archive contents and reused; archives are cached locally
and their vendor SHA256 is checked on every reuse. A failed second download or
extraction can be retried without replacing the first completed asset. Existing
partial/changed directories are preserved as `NAME.previous-ID` before repair;
an ordinary publication failure restores the previous destination. Unexpected
links/junctions fail closed instead of being followed or deleted.
Downloads stay in ignored `data/wasi-runtime`; no Docker, WSL, VM or system install
is needed. Engine/module hashes are checked again before execution. Review the
runtime supply chain before opting in. Other platforms fail closed for this backend.

After inspecting a pinned match and its files, choose a Python example:

```sh
python scripts/run_missing_link_example.py --match-id ID --entrypoint bridge/test_bridge.py --approve --report data/example.json
```

An independent test can be supplied with `--reviewed-test PATH` and
`--entrypoint reviewed_tests/FILENAME.py`; these are human-owned fixture checks,
not a manual import of analysis. The API never reads arbitrary host paths.
Only pinned public Python source, bridge text and explicitly reviewed tests enter
a fresh temporary directory. The guest sees that copy and Python stdlib only.
Python starts with `-S -P`, without project `PYTHONPATH`: no `sitecustomize`,
`usercustomize` or `.pth` hooks run automatically. The reviewed entrypoint is
started by a trusted bootstrap; project dependencies are then available behind
the standard library rather than shadowing startup modules.

[Wasmtime/WASI capabilities](https://docs.wasmtime.dev/security.html) deny host
paths, inherited guest environment, network and native subprocesses. Limits are
256 MiB guest linear memory, 5 billion fuel units, 15-second WASM timeout,
45-second host watchdog and 32 KiB per output stream. Guest writes are ephemeral.
This is not a VM, a complete host-memory quota or a guarantee against runtime
vulnerabilities. Small pure-Python examples are supported; native extensions,
GUI applications, services and real target integration remain unverified.

The three real cases test source-aware usefulness, not general discovery accuracy:
Unicode filename adaptation, independent prose truncation, and incompatible CSS
layout. The cases are old; maintainer interest/current deployment needs review.
No successful target integration, general provider-quality benchmark or fresh
user-demand volume has been established. Controlled example/ablation results are
reported separately, with their assumptions and limits.

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

The optional `tests/test_missing_link_e2e.py` acceptance test connects the browser
to the actual local HTTP handler, service and temporary SQLite database. GitHub
source acquisition is fictional and AI is off. It covers analysis, reviewed
discovery, maintainer correction, stale-example rejection, reevaluation and
restart persistence. If the pinned WASI runtime is installed, it also runs fixed
fixture code through the actual example endpoint and checks the persisted receipt.
No real account database is modified, and no target integration is claimed.

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
POST /api/missing-link/example    {match_id, entrypoint, approved:true, reviewed_tests?:[{path,content}]}
GET  /api/missing-link/export?match_id=ID
GET  /api/missing-link/package?match_id=ID
```

POSTs require bounded JSON and the local same-origin header. Repository content,
models and imported analysis cannot expand these permissions. The analytics JSON
export is still not a complete/restorable backup; back up the SQLite database to
retain Missing Link jobs, corrections and history too.
