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
