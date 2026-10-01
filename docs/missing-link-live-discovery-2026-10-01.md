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

Protocol freeze: **72475d4**, pushed before the first paid job. The eight initial
runs took place on **1 October 2026, 17:02–17:33 UTC**, without changes to product
code, prompts, sampling or provider settings. Metadata preflight found all inputs
public, non-archived and issue-enabled. The seventh frozen input redirects to
**`chalk/strip-ansi`**; the input was not replaced, and discovery correctly excluded
the canonical source repository.

### Outcome

**Useful mechanisms and sound rejections were found, but a new actionable external
connection is still not demonstrated.** The live pipeline selected **24 issues**,
compared **20**, and saved **34 comparisons: 24 rejected, 10 investigate**. There
were no `direct`, `adapter`, `extraction`, `external_lead` or follow-up-eligible
results. Four jobs completed normally; four completed with `partial=true` because
one selected candidate each failed exact-quotation validation. No candidate was
replaced or retried. No selected URL overlaps selected issues in earlier account
investigations.

These are pipeline classifications, not an independently measured false-positive
rate. In particular, the independent ANSI review below found a useful narrow
contribution that the ledger lost. A complete issue rejection and the absence of
any partial value must not be treated as equivalent.

| Source | Eligible files sampled | GitHub reads | Live AI calls | Comparisons: rejected / investigate | Reserved USD | Token-based estimate USD |
| --- | --- | --- | --- | --- | --- | --- |
| More Itertools | 23 / 23 | 51 | 6 | 3 / 0; one extraction failure | 0.0914807 | 0.0225798 |
| Cachetools | 24 / 31 | 55 | 7 | 3 / 4 | 0.1047824 | 0.0252963 |
| Marshmallow | 24 / 83 | 56 | 6 | 2 / 1; one extraction failure | 0.1029979 | 0.0255535 |
| Babel | 24 / 150 | 50 | 6 | 1 / 2; one extraction failure | 0.0865379 | 0.0187395 |
| Mistune | 24 / 83 | 53 | 6 | 3 / 0; one extraction failure | 0.0884845 | 0.0216100 |
| p-retry | 8 / 8 | 41 | 7 | 4 / 1 | 0.1009594 | 0.0264283 |
| strip-ansi | 8 / 8 | 41 | 7 | 5 / 0 | 0.0832357 | 0.0194390 |
| Zod | 24 / 555 | 58 | 7 | 3 / 2 | 0.1054314 | 0.0282944 |
| Total | Bounded samples, not whole repositories | **405** | **52** | **24 / 10** | **0.7639099** | **0.1879408** |

All 52 calls have completed Responses traces and provider-reported usage, with
model **gpt-6-luna**. They comprise eight capability interpretations, 24 request
extractions and 20 comparisons. A completed API response is not necessarily a
valid interpretation: four request outputs failed semantic quotation validation.
All saved comparisons have `analysis_source=model` and analysis contract **13**;
no coding-agent interpretation was imported.

The shared allowance now holds **$2.6218682** in conservative reservations,
leaving **$7.3781318** under the **$10 cumulative ceiling**. The approximately
**$0.19** token-based estimate for this cohort is not an invoice and does not
refund its approximately **$0.76** reserved amount. No larger allowance, reset,
automatic retry or extra paid recovery run was used.

### Independent evidence checks

