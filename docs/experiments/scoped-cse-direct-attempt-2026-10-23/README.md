# Direct attempt: local CSE for finite runtime sums

The direct attempt meets the full frozen contract: **13/13 samples pass both
numeric correctness and the sine-work limit**. Stop this case before source
search. No Missing Link discovery, donor, subagent or paid AI API was used.
This is a successful direct solution, not evidence of externally assisted
reasoning or autonomous software discovery.

## Fixed starting point

[PR #137](https://github.com/Daniele-Cangi/RepoTraction/pull/137) was merged at
`52c1fa8d8adc3626ac68f54e1971dba50bc9eb7c` after a clean review of
`585c8deaa9db87709f0758ce94146b2ab74d21b0` and all four Windows/Linux CI jobs
passed. The target remains SymPy `c60dafcb4e3961aa6dea5193e9e1e864b662141d`,
version 1.15.0.dev. The [acceptance criteria](../scoped-cse-obstacle-2026-10-23/acceptance-before-source-search.md)
and [fixture](../scoped-cse-obstacle-2026-10-23/test_scope_contract.py) were frozen
at `471213561b288d6f616540f216b5f758955f70b3`. Their portable hashes still match
the baseline. None of the earlier experiment files were changed.

The maintainer's scope-handling suggestion and our helper-compilation idea were
already disclosed in that baseline. This attempt uses those direct ideas and
the target's own `lambdify`/CSE hooks. No source-of-solution search occurred.

## What runs

[scoped_lambdify.py](scoped_lambdify.py) is an experiment-local adapter. Each
finite sum becomes a callable whose per-iteration body is compiled by native
`lambdify(cse=True)` with the bound index as a local input. Other inputs are
passed explicitly; a bound name shadows the corresponding outer input. Nested
sums are lowered from the outer limit inward, preserving dependent inner bounds.
The enclosing expression is then compiled by the same native CSE.

For the literal report, the generated outer callback calls a sum helper; its
per-iteration body is:

```python
def _lambdifygenerated(x, e, n, i):
    x0 = sin(x[i])
    return e**2*x0**2 + e*x0 + x[i]
```

The sine assignment now has its index available. There is no dispatch on test
names, expression strings, numeric samples or the particular formula. No cache,
new runner, transport or production integration is introduced. The adapter and
its tests live entirely in RepoTraction; the ignored SymPy checkout is pristine.
There are no upstream writes or Satellite operations.

## Observed comparison

The old measurements below are taken unchanged from the
[frozen baseline](../scoped-cse-obstacle-2026-10-23/baseline.json).

| Path | Correct samples | Samples also meeting the work limit |
| --- | ---: | ---: |
| Native CSE | 2/13 (9 exceptions, 2 wrong values) | 2/13 |
| Disable CSE | 13/13 | 0/13 |
| Ignore all sum-bound symbols in CSE | 13/13 | 2/13 |
| Direct local-helper prototype | **13/13** | **13/13** |

The hand-written loop already solved the literal formula with four sine calls;
the prototype's improvement is automatically handling all six fixed expression
families without manually writing a numeric loop for each formula.

| Frozen family | Observed sine calls, in fixture sample order |
| --- | --- |
| Reported sum | 4, 1, 6 |
| Independent sums, same index name | 6, 5 |
| Nested dependent bounds | 3, 10 |
| Shared outer work | 3, 5 |
| Index free outside / bound inside | 5, 3 |
| Ordinary CSE without sums | 1, 1 |

The literal result is `30.017956315903607`, with four sine calls instead of the
eight in the correctness workarounds. [result.json](result.json) records each
sample, count and output, generated callback sources, instrumented construction
and evaluation times, environment and file identities. The counted function
delegates to the original fixture counter, which returns `math.sin`; the frozen
assertions still execute. [contract-log.txt](contract-log.txt) captures six
inherited fixture methods plus four adapter guard tests, all passing.

The instrumented timings are single observations. This makes **no wall-time
speedup claim**: compiling additional callbacks and calling Python helpers adds
overhead. All enclosing inputs are passed to each helper, including unused ones.
There is no claim of globally optimal CSE or loop-invariant code motion.

## Verification and limits

The unchanged fixture is imported with a namespace proxy that substitutes only
`lambdify`; it retains the original expressions, assertions, tolerances, samples,
return-shape checks and work limits. Four additional tests cover helper-name
collision, disabled-CSE delegation, and explicit rejection of other backends and
reversed bounds.

The upstream selection `test_lambdify.py -k "cse or Sum"` passes **3 tests,
158 deselected**, with the adapter temporarily installed at that test module's
imported entry point. See [upstream-regressions.txt](upstream-regressions.txt).
Those existing CSE tests have no sums, and the existing Sum test disables CSE;
they verify delegation. The frozen fixture exercises the changed sum path.
Hypothesis 6.170.7 and sortedcontainers 2.4.0 are the existing isolated test
dependencies in ignored data, not new product dependencies.

Native measurements are Windows/Python 3.13.5 only. RepoTraction CI remains its
ordinary Windows/Linux Python 3.10/3.13 matrix; it does not install SymPy or run
these experiment-local tests. A green matrix must not be described as native
cross-platform validation of the adapter.

This is a constrained prototype, not an upstream-ready replacement for
`lambdify`. Its sum path supports flat Symbol arguments with distinct printed
names, scalar math, list/tuple expression containers, and finite nonempty
ascending integer ranges. The frozen inputs fall within that domain. Other
backends, general binders, matrices containing sums, infinite/reversed sums and
arbitrary argument structures are outside its claimed support. No Sum or disabled
CSE delegates to the original native API. Visible authored tests do not establish
correctness for all symbolic expressions, nor a previously blocked agent.

## Reproduce without changing the target

Use the exact pinned checkout from the preceding baseline. Ensure it is first
on the import path; an installed SymPy 1.14.0 is not the target.

```powershell
$targetRoot = (Resolve-Path data/discovery-obstacle-baseline-2026-10-23/target).Path
$directRoot = (Resolve-Path docs/experiments/scoped-cse-direct-attempt-2026-10-23).Path
python -I -c "import sys,unittest; from pathlib import Path; sys.path[0:0]=sys.argv[1:3]; import sympy; assert Path(sympy.__file__).resolve().is_relative_to(Path(sys.argv[1]).resolve()); suite=unittest.defaultTestLoader.discover(sys.argv[2],pattern='test_direct_adapter.py'); result=unittest.TextTestRunner(verbosity=2).run(suite); raise SystemExit(not result.wasSuccessful())" $targetRoot $directRoot
```

For the upstream delegation controls, use the same import paths plus the isolated
test dependencies and temporary process-only substitution:

```python
import importlib
import pytest
import sympy
from scoped_lambdify import scoped_lambdify

module = importlib.import_module("sympy.utilities.lambdify")
native = module.lambdify
module.lambdify = scoped_lambdify
try:
    code = pytest.main([
        str(target_root / "sympy/utilities/tests/test_lambdify.py"),
        "-q", "-k", "cse or Sum",
    ])
finally:
    module.lambdify = native
```

`target_root` denotes that pinned checkout. `sympy.lambdify` remains native for
the adapter's delegation; no source file or installed package is patched.

## Consequence for Missing Link

This case is closed as **directly solvable under the frozen scope**. The stock
API defect was real; it did not imply an external idea was necessary. Do not
make the criteria harder, start donor retrieval, or attribute this prototype to
Missing Link. A future transfer experiment needs an independently meaningful
remaining obstacle; this case supplies no such justification. No further search
or experiment is initiated by this report.
