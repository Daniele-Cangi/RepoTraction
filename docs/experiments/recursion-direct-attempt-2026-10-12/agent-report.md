# Direct development attempt: pytest #8482

Dispatch: 2026-10-12 11:30:50 UTC. Deadline: 11:45:50 UTC.
Work completed and frozen before the deadline, on 2026-10-12 around 11:40 UTC.
Target HEAD: `aec0291ed14c724873bfcea99d5dfd739f75a68f`.
One ordinary agent; no delegation, dependency installation, paid API calls,
external messages, pushes, or PRs. Only the allowed public inputs and native
checkout were inspected. No withheld assessment material was inspected.

## Result and approach

The unchanged original MagicMock workload now produces an ordinary pytest
collection-error report within the 15-second observation cap, with exit status
2, `RecursionError`, `reported_recursion.py`, and the `func` frames. Three fresh
ordinary runs finished in 2.181, 1.919, and 2.630 seconds. The unmodified baseline
ordinary run timed out after 15.017 seconds, with no output captured. This is a
censored observation; I do not infer an exact speedup from it.

`Traceback.recursionindex` still visits frames in order and compares earlier
states at the same path, code **identity**, and line. It indexes states whose
locals contain only exact inexpensive builtin scalar types or ordinary Python
functions. It never hashes arbitrary objects, and it still compares such
objects against both arbitrary and simple earlier values in the original
order. This retains cross-type custom equality and equality-error behavior.

The remaining locals-dictionary comparisons have a default budget of 500 per
traceback search. Exceeding it raises a distinct internal exception; the
formatter explicitly reports that the origin is unknown because comparison
stopped. Ordinary output retains the first and last ten frames for long
tracebacks. With `tbfilter=False` / `--full-trace`, this budget fallback keeps all
frames and the uncertainty warning. `recursionindex(max_comparisons=None)`
provides the unlimited exact search when its cost is acceptable.

This is a **diagnostic precision tradeoff**, not an equivalent origin algorithm.
A repetition requiring more than 500 dictionary comparisons can be missed by
the default search. The warning says so; it never labels that outcome as a
detected repeated state. One arbitrary `__eq__` can itself hang or perform
unbounded internal work: bounding the number of calls cannot preempt it. The
15-second cap remains an experiment boundary, not a general runtime guarantee.

## Existing direct comparators considered

- The supplied discussion discloses `--tb=native` as a working workaround. I
  measured it before modification and paired it with all three candidate runs.
  The implementation does not globally select native output.
- Withdrawn #8651 starts from the last frame in each position group. Its author
  acknowledges that `[a(0), a(0), ..., a(0), a(1), a(2), a(3)]` defeats that
  assumption. I retained the first repeated state and added a distinct-tail
  regression using `[0, 0, 1, 2, 3]` instead of adopting that algorithm.
- The supplied other work lists #14219 for equal code objects and merged #8694
  removing the eval wrapper. The target already uses direct dictionary equality
  and code identity. Both remain; a regression now verifies distinct, equal
  native code objects do not share a recursion state.

## Changes and size

- `src/_pytest/_code/code.py`: 57 added lines, 6 deleted lines (net +51).
- `testing/code/test_recursionindex_limits.py`: 120 added lines, 15 test cases.
- No dependency changes. No existing tests or original reproduction changed.
- Reproduction SHA256 observed after the runs:
  `5469BB8A87A8305D92E6A6FD382265D6FFA4E5CB47F3B8EC44BABC00EAD75D0C`.
- `git add -N` was used only for the newly added test module so the complete
  source-and-test change is included in `agent.patch`.

## Native environment and commands

Working directory for every run:
`C:/Users/dacan/Documents/Codex/2026-08-17/vo/outputs/github-pulse/data/recursion-direct-attempt-2026-10-12/target`.

Python executable:
`C:/Users/dacan/Documents/Codex/2026-08-17/vo/outputs/github-pulse/data/agent-assistance-probe-2026-10-12/venv/Scripts/python.exe`.
Observed version: CPython 3.13.5, 64-bit Windows, MSC v.1943 AMD64.
Every native command set `PYTHONPATH=<target>/src` and
`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`. Imported `_pytest._code.code.__file__` was
verified to be `<target>/src/_pytest/_code/code.py` before development.

Commands/outcomes (below, `PYTHON` denotes the executable above):

1. `PYTHON -c 'import _pytest._code.code; print(_pytest._code.code.__file__)'`
   confirmed the assigned checkout.
2. Reproduction child command:
   `PYTHON -m pytest ../reported_recursion.py --capture=no -q`.
   Native comparator adds `--tb=native`. Each individual child was executed
   using `subprocess.run(..., capture_output=True, timeout=15)`; timeout and
   actual return status were recorded. No faulthandler instrumentation.
