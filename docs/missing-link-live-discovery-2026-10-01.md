# Missing Link live discovery evaluation

## Frozen protocol

Product baseline: merged `main` **d7023f7f8bcd48a511d3d9622143bd3647c0d8fe**
(PR #29), analysis contract **13**. This protocol is committed and pushed before
the first paid call. Product code, prompts, provider settings and sampling stay
unchanged throughout the initial cohort. Previous experiments remain intact.

The eight repository-only inputs below were selected before reading their issues
or search results. None was a source repository in the existing account history.
Metadata-only preflight will check canonical names, public visibility and archive
status; a failing preflight is recorded, not replaced with an easier case.

| Order | Source repository | Domain |
| --- | --- | --- |
| 1 | `more-itertools/more-itertools` | Iterator composition |
| 2 | `tkem/cachetools` | Cache policies |
| 3 | `marshmallow-code/marshmallow` | Serialization and validation |
| 4 | `python-babel/babel` | Localization |
| 5 | `lepture/mistune` | Markdown parsing |
| 6 | `sindresorhus/p-retry` | Asynchronous retry |
| 7 | `sindresorhus/strip-ansi` | Terminal-text normalization |
| 8 | `colinhacks/zod` | TypeScript schema validation |

This is a small purposive sample of five Python and three JavaScript/TypeScript
projects, not a random sample or a precision/recall benchmark. Fresh sources do
not guarantee fresh discovered issues; overlaps will be reported. Compiled
languages remain outside this cohort's coverage.

Run one initial investigation per eligible source, in the fixed order, through
the real local HTTP API: `action=discover`, `use_ai=true`, `max_candidates=3`,
`max_requests=80`, and empty issue/query fields. Keep the product's 24-file source
acquisition limit. Do not supply issues, tailor queries, import interpretations,
correct capabilities, replace candidates, retry paid failures automatically,
execute bridges or publish to third-party repositories.

OpenAI **gpt-6-luna** remains configured with Responses, strict JSON schemas,
medium reasoning and at most eight calls per job. The configured estimates are
$0.10 input / $0.50 output per million tokens, checked against the
[official model documentation](https://developers.openai.com/api/docs/models/gpt-6-luna).
The per-job reservation ceiling remains **$2**. The user raised the existing
shared allowance `missing-link-verification-2026-09-30` from **$4 to $10 total**,
not $10 additional. Starting conservative reservations are **$1.8579583**;
remaining headroom is **$8.1420417**. Preserve that allowance ID and all previous
reservations; do not reset, refund or create another allowance.

Reservation ceilings and token-based usage estimates are application-side
accounting, not provider invoices or changes to OpenAI account spending limits.
Unknown usage is not zero. The ignored local `.env`, credentials and account
database must not be committed or included in public reports.

## Assessment

Save raw initial-run reports separately under ignored
`data/luna-discovery-2026-10-01/`. Retain job IDs, source revisions, acquisition
coverage, generated queries, selected issue URLs, provider traces, validation
errors, classifications and discovery qualification. Empty, failed and partial
results remain part of the cohort. Candidate-local validation failures are charged
failures, not correctly rejected false positives. A transport/authentication
failure pauses paid work until its cause is understood; no automatic paid retry.

After saving each initial result, independently inspect returned candidates and
their pinned evidence. Assess relevant contribution, mandatory compatibility,
current actionable demand, prior reference/use and novelty separately. A model
label, syntactically valid response or missing detected reference is not proof of
a useful new connection. Record unsupported positives and sound rejections as
well as any supported lead; do not require or manufacture a winner.

This evaluation exercises GitHub acquisition, live AI interpretation, persistence
and API export. It does not claim complete repository analysis, integration,
execution, adoption or browser interaction testing. No UI features or structural
refactors are included in this cohort.

## Results

Pending the initial live runs. This section will be updated with all outcomes,
independent evidence checks and actual reservation/usage accounting.
