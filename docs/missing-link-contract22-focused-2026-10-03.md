# Missing Link: contract-22 focused Luna retest

## Outcome

**Partial experiment: one of three prescribed repositories attempted.** Luna
identified two relevant, operation-cited escaping primitives and did not credit
a documentation-only candidate as executable behavior. No complete requirement
or eligible external lead was established. A candidate-local target acquisition
failure stopped the segment under its frozen rules; Zod and python-dotenv were
not started. This is not a completed three-repository benchmark.

The [protocol](missing-link-contract22-focused-protocol-2026-10-03.md) was committed
and pushed as `d0c9e2e` before spending. Executable code stayed at merged
`93eafcfef84dd465680c0ae33f8cd272153296ec`, contract **22**. The provider stayed
OpenAI `gpt-6-luna`, Responses API, streaming, strict schema and medium reasoning,
with the existing byte/token/call limits and cumulative allowance unchanged.

Only repository names were inputs. No issues, custom queries or old analyses
were supplied. The production investigation CLI used the real local HTTP API,
GitHub API and configured provider. No acquired/generated code was executed,
analysis manually imported, job resumed or automatically retried.

## Recorded run and spending

| Measure | Observed value |
| --- | --- |
| Source input | `sindresorhus/escape-string-regexp` |
| Pinned source revision | `a7f7dabaf336bda98d2166848af15d9168b10bcf` |
| Job | `b253327c079d422ba60c7c5f7ec2e00a` |
| Job outcome | Completed, partial: one candidate acquisition failure |
| GitHub requests charged to job | 26 |
| AI reservations / terminal receipts / JSON outputs | 6 / 6 / 6 |
| Interpretation phases | 1 enrichment, 3 request extractions, 2 comparisons |
| Stored assessments / eligible leads | 3 / 0 |
| New conservative reservation | USD 0.0559791, below the USD 0.60 segment cap |
| Reported-token cost estimate | USD 0.0096997 at configured rates; not an invoice |
| Maximum encoded provider request | 51,573 bytes, below 180,000 |
| Original cumulative allowance | USD 10; 395 reservations / USD 6.089778 reserved |
| Remaining ledger headroom | USD 3.910222 |

All six paid attempts have terminal receipts and completed JSON outputs. There
were no provider transport failures or unknown receipts in this segment. Earlier
unknown outcomes remain charged; the allowance was not reset or replaced.

## Fresh answer inspection

### Actual runtime operation, not its declaration

