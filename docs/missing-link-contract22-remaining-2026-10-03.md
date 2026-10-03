# Missing Link: remaining contract-22 Luna retest

## Outcome

**Both prescribed inputs completed, without candidate or provider errors.** Zod
yielded two source-grounded partial mechanisms, not complete solutions;
python-dotenv yielded three non-fitting comparisons. None of the eight stored
assessments is eligible for follow-up or isolated execution. This completes the
remaining-input segment, not a blind discovery benchmark or a novelty claim.

The [protocol](missing-link-contract22-remaining-protocol-2026-10-03.md) was
committed and pushed as `a686b74` before spending. Executable code stayed at
`fc1ed8ff4d1e50f70888debf14d8a6e30d668389`, contract **22**, with the unchanged
OpenAI `gpt-6-luna` Responses/streaming/strict-schema provider. Only repository
names were inputs: no issue URLs, custom queries or prior analyses. Production
CLI -> local HTTP job API -> GitHub/provider -> stored result -> HTTP export was
exercised. No acquired/generated code was executed or analysis manually imported.

The [first segment](missing-link-contract22-focused-2026-10-03.md) remains
stopped and immutable after escape-string-regexp's empty-target failure. Across
the two segments all three repository inputs have now been attempted, but the
earlier failure is not erased and the experiments are not combined into a
single uniformly completed cohort.

## Recorded runs and spending

| Measure | Zod | python-dotenv |
| --- | --- | --- |
| Input | `colinhacks/zod` | `theskumar/python-dotenv` |
| Pinned revision | `0b216ef674e297ebe41d8bf902262e56f8755822` | `0b2880591780a426b0551436f47a17e7a76d954f` |
| Job | `3e88a1d1fb3d402f9aa35e9e79702cd0` | `cc7c80eb9b8349d49679a45bcdd74604` |
| Outcome | Completed | Completed |
| GitHub requests / cache hits | 32 / 24 | 32 / 24 |
| Structural capabilities / AI-enriched | 99 / 8 | 77 / 8 |
| AI reservations / terminal receipts / JSON outputs | 7 / 7 / 7 | 7 / 7 / 7 |
| Request extractions / comparisons | 3 / 3 | 3 / 3 |
| Stored assessments / eligible leads | 5 / 0 | 3 / 0 |
| Candidate failures / unknown receipts | 0 / 0 | 0 / 0 |
| Conservative reservation, USD | 0.117217 | 0.1111746 |
| Reported-token estimate at configured rates, USD | 0.0295493 | 0.0241979 |
| Maximum encoded provider request, bytes | 177,174 | 161,967 |

The segment added **14 reservations / USD 0.2283916**, below its USD 0.40 cap.
Reported-token cost estimate is USD 0.0537472, not the invoice. The original
USD 10 allowance remains `missing-link-verification-2026-09-30`, now **409
reservations / USD 6.3181696**, with USD 3.6818304 ledger headroom. Earlier
uncertain attempts stay charged; no reset, replacement allowance, retry or
refund was used. All requests stayed below the 180,000-byte limit.

## Zod: operation ownership and usefulness

Enrichment cited `failure`'s own error-construction body rather than borrowing
`safeParse`, and `getEnumValues`' reverse-enum filtering body rather than only
its declaration. This is improved attribution in these fresh answers, not a
controlled causal accuracy result: searches and selected issues differ from
earlier evaluations. Body provenance does not prove semantic compatibility.

