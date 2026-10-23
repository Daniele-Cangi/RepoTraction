# Demand selection before reading candidate discussions

Recorded before the search or any donor/source search for this cohort.

- Search public open issues in `networkx/networkx`, with label `enhancement`.
- Exact query: `repo:networkx/networkx is:issue is:open label:enhancement`.
- Sort: updated descending. Inspect at most the first 12 results, in returned order.
- Choose the first request that specifies an observable software operation or invariant,
  can be exercised on a pinned target locally without paid services, special hardware,
  private data or external services, and is not already implemented on that target.
- Exclude administrative/documentation-only requests, tracking umbrellas without one
  bounded operation, requests with no independently definable acceptance, and requests
  whose discussion already supplies a complete implementation. Record exclusions.
- Do not exclude a request merely because a direct solver might solve it.
- Do not consult other projects, solution sources, patches or donor mechanisms during
  selection and native acceptance preparation. Public discussion suggestions are part
  of the common input and must be disclosed.
- Stop after this pool. If none qualifies, report that outcome rather than silently
  broadening the search or selecting an attractive solution.

The project choice is deliberate, not a random sample: NetworkX is executable locally
and permits native checks of algorithms and invariants. One selected case cannot
establish general effectiveness or success rates across repositories.

## Empty initial pool and metadata correction

The initial exact search returned zero issues. No issue body was returned or read.
Repository label metadata (GitHub labels endpoint) shows `New feature` and
`type: Enhancements`, rather than `enhancement`. Before reading any candidate,
correct only the label predicate to match those existing labels:

`repo:networkx/networkx is:issue is:open label:"New feature","type: Enhancements"`

The other bounds, returned order, eligibility criteria and stop rule are unchanged.
This is a recorded second acquisition, not a claim that the empty query selected a
case. No new pool is permitted after these first 12 candidates.
