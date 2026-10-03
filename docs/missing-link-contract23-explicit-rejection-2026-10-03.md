# Missing Link: preserve explicit non-fit verdicts (contract 23)

## Bounded correction

The frozen contract-22 Luna runs exposed an inconsistency: an explicit
`rejected` verdict could become `investigate` when mandatory checks were
undetermined, absent, or supported only by passive scope compatibility. This
changed the classification/filter despite the model explicitly declining the
connection. The cases remained ineligible, but “Needs investigation” was misleading.

The correction is limited to `missing_link/analysis.py`: unknown/no-hard checks
and absence of existing behavior still downgrade **non-rejected** suggestions;
they no longer revive an explicit rejection. Hard conflicts still force
rejection. All candidate, requirement, citation and partial-operation validation
continues before a verdict is stored. No new logic is added to `app.py`.

A semantic non-fit verdict does not manufacture technical conflict evidence:
undetermined checks remain undetermined, with no incompatible requirements
invented. An explicit full rejection may retain valid partial or supported parts
without becoming an eligible external connection. Existing same-project,
known-reference, non-actionable and other qualification rules remain intact.
Model/import conclusions are still interpretations, not executed proof.

## Versioning and history

`ANALYSIS_CONTRACT_VERSION` advances from 22 to **23** because normalized results
change. New assessment IDs and provider identities use the new contract. Old
21/22 records are preserved and treated as historical/stale by the existing
currentness check; there is no data migration, automatic reevaluation, import,
rewrite or change to prior receipts and spending.

The owned evaluation server remains loaded on frozen contract 22 for reviewing
the live experiments. This offline fix does not restart it, silently relabel its
results or claim that the dashboard already shows contract-23 analyses. Starting
merged contract-23 code will mark the older evidence historical, not regenerate
it. Any new paid discovery needs a separately scoped experiment.

## Offline verification

- Twelve new regression tests cover explicit rejection with unknown/missing
  mandatory checks, optional-only and passive scope checks, incomplete/unclear
  demand and omitted constraints, partial/supported parts, input immutability,
  invalid references/IDs, positive downgrades and hard conflicts. Model and
  coding-agent paths are checked; provider responses are mocked with network
  creation blocked and no reservations.
- Fixture storage, service state and handoff export preserve `rejected` /
  `not_a_fit`; isolated execution rejects the case before running anything.
- A browser regression uses the shared validator's normalized fictional result.
  It appears under “Not a fit”, not “Investigate”, with no asserted execution or
  POST. Older partial-full-rejection UI behavior remains covered. No live account
  app, GitHub, provider or acquired code is used by these browser tests.
- Historical-contract fixtures cover both 21 and 22, distinct current IDs,
  visible staleness and byte-equivalent stored records with zero spending.
- The complete Windows offline suite passes **915 tests**, including the local
  browser fixtures; source startup `app.py --help` and `git diff --check` pass.

## Retained-output replay, not a new model result

The three frozen contract-22 jobs (escape-string-regexp, Zod, python-dotenv)
were revalidated ephemerally using their stored original comparison outputs,
pinned sources/demand, provider citation normalization and inspection-only
proposal gate. The provider completion was mocked with the retained output;
network creation and AI reservations were blocked. Nothing was imported/saved
as a new analysis, and no acquired/generated code was executed.

Across **11 assessments**, six previously revived explicit rejections now stay
rejected and receive `not_a_fit`: the README-only comparison, Zod's three
non-contributions, and python-dotenv's environment-documentation/data-dictionary
comparisons. The VS Code hard-conflict rejection remains rejected; four partial
mechanisms remain `investigate` / `partial_contribution`. No result becomes eligible.

Checks and bridges are unchanged after the normal proposal/storage redaction
gates. Both Mosfet proposals retain their pre-existing **blocked inspection ZIP**
status caused by package bounds; JSON handoff remains available. This is not a
new extraction/validation failure or a claim that those ZIPs are downloadable.

Independent read-only hashing confirms all **12 Missing Link tables** and **111
frozen evaluation JSON artifacts** remain identical around the fix/tests/replay.
The original USD 10 ledger remains **409 reservations / USD 6.3181696**, no jobs
are queued/running, and python-babel/Babel remains paused. Unknown old attempts
stay charged. Local ignored audit files are retained separately from published
reports and account evidence.

The [remaining live segment (PR #43)](https://github.com/Daniele-Cangi/RepoTraction/pull/43)
is documentation-only and separate from this code correction. Discovery relevance,
broader parsers/resolvers, UI/key entry and forced isolation are not included.
Next is a targeted review of this invariant, not a universal completeness review
or another paid run.
