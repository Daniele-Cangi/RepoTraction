# Native acceptance before an agent attempt or source search

Target: NetworkX `6da4704cbf32ba6f50f6d9c46cc0a071e3a87985`.
Public need: #3825 asks for faster minimum spanning arborescences on large matrices;
maintainers explicitly prefer an algorithmic improvement. It provides no original
matrix, desired runtime, or original developer deployment. The following graph
family and threshold are engineering experiment choices, not maintainer demands.

1. Keep the existing `minimum_spanning_arborescence` API and exact optimum. Every
   successful result must span the original nodes, have n-1 original directed
   edges, be acyclic and connected, and have optimal total original weight. Do not
   replace this with greedy edges, a cost alone, an approximate answer or a known
   optimum hard-coded for the fixture. Tied optimal edges need not be identical.
2. Run `native_acceptance.py` against the actual modified target. Its independent
   exhaustive parent-choice oracle covers nested cycle choices, 12 small seeded
   positive/negative-weight graphs, parallel edges, mixed labels, self-loops,
   default/custom weights, preserved attributes, partitions, tied weights,
   singleton and disconnected cases. It uses no optimum branching solver to
   calculate its answer. The existing API fills missing weight attributes; that
   control compares default-normalized input, permitting absent or explicitly
   default-valued weights. All other attributes and fully weighted inputs must
   stay unchanged. Fixing that unrelated existing default-fill side effect is
   not a new required obstacle.
3. Run the unchanged upstream tree regression directory, reporting skips/xfails,
   environment changes and new dependencies. A faster implementation in this
   real API is required; donor-only or stand-alone prototype results do not count.
   No new runner, transport or product infrastructure is part of this case.
4. Performance family: the committed `measure_native.py` constructs a complete
   weighted digraph, no self-loops, with integer weights 1..1,000,000. Public
   development cases are n=50/100/200, seed=20261012. Fixed assessment cases are
   n=75/150, seed=20261013. They are synthetic matrix-shaped cases, not the user's
   unavailable matrix. Hash the input and check the returned topology, weight and
   input preservation. For candidate assessment, alternate original and candidate
   in three fresh paired processes per case on the same platform/environment.
   Record startup/total process wall time separately from algorithm wall/CPU time.
   Each process has a 30-second observation cap; retain any timeout as censored.
5. A full local performance success needs median algorithm wall time at least
   2x lower than the original at both n=100/200 and the fixed n=75/150 assessment
   cases, while all correctness controls pass. At n=50 the median may not regress
   by more than 20%. These are frozen practical benefit gates, not a complexity
   proof or a generally representative workload. Report all measurements, not only
   wins. An uncensored comparator is required for an exact ratio; setup or censored
   observations without a demonstrable bound remain inconclusive. Do not tune
   seeds, thresholds, weights, tests or the observation cap after candidate results.
6. An implementation may cover a clearly declared supported fast path and retain
   the original API path elsewhere. Disclose that scope and any changed guarantee;
   all benchmark cases and the original correctness checks remain in scope.
   Before any implementation is ready for merge, relevant native Windows/Linux
   tests and the complete product CI must pass. This preparation alone is not a
   modified-target or portability result.

## Direct comparison and stop

The current native implementation is a working exact direct baseline. The issue
already supplies Tarjan/Gabow references and an unfinished public fork. Related
open PR #2117 proposes avoiding retained intermediate graphs. Disclose all this
to the ordinary agent; it may investigate normally and use that work. None is a
novel Missing Link donor. Their performance on current main is unmeasured. If a
public direct proposal is adopted, it must be assessed as a direct alternative,
including adaptation cost; do not call the current baseline the best possible.

One ordinary fresh-context attempt, if separately authorized, comes first. Freeze
its patch and failures. If it meets the criteria, stop this case with another
direct success. If it does not, identify the exact failed invariant or measured
cost before any source investigation. A budget-limited attempt is an observed
failure to finish within the bound, not proof the agent could never solve it.

Only then could one existing Missing Link request-led investigation propose a
source-owned idea, with no operator-selected donor or target bridge supplied.
Ordinary and assisted continuations would need the same checkpoint/tools/limits,
separate authorization, and source-to-target adoption evidence. A narrower partial
advance may be useful but must be reported against the failed criterion rather
than labelled full performance success. No such search, continuation or paid
call is authorized or executed by this preparation.