Enrichment selected capability `4224b14bec3b0b83ca06`,
`index.js:escapeStringRegexp`, rather than the `.d.ts` candidate. It described
string validation, regex-metacharacter replacement and hyphen encoding from the
[actual function body](https://github.com/sindresorhus/escape-string-regexp/blob/a7f7dabaf336bda98d2166848af15d9168b10bcf/index.js#L1-L11).
It also retained the documented safe-insertion/context limitations. The type
declaration remains structural context, without runtime ownership or body credit.

The previous contract-21 run selected three different requests under the `.d.ts`
ID. This fresh run's different model-derived searches produced the issues below.
That is a useful observed change, not a controlled causal accuracy comparison or
proof that the connections are novel.

### Two useful mechanisms, not two finished solutions

[Jester #4](https://github.com/absszero/Jester/issues/4) reports test-name
metacharacters interfering with Jest selection. Luna connected the runtime
escaping operation to that specific transformation, citing the function's
complete 11-line body. Both checks retain `partial_behavior`, with integration,
host runtime, name extraction and actual Jest invocation explicitly unknown.
The raw `adapter` suggestion is conservatively stored as `investigate` /
`partial_contribution`, with no follow-up eligibility.

[ioBroker.javascript #2239](https://github.com/ioBroker/ioBroker.javascript/issues/2239)
concerns regex construction from path-derived values. Luna again identified the
escaping operation but did not claim that either target mirror function calls
it. It kept project-specific regression tests unestablished. Request extraction
separated the proposed transformation, the two required integration sites and
optional tests. Timeline references and a fixed label did not override incomplete
discussion: resolution stays unclear, rather than being assumed open/actionable.

All four partial-review anchors cite `index.js#L1-L11`, inside the selected
operation and containing its body. None borrows a sibling implementation, a
signature-only declaration or a README claim. This establishes provenance for
these bounded mechanisms, not execution, complete compatibility or adoption.

### Documentation resemblance is not implementation

For ioBroker, the model also considered the product-level README candidate
`d4d60d458d9a05931b41`. It explicitly rejected implementation credit: all three
checks are `not_demonstrated`, with no partial support or runnable bridge.
The persisted qualification is `similarity_only`, never eligible. This is a
properly declined documentation-based implementation claim, not evidence of a
hard technical incompatibility.

There is a bounded presentation/normalization inconsistency worth retaining in
the follow-up list: raw classification `rejected` becomes `investigate` because
the mandatory checks are undetermined. The UI accurately says contribution is
not demonstrated, but its classification/filter says “Needs investigation”.
This does not expose an eligible lead; preserving an explicit non-fit verdict
should be reviewed separately, not hidden by calling this a fully rejected UI
card. No classification change is included in this report-only branch.

## Why the segment stopped

The third retrieved issue was
[Witiers/CVEs #5](https://github.com/Witiers/CVEs/issues/5). Its repository is
public and non-archived, but a separate read-only GitHub check of
`repos/Witiers/CVEs/commits/main` returned **HTTP 409: Git Repository is empty**.
There is no default-branch commit to pin as target evidence.

The extraction call is retained and charged. The candidate is recorded as
`target_context_unavailable`, with no compatibility result. The backend completed
the other candidates and marked the job partial; the production CLI exited 1.
The frozen protocol requires stopping on any nonzero driver exit, so the wrapper
did not start Zod/python-dotenv or replace this candidate. This is a target-data
limitation handled defensively, not a Luna outage or proof that a regex escaping
function can remedy an XSS report. No security exploit or remediation was tested.

## Verification and preserved history

The local evaluation server was restarted on merged contract-22 code, using the
production HTTP handler and no analytics scheduler. Browser baseline and result
checks found a rendered page, no reported JavaScript errors or framework error
overlay, and working repository selection. All three new assessment IDs appeared
for escape-string-regexp with the correct partial/similarity-only and unexecuted
labels; the job displayed its candidate-failure warning. No paid UI button was
pressed during verification.

The exercised story was repository-only CLI input -> production job endpoint ->
public acquisition and Luna -> persisted assessments -> HTTP export and dashboard
rendering. Read-only reconciliation confirms account identity, frozen provider
fingerprints, stored/exported contract-22 data and reservation/receipt accounting.
Historical job/match/snapshot payload hashes, the entire old reservation prefix
and **95 earlier evaluation report hashes** are unchanged. Babel is still paused
and no job is queued or running.

The fresh Windows offline suite passed **902 tests**; source CLI startup also
passed. Raw outputs, receipts, exports, reconciliation and browser captures are
retained in the ignored owned directory
`data/luna-discovery-contract22-2026-10-03/focused-01/`, not published as account
history or imported into the analysis pipeline.

The OpenAI-docs check preserved the requested model and checked its configured
rates. The verification skills guided browser/API/storage checks; they did not
add features or alter the discovery algorithm.

## Remaining gate

1. Freeze a separate, explicitly scoped segment for the two unstarted inputs;
   do not silently resume this stopped experiment. Zod shared-operation and
   python-dotenv scope attribution have no fresh live result here.
2. Review the narrow rejected-to-investigate consistency issue. Keep parser
   completeness and broader resolver extensions outside this validation cycle.
3. Treat generated fixtures as unexecuted examples. A package's minimum Node
   version alone does not establish the minimum for an example's built-ins or
   test harness; target call sites, adoption and full acceptance remain unknown.
4. Defer UI/key-entry feature work and forced isolation until the core evidence
   gate is met. These useful primitives do not qualify a complete external lead.
