# Missing Link: offline query and selection audit

## Outcome and scope

One bounded query-generation defect was reproduced and corrected: removing a
compound source package name could erase useful context from the first search
phrase, while an intact contextual alternative was already available. This is
an offline retrieval correction, **not evidence of improved live discovery**.
Candidate ranking, provider prompts, capability limits and compatibility verdicts
are unchanged. No feature, parser expansion or logic in `app.py` is added.

The audit starts from merged `d6c9949`, analysis contract **23**, and reads the
three retained contract-22 jobs from the
[first](missing-link-contract22-focused-2026-10-03.md) and
[remaining](missing-link-contract22-remaining-2026-10-03.md) live segments. Only
stored source snapshots, model outputs, retrieval metadata and selected
discussions are used. No GitHub/provider requests, manual imports, new analyses,
native execution of acquired/generated code or isolated runs are performed.

## Capability selection: what was actually supplied

Re-extracting declarations from the pinned acquired text and running the current
bounded selector reproduces the **exact ordered capability IDs** recorded in
each original enrichment call's context report:

| Retained input | Structural capabilities | Offered to enrichment | Model-enriched |
| --- | ---: | ---: | ---: |
| `sindresorhus/escape-string-regexp` | 2 | 2 | 1 |
| `colinhacks/zod` | 99 | 30 | 8 |
| `theskumar/python-dotenv` | 77 | 30 | 8 |

The dotenv Python literal-`__all__` hints correctly prioritize all eight acquired
public API candidates, including `load_dotenv` and `dotenv_values`. Losing the
useful query context happens **after** this selection, not because those APIs
were withheld from the model.

Zod exposes a separate coverage limitation: its acquired `core/parse.ts` contains
typed exports such as `safeParse`, initialized through factory calls, that the
partial JS/TS declaration scanner does not turn into capability candidates.
The offered sample consequently contains internal helpers and locale functions;
query generation cannot recover an API absent from that candidate set. This is
not proof that Zod lacks these operations. A narrowly specified callable-export
coverage task needs its own positive/negative fixtures; universal npm/resolver
completeness is not included in this correction.

## Reproduced defect and bounded correction

For `python-dotenv`, the source-name filter recognizes the whole token sequence
`python dotenv`. The old first-contextual-phrase rule therefore selected weakened
phrases even when subsequent model terms needed no source-name stripping:

| Capability | Previous generated phrase | Generated phrase after correction |
| --- | --- | --- |
| `load_dotenv` | `environment loading` | `environment variable override` |
| `dotenv_values` | `parse to dictionary` | `dotenv stream parsing` |

The correction prefers the **first supplied multiword phrase that needs no
source-name removal**. If none exists, the first cleaned contextual phrase
remains the fallback; specific singleton mechanisms and fragmented-term cleanup
remain supported. Generic-word cleanup alone does not demote a phrase. Nothing
is inferred, added to a search term or reintroduced from the excluded source name.
An individual mechanism word is not banned merely because it is also part of a
compound package name.

The other dotenv query (`python build dotenv command string`) is unchanged, as
are all Zod and escape-string-regexp queries in the ephemeral replay. The three
query cap, per-file/quality prioritization, phrase/query length bounds, public/open
scope and explicit query/issue overrides remain intact. Better specificity here
does **not** establish that these alternative queries return more useful issues.

## Candidate ranking: evidence, not a speculative rewrite

The retained selections demonstrate lexical false positives: the dotenv command
query selected the VS Code workspace-symbol issue, and the generic dictionary
query selected study-table documentation. Title overlap is only a retrieval
hint, not evidence that the implementation meets a demand. Full discussion and
operation checks correctly keep these comparisons ineligible.

The current ranking explicitly balances projects and queries before title
overlap; its existing regression tests require this behavior. The saved search
record retains selected candidates with query indices/upstream ranks and page
counts, **not the complete unselected pool**. Search responses are not cached by
the job reader. Therefore this audit cannot reconstruct a different full-pool
ranking or demonstrate that a better unselected issue was available. No ranking
rewrite, invented replacement candidate or quality gain is claimed.

For the next controlled experiment, the owned evaluation harness should retain
the sanitized bounded retrieval pool (public URL, title, state and per-query rank,
not raw bodies) before selection. That permits an honest selection audit without
adding manually chosen issues or changing the search budget.

## Verification and preservation

- Five new offline tests cover the retained compound-name cases, alternative
  source-name spellings, model/maintainer inputs, stripped-phrase fallback,
  generic cleanup, input immutability and service search/checkpoint persistence.
  The new defect regressions reproduce the previous behavior before the fix.
- All **49** discovery tests pass, including package/fragment filtering, singleton
  mechanisms, module diversity, public scope, explicit overrides and frozen
  candidate order on resume.
- The complete Windows offline suite passes **920 tests**. Source startup
  `app.py --help` and `git diff --check` also pass.
- Read-only before/after hashing preserves all **12 Missing Link tables** and
  **111 frozen evaluation JSON artifacts**. The replay computes new query strings
  only in memory and separate ignored audit files; historical queries, candidates,
  verdicts and receipt records are not rewritten.
- The original USD 10 allowance stays at **409 reservations / USD 6.3181696**
  conservatively reserved, leaving **USD 3.6818304**. This is not an invoice;
  unknown earlier attempts remain charged. No jobs are queued/running, and the
  earlier Babel job remains paused.

Analysis contract 23 stays unchanged: this patch changes automatic retrieval
phrase preference, not result normalization or identity. Persisted candidate
checkpoints continue to bypass retrieval/reranking. The existing evaluation
server remains loaded on merged `d6c9949`; it is not restarted onto unreviewed code.

Next: review this invariant, then freeze a separate five-repository, repository-only
experiment with no preselected issues, bounded spend inside the original allowance,
retained retrieval pools and a failure/stop rule. Only an eligible, source-grounded
lead justifies an isolated test. UI/key-entry work and broader parser support do
not replace that validation gate.
