# Native acceptance, before source search

Target: NetworkX `9d866a5f447d9fe1c989b31f90c520dc2813ee26`, issue #8128.
The public request asks for minimum-length simple cycles and an algorithmic
advantage over generating all cycles and filtering. It does not specify a
workload, a speedup, a public signature or a universal polynomial-time algorithm.
The last comment explicitly raises the Hamiltonian-cycle difficulty. No general
complexity improvement or practical production need is established by this case.

## Fixed experimental interpretation

Use `nx.simple_cycles(G, length_bound=None, *, min_length=0)`. The lower bound
is inclusive: `min_length <= len(cycle) <= length_bound`, with no upper limit
when `length_bound is None`. The issue's prose says "at least" but its sample
filter uses `>`; inclusive semantics and the exact signature are experiment
choices, not an upstream-approved API. Negative lower bounds raise ValueError;
an interval whose lower bound exceeds its upper bound yields no cycles.

1. Return every eligible cycle exactly once, preserving directed rotation and
   undirected rotation/reversal equivalence. Preserve existing multigraph node-
   sequence semantics, self-loops, parallel-edge 2-cycles and unsortable labels.
2. Default calls retain existing results, including positional `length_bound`.
   Do not mutate the input. Both bounded and unbounded calls must work.
3. Keep the entire pinned `networkx/algorithms/tests/test_cycles.py` unchanged.
   All available native tests must pass, with skips/dependencies reported.
4. Validate against the frozen brute-force oracle on small graphs, the public
   example and seed-fixed controls. Test data and timing workloads are available
   equally to both arms; they are not secret or adapted after a source is seen.
5. Measure the requested efficiency separately from API completion. A wrapper
   that filters current output is a legitimate functional baseline, not proof
   of less cycle-search work or a new useful algorithm.

The extra input-error and compatibility checks are assessor controls, not new
claims about what the requester explicitly demanded. A mismatch on those is
reported separately from failure of the requested cycle operation.

## Comparison and decision

`native_acceptance.py` freezes the oracle, graph construction, output digest and
timing procedure. The unmodified target plus a visible enumerate/filter adapter
is the executable reference. Freeze its observations before either solver or
Missing Link searches. The adapter never patches target code. A candidate must
also reproduce the reference digest on every timed workload, outside timing.

The positive workload families are dense directed, dense undirected, and graphs
with many short cycles plus a longer cycle. Output-rich, sparse and acyclic
controls guard against just optimizing empty output. These are synthetic probes
of the request, not a representative sample of production use. Fast rejection
of `min_length > |G|` alone earns no efficiency-discovery credit.

After correctness passes, evaluate the pinned original, direct patch and assisted
patch sequentially on the same idle host/interpreter. Use nine batches, rotating
the arm order each batch, the same baseline-calibrated iteration counts and
250 ms minimum target batch duration (100 iterations maximum). Report every
batch, output count/digest, median and range. Do not compare timings from agents
running concurrently. Fixed final evaluation is outside both development budgets
and supplies no feedback for another implementation attempt.

An efficiency demonstration requires at least 1.25x geometric-mean speedup on
the four positive workloads against enumerate/filter, and no control slowdown
greater than 20%. To attribute additional practical help to Missing Link, require
the same margin against the direct arm as well, with the aggregate ratio above
1.10 in at least seven of nine paired batches. Otherwise report parity, regression
or inconclusive timing; do not tune workloads or thresholds. These are decision
thresholds for this experiment, not significance tests or requester requirements.

A partial functional contribution can instead be reported if the assisted patch
passes an original requested invariant that the direct arm still fails, without
losing another requested invariant or native regression. An API-only advantage
is not evidence of a better search algorithm. Report all failures, not just counts.

Any assistance claim additionally needs exact source revision/citations, the
specific transferred operation and its corresponding target change, plus a check
whether the direct arm found it independently or the public discussion already
supplied it. A self-report, relevant hit, named technique or donor-only test is
insufficient. A single unblinded pair cannot establish causality, general novelty,
maintainer acceptance or the necessity of external help.

If both solve the same operation with no stable efficiency advantage, that is
no demonstrated incremental benefit. If Missing Link chooses direct/defer/none,
record that decision and continue the assisted solver with the remaining budget;
do not cancel the control, add a donor or select another problem.
