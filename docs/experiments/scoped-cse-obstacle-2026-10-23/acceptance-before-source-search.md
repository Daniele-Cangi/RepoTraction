# Frozen scope: correct reuse of repeated expressions inside finite sums

Target: SymPy `c60dafcb4e3961aa6dea5193e9e1e864b662141d` (observed main,
version 1.15.0.dev). Public demand: sympy/sympy#27971. No donor search or
source-of-solution inspection has occurred. Target code and its own documentation
are baseline evidence, not donors. This file and the native fixture are committed
before measuring the extended controls or looking for external techniques.

## Need and limits

The reported `lambdify(..., cse=True)` callback hoists a repeated expression using
a sum's bound index into an outer assignment. Calling it then fails. The literal
reported expression has a plus sign; its native reference value is about
30.0179563159, not the minus-sign transcript's 29.9823753593. Do not change the
literal expression to fit that transcript.

The original correctness problem has an available workaround: disable CSE.
The target's public `cse(ignore=...)` API also supports a conservative direct
baseline that ignores every Sum-bound symbol. These alternatives must be credited.
The further engineering question is whether useful repeated work can be eliminated
without moving a computation outside the scope of its inputs. This is a derived
optimization contract, not a claim that the issue author supplied numerical
operation-count thresholds or has no workaround.

The maintainer already suggested special handling of bound symbols. Merely
recommending scope awareness is therefore not a new contribution. Our own direct
ideas include lowering each sum through a helper compiled in its local scope;
that idea must also be disclosed to a future direct attempt and not credited to
a subsequently found source.

## Fixed native contract

Use `test_scope_contract.py` against the exact target checkout with the scalar
math backend. The counted sine function returns `math.sin` unchanged. Six test
families contain 13 fixed input samples:

1. The reported finite runtime sum, including different lengths and values.
2. Independent sums using the same bound-index name.
3. Nested finite sums with the inner bound depending on the outer index.
4. Repeated work independent of the loop, shared across returned expressions.
5. The same symbolic index free outside a sum and bound inside it.
6. Ordinary CSE without sums, to preserve already useful optimization.

Correctness requires successful construction and evaluation, matching independent
Python/math formulas within relative and absolute tolerance 1e-12. Returned
structure must be preserved. Different calls must honor their own input values.
The supplied finite positive bounds and adequately sized scalar lists define the
domain; infinite sums, integrals, symbolic limits and other backends are excluded.

The incremental optimization criterion is at most one sine evaluation for each
required loop iteration, plus one for a shared outer computation where present.
These deterministic counts are an engineering target fixed before donor search,
not a user-facing speedup claim. No particular algorithm, helper layout, variable
name or generated-source spelling is required. Whole-workflow performance and
construction overhead would need separate measurement before a speed claim.

## Baselines to measure unchanged

- Ordinary public `lambdify(..., cse=True)`.
- The real workaround `cse=False`: correctness reference, with optimization losses
  reported rather than hidden.
- A generic target-API-only workaround: collect all Sum `bound_symbols`, then
  supply `lambda expr: sympy.cse(expr, ignore=bound_symbols, list=False)`.
- A hand-written loop for the literal reported formula, computing its sine once
  per iteration. This is a strong direct comparator for that formula, not an
  automatic compiler for arbitrary expressions.

Measure correctness and work separately. A correctness-only success is not a
complete optimization success; no-CSE and ignore-bound baselines remain usable.
Do not compare only with the broken default and call that an external advantage.

## Advancement rules

This PR selects the obstacle and freezes baseline/tests only. It does not run
Missing Link discovery, dispatch agents or authorize paid calls. Next, a direct
attempt may use the target's own code/hooks, the known scope-handling suggestion
and helper-compilation idea on these unchanged tests. If it meets the contract,
stop: no external source is needed for this case. Failure of the stock API is not
evidence that a development agent is blocked or that Missing Link is necessary.

Only after a remaining criterion is identified can a separately reviewed
request-led experiment select queries and a source. No source is preselected here.
If that later experiment returns a valid empty result or a direct/defer decision,
stop and report it. Candidate validation failure also stops this one-case probe;
there is no second case, retry, replacement or hidden continuation. Never alter
these criteria after inspecting a source to manufacture a positive result.

All modifications and artifacts belong to RepoTraction. The target checkout under
ignored RepoTraction data is unmodified; no upstream issue/PR writes or merges,
Satellite operations, new runner/transport or paid AI calls are part of this work.
