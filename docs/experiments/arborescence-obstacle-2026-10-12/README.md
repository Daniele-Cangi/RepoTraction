# Selected next obstacle: exact minimum arborescence at lower cost

After #127's direct success, choose the real request
[NetworkX #3825](https://github.com/networkx/networkx/issues/3825).
The maintainer calls for a faster algorithm; a public implementation attempt
describes getting stuck connecting cycle contraction to expansion. That is
historical human evidence, **not** an observed block of a new agent.

The native target is pinned to `6da4704cbf32ba6f50f6d9c46cc0a071e3a87985`.
This preparation supplies a real software cost and exact independent small-graph
controls. It demonstrates no Missing Link contribution, no new patch, no adoption
and no general speedup. No source/donor search, new agent or paid API call ran.

| Synthetic complete digraph | Edges | Algorithm wall time | Returned weight |
| --- | ---: | ---: | ---: |
| 50 nodes | 2,450 | 0.318 s | 831,069 |
| 100 nodes | 9,900 | 2.234 s | 1,038,891 |
| 200 nodes | 39,800 | 18.598 s | 1,078,246 |

These are one observation per size on Windows/Python 3.13.5, actual current native
API, seed 20261012. Graph construction and checks are outside algorithm timing;
process wall time is also retained in [baseline.json](baseline.json). This is
not the user's original matrix, which was not supplied. Three points/one seed
do not establish asymptotic complexity or representative application benefit.
All returned graphs spanned the inputs and the fully weighted inputs stayed
unchanged. Large-case optimal weights are native solver outputs, not independently
enumerated optima; only the small-graph controls have that independent oracle.
The benchmark is synthetic; a future useful result still needs exact
native answers and cannot be presented as a user deployment.

[native_acceptance.py](native_acceptance.py) passes seven test methods, including
12 seeded subcases and an independent exhaustive optimum oracle. The unchanged
native tree directory reports **219 passed, 2 skipped, 1 xfailed**; see
[native-tests.log](native-tests.log). Skips are upstream slow tests and the xfail
is an existing upstream expectation. No original tests were edited or removed.

Initial test setup failed because installed NetworkX 3.3 metadata registered an
obsolete backend name while imports used pinned 3.7 code; [setup-failure.log](setup-failure.log)
retains this failure. An isolated venv with existing system dependencies and an
offline editable install (`--no-index --no-deps --no-build-isolation`) of the pin
provided correct package metadata. Global packages and tracked native source
stayed unchanged. Benchmark algorithm measurements preceded this metadata fix;
any future paired comparison must use the same corrected environment for both
variants and take fresh original measurements. The initial controls also caught
a mistaken oracle keyword and an unrelated existing missing-weight/default-fill
side effect. Both were resolved before freeze, with no candidate implementation
in sight; default-normalized input equivalence is explicit in the final criteria.

[demand.json](demand.json) preserves complete issue discussion and related direct
work. The unfinished `CyberMobius` fork and open direct PR #2117 are already known
alternatives. Their runtime on current main is unmeasured; a faster proposal must
be compared with any adopted working direct alternative. Ordinary research is
allowed. They cannot be relabelled novel external techniques.

[selection.json](selection.json) records purposive reconnaissance and exclusions,
including jsonschema #1536's already published direct fix. This is neither a
random sample nor a rule selected before reading issues. Donor availability did
not choose the need. The prior #125 and #127 results remain unchanged.

The [acceptance](acceptance-before-source-search.md) and [ordinary prompt](common-agent.md)
are frozen before an attempt or source search. The 2x gate and additional seeds
are experiment choices, not maintainer requirements. First seek a direct native
implementation; stop if it succeeds. Assistance requires an observed residual
obstacle, a concrete source-owned contribution and matched ordinary continuation.
No further cohort, old allowance, timeout change or automatic merge is implied.

The upstream [automated contribution policy](https://networkx.org/documentation/latest/developer/contribute.html#automated-contributions-policy)
was read as required by its AGENTS.md. This local RepoTraction study submits no
upstream issue, comment or PR. A future upstream contribution is outside this
stage and requires the personal human understanding/review specified there.
Product CI remains unchanged; native Windows/Linux proof will be required before
any future target implementation is considered ready for merge. There is no new
runner, service, framework, store, provider, scheduler or infrastructure change.
