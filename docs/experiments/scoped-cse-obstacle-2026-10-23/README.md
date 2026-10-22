# Selected obstacle: scope-safe CSE for finite runtime sums

The selected public software defect is [SymPy #27971](https://github.com/sympy/sympy/issues/27971):
`lambdify(..., cse=True)` can extract a repeated expression out of the sum that
binds its index. The resulting callback fails when called. It is still reproducible
on the acquired main revision `c60dafcb4e3961aa6dea5193e9e1e864b662141d`,
version 1.15.0.dev. All changes here are RepoTraction experiment artifacts.
The target checkout is unmodified. Satellite was not read, modified or executed.

The issue author's reduced example originates from gravity-model work. We did
not acquire the original application or its data. This is a real upstream bug
with a reduced reproduction, not an independently observed blocked agent.

## Criteria fixed before solution-source search

[Acceptance](acceptance-before-source-search.md), the native
[fixture](test_scope_contract.py), [demand](demand.json) and upstream license
were committed at `471213561b288d6f616540f216b5f758955f70b3`, before measuring
the extended controls and before any donor search. The initial reported bug and
the target's own workaround APIs were inspected before that commit. Selection
was purposive, not randomized or blind; [selection.json](selection.json) records
both target-demand queries and known direct ideas. Other returned issues were
not natively judged and must not be treated as negatives.

The source issue's literal expression has a plus sign, while part of its printed
transcript has a minus sign. We retain the literal plus-sign expression and use
an independent Python/math oracle: approximately **30.0179563159036** for the
reported values. We do not change the expression to reproduce the inconsistent
printed number.

The six fixed families have **13 input samples**: the reported sum, independent
sums with the same index name, nested dependent bounds, loop-invariant shared
work, a symbol free outside and bound inside a sum, and ordinary CSE without sums.
The semantic contract and an additional deterministic repeated-work criterion
are evaluated separately. The operation-count criterion is an explicit engineering
goal for useful optimization, not a numerical threshold quoted from the reporter.

## Measured direct baselines

All measurements below use the actual pinned SymPy, not a rewritten CSE simulator.
The numeric backend is scalar `math`; its counted sine function returns the same
value as `math.sin`.

| Baseline | Correctness over 13 samples | Correctness plus repeated-work criterion | Literal reproduction |
| --- | --- | --- | --- |
| Native `cse=True` | 2 pass, 2 wrong values, 9 exceptions | 2 pass, 11 fail/error | `TypeError`, index escapes its loop |
| Real workaround `cse=False` | 13 pass | 0 pass, 13 retain repeated work | Correct, 8 sine calls |
| Public API `cse(ignore=all Sum-bound symbols)` | 13 pass | 2 pass, 11 retain repeated work | Correct, 8 sine calls |
| Hand-written loop for the literal formula | Correct for that formula | 4 sine calls for 4 iterations | Not a generic symbolic compiler |

The ordinary CSE-without-sums control passes under the ignore-bound workaround;
disabling all CSE loses that already available optimization. The shadowed-symbol
control shows a silent numeric error under stock CSE, not merely an exception.
For the generic workarounds, the remaining obstacle is obtaining the local
reuse while preserving binding semantics. Correctness-only workarounds are useful
and must not be discarded to make an external technique look better.

These counts do not establish whole-program latency, an asymptotic bound, or a
performance advantage over a hand-written implementation. The latter already
meets the count target for the literal example. The potential generic contribution
would be generating correct optimized callbacks from the supported expression
family rather than rewriting each formula by hand.

## Verification and scope

[baseline.json](baseline.json) records exact target revision/blob/file identities,
portable fixture hashes, environment, generated code and outcomes.
[native-logs.json.gz](native-logs.json.gz) contains the six captured fixture runs
(three policies, correctness-only and combined criteria) and the final upstream
regression output. Expected contract failures are the observed target obstacle;
they are not RepoTraction regressions or failed model responses.

The existing upstream CSE regressions also pass: **2 passed, 159 deselected**
from `sympy/utilities/tests/test_lambdify.py -k cse`. The first collection attempt
could not run tests because Hypothesis was absent. The required test dependencies
were then installed only in ignored experiment data, and collection/execution
passed without changing target code. No product dependency was added.

Native observations are **Windows / Python 3.13.5 only**. The ordinary RepoTraction
Windows/Linux CI checks this PR independently; it does not install SymPy or execute
this experimental fixture. Do not claim native cross-platform verification from
the RepoTraction matrix. No paid AI call, subagent, donor search, solution package
selection, upstream write or new runner/transport was used.

To reproduce the contract, acquire the target at the exact revision, then run the
ordinary unittest fixture with that checkout first on Python's import path:

```powershell
$targetRoot = (Resolve-Path data/discovery-obstacle-baseline-2026-10-23/target).Path
$contractFile = (Resolve-Path docs/experiments/scoped-cse-obstacle-2026-10-23/test_scope_contract.py).Path
python -I -c "import sys,runpy; target,fixture=sys.argv[1:]; sys.path.insert(0,target); sys.argv=[fixture]; runpy.run_path(fixture,run_name='__main__')" $targetRoot $contractFile
```

The default policy is native CSE: failure is expected on this pinned baseline.
For the correctness-only comparison, load the same fixture using `runpy.run_path`,
set `ScopeContract.check_work=False`, and run the class with unittest. Set
`ScopeContract.cse_policy=False` for no-CSE; for the conservative policy, supply a
callable collecting Sum `bound_symbols` with `sympy.preorder_traversal` and returning
`sympy.cse(expr, ignore=bound_symbols, list=False)`. These are target API controls,
not a replacement compiler. Fixture hashes use bytes with CRLF normalized to LF
only. The upstream license is copied verbatim, including its original whitespace.

## Next gate

The controls are authored and visible, not held out. Passing them is not proof
for every symbolic binder or numerical input. A future correction must operate
on expressions generally rather than dispatching on fixture names or values,
and must retain the relevant native upstream regressions.

First make a direct attempt on the unchanged contract using the target's existing
hooks and all already known ideas. In particular, the maintainer's scope-handling
suggestion and our helper-compilation idea are baseline knowledge, not discoveries
to credit to a later donor. If the direct attempt passes, stop and record that
Missing Link was unnecessary for this case.

Only a remaining failed criterion would justify preparing a request-led source
search. No source has been chosen and no search is started here. This preparation
does not claim an external idea is necessary, a new connection exists, or another
agent has been unblocked. Any later proposal must improve on the conservative
direct workaround while retaining correctness and the ordinary CSE control.
