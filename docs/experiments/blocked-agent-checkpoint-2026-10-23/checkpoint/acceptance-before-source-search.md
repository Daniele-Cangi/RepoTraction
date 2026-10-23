# Candidate 3: evaluation of polylogarithms

SWE-bench Verified task `sympy__sympy-13852`, base revision
`c935e1d106743efd5bf0705fbeedbd18fadff4dc`. Use the exact final submission from
the preserved agent trajectory, not its different published evaluation patch.
No source-of-solution search, successful trajectory, fixing PR or reference
implementation patch has been inspected.

## Independent task and tests, frozen before local reproduction

The original demand explicitly expects `polylog(2, Rational(1, 2))` and its
functional expansion to yield `pi**2/12 - log(2)**2/2`. A second part challenges
the polar term in the expansion of order-one polylogarithms. These formulas and
the suggested logarithm expression are already task knowledge, not ideas a later
donor can claim to supply.

`independent-tests.patch` is the upstream benchmark test patch projected from
dataset revision `c104f840cc67f8b6eec6f759ebc8b2693d585d4a` without deserializing
its reference implementation or hints columns. Apply it unchanged to the base
and the base plus the actual submitted agent patch. It modifies only
`sympy/functions/special/tests/test_zeta_functions.py`.

Run that complete native module and isolate `test_polylog_values`, the task's
FAIL_TO_PASS test. Also record direct evaluation and functional expansion of
the half-argument example already present in both the task and independent test.
This diagnostic does not replace the native test or add a new example.

The candidate qualifies only if the task test still fails semantically and the
explicit original half-argument evaluation remains unsatisfied by the actual
submitted patch. Do not correct the patch, redefine symbolic evaluation as
numerical agreement, or call a formatting mismatch an unresolved computation.

The independent tests include additional special values and branch-consistency
checks beyond the explicit half-argument request. Their formulas and tolerance
come from upstream, not from a RepoTraction generalization. Report their failures
separately from the explicit request and do not imply that the requester supplied
all of those acceptance examples. Preserve their randomness; record seed 0 for
both local states. Do not rewrite or weaken the tests.

## Later comparison, not dispatched here

Freeze all native failures/exceptions in both states, including pre-existing
environment limitations. A later complete correction must pass the independent
task test and introduce no additional failures/exceptions in the full module.
An advance on the explicit request while broader controls remain failing is a
partial result, not full success. Ordinary progress must be credited before any
assistance claim; do not keep making the task harder to require Missing Link.

Any later ordinary/assisted continuations must use the same actual failed patch,
original demand, known formulas, failure feedback and ordinary investigation
allowance. Use the existing Discover path for the assisted source; preserve its
ability to choose direct work or no source. Count source-generation overhead.
No new runner, agent dispatch, paid AI call or donor search is part of this PR.

This is a historical submitted failure, not a live upstream bug or an agent
consciously declaring an impasse. It does not establish present-day difficulty,
novelty, external-source necessity or Missing Link benefit. Stop selection after
this third candidate even if it fails qualification. Preserve all screened cases.
