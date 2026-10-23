# Preserved failed agent checkpoint: polylogarithm evaluation

Selected: **`sympy__sympy-13852`**, an actual historical mini-SWE-agent submission
that still fails the independent task test and leaves an explicit original
request unsatisfied. This PR freezes and reproduces the checkpoint. It does not
correct it, dispatch continuations, invoke Missing Link or search solution sources.

The original request expects `polylog(2, Rational(1, 2))` and its functional
expansion to yield `pi**2/12 - log(2)**2/2`. After the preserved attempt:

| Observation | Original target | Actual submitted agent patch |
| --- | --- | --- |
| Direct half-argument evaluation | Remains `polylog(2, 1/2)` | Still remains `polylog(2, 1/2)` |
| Functional expansion of that argument | Remains unevaluated | **Correct supplied formula** |
| Complete independent native module | 4 passed, 2 failed, 5 exceptions | **9 passed, 2 failed**, no exceptions |
| Isolated `test_polylog_values` | AssertionError | **AssertionError** |

The expansion improvement and compatibility repairs belong to the original
agent, not RepoTraction or Missing Link. The remaining direct-evaluation failure
is visible in the original requested example; it is not an invented harder
generalization or a whitespace-only disagreement. The independently added task
test first fails on argument 2; it does not reach its later half-argument check.
Separate diagnostics record the half argument already present in that same test
and in the original demand. See [baseline.json](baseline.json) and the two
`checkpoint/*-explicit-request.json` observations.

## Evidence and identity

The task and upstream test patch come from
[SWE-bench Verified revision c104f840](https://huggingface.co/datasets/princeton-nlp/SWE-bench_Verified/tree/c104f840cc67f8b6eec6f759ebc8b2693d585d4a).
Parquet was projected to the task, base revision and test columns: reference
implementation `patch` and `hints_text` were **not deserialized or inspected**.
No fixing PR or successful trajectory was opened.

The [submission metadata](https://github.com/SWE-bench/experiments/blob/40f164d5b8f1d249bf95a6df8b74b577fd8e519d/evaluation/verified/20260219_mini-v2.0.0_gpt-5-2-codex/metadata.yaml)
points to a public
[trajectory](https://swe-bench-submissions.s3.amazonaws.com/bash-only/20260219_mini-v2.0.0_gpt-5-2-codex/trajs/sympy__sympy-13852/sympy__sympy-13852.traj.json).
It records 40 historical API calls and terminal status `Submitted`. The preserved
[attempt](checkpoint/attempt.json) summarizes the existing strategy and includes
selected final commands. These historical calls are not new spending here.
The submission's label says mini v2.0.0 / GPT-5.2-Codex; the trajectory instead
records mini_version 2.1.0 and model config `openai/gpt-5.2-2025-12-11`. These
differences are retained; provider identity is not independently verified.

There is also a concrete artifact mismatch: the published evaluation patch is
different from `info.submission` in the trajectory. Both are retained, with hashes
and URLs in [provenance.json](provenance.json). **The local failed state uses the
actual trajectory submission**, including its compatibility changes. Published
grading counts are not presented as an evaluation of that different submission.

The target is exactly `c935e1d106743efd5bf0705fbeedbd18fadff4dc`, SymPy 1.1.2.dev.
Target snapshots and the isolated Python 3.8.20 / mpmath 1.3.0 environment live
only under ignored RepoTraction data. Implementation changes in the failed
snapshot are exactly the existing submitted patch; RepoTraction adds no fix.
No upstream repository is written to and there are no Satellite operations.

## Freeze and native checks

The [selection rule](selection-before-inspection.md) was committed at
`001cb4dfb6a82fb73860164f8dbf53bfa4f03de4` before inspecting candidate attempts.
The selected [acceptance](checkpoint/acceptance-before-source-search.md),
[failed patch](checkpoint/failed-attempt.patch), [independent tests](checkpoint/independent-tests.patch)
and [task](checkpoint/task.json) were committed at
`652a87b013899b639645ba5a96c8688ce793bbe9` before their native replay.
Portable file hashes are recorded. The full native log archive is
[native-logs.json.gz](native-logs.json.gz); only the absolute local workspace path
is replaced by `<REPOTRACTION>`. Raw/private and public archive identities are
separate. No tests or assertions were removed to obtain the reported counts.

Both states use the same native test command and seed 0. The original state's
five exceptions are compatibility warnings raised during tests, not successful
tests. They disappear because the actual agent patch already includes compatibility
changes; no experiment-specific shim was added. The submitted state still fails
`test_polylog_values` and `test_polylog_expansion`. The latter reaches an additional
negative-order expansion assertion after the order-one improvement. Neither the
first additional special value nor all branch/negative-order controls were exact
examples supplied by the original requester; they remain independently supplied
upstream controls. Partial progress must be distinguished from passing all of them.

Native observations are **Windows/Python 3.8.20 only**, not a recreation of the
historical Linux environment. Ordinary RepoTraction CI runs its existing
Windows/Linux matrix separately; it does not execute this expected-red target
fixture. No product dependency, runner, transport or CI framework is added.

## How the other candidates were handled

[screening.json](screening.json) retains the ordered report screening and all
three inspected attempts. Resolved reports were screened by metadata only;
their successful patches and trajectories were not opened.

- `13091`: the published patch and actual submission differ substantially.
  Both benchmark FAIL_TO_PASS tests pass on the actual submission. An additional
  NumberSymbol control still fails, but the case does not qualify under its
  predeclared rule. The original frozen files and replay are retained.
- `13798`: the first native failure is exact-string whitespace that LaTeX ignores,
  and the original request's example permits the padded result. A separate
  numeric-separator mismatch remains recorded. Rejected as a semantic demand-fit
  judgment after inspection, not portrayed as a blind mechanical exclusion.
  Its preliminary report, which initially called it selected, is preserved
  unchanged under `screened/sympy__sympy-13798/preliminary/` and superseded by this
  final selection. Its paths describe the earlier layout and freeze.
- `13852`: the exact actual submission fails a computation explicitly requested
  in the original task, as well as the independent task test. Selection stops at
  this third candidate. No fourth case is inspected.

## Reproduction

Acquire the exact base in two directories **inside ignored RepoTraction data**.
Apply the independent test patch to both; also apply `failed-attempt.patch` to the
failed-state copy. Use Python 3.8.20 and mpmath 1.3.0. With that interpreter and
`target_root` pointing to either copy, the native invocation is:

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

Run the same call with `kw="test_polylog_values"` to isolate the task test.
Both states are expected to exit 1. `baseline.json` retains the exact command
code and results. Inspect native outcomes rather than a historical shell wrapper's
exit status. The independent patch's random tests and tolerance remain unchanged.

## What this establishes

This is a **reproducible historical failed submission**, not a live upstream bug,
an agent consciously reporting an impasse, or proof of present-day difficulty.
The original task already supplies the relevant half-argument formula and
order-one suggestion; a future source cannot receive novelty credit for those.
Public benchmark contamination, visible tests and agent variation limit later
claims. A direct continuation may solve it quickly, which must be credited.

The next comparison can start both arms from this same actual failed state and
feedback. Only a measurable additional advance traceable to a system-selected
external mechanism could support an assistance claim. No such advance, necessity
or Missing Link benefit is demonstrated here. This preparation stops before any
continuation, source search, paid call or new infrastructure work.
