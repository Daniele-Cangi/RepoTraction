# Missing Link second held-out cohort — 30 September 2026

## Frozen protocol

Product baseline: merged `main` **b46cad8**, including PR #16; analysis contract
**7**. This protocol is committed before the first paid investigation. No product,
prompt, provider or sampling changes are allowed during the cohort. Earlier
experiments and failures remain unchanged in their original reports.

The inputs below were selected before viewing any of their issues or search
results. Read-only account history confirms that none was a source repository in
a previous investigation. Metadata-only GitHub preflight confirmed all five
public and non-archived, with their canonical names unchanged.

| Fixed order | Source repository | Domain |
| --- | --- | --- |
| 1 | `yaml/pyyaml` | YAML parsing and serialization |
| 2 | `kurtmckee/feedparser` | RSS/Atom feed parsing |
| 3 | `jd/tenacity` | Retry policies |
| 4 | `agronholm/anyio` | Structured asynchronous concurrency |
| 5 | `sindresorhus/pretty-bytes` | Human-readable byte-size formatting |

This is a small purposive, language-biased exploratory sample: four Python
projects and one JavaScript project. It is not random, representative, or a
precision/recall benchmark. New source inputs do not guarantee that the pipeline
will discover issue URLs absent from earlier experiments; any overlap will be
reported, not replaced.

Run these repository-only inputs sequentially through the live local HTTP API:
`action=discover`, `use_ai=true`, `max_candidates=3`, `max_requests=80`, and empty
issue/query fields. Source acquisition retains the product's 24-file bound.
Automatic queries and candidate ranking remain unchanged. No manual analysis
imports, capability corrections, supplied issues, tailored queries, candidate
replacement, automatic paid retries, bridge execution or third-party publication
are permitted. Record empty, failed, partial and paused outcomes, including
charged validation failures. A transport/authentication failure stops paid cohort
work until its cause is understood; it does not trigger a login or paid retry.

