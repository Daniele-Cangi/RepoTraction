# Direct continuation: polylog checkpoint solved within the frozen contract

The direct attempt passes **all 11 tests** in the unchanged native module from
the checkpoint prepared in [PR #139](https://github.com/Daniele-Cangi/RepoTraction/pull/139).
Direct evaluation of `polylog(2, Rational(1, 2))` now returns the requested
`pi**2/12 - log(2)**2/2`; functional expansion returns the same expression.
The explicit original request and the independent additional controls pass.
This case stops before any Missing Link invocation or source search.

## Starting point and change

PR #139 was merged as `34a6918308ce919d5e4783f0f049c8907e8e2eca` after a clean
review of `012314caa3e3714fd79cf185abae584c82c3f349` and four successful
Windows/Linux CI jobs. The pinned SymPy revision remains
`c935e1d106743efd5bf0705fbeedbd18fadff4dc`, version 1.1.2.dev.

A separate ignored target copy was initialized with the exact actual agent
[submission](../blocked-agent-checkpoint-2026-10-23/checkpoint/failed-attempt.patch)
and the unchanged independent upstream test patch. A fresh before-run reproduced
**9 passed, 2 failed**, matching the frozen checkpoint. The original checkpoint
source, tests, demand, acceptance and previous evidence were not modified.

[direct.patch](direct.patch) is incremental against that actual submitted state.
It changes one implementation file, `sympy/functions/special/zeta_functions.py`:

- Put the already supplied half-argument formula in the automatic `eval` hook,
  so ordinary construction evaluates it. Remove its duplicate expansion-only
  case. The earlier attempt had supplied the formula in the wrong hook for the
  direct-evaluation request.
- Add the exact order-two value at argument 2, already supplied by the independent
  test, with its specified principal-branch imaginary term.
- Combine the existing negative-integer derivative recurrence over a common
  denominator using the target's own `together`. This preserves a useful rational
  form and passes the independently supplied negative-order expansion controls.

The formulas and expected behavior were already known task/test context. No
reference implementation, successful trajectory, fixing PR, external documentation
or donor implementation was consulted. There is no fixture-name or input-sample
dispatch, numeric tolerance change, new dependency or runner. Exact special-value
cases are ordinary symbolic-function evaluation rules; this is not a general
algorithm for evaluating arbitrary polylogarithms in closed form.

## Measured results

| Check | Actual failed checkpoint | Direct continuation |
| --- | --- | --- |
| Original half-argument direct evaluation | Unevaluated | **Requested exact expression** |
| Original half-argument functional expansion | Correct | Correct |
| Complete frozen native test module | 9 pass, 2 fail | **11 pass, 0 fail** |
| Existing source-file doctest groups | 5 pass | **5 pass** |

No native test or assertion was added, removed or changed. The fixture's byte
identity was compared with the preserved failed-state fixture. Its random seed
remains 0; all original tolerances and random loops remain in place. The separate
half-argument diagnostic confirms direct symbolic evaluation, not just numerical
agreement. See [explicit-request.json](explicit-request.json).

[result.json](result.json) records source/patch identities, frozen-file hashes,
environment, the exact native command code and outcomes. Captured logs are
[before.txt](before.txt), [after.txt](after.txt),
[before-doctest.txt](before-doctest.txt) and [after-doctest.txt](after-doctest.txt).
The absolute local workspace prefix is replaced by `<REPOTRACTION>`, and Git
normalizes CRLF to LF for the committed public logs. `log_sha256` identifies those
exact Git blob bytes; verify them with `git show <revision>:<path>`, or normalize
CRLF to LF before hashing a Windows worktree. The original public Windows CRLF
and original private log hashes are recorded separately. Trailing spaces and
other text remain intact. `direct.patch` passes `git apply --check` on the original
failed state without mutating it.

Native verification is local Windows/Python 3.8.20 with the existing isolated
mpmath 1.3.0 environment. RepoTraction's ordinary Windows/Linux CI remains a
separate regression gate; it does not execute these SymPy experiments. No product
implementation or CI configuration changes. Full SymPy integration, broader
suite/lint checks and upstream acceptance have not been evaluated. Single-run
timings in the receipt are observations, not a performance claim.

## Reproduce

Create a separate ignored target copy at the pinned revision. Apply the frozen
actual agent submission, the independent test patch and then `direct.patch`.
With that target first on the import path and the recorded interpreter/dependency:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(target_root))
import sympy
assert Path(target_root).resolve() in Path(sympy.__file__).resolve().parents
ok = sympy.test(
    "sympy/functions/special/tests/test_zeta_functions.py",
    subprocess=False, colors=False, seed=0,
)
raise SystemExit(0 if ok else 1)
```

The source-file documentation check uses `sympy.doctest` on
`sympy/functions/special/zeta_functions.py`, also with `subprocess=False` and
`colors=False`. Its reported count is five doctest groups, not five individual
example statements. The two doctest runs use separate processes.

## Consequence

This is a **direct correction**, not a Missing Link transfer result. The current
attempt has the frozen tests and observed feedback, unlike the original historical
attempt; these observations do not establish a fair model-performance comparison.
Visible benchmark tests and prior context also prevent a novelty or held-out
capability claim. Other exact values can still remain unevaluated; the numerical
consistency controls do not promise automatic closed forms for all their inputs.

The historical failure was real, but the present continuation needs no external
mechanism to pass the frozen scope. Credit that result and close this case.
Do not harden its criteria, dispatch an assisted arm, search for a donor or select
another case automatically. No paid AI API, subagent, upstream write or Satellite
operation was used. No further experiment is initiated by this result.