**A real narrow contribution was undercounted.** For
[os-exec-mcp #2](https://github.com/kimata1007/os-exec-mcp/issues/2), the acquired
request explicitly includes optional ANSI stripping in its output-normalization
work. The [pinned strip-ansi implementation](https://github.com/chalk/strip-ansi/blob/622cca7b5dd4621cf85e5b517f396f94d8959d2e/index.js#L5)
exports the relevant string transformation and delegates escape matching to
`ansi-regex`. However, the model's 15 extracted requirements omit ANSI removal as
an independently checkable item. Its output-budget requirement bundles several
unrelated behaviors, and every check reports no demonstrated contribution.
The summary acknowledges useful cleanup while the derived ledger says
`not_a_fit` with zero supported requirements.

This is a concrete **request-granularity/contribution recall defect**, not proof
that the library solves the entire MCP redesign. Stream boundaries, output
budgeting, policy integration, prior use, execution and adoption remain unverified.
The observation is recorded here only; the stored model result was not edited or
replaced with a hand-authored analysis.

**An implemented retry mechanism was correctly separated from integration.**
[p-retry's pinned implementation](https://github.com/sindresorhus/p-retry/blob/1472907affe8d6107aba5884abc36d6361b3042e/index.js#L66)
calculates exponential delays and runs retryable operations. It supports the
backoff part of [the fetch-wrapper exercise](https://github.com/vision72/eight-weeks-to-full-stack/issues/7),
but not an already-integrated `fetchWithRetry(baseFetch)` adapter or its mock-API
test. The ledger retains `needs_review`, including **435-day-old activity**. This
is a plausible building block, not a demonstrated new current adoption opportunity.
For [Codex #48729](https://github.com/openai/codex/issues/48729), retry primitives
do not themselves move local runtime preparation outside the startup deadline;
that remains caller work. The source starts its retry clock before calling the
operation. The whole-request rejection is defensible, while partial retry behavior
is retained separately.

**Misleading similarities were refused.** For
[MSYS2 #31523](https://github.com/msys2/MINGW-packages/issues/31523),
[More Itertools' `with_iter`](https://github.com/more-itertools/more-itertools/blob/1ea82a711c69f590054987b5cb194157f8ce8ac4/more_itertools/more.py#L566)
wraps an iterable's context lifetime; it does not provide Jiter's JSON parser or
UCRT packaging. For [the LRU exercise](https://github.com/joanne342/My-Coursework-Planner/issues/343),
[Cachetools' FIFO decorator](https://github.com/tkem/cachetools/blob/3c082c654c2804b9354e4b62dbd2994f1aac464d/src/cachetools/func.py#L35)
uses the wrong eviction policy. For
[the Go CLI migration](https://github.com/EngBlock/open-skills/issues/10), reusing
the JavaScript strip-ansi runtime contradicts the explicit removal of the Node.js
prerequisite. These are genuine rejected false positives, not validation failures.

Other cautions also held: a topic-only memoization issue is `reference_only`;
the tenant-scoping proposal is not credited as existing durable isolation; Babel
locale matching does not fix a MySQL connection-limit failure; Mistune parser
hooks do not implement OSV scanning or Foundry hosting. The Note-schema issue
[already mentions Zod](https://github.com/hasnaintypes/noteflow-app/issues/14), so
its comparisons remain `reference_review`, not novel discovery.

### Reliability and coverage defects

Four selected candidates failed at request extraction because generated quotations
were not contiguous unchanged spans of their cited supplied discussion source:

| Source | Candidate | Failed requirement | Charged reservation USD |
| --- | --- | --- | --- |
| More Itertools | [Larch #4763](https://github.com/zhupanov/larch/issues/4763) | r1 | 0.0123520 |
| Marshmallow | [Code Audit Pipeline #115](https://github.com/jakebromberg/code-audit-pipeline/issues/115) | r7 | 0.0110858 |
| Babel | [Apiome #1114](https://github.com/apiome/apiome/issues/1114) | r2 | 0.0072982 |
| Mistune | [GAIA #1111](https://github.com/amd/gaia/issues/1111) | r2 | 0.0079924 |

The Larch attempt dropped a Markdown emphasis delimiter; the GAIA attempt inserted
a space before a closing parenthesis. GAIA's own inference even noted that its
quotation needed correction, but left the invalid quotation in place. The strict
validator correctly refused both. They are not source-fetch failures or correctly
rejected compatibility matches. Relaxing validation or silently repairing the
quotations would hide the reliability problem rather than solve it.

Acquisition and prompt coverage also limit this evaluation:

- **Zod's main implementation was poorly represented.** Its 24/555 eligible-file
  sample includes many index shims, fixtures and benchmarks, but none of
  `packages/zod/src/v4/core/schemas.ts`, `core/parse.ts` or their v3 implementation
  equivalents. The two enriched code mechanisms are benchmark runners; the schema
  capability is documentation-backed. Consequently, two of three generated
  queries concern benchmarks rather than schema validation. This is source-selection
  bias, not evidence that Zod lacks validation mechanisms or that a larger AI budget
  would repair unseen implementation.
- **One comparison had no implementation context.** Marshmallow call 6, for
  [Decomp Thing #136](https://github.com/minsago-elite/decomp_thing/issues/136), records
  `implementation_context_missing=true`. Its result remains an investigation,
  not source-verified compatibility. File acquisition coverage does not guarantee
  that those files fit in each model call's evidence context.
- **Structural documentation filler can pollute queries.** strip-ansi generated
  `chalk strip ansi documentation states escape`: atomic package-name terms were
  recombined after per-term filtering. This is not a useful problem phrase, and
  it consumes retrieval capacity despite the canonical source exclusion.
- **Lexical matches are not demand.** Selected results include exercises, a
  topic/video link, an automated failure report and broad unrelated migration
  trackers. Some issues remain context-incomplete because linked discussions were
  not acquired. No absence of references, old activity or bounded search proves
  novelty, resolution, adoption or absence of demand.

### Persistence and software checks

After all jobs became idle, the owned loopback evaluation server was stopped and
restarted against the same account database and `.env`. All eight terminal jobs
remained present; **all 34 JSON exports were identical** to the saved initial-run
exports. Luna, the $10 ceiling and the existing $2.6218682 allowance reservation
total survived restart, with **zero additional paid calls**. Earlier jobs and
reservation history were not reset. The traffic collection scheduler was not
started for this API-only evaluation.

The focused Missing Link regression suite passed **287 tests**; the complete
Python 3.13 suite passed **545 tests**. These offline checks are separate from
the 52 live model calls and do not certify semantic discovery quality. No browser
interaction, generated bridge execution, target integration or publication to
third-party projects was performed.

### Next work before interface features

These are proposed corrections, **not implemented by this evaluation**:

1. Make demand citations robust without weakening exact-span provenance. Add the
   four real quotation failures as bounded regression fixtures; retain billable
   failure accounting and explicit partial outcomes.
2. Preserve independently useful and optional subrequirements, including ANSI
   stripping. Distinguish a partial mechanism from whole-issue completion, without
   crediting adapter code or compatible scope as already implemented behavior.
3. Improve monorepo/public-export source selection and reserve actual implementation
   context for comparison. Detect missing implementation before spending a
   comparison call, rather than promoting documentation or catalogue descriptions.
4. Remove recombined project-name/documentation filler and improve retrieval of
   concrete actionable demand. Validate changes with regression cases, then freeze
   another fresh repository-only cohort; do not turn these observed cases into a
   handpicked success benchmark.

The priority is discovery reliability and useful contribution recall, not a more
expensive model, larger default spend, UI features or compiled-language expansion.

### Reproduction and retained inputs

Run the existing opt-in driver against a locally configured provider, for example:

```powershell
python scripts/investigate_missing_link.py --repo more-itertools/more-itertools --max-candidates 3 --use-ai --report data/luna-discovery-2026-10-01/01-more-itertools.json
```

This starts a **new paid run**, not replay of the reported experiment. Results can
change with source revisions, GitHub indexing, discussions and model variability.
Do not rerun an initial report path if preservation of the original evidence is
required. Raw reports/checkpoints remain in ignored local storage; credentials,
the account database and raw provider payloads are not in this pull request.

The fixed selected URLs are retained below, including failures. Query phrases omit
the common `is:open in:title,body -repo:SOURCE`; the GitHub API additionally applies
`is:issue is:public`.

| Source | Generated query phrases | Selected issues in order |
| --- | --- | --- |
| More Itertools | `python iterator chunk lists`; `python fixed width iterable groups`; `python iterable exactly one item` | [MSYS2 #31523](https://github.com/msys2/MINGW-packages/issues/31523), [Computer System #89](https://github.com/tsuyoshi-otake/computer-system/issues/89), [Larch #4763](https://github.com/zhupanov/larch/issues/4763) |
| Cachetools | `python memoization`; `python memoization key`; `python lru cache` | [Coursework #343](https://github.com/joanne342/My-Coursework-Planner/issues/343), [Theory #22](https://github.com/GeekchanskiY/THEORY/issues/22), [Trajectory-IR #317](https://github.com/Coder-s-OG-s/Trajectory-IR/issues/317) |
| Marshmallow | `python schema metaclass fields`; `python field validation hooks`; `python nested validation error merge` | [OKF Parser #52](https://github.com/franklinbaldo/okf-parser/issues/52), [Code Audit Pipeline #115](https://github.com/jakebromberg/code-audit-pipeline/issues/115), [Decomp Thing #136](https://github.com/minsago-elite/decomp_thing/issues/136) |
| Babel | `python locale negotiation`; `python localized list formatting`; `python cldr plural evaluator` | [Perf Reports #74494](https://github.com/PennyDreadfulMTG/perf-reports/issues/74494), [QuantEcon #676](https://github.com/QuantEcon/lecture-python-intro/issues/676), [Apiome #1114](https://github.com/apiome/apiome/issues/1114) |
| Mistune | `python markdown parser factory`; `python parser lifecycle hooks`; `python plugin name resolution` | [GAIA #1111](https://github.com/amd/gaia/issues/1111), [Scorecard #5234](https://github.com/ossf/scorecard/issues/5234), [Agent Framework #8742](https://github.com/microsoft/agent-framework/issues/8742) |
| p-retry | `javascript async retry`; `javascript retry wrapper`; `javascript retry failure policy` | [Fetch Wrapper #7](https://github.com/vision72/eight-weeks-to-full-stack/issues/7), [Codex #48729](https://github.com/openai/codex/issues/48729), [Zellij #5341](https://github.com/zellij-org/zellij/issues/5341) |
| strip-ansi | `javascript ansi escape removal`; `chalk strip ansi documentation states escape` | [OS Exec MCP #2](https://github.com/kimata1007/os-exec-mcp/issues/2), [Open Skills #10](https://github.com/EngBlock/open-skills/issues/10), [Australia Employment RAG #225](https://github.com/Ruihang2017/AustraliaEmploymentRAG/issues/225) |
| Zod | `typescript benchmark runner`; `typescript benchmark dispatch`; `typescript runtime schema validation` | [Noteflow #14](https://github.com/hasnaintypes/noteflow-app/issues/14), [Trade Simulation #723](https://github.com/drevendev/trade_simulation/issues/723), [Home #732](https://github.com/home-lang/home/issues/732) |

Pinned source revisions and corresponding local job IDs:

| Source | Revision | Job ID |
| --- | --- | --- |
| More Itertools | `1ea82a711c69f590054987b5cb194157f8ce8ac4` | `15ed157155c842f681a6f2f8ab188248` |
| Cachetools | `3c082c654c2804b9354e4b62dbd2994f1aac464d` | `6f75395487984cdfb11dfa89bd71568e` |
| Marshmallow | `1c63bdaf7fba217b8736e6eca8a1fcf377e41161` | `06e3f838d0e74b0dbc1578ae0e5265f9` |
| Babel | `e2a17919f0eb988bfea2883b00793ca4d5d37c4f` | `50ca969725af4ff6b913e8f026a12d18` |
| Mistune | `a1b50bc12e066e5707ff797f821829bfcdab03b5` | `cd254d172ae940e4a96b65a809ad342a` |
| p-retry | `1472907affe8d6107aba5884abc36d6361b3042e` | `3c325c23cf824d359d3348213b4caeb7` |
| strip-ansi | `622cca7b5dd4621cf85e5b517f396f94d8959d2e` | `db0eee7f7a8e4fb2abc357341227dc64` |
| Zod | `004d800c9e3cd4c79930f55aa4ad080225b22efd` | `ab58714df5be4878873a714df71d647d` |
