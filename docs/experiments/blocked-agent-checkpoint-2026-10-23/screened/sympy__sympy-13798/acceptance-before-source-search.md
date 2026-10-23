# Candidate 2: custom LaTeX multiplication separator

SWE-bench Verified task `sympy__sympy-13798`, original SymPy revision
`7121bdf1facdd90d05b6994b4c2e5b2865a4638a`. The task requests arbitrary
`mul_symbol` values, including a thin space, preserving backward compatibility.
No donor, fixing PR, reference implementation patch or successful trajectory has
been inspected. Tests and task were projected independently of the agent attempt.

Use the exact submission in the selected trajectory's `info.submission`, stored
as `failed-attempt.patch`, not an assumed equivalent patch from its evaluation
directory. Preserve and disclose differences between these public artifacts.

## Fixed tests before local replay

Apply `independent-tests.patch` unchanged to both the original base and the same
base with the submitted patch. Dataset revision:
`c104f840cc67f8b6eec6f759ebc8b2693d585d4a`. It adds two assertions to the existing
`test_latex_basic`, for a symbolic product with a custom thin-space separator and
numeric factors that still require an unambiguous separator. These requirements
and expected strings come from the independent upstream test patch; RepoTraction
adds no new behavior, numeric threshold or algorithm requirement.

Run the entire native `sympy/printing/tests/test_latex.py` module on both states
with the same interpreter and dependencies. Report the full output and all
failures, exceptions, skips and expected failures. A shell exit code alone is not
a test verdict. Also invoke `test_latex_basic` alone to isolate the task failure.

This candidate qualifies only if that independent FAIL_TO_PASS test still fails
on the actual submitted patch with a semantic assertion, not only a tooling or
installation error. Do not correct the attempt in this preparation. If it passes,
retain the rejection and proceed only within the predeclared three-candidate cap.

For any later continuation, success requires the unchanged `test_latex_basic`
to pass, with no additional failures/exceptions in the full module relative to
the frozen checkpoint. Existing baseline failures must stay visible. Equal or
better test counts do not establish external-transfer benefit by themselves.

## Stop after reproduction

This PR only acquires and freezes a checkpoint. Do not dispatch agents, make
paid AI calls, search mechanism sources or run Missing Link. A subsequent
comparison must give ordinary and assisted continuations the same failed patch,
known task context, feedback and ordinary investigation allowance. Only the
assisted arm receives the mechanism selected by the existing Discover path;
source-generation overhead is additional cost. Direct success, an empty search
or equal outcomes must remain honest negative results without changing criteria.

The checkpoint is a historical submitted failure, not proof of a live upstream
bug, conscious impasse, present-day difficulty, or a need for an external idea.
Benchmark contamination and variation between continuation agents limit causal
claims. No upstream repository, Satellite or historical experiment is modified.
