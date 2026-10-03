# Missing Link discovery relevance audit

## Outcome

The offline replay reproduces every saved query and candidate decision in the
latest three-source experiment. **No ranking-contract regression was found.**
The weak point is retrieval relevance, not evidence that a strict qualification
gate should be relaxed. Six of the nine selected discussions stay selected even
when title overlap is moved ahead of diversity. Several of those six are already
known non-fits from acquired context.

No production ranking, provider contract, historical assessment or eligibility
changed. No GitHub acquisition, paid call or bridge execution occurred.

## Scope and reproducibility

This 2026-10-04 audit uses the retained pools and checkpoints from the
[contract-25 repository-only test](missing-link-contract25-three-repo-result-2026-10-03.md),
not a fresh observation of GitHub issues. Sources are `jaraco/path`,
`pallets/itsdangerous` and `d3/d3-array`, at the job IDs and revisions pinned in
that report. Production code is merged `8e5732d5d776f22bece1ba8a264008ef13279fd0`.

The owned local audit reads SQLite in `mode=ro` and the frozen sanitized search
pools. It verifies:

- Recomputed `problem_queries` equal the saved queries for all three jobs.
- `select_candidates` returns the exact saved three candidates and pool size.
- An independent priority trace reproduces the complete production ordering of
  each pool, not just its first three candidates.
- Single-capability query derivation identifies the mechanisms feeding each
  saved query without issuing alternative searches.
- Before/after hashes match for 12 Missing Link tables and 369 prior artifacts.

The private helper and outputs are under
`data/missing-link-discovery-relevance-2026-10-04/`; local data stays ignored and
is not published. Three synthetic audit checks and all 49 focused discovery
tests pass. This documentation-only audit did not rerun the full application
suite; the preceding merged change had 980 passing local tests.

Original allowance remains **461 reservations / USD 7.2123066**, with
USD 2.7876934 unreserved. Reservations are conservative accounting, not an invoice.
Paused investigations and unknown earlier attempts remain unchanged.

## Query coverage and thin pools

Each source has eight model-enriched capabilities, but only three contribute a
query. Quality tiers and module diversity intentionally bound exploration; the
other five are not searched in this segment. They can still participate in later
comparison. An omitted query is not evidence of a missed useful connection.

| Source | Query mechanisms | Returned rows per query | Candidates after within-source deduplication |
| --- | --- | --- | ---: |
| Path | `only_newer`, `compound`, `load` | 39 / 2 / 37 | 78 |
| ItsDangerous | `dump_payload`, `want_bytes`, `TimestampSigner.sign` | 40 / 40 / 40 | 120 |
| D3-array | `bin`, `bisector`, `group` | 3 / 38 / 38 | 79 |

Path's chmod query returns only two titles, neither sharing a query term.
D3's histogram query returns three titles, also with zero title overlap.
D3's bisector query returns 38 candidates; only the selected hosted-help issue
has any title overlap, through the single word `search`.

Across the three separately deduplicated pools, 211 of 277 candidate hints have
zero title overlap with their retrieving query. **This is not a 75.6% irrelevance
rate**: searches include issue bodies, and those bodies are not retained for
unselected candidates. Zero-overlap titles may conceal relevant demand.

## What diversity changes

The declared policy is external/open first, then project and query diversity,
then title overlap and upstream rank. Existing regression tests explicitly
require diversity ahead of overlap. At the third selection in each source, an
unrepresented query wins over additional lexical hits from an already-used one.

An offline counterfactual retains external/open guards but moves title overlap
ahead of diversity. It changes only the third candidate in each source:

| Source | Actual third candidate and overlap | Lexical-first alternative and overlap |
| --- | --- | --- |
| Path | zedBSD #2, POSIX compliance; 0 | DazzleTools/preserve #39, destination-aware MOVE/COPY; 2 |
| ItsDangerous | nz-election-evidence #10, external timestamp anchor; 1 | seerdb #1496, text bytes versus hex decoding; 2 |
| D3-array | Timeline #440, graph roadmap; 0 | RuboCop #11375, hash-layout grouping; 1 |

These alternatives are **unqualified search hints**, not better leads. The
counterfactual is not installed in production. Its local candidate objects retain
their original production `selection_order`; their list position represents
counterfactual order. No semantic label or eligibility is assigned to them.

Two actual zero-overlap selections yielded grounded but ineligible partials:
zedBSD's traversal primitive and Timeline's arithmetic mean. A blanket
zero-overlap rejection would discard those observations. Conversely, RuboCop's
layout grouping is a different concept from D3 runtime data grouping despite
the shared word. A lexical-first rule alone is not a demonstrated fix.

## Why lexical similarity is insufficient

Retained acquired context, rather than title intuition, establishes these
already documented mismatches:

- **Copying:** modification-time skipping does not provide Hermes's failure-safe
  atomic publication.
- **Tokens:** ItsDangerous's compressed serialized bytes are at most a transport
  primitive for an LLM token-compression study, not measured model-token savings.
- **Bytes:** a scalar UTF-8 conversion does not detect mixed NumPy array inputs.
- **Search:** a sorted-array insertion-point bisector is not hosted-help search.
- **Grouping:** runtime collection grouping is not a TypeScript key-tree generator.

The weak retrieval therefore survives increased title overlap. Missing runtime,
data-shape, acceptance and adoption context matters more than shared vocabulary.
Eight of nine acquired discussions also remain context-incomplete. The previous
experiment's three partials, eight non-fits, one similarity-only result and zero
eligible leads remain exactly as stored.

## Next bounded step

Before another paid discovery segment, specify and validate a **demand-to-mechanism
triage**, separate from final compatibility qualification:

1. Use retained acquired discussions to test whether runtime, input/output shape
   and requested outcome distinguish the known non-fits above. Preserve unknown
   or incomplete demand; do not invent positive labels from partial contributions.
2. Freeze the triage policy, its context/request bounds and positive/negative
   fixtures before testing a new candidate-selection strategy. Titles alone must
   not produce compatibility verdicts or blanket rejection of broad requests.
3. If assessing the three counterfactual alternatives, acquire their discussion
   contexts under a separately declared read-only API protocol. Do not import a
   hand-written analysis or claim they are useful before acquisition.
4. Only then compare policies on a fresh, frozen repository-only segment within
   the unchanged cumulative allowance. Report coverage, correct rejections and
   eligible utility separately; do not select cases after seeing outcomes.

No new strategy is validated by this audit. A grounded eligible connection is
still required before isolation, UI redesign or key-entry work. Intermittent
GitHub identity failures remain a separate pending diagnostic task.