3. `PYTHON -m pytest testing/code/test_excinfo.py -q`:
   **190 passed, 11 skipped in 8.30 s**, exit 0.
4. `PYTHON -m pytest testing/code/test_recursionindex_limits.py testing/code/test_excinfo.py -q -rs`:
   **205 passed, 11 skipped in 8.18 s**, exit 0.
5. `PYTHON -m pytest testing/code/test_code.py -q -rs`:
   **17 passed in 0.65 s**, exit 0.
6. `git diff --check`: exit 0. Git emitted only the Windows LF-to-CRLF advisory
   for the new file when adding it with intent-to-add. `ruff` was unavailable;
   it was not installed or run.

Optional skips were: decorator missing (1), jinja2 missing (1), and
exceptiongroup missing (9). Existing source/tests were retained; nothing was
deleted, disabled, or changed to skip a regression.

### Original workload observations

Times are child wall times including startup, collection, and reporting, as
measured with `time.perf_counter()` around the timeout-capped subprocess.

| Run | Ordinary status / seconds | Native status / seconds |
| --- | --- | --- |
| Baseline, before patch | timeout / 15.017 | 2 / 1.919 |
| Candidate preliminary | 2 / 2.123 | not paired in this preliminary trial |
| Candidate pair 1 | 2 / 2.181 | 2 / 1.883 |
| Candidate pair 2 | 2 / 1.919 | 2 / 2.079 |
| Candidate pair 3 | 2 / 2.630 | 2 / 2.332 |

All candidate ordinary outputs were 7,780 bytes and all paired native outputs
10,515 bytes. All contained `RecursionError`, `reported_recursion.py`, and
`in func`. The ordinary diagnostic included:

```text
E   RecursionError: maximum recursion depth exceeded
!!! Recursion error detected, but the origin of the recursion could not be located within the locals comparison limit.
  Locals comparison stopped; a repeated state may have been missed.
  Displaying first and last 10 stack frames out of 963.
  Pass `--full-trace` to see all frames.
```

### Equality-work measurement

The measurement uses native traceback/frame objects at the same code identity
and line, each with a distinct custom value whose `__eq__` increments a counter
and returns false. The baseline function was extracted via Python AST from
`git show HEAD:src/_pytest/_code/code.py` and invoked on those same native
Traceback objects; no baseline source was modified. The candidate uses the
actual patched `Traceback.recursionindex()`.

| Frames | Baseline calls / seconds | Candidate calls / seconds | Candidate result |
| --- | --- | --- | --- |
| 20 | 190 / 0.001997 | 190 / 0.001863 | None, exact search completed |
| 40 | 780 / 0.003768 | 500 / 0.002989 | comparison limit, origin unknown |
| 80 | 3160 / 0.007967 | 500 / 0.002955 | comparison limit, origin unknown |
| 160 | 12720 / 0.015734 | 500 / 0.002906 | comparison limit, origin unknown |

These fast synthetic values demonstrate the call bound, not the practical
MagicMock speedup. The actual preserved workload measurements above supply
the practical observation. This does not claim linear exact matching for
arbitrary custom equality. For simple differing scalar locals, a native test
also checks 160 states complete with a zero dictionary-comparison budget.

## Acceptance and remaining limitations

1. Observed original workload requirement passes in three fresh paired candidate
   processes: useful ordinary RecursionError diagnostics and collection exit 2
   within each 15-second cap.
2. All six small native controls pass: immediate repetition, repetition before
   a distinct tail, no repetition, equal distinct unhashable values, unavailable
   equality, and equal distinct code objects. They are in the new native test
   module. Equality unavailability remains an explicit error diagnostic.
3. Full existing `test_excinfo.py` passes with the stated optional skips,
   including origin index, no-index fallback, equality errors, hidden frames,
   and full-trace behavior. `test_code.py` also passes.
4. Counts, original-workload time, source size, and dependencies were measured.
   Default origin precision is intentionally conceded after the comparison
   budget. The new tests verify a real later repetition is unknown by default
   but found at index 40 with `max_comparisons=None`.
5. No reproduction changes, global recursion-limit changes, test deletion or
   skipping changes, global native-output switch, diagnostic suppression,
   fixture-name special case, or MagicMock special case was introduced.

Remaining uncertainties: this is not merge-ready platform-wide evidence.
The full repository suite, lint/type checks, and broader Windows/Linux CI were
not run. Optional missing-dependency tests remain unverified. The fixed budget
of 500 is a policy choice needing maintainer review; it may stop a cheap custom
comparison search unnecessarily. A single hostile/slow equality call, very
large locals, pathological builtin hash collisions, and full-trace rendering
cost are not universally bounded by this patch. Broader property-based or
adversarial semantics validation would be valuable before merge.

No further iteration or tests will be performed after saving the final patch
and this report. Independent assessment belongs to the parent.
