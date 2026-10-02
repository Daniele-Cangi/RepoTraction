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

Pending. Results will be recorded after the initial cohort; this protocol must not
be rewritten to fit outcomes.