Provider remains OpenAI **gpt-6-luna**, Responses with strict JSON schemas,
medium reasoning, and at most eight calls per job. Configured token estimates
remain $0.10 input / $0.50 output per million tokens, consistent with the
[official model page](https://developers.openai.com/api/docs/models/gpt-6-luna)
checked before this cohort. Per-job reservation ceiling remains **$2**.

The user explicitly raised the existing shared allowance
`missing-link-verification-2026-09-30` from **$2 to $4 total**, not $4 additional.
Before this cohort, conservative reservations were **$1.3833588**, leaving
**$2.6166412**. Keep the same allowance ID, account database and reservation
history; do not reset/refund reservations, enlarge limits further, or create a
new allowance. Unknown usage is not zero. These are application-side estimates,
not a provider invoice or a modification to OpenAI organization/project limits.
The ignored local `.env` and credential must never be committed or included in
reports.

## Assessment and evidence

Save raw reports separately under ignored
`data/second-heldout-discovery-2026-09-30/`. Keep source revisions, acquisition
coverage, queries, selected URLs, job IDs, provider traces, validation errors,
comparison classifications and derived discovery qualification in checkpoints
and reports. Do not overwrite previous cohorts.

After each initial result is saved, independently inspect only its selected
candidates and their pinned code/discussions. Distinguish processing success,
grounded contribution, complete mandatory compatibility, current actionable
demand, prior reference/use, novelty, execution, integration and adoption. A model
label or absent reference is not independent proof of a new useful connection.
Describe rejected false positives and incomplete comparisons alongside any
supported connection. No winner is required or manufactured, and no interface
features or isolated bridges are added during this discovery cohort.

The known root-level `__init__.py` relative-import limitation was intentionally
deferred by the user. Flat/`src` layout selection and public-class sampling fixes
are included in the frozen product baseline. Those static hints still are not a
complete Python import resolver, dependency closure, or execution proof.

## Results

Protocol freeze: **69cda38**, pushed before the first paid job. The five initial
runs finished on 30 September 2026, without changes to that protocol or baseline.

### Outcome

**A new useful external connection is still not demonstrated.** Missing Link
selected 15 external issues autonomously, compared 12 of them, and saved 22
capability/request comparisons: **16 rejected, six investigate**, and no
`external_lead` or follow-up-eligible result. Three candidate-local extraction
failures remain visible and charged; they are not compatible matches or verified
false-positive rejections. Four jobs completed normally; Pretty Bytes completed
with `partial=true` after all three selected candidates failed validation.

Independent review found genuine reusable mechanisms, useful false-positive
rejections, and limitations in reference detection and contribution attribution.
It did not establish novelty, target integration, execution or adoption. No
selected issue URL overlaps selected candidates in the earlier account jobs.

| Source | Eligible files sampled | GitHub reads | AI calls | Comparisons: rejected / investigate | Reserved USD | Usage estimate USD |
| --- | --- | --- | --- | --- | --- | --- |
| PyYAML | 24 / 53 | 45 | 7 | 5 / 1 | 0.1066669 | 0.0262987 |
| Feedparser | 24 / 218 | 45 | 7 | 4 / 1 | 0.1072282 | 0.0265465 |
| Tenacity | 24 / 25 | 45 | 7 | 2 / 2 | 0.1060508 | 0.0238436 |
| AnyIO | 24 / 108 | 45 | 7 | 5 / 2 | 0.1107092 | 0.0279321 |
| Pretty Bytes | 8 / 8 | 27 | 4 | 0 / 0; three extraction failures | 0.0439444 | 0.0084009 |
| Total | Bounded eligible-file samples | 207 | 32 | 16 / 6 | **0.4745995** | **0.1130218** |

Eligible-file coverage does not mean whole-repository, whole-prompt or dependency
coverage. Even Pretty Bytes' 8/8 eligible files retain an incomplete coverage
flag; omitted/unsupported sources and interpretation limits remain unknown.
Usage estimates use provider-reported input/output tokens at the configured
prices, not an invoice or a refund of conservative reservations.

### Queries, selected requests and independent assessment

Query strings below omit the common appended
`is:open in:title,body -repo:SOURCE`; the API additionally enforces
`is:issue is:public`. Queries, ranking and selected requests were not edited.
The first four sources read two pages per query. Pretty Bytes read two pages for
the first query and one each for the remaining two. Search is bounded and cannot
establish the absence of demand.

**PyYAML** — `python yaml token stream`, `python yaml loader pipeline`,
`yaml document node composition`.

- [CaseHub #426](https://github.com/casehubio/casehub-pages/issues/426): event
  parsing, node composition and event emission were all rejected. The issue
  requests a CST-backed visual authoring environment, typed references, project
  graph and synchronized editor, not merely YAML parsing. The
  [pinned parsing API](https://github.com/yaml/pyyaml/blob/34a9bf82357f4952d8f194a5a31f1c39743652d0/lib/yaml/__init__.py#L40)
  supplies events, not that editing contract. This is a correctly refused
  surface-level match; hypothetical future glue is not a discovered solution.
- [PaddleDetection #9502](https://github.com/PaddlePaddle/PaddleDetection/issues/9502):
  SafeLoader received `investigate / needs_review`; token scanning was rejected.
  The [pinned loader](https://github.com/yaml/pyyaml/blob/34a9bf82357f4952d8f194a5a31f1c39743652d0/lib/yaml/loader.py#L31)
  composes the parsing pipeline with SafeConstructor, a relevant mechanism.
  However, the issue **already names PyYAML and explicitly proposes SafeLoader**.
  The stored reference detector returned zero hints because this spelling/prose
  is outside its narrow matching rules. Independent review overrides any novelty
  inference: this is known suggested use, not a new connection. All target loading
  paths, constructor policies and execution remain unverified. The untrusted YAML
  reproducer was read, never executed.
- [Devops CLI #591](https://github.com/dan-petty/devops-cli/issues/591): YAML token
  scanning was rejected against LLM reasoning-token accounting. Tokens and
  streaming are shared vocabulary, not the same interface or required outcome.

**Feedparser** — `python rss atom feed parsing`,
`python custom date parser registration`, `python xml encoding detection`.

- [Linnet #5](https://github.com/Guesswhat-Studio/Linnet/issues/5): parsing and HTTP
  retrieval were rejected as complete solutions, both `reference_review`.
  `feedparser.parse` genuinely supports the feed-parsing subrequirement, but the
  issue already links Feedparser documentation and requests its use. LLM
  summarization, digest rendering, configuration and extension registration are
  target work, not supplied by the parser. This is a recognized prior reference,
  not novel discovery.
- [Repomix #1878](https://github.com/yamadashy/repomix/issues/1878): stream encoding
  conversion received `investigate / similarity_only`; feed parsing was rejected.
  The [pinned converter](https://github.com/kurtmckee/feedparser/blob/a22c5521cbb109871f1a2318948581901bd47e26/feedparser/encodings.py)
  has a real encoding-conversion path, but it is feed/XML-oriented Python code.
  The target requires arbitrary legacy-encoded source files to reach an existing
  JavaScript decoding path while still excluding real binaries. A generic
  converter establishes neither that classification policy nor the packer
  integration. No requirement was marked satisfied for this comparison.
- [HSPsquared #105](https://github.com/respec/HSPsquared/issues/105): feed parsing
  was rejected against a hydrological model's SPECL ACTIONS/STATE and HDF5 table
  work. An RSS/Atom parser is not a compatible simulation parser or scheduler.

**Tenacity** — `python retry decorator`, `python async retry loop`,
`tornado future retry`.

- [GenAI #2938](https://github.com/googleapis/python-genai/issues/2938):
  AsyncRetrying received `investigate / needs_review`; synchronous retry sleep
  was rejected. The [pinned async loop](https://github.com/jd/tenacity/blob/3e58094d3bc414975aad9eadf343a32bdb3b89b3/tenacity/asyncio/__init__.py)
  awaits its configured sleep, whereas
  [nap.sleep](https://github.com/jd/tenacity/blob/3e58094d3bc414975aad9eadf343a32bdb3b89b3/tenacity/nap.py)
  calls blocking `time.sleep`. This is a useful mechanism distinction and a
  correct negative control, conditional on selecting a nonblocking cancellable
  sleep. Independent inspection of the
  [target revision named by the issue](https://github.com/googleapis/python-genai/blob/0ec3d8a4b2c85817434045dad739f6227c2d5c4c/google/genai/_api_client.py)
  finds **existing Tenacity imports and AsyncRetrying use**, plus an upload branch
  already using `await asyncio.sleep`. Its
  [manifest](https://github.com/googleapis/python-genai/blob/0ec3d8a4b2c85817434045dad739f6227c2d5c4c/pyproject.toml)
  declares `tenacity>=8.2.3, <9.2.0`. The bounded issue-only reference scan missed
  that prior dependency. Extending use to the defective upload branch might be
  relevant internal work, but is not a new library connection; changing that one
  sleep may also be sufficient. No target fix or cancellation test was executed.
- [Dask #5198](https://github.com/dask/distributed/issues/5198): the generic retry
  decorator received `investigate / similarity_only`, with a **1,870-day activity
  age blocker**. It does not explain a Dask Future/scheduler lifecycle KeyError.
  The unresolved label and retry vocabulary do not establish current demand or
  a compatible fix.
- [Openawesome #12](https://github.com/chenz24/openawesome/issues/12): Tenacity's
  retry decorator was rejected against a catalog submission explicitly requesting
  a different library, backon. A library listing is not a request for a substitute
  implementation of the named project.

**AnyIO** — `python lazy module imports`, `python worker thread coroutine bridge`,
`python async thread offload`.

- [Comic Pile #2978](https://github.com/JoshCLWren/comic-pile/issues/2978): the lazy
  attribute importer received `investigate / needs_review`; metadata rewriting
  via `fix_package_names` was rejected. The
  [pinned internal helper](https://github.com/agronholm/anyio/blob/1a43476df1fcc80ed6b0303c1898cb51c7ae4fa7/src/anyio/_lazyimport.py)
  genuinely defers mapped imports and caches resolved values. This is an
  interesting mechanism outside the source project's headline purpose, but it
  depends on a specific caller/module configuration and is not a supported
  drop-in public router API. It does not register FastAPI routes, remove duplicate
  application construction or measure cold-start improvements. No target
  integration or new useful connection has been verified.
- [REPL MCP #7](https://github.com/iota-uz/repl-mcp/issues/7): cross-thread coroutine
  dispatch received `investigate / similarity_only`; worker-thread offload was
  rejected. The request needs cancellation/draining of a submitted owner-loop
  future on KeyboardInterrupt and possible session recovery. The dispatch
  interface does not establish that policy. Worker abandonment is not coroutine
  cancellation or transport cleanup; the
  [pinned offload contract](https://github.com/agronholm/anyio/blob/1a43476df1fcc80ed6b0303c1898cb51c7ae4fa7/src/anyio/to_thread.py)
  explicitly leaves abandoned threads running.
- [Sentry #4692](https://github.com/getsentry/sentry-python/issues/4692): worker
  offload, a blocking portal and coroutine gathering were all rejected, with
  `partial_contribution` preserved separately. Offloading a synchronous file read
  or preparation callable is genuine reusable behavior, but it does not implement
  awaitable flush, Spotlight support or async client cleanup. **Two other partial
  labels rely only on not changing capture APIs**, a scope-compatible observation,
  not a positive reusable contribution. These labels should not be counted as
  evidence of a discovered mechanism. The existing rejection/follow-up guards
  remain intact; contribution attribution still needs tightening.

**Pretty Bytes** — `java script human readable byte size`,
`java script localized decimal formatting`, `java script big int unit scaling`.

- [Hardwood #872](https://github.com/hardwood-hq/hardwood/issues/872): a genuine
  request for machine-readable CLI output, but requirement extraction failed an
  exact contiguous-quote check. No compatibility comparison exists. Do not count
  it as either a solution or a correctly rejected false positive.
- [WordPress #1](https://github.com/chanhnghiem/wordpress/issues/1): a pasted
  `functions.php` listing, last updated in 2015. Extraction produced no grounded
  requirement and failed closed; this is retrieval noise, not unmet demand.
- [Cloud Lab #2](https://github.com/ikavvii/cloud-computing-lab-kit/issues/2): an exam
  preparation manual, not a specified adoption request. Extraction produced no
  grounded requirement and failed closed. No paid retry or candidate replacement.

The validation failures above were candidate-local `invalid_candidate_analysis`,
not transport/authentication failures. All four Pretty Bytes provider responses
reported `completed`; that does not mean their analyses passed local validation.

### Reproduction identifiers

| Source | Pinned source revision | Job ID |
| --- | --- | --- |
| PyYAML | `34a9bf82357f4952d8f194a5a31f1c39743652d0` | `4cf8c83d5331453ea58ea843bc61cf36` |
| Feedparser | `a22c5521cbb109871f1a2318948581901bd47e26` | `74e180e9dd2d4379aa4457702432935e` |
| Tenacity | `3e58094d3bc414975aad9eadf343a32bdb3b89b3` | `fa98775407064ef5af2c4a17b05be65e` |
| AnyIO | `1a43476df1fcc80ed6b0303c1898cb51c7ae4fa7` | `68795e3e7fca4097ba2bcb560c536096` |
| Pretty Bytes | `a35ed21bb4169c0bf40942ffa2987a06b8cd2854` | `627b523120e44d8580d88d93e6374696` |

Ignored raw reports and persistent account checkpoints retain acquisition,
selection, discussions, match IDs, source excerpts, provider traces and validation
errors. Public discussions may change after collection; source links are pinned.
No raw reports, database, account screenshots or credentials are committed.

### Budget and verification

The existing shared allowance now reserves **$1.8579583 of $4**, leaving
**$2.1420417**. This includes previous experiments, not just this cohort. Its ID
and earlier reservations were preserved; there were no resets, refunds, automatic
paid recoveries or further allowance increases. The model remains gpt-6-luna;
the application budget change does not change OpenAI account/project limits.

- `python -m unittest discover -s tests`: **280 tests passed** on the merged
  product baseline. Mock tests make no paid provider calls.
- Read-only browser checks verified the restarted app, four rendered Tenacity
  cards and their eight export links, qualification labels, no JavaScript errors
  and no horizontal overflow at desktop and 390-pixel mobile widths. No analysis,
  import, feedback or execution action was submitted through the browser.
- Live API jobs/match classifications/contract 7 agree with saved reports; all 22
  match IDs are persisted in SQLite. No jobs remained running or queued after the
  cohort. The local server remains available.
- Independent selected-issue and pinned-source inspection used public GitHub
  reads only, outside the 207 investigation reads. No supplied issue, manual
  interpretation import, downloaded/generated code execution, isolated bridge or
  publication to target projects occurred.

### Next work, before more paid runs or interface features

1. **Prior-use/context acquisition:** plain package mentions/import aliases and
   bounded target manifests/code must inform reference review. PaddleDetection
   and GenAI are concrete regression cases. Preserve identity/intent uncertainty;
   absence of a textual match must never become a novelty claim.
2. **Contribution attribution:** distinguish a useful executable mechanism from
   passive scope compatibility, missing target glue and a true runtime conflict.
   Sentry's unchanged capture-API observation must not inflate supported reuse.
3. **Retrieval quality and provider reliability:** retain exact-quote validation,
   diagnose the Hardwood failure without an automatic paid retry, and filter
   code dumps, manuals and catalog submissions before expensive comparison.
   Evaluate any retrieval change on a fresh frozen sample rather than promoting
   hand-picked winners from this one.

The experiment demonstrated autonomous retrieval and several defensible negative
decisions. It also surfaced an unexpected internal lazy-import mechanism, but
that is a hypothesis for review, **not yet a new useful connection**. More budget
alone does not address the remaining context, attribution and retrieval limits.
