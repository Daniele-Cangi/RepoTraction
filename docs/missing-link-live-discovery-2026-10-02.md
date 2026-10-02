# Missing Link: contract-16 live retest

## Frozen protocol

Product baseline: merged `main` **0c9bb97beec853891ec668828cd22c0f404f762a**
(PR #31), analysis contract **16**. This protocol is committed and pushed before
the first paid call. Product code, prompts, provider settings and sampling remain
unchanged throughout this cohort. Previous experiments and original interpretations
remain intact; no historical-result migration or manual analysis import is allowed.

### Group A: repeated sources

Repeat the eight source inputs from the [1 October cohort](missing-link-live-discovery-2026-10-01.md),
in the same order. These are **not held-out** inputs: their earlier results are
known. Run fresh autonomous discovery, not explicit replay of previously selected
issues. Source revisions, search results and chosen issues may differ; this is an
operational before/after comparison, not a controlled measurement of causal gains.

| Order | Source input | Domain |
| --- | --- | --- |
| 1 | `more-itertools/more-itertools` | Iterator composition |
| 2 | `tkem/cachetools` | Cache policies |
| 3 | `marshmallow-code/marshmallow` | Serialization and validation |
| 4 | `python-babel/babel` | Localization |
| 5 | `lepture/mistune` | Markdown parsing |
| 6 | `sindresorhus/p-retry` | Asynchronous retry |
| 7 | `sindresorhus/strip-ansi` | Terminal-text normalization; prior canonical redirect to `chalk/strip-ansi` |
| 8 | `colinhacks/zod` | TypeScript schema validation |

### Group B: new sources

The five inputs below are fixed **before reading their issues or search results**.
Selection is by general domain, not known matches. Metadata-only preflight checks
canonical name, public visibility, archive status and prior source-history overlap.
Ineligible inputs remain recorded and are not replaced by easier cases.

| Order | Source input | Domain |
| --- | --- | --- |
| 9 | `jquast/wcwidth` | Unicode terminal-cell width |
| 10 | `python-humanize/humanize` | Human-readable formatting |
| 11 | `theskumar/python-dotenv` | Environment-file configuration |
| 12 | `sindresorhus/escape-string-regexp` | Literal regular-expression escaping |
| 13 | `caolan/async` | Asynchronous control flow |

This is a small purposive Python/JS/TS sample, not a random benchmark or a claim
of universal parser coverage. Fresh sources do not guarantee fresh target issues;
overlaps with past selected issues and between groups will be reported separately.

## Execution and spending boundaries

Use the real local HTTP API, one initial job per eligible input, serially in the
fixed order: `action=discover`, `use_ai=true`, `max_candidates=3`, `max_requests=80`,
empty `issue_url` and `query`. Keep the existing 24-file source acquisition bound.
Do not supply issues, tailor queries, correct capabilities, replace screened
candidates, retry paid failures automatically or import prewritten interpretations.
No source, bridge or third-party code is executed during discovery; no third-party
issue, pull request or message is published.

Use the existing configured OpenAI **gpt-6-luna**, Responses API, strict JSON schema,
medium reasoning, streaming and 12,000 maximum output tokens. Keep at most eight
AI calls and **$2 reserved per job**, with the existing **$10 cumulative ceiling**
and allowance ID `missing-link-verification-2026-09-30`. Starting application-side
reservations are **$2.6218682** across **173 reservations**, leaving **$7.3781318**.
Do not reset/refund that ledger, create another allowance, or treat $10 as an
additional budget. Keys and `.env` contents must never appear in reports or commits.

The configured standard estimates ($0.10 input / $0.50 output per million tokens)
were checked against the [official Luna documentation](https://developers.openai.com/api/docs/models/gpt-6-luna)
on 2 October 2026. Actual reservation enforcement remains in the product before
HTTP. Reservations and reported token-based estimates are not provider invoices;
unknown usage is not zero. This is not a change to OpenAI account spending limits.

Pause the cohort on transport/authentication failure, cancellation, account change,
or exhaustion of the existing allowance. Candidate-local partial results remain
recorded and do not cause retries or replacements. Source/preflight failures with
zero AI calls remain failed/empty cohort entries, not negative compatibility evidence.

## Evidence and assessment

Store raw initial reports separately under ignored `data/luna-discovery-2026-10-02/`.
Retain job IDs, pinned source/target revisions, coverage, generated queries, selected
URLs, screening decisions, provider traces, reported usage, validation failures,
classifications and qualification. API-exported results must survive persistence.
Compare Group A to the frozen earlier report, including source/issue changes,
quotation failures, per-requirement contributions, implementation-context gaps
and acquisition bias. Group B measures autonomous behavior on new source inputs.

Independently inspect each returned candidate against its acquired discussion and
pinned source evidence. Record useful existing contributions, mandatory conflicts,
sound rejections, unsupported positives and unresolved adoption/novelty claims.
A schema-valid answer or model label is not semantic proof. Paid validation failures
are not correctly rejected false positives. A rejected whole request may still
contain a useful narrow contribution. No winner or useful new connection is required
or manufactured; an empty result remains a valid evaluation outcome.

Only after completing and freezing the discovery results, an independently grounded,
useful candidate may receive an isolated proof using the existing WASI runner,
without Docker, network, host subprocesses or third-party publication. Treat fixture
execution separately from fulfillment of the real request. If no defensible candidate
exists, report that instead of building a forced bridge. No interface feature or
parser/resolver extension is part of this evaluation.

## Results

Protocol freeze: **f9147d5**, pushed before the first paid job. The 13 initial
runs took place on **2 October 2026, 11:47–12:39 UTC**, with no changes to product
code, prompts, provider configuration, queries or sampling. All inputs passed
metadata-only preflight; `sindresorhus/strip-ansi` again resolves to `chalk/strip-ansi`.
No issue was supplied, candidate replaced, paid failure retried or interpretation
imported. Empty and partial outcomes remain in the cohort.

### Outcome

**The pipeline discovers relevant building blocks and rejects misleading similarities,
but this cohort still does not demonstrate a new actionable external connection.**
It selected **36 distinct issues**, compared **31**, screened two reference-only
bodies before extraction, and retained three charged extraction failures. The
saved output contains **57 comparisons: 45 rejected, 12 investigate**. Ten jobs
completed normally (including one empty search); three completed with `partial=true`.

There are no `direct`, `adapter`, `extraction`, `external_lead` or follow-up-eligible
results. Qualification is **9 partial_contribution, 35 not_a_fit, 11 similarity_only,
1 needs_review and 1 not_actionable**. These are pipeline labels, not a measured
precision/recall or false-positive rate: some rejected rows concern article content,
not real implementation requests, and some whole rejections retain useful primitives.
Multiple capability rows for one issue are not independent discoveries.

| Group | Sources | Selected / compared issues | Comparisons: rejected / investigate | Live calls | GitHub reads | Reserved USD | Token estimate USD |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A: repeated sources | 8 | 24 / 21; two screened, one failure | 28 / 11 | 51 | 296 | 0.8039737 | 0.2077337 |
| B: new sources | 5 | 12 / 10; two failures, one empty source | 17 / 1 | 27 | 234 | 0.4186921 | 0.1085726 |
| Total | **13** | **36 / 31** | **45 / 12** | **78** | **530** | **1.2226658** | **0.3163063** |

| Source | Eligible files sampled | Live calls | Rejected / investigate | Reserved USD | Token estimate USD |
| --- | --- | --- | --- | --- | --- |
| More Itertools | 23 / 23 | 7 | 4 / 0 | 0.1186107 | 0.0328413 |
| Cachetools | 24 / 31 | 5 | 1 / 3; one screened body | 0.0866976 | 0.0240865 |
| Marshmallow | 24 / 83 | 7 | 5 / 0 | 0.1140093 | 0.0288327 |
| Babel | 24 / 150 | 7 | 6 / 0 | 0.1138002 | 0.0310705 |
| Mistune | 24 / 83 | 6 | 4 / 0; one extraction failure | 0.0956951 | 0.0241842 |
| p-retry | 8 / 8 | 5 | 4 / 0; one screened body | 0.0795071 | 0.0205877 |
| strip-ansi | 8 / 8 | 7 | 0 / 8 | 0.0786228 | 0.0171219 |
| Zod | 24 / 555 | 7 | 4 / 0 | 0.1170309 | 0.0290089 |
| wcwidth | 24 / 92 | 7 | 4 / 1 | 0.1088812 | 0.0279448 |
| Humanize | 24 / 27 | 6 | 4 / 0; one extraction failure | 0.0967294 | 0.0273286 |
| python-dotenv | 24 / 30 | 7 | 5 / 0 | 0.1100179 | 0.0280872 |
| escape-string-regexp | 8 / 8 | 1 | No selected issue; no comparison | 0.0084322 | 0.0010032 |
| Async | 24 / 191 | 6 | 4 / 0; one extraction failure | 0.0946314 | 0.0242088 |

All **78** calls have completed Responses traces, provider-reported usage and
matching retained reservations: **13 capability interpretations, 34 request
extractions and 31 compatibility calls**. Every saved comparison is
`analysis_source=model`, contract **16**. The largest actual request is **173,953
bytes**, below 180,000, and every compatibility trace includes implementation
context. A completed provider response does not imply a valid or useful analysis.

The unchanged allowance now contains **251 reservations** (173 prior + 78 current),
totaling **$3.844534**, leaving **$6.155466** under the existing $10 ceiling. The
approximately **$0.32 token estimate** is separate from the approximately **$1.22
reserved for this cohort**; neither is an invoice, refund or new allowance.

### Comparison with 1 October

All eight Group A source revisions are unchanged. Only three selected issue URLs
recur: THEORY #22, GAIA #1111 and Codex #48729. No selected URL repeats within the
current 13-source cohort; no Group B selected URL appears in earlier account
investigations. Source novelty does not establish useful-match novelty.

| Repeated-source metric | 1 October, contract 13 | 2 October, contract 16 |
| --- | --- | --- |
| Selected / compared issues | 24 / 20 | 24 / 21 |
| Live AI calls | 52 | 51 |
| Quotation-validation failures | 4 | 0 |
| Other extraction failures | 0 | 1 (35 requirements exceed 30) |
| Comparisons | 34 | 39 |
| Missing implementation-context comparisons | 1 | 0 |
| Qualified external leads | 0 | 0 |

With indexed source-span selection, no quotation failures occurred in this sample, and
Zod's sample now includes actual v4 parsing/schema/error implementation rather
than benchmark mechanisms. The independent optional ANSI behavior is credited
in a different issue. These are operational improvements, **not causal proof of
higher discovery accuracy**: most selected issues changed, and GAIA still fails
end-to-end for a different reason. The offline contract-16 replay separately
packed all 8 enrichment, 24 extraction and 20 previous comparison inputs at a
maximum **164,617 bytes**, stopping at a no-spend fixture before HTTP without
rewriting history. It checks feasibility, not model correctness.

### Independently reviewed contributions and rejections

- **Useful chunking, incomplete project delivery.**
  [ml-pipes #42](https://github.com/trained-by-humans/ml-pipes/issues/42) requests
  list chunks with a partial final group. The
  [pinned `chunked` implementation](https://github.com/more-itertools/more-itertools/blob/1ea82a711c69f590054987b5cb194157f8ce8ac4/more_itertools/more.py#L215)
  provides that primitive; typing, integration, documentation and acceptance
  tests remain work. Partial contribution is retained despite whole rejection.
  The same issue's `grouper` comparison is a sound refusal: fixed-width tuples
  with fill/drop/strict policies are not the requested list/partial semantics.
- **Optional ANSI stripping is credited, not certified remediation.**
  [Codex-plugin-cc #23](https://github.com/openai/codex-plugin-cc/issues/23)
  includes an independently optional preprocessing operation. The
  [pinned JS transform](https://github.com/chalk/strip-ansi/blob/622cca7b5dd4621cf85e5b517f396f94d8959d2e/index.js#L5)
  supports it; JSONL wiring and other paths remain unknown. `needs_review` is
  appropriate. A comment already reports a submitted fix, whose linked PR was
  not acquired: this is not proven novel or still unresolved. README/type rows
  do not constitute additional runtime solutions.
- **Cell width is not a runtime segmentation or shaping fix.**
  [Terminal-ui #2](https://github.com/Ismail-elkorchi/terminal-ui/issues/2)
  requires qualifying a fixed Bun release in native Linux/macOS
  lanes; Python grapheme-boundary code cannot perform that qualification. For
  [Codex #50208](https://github.com/openai/codex/issues/50208), wcwidth wrapping
  remains `similarity_only`: cell/grapheme boundary handling does not establish
  Bengali glyph shaping or integration into the renderer. For
  [Deep-funding #4](https://github.com/pengpengyi92/deep-funding/issues/4),
  the relevant wrapping primitive is retained as partial contribution, but its
  default preservation of terminal controls conflicts with inert provider text.
- **Dotenv is not YAML repair or kernel lifecycle.**
  [Zerotrustmirror #10](https://github.com/5h4d0wn1k/zerotrustmirror/issues/10)
  concerns Python source mislabeled as YAML and missing advertised fixture files.
  Dotenv parsing/JSON display does not fix those defects. An IPython `%dotenv`
  magic likewise cannot configure kernel ports or reopening in
  [Bluesky #314](https://github.com/bluesky/bluesky-queueserver/issues/314).
  Conversely, [pgfsm #438](https://github.com/pgfsm/fsm/issues/438) has a genuinely
  related optional .env bootstrap, retained as partial contribution; four-SDK
  flag precedence, validation, tests and help remain new integration work.
- **Dependency scheduling is a building block, not TaskFlow.**
  [TaskFlow #898](https://github.com/delinoio/oss/issues/898) distinguishes selected
  requirements from provisional design and explicitly excludes immediate product
  implementation/migration. The
  [pinned `auto` implementation](https://github.com/caolan/async/blob/3921e54bd0704157dbea238fdfcc0c3619abde1a/lib/auto.js#L151)
  really waits for prerequisites, limits concurrency and passes results, so a
  narrow scheduling contribution is defensible. It is not the Rust product,
  native manifest graph, cache or session controller. `cargoQueue`'s batching
  interface has no demonstrated named prerequisite graph; its rejection is sound.

The independent review also supports rejection of Python locale lookup for a
C++/Bazel runtime policy, Markdown hooks for venv pip installation, and runtime
retry for a TypeScript static diagnostic. Later-comment changes, incomplete
linked context and stale-activity hints remain distinct from proof of resolution.
No third-party commands, exploit snippets, credentials or publication instructions
in source material were executed.

### Failures that still need correction

Three paid extractions reach the same generic local error, but have two different
causes. They are **not correctly rejected compatibility false positives**.

| Source / candidate | Actual raw output | Charged reservation USD |
| --- | --- | --- |
| Mistune / [GAIA #1111](https://github.com/amd/gaia/issues/1111) | 35 requirements; existing maximum is 30 | 0.0088834 |
| Humanize / [Source Code Review Tool #14](https://github.com/jatinsingh1603/Source-Code-Review-Tool-TIET/issues/14) | 33 requirements; existing maximum is 30 | 0.0094007 |
| Async / [iblog #10](https://github.com/gnipbao/iblog/issues/10) | Zero requirements; model correctly identifies an explanatory article with no actionable request | 0.0100623 |

`missing_link/analysis.py` accepts 1..30 requirements. The provider request schema
in `missing_link/contracts.py` has no corresponding array bounds, and the request
prompt asks for atomic extraction without stating the 30-item limit. The strict
wire shape therefore permits the 35/33 outputs that local validation subsequently
rejects. Align the existing bound in schema, prompt and local validation, with
accurate underflow/overflow diagnostics and tests; do not silently truncate, relax
provenance, increase limits or spend on automatic retries.

The zero-item response needs a separate **typed non-demand outcome**: ordinary
article content should stop before compatibility without fabricated requirements.
In [TIL #271](https://github.com/viphat/til/issues/271), the model acknowledges that
the body is an article with no explicit requested deliverable, yet creates seven
inferred mandatory article-coverage requirements and compares code against them.
Those two rejected rows are not evidence of actual implementation demand. Keep
strict requirements for real demands while representing reference/non-demand
content explicitly. Link-only screening helped two cases but is not sufficient
for long educational bodies.

Other limitations remain recorded rather than expanded into parser work:

- The chunking issue's statement that a built-in operation is absent becomes a
  potential prohibition blocker. A statement of the current gap is not necessarily
  a ban on dependencies. Project documentation/test deliverables also need careful
  separation from runtime incompatibility; do not weaken actual constraints.
- TinyAGI ANSI logger cleanup and Humanize presentation primitives remain bundled
  with application-level criteria and are not independently credited. This is
  contribution-recall uncertainty, not evidence that complete fixes exist.
- python-dotenv's acquired exports include `load_dotenv`/`dotenv_values`, but its
  eight enriched mechanisms emphasize CLI, IPython and lower-level editing/parser
  APIs. Large export surfaces remain a bounded sampling/ranking problem.
- escape-string-regexp's one generated query returns zero issues: an empty
  retrieval sample, not absent demand. No manual query tuning was done.
- wcwidth's 24-file snapshot omits imported support modules; an implementation
  excerpt is not an import-complete reproduction bundle. GitHub's primary-language
  label is C, but this run acquired Python; no compiled-language coverage is claimed.
- Full acquired discussion is not full model evidence. Life-optimizer's request
  context exposes 189 spans and omits 144 visible spans; `discussion_complete=false`
  is retained. Its 25 extracted requirements do not cover every body criterion.
  Zod returns nine enriched capabilities despite the advisory eight-item prompt;
  this stays within accepted code bounds but is not an enforced output target.
- A Valkey inspection ZIP exceeds the existing per-file handoff bound. JSON/source
  export remains available; the warning is not an AI error or absent evidence.

### Persistence, browser and isolation

Before and after restarting the idle server, all **57 API match exports** exactly
equal their original saved wrappers. Pinned snapshot revisions, job inputs,
traces, usage, reservations and allowance totals reconcile. The two integrity
reports are identical. No extra AI calls occurred during tests or restart, and
no saved result was migrated or manually reclassified.

**697 offline tests pass.** After restart the real Missing Link browser page loads
with meaningful saved results and no page/console errors. This is a read-only
reload check, not a claim of exhaustive click-flow testing. The server remains
available at `http://127.0.0.1:8765/`.

**No isolated example was attempted.** The useful `needs_review` sanitizer is
JavaScript; the existing runner executes opt-in pure Python under WASI. Useful
Python primitives have rejected whole matches, unresolved/generic demand, or
incomplete reproduction dependencies. No rejected result was promoted, snapshot
gate bypassed, old winner substituted or JS mechanism reimplemented in Python to
manufacture a successful proof. Real target integration and adoption remain untested.

Raw initial reports, complete reviewer notes, source revisions, job IDs, provider
outputs and before/after integrity records remain locally under ignored
`data/luna-discovery-2026-10-02/`. They are not imported interpretations and are
not published with the account database, keys or real-account screenshots.

Next priority: correct the bounded request contract and non-demand representation
with offline fixtures first, then explicitly scoped live verification. Separately
evaluate contribution granularity and retrieval coverage. UI/key-entry features,
universal parser/resolver completeness and Go/Rust expansion remain deferred.