| Autonomously retrieved request | Answer inspection | Stored contract-22 result |
| --- | --- | --- |
| [codexa #23](https://github.com/sayam-1705/codexa/issues/23): side-effect-free configuration validation | Global `config` getter/setter does not implement registry isolation or validation. Raw verdict explicitly rejects it. | `investigate` / `similarity_only`; ineligible |
| [WuppieFuzz #386](https://github.com/TNO-S3/WuppieFuzz/issues/386): recursive OpenAPI refs crash | `isRecursive` offers stack-based cycle detection over Zod schemas. `isRef` is only an object predicate, correctly denied cycle-detection credit. | One `partial_contribution`, one `similarity_only`; both `investigate`, ineligible |
| [Mosfet #120](https://github.com/busycaesar/Mosfet/issues/120): structured-question validation and pause/resume | `validateFallback` provides synchronous supplied-schema pass/fail, not the requested schemas, structured results, error handling or pause/resume. Global `config` is not payload validation. | One `partial_contribution`, one `similarity_only`; both `investigate`, ineligible |

The cycle-walker partial cites its selected body at
[`memoizer.ts` lines 50–181](https://github.com/colinhacks/zod/blob/0b216ef674e297ebe41d8bf902262e56f8755822/packages/zod/src/v4/core/memoizer.ts#L50-L181),
split into three bounded evidence spans. It requires adapting Zod's internal
schema graph to OpenAPI `$ref` resolution and **porting TypeScript to Rust**;
it is mechanism inspiration, not a directly reusable runtime dependency or
verified crash remedy. Resolution/context is incomplete.

The validator partial cites its own
[`parse.ts` lines 151–172](https://github.com/colinhacks/zod/blob/0b216ef674e297ebe41d8bf902262e56f8755822/packages/zod/src/v4/core/parse.ts#L151-L172).
It returns a boolean and throws on a Promise. Partial credit for requirement
parts `r13`, `r14`, `r15` does not establish structured output, graceful error
handling or full compliance. It is an internal helper, not an established public
entrypoint; target files were not supplied. Every retained partial anchor lies
inside and cites the selected operation's body. No complete requirement is credited.

## python-dotenv: false resemblance declined

Enrichment describes `load_dotenv`/`dotenv_values` from their own forwarding
bodies and cites dependency context separately. The IPython package entrypoint
delegates to the registration function; the magic's body is contextual, not an
independent implementation owned by that wrapper. No borrowed/nested body is
credited as positive or partial support in these comparisons.

| Autonomously retrieved request | Answer inspection | Stored contract-22 result |
| --- | --- | --- |
| [StreamGive #164](https://github.com/StreamGive/streamgive-backend/issues/164): document environment-loading precedence | Python's `load_dotenv` cannot document the Node backend's actual call sites, CI/test precedence or `process.env` read timing. Target package metadata confirms Node/dotenv, not those behaviors. Raw verdict rejects it. | `investigate` / `similarity_only`; ineligible |
| [VS Code testissues #16950](https://github.com/vscodenpa/testissues/issues/16950): workspace-symbol command and method suggestions | `%dotenv` registration is not a VS Code command, language server or completion engine. Both mandatory checks are incompatible. Old demand is flagged separately, not assumed resolved. | `rejected` / `not_a_fit`; ineligible |
| [cumulus-library #659](https://github.com/smart-on-fhir/cumulus-library/issues/659): data dictionary to Markdown table documentation | `dotenv_values` parses dotenv configuration, not the study dictionary schema or Markdown generation. Raw verdict rejects it. | `investigate` / `similarity_only`; ineligible |

These are useful negative outcomes, not useful connections. Search terms such
as "parse to dictionary" remain broad and can retrieve semantically remote
requests. Bounded selection of internal helpers and global configuration also
limits Zod discovery. This is a quality limitation to evaluate separately, not
permission to expand the parser/resolver contract during the frozen run.

## Remaining inconsistency and preserved evidence

Five fresh explicit raw `rejected` verdicts (three Zod, two python-dotenv) become
`investigate` because mandatory checks are undetermined. The VS Code hard-conflict
rejection stays rejected. This confirms the narrow classification inconsistency
from the first segment; it does **not** turn these cases into eligible leads.
Fix it separately and offline, preserving unknown checks as unknown rather than
inventing technical conflicts. Do not relabel the frozen contract-22 results.

Read-only reconciliation compared actual inputs, receipts, outputs, stored
payloads and API exports. Historical job/match/snapshot hashes, old reservation
prefix and **102 previous report hashes** are unchanged. No job is queued or
running and Babel remains paused. Raw material and audit artifacts are retained
in the ignored owned `data/luna-discovery-contract22-2026-10-03/remaining-01/`
directory, not published or imported as account analyses. Executable code is
unchanged from the prior 902-test Windows offline verification; this report
does not claim a new full-suite or browser run.

The OpenAI-docs check preserved the requested provider and checked configured
rates; no model or provider migration was made. No UI/key-entry feature,
publication, security test or forced isolated demonstration was included.

Next: correct explicit-rejection normalization, with no paid calls; then freeze
a separate quality experiment for discovery relevance if desired. No complete
eligible lead has been established, so isolated execution remains gated.
