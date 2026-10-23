# Frozen contract for the failed SymPy comparison attempt

Task: `sympy__sympy-13091` from SWE-bench Verified. Target base:
`d1320814eda6549996190618a21eaf212cfd4d1e`, SymPy 1.1.2.dev.
The preserved agent patch changes only `Basic.__eq__` / `Basic.__ne__`.
No reference implementation patch or successful trajectory has been inspected.

The independent task asks that comparisons with an unknown foreign type allow
Python's reflected comparison to run, preserving symmetric results. Existing
known-number comparisons must remain consistent. The task itself already
mentions returning NotImplemented from Basic; that is baseline knowledge, not a
mechanism that a future source search could claim to discover.

## Independent tests, fixed before local reproduction

Use `independent-tests.patch` unchanged. It is the benchmark's upstream test patch,
projected from dataset revision `c104f840cc67f8b6eec6f759ebc8b2693d585d4a` without
deserializing its reference implementation `patch` or `hints_text` columns.
It modifies only `sympy/core/tests/test_basic.py` and
`sympy/core/tests/test_numbers.py`.

The task's FAIL_TO_PASS tests are `test_equality` and
`test_comparisons_with_unknown_type`. The same independent patch also adds
`test_NumberSymbol_comparison`; retain that control. No new derived numerical
threshold, invented generalization, custom class exception or stronger demand is
added by RepoTraction. Run the complete two patched test modules and preserve
their native output, including unrelated pre-existing exceptions or xfails.

The checkpoint qualifies only if the exact submitted patch applies to the exact
base, at least one task FAIL_TO_PASS assertion remains false locally, and the
failure concerns comparison semantics rather than only installation or tools.
Do not correct the patch in this preparation.

## Baseline and any later advancement

Record both (A) the original target plus the independent test patch and (B) the
same target plus the exact submitted agent patch and the same test patch. Use
the same interpreter, dependencies and native test command. Do not infer
success from the evaluation shell's exit status: inspect native test outcomes.
The published submission report and raw test output are separate evidence; any
disagreement between their coverage or counts must remain visible.

A later continuation must pass all three named semantic tests without changing
tests, and introduce no additional failures/exceptions in the complete two-module
regression set compared with the frozen checkpoint. Existing unrelated failures
are not successes and must remain reported. Any proposed resolution of those
failures is outside this case unless it is necessary for the frozen contract.

This PR performs acquisition and reproduction only. It does not run a direct
continuation, Missing Link, an assistance comparison or a donor search. Later,
both continuation arms must start from the same failed patch, known task context
and observed failures, with equal ordinary investigation allowances. Source
planning/selection must use the existing request-led path and its cost must be
reported separately. No continuation or paid AI call is authorized by this file.

Historical submitted failure is not proof of present-day difficulty, a live
upstream bug, an agent consciously declaring itself stuck, or external assistance
being necessary. A subsequent ordinary success selects this case out of an
assistance claim. Empty retrieval, equal outcomes and no improvement remain valid
negative results. Do not replace the case or harden its contract to force a win.
