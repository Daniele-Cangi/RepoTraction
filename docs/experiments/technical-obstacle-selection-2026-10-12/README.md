# Selected obstacle: useful recursion diagnostics without quadratic work

Select pytest's traceback recursion diagnosis for the next agent-assistance
attempt. The practical defect is [pytest #8482](https://github.com/pytest-dev/pytest/issues/8482):
reporting a test's `RecursionError` can itself fail to finish promptly when local
variables have expensive equality operations. This is a current native software
failure, not an invented requirement or a claim that an agent is already blocked.
No new development agent, Missing Link source search or paid AI call has run.

Target revision: `aec0291ed14c724873bfcea99d5dfd739f75a68f`, the observed current
pytest main. Imports were verified from this exact checkout, with Python 3.13.5
on Windows. This is a new selection; #125 remains inconclusive and unchanged.
No timeout, transport, budget or product infrastructure is changed.

## What failed and what still works

| Native observation | Result |
| --- | --- |
| Original public reproduction, ordinary pytest formatting | Did not finish within 15.023 seconds; child stopped at the pre-set 15-second observation cap |
| Same reproduction, disclosed `--tb=native` workaround | Completed in 1.617 seconds, exit 2, correctly reporting collection `RecursionError` |
| Actual `Traceback.recursionindex`, 20 / 40 / 80 / 160 frames with distinct unhashable local values | 190 / 780 / 3,160 / 12,720 equality calls, exactly n(n-1)/2 |
| Current recursion-focused native tests | 8 passed, 1 skipped |
| Entire native `testing/code/test_excinfo.py` | 190 passed, 11 skipped |
| Six small native semantic controls | Passed |

The timed-out result is censored: it does not prove an infinite hang or establish
the eventual unmodified runtime. The first process emitted no captured bytes
before it was stopped; buffered output is not evidence that test code never ran.
The equality-count probe uses real Python traceback frames and the actual pytest
method. Its counting objects expose structural cost; they are not the original
MagicMock workload, and their timing is not a claimed user-facing speedup.

A supplementary unbuffered run with `faulthandler.dump_traceback_later(5)` ended
with Windows exit code 3221225477 (access violation). Its stack includes
`recursionindex` and path lookup while formatting. This instrumented run is
recorded separately and excluded from the performance comparison. Whether the
instrumentation, Python, workload or their interaction caused that crash is
unknown. Do not run this intrusive diagnostic in the future comparison.

The native workaround is a real alternative. The selected task concerns keeping
pytest's ordinary formatted diagnostic useful without requiring that switch;
it does not claim users have no workaround. Existing fallback already discloses
when the recursion origin cannot be established. An improved bounded fallback
may be useful, but any lost origin information must be stated explicitly.

## Why this is a defensible technical obstacle

`Traceback.recursionindex()` groups frames by source path, code-object identity
and line, freezes local dictionaries, then compares each dictionary with earlier
ones in the group. This is quadratic for distinct states. Comparing arbitrary
user objects can be expensive, stateful, unhashable or raise an exception.

The withdrawn [direct PR #8651](https://github.com/pytest-dev/pytest/pull/8651)
tried a linear strategy anchored on the last frame. Its author acknowledged a
[counterexample](https://github.com/pytest-dev/pytest/pull/8651#issuecomment-846466342):
repeated states can occur before a different final tail. Both the proposal and
complete supplied discussion are retained in [demand.json](demand.json), and must
be disclosed to the ordinary agent as existing direct work. The merged #8694
removed an eval wrapper; the present code already includes that simplification.
The closed, unmerged #14219 documents equal-but-distinct code objects, another
correctness constraint. None is a selected external donor.

This creates a narrow tradeoff between diagnostic work and accurate repeated-state
detection. We are not asking for exact linear-time equality matching over all
arbitrary Python objects: that guarantee is unjustified, and a single equality
operation can itself fail to return. Nor does a repeated traceback state prove
that the program would loop forever. Preserve the actual diagnostic semantics.

Selection was purposive engineering reconnaissance, documented in
[selection.json](selection.json), not a randomized demand sample. An alternative
jsonschema error-reporting case was inspected but not run natively; it introduces
a broader policy question about the best error. No donor availability or source
technique was used to choose this obstacle.

## Next step and stop rule

First give an isolated ordinary development agent the public need, pinned target,
direct workaround/proposal, semantic criteria and native tools. It must attempt
the strongest direct correction. A software failure is not proof of an agent
block. If its correction meets the frozen criteria, report that result and stop;
do not make the task harder to create demand for Missing Link.

Only if a meaningful criterion remains failed should the existing Missing Link
path choose and inspect a source-owned technique, then deliver it without target
bridge code to a continuation agent. Compare ordinary and assisted continuations
from the same checkpoint, including treatment preparation cost and whether the
source idea actually changed the implementation. Partial progress is reported
against the remaining failed criterion, not as complete resolution or causation.

The [criteria](acceptance-before-source-search.md), unchanged public reproduction
and native control fixture are prepared before any such source search. This PR
selects and reproduces the obstacle only. It does not authorize or dispatch a new
agent cohort or paid calls, reuse #125's allowance, create a runner, or merge
automatically. Any future modification needs relevant native regressions and
complete Windows/Linux CI. Current native measurements are Windows-only; the
RepoTraction CI is a separate product-regression check.

## Portable verification correction

Use [portable-fixture-manifest.json](portable-fixture-manifest.json) to verify the
frozen fixtures on Windows or Linux. Read each fixture as bytes, replace CRLF
byte pairs with LF, then compute SHA-256 and compare with that file's
`canonical_sha256`. Do not trim whitespace or apply another transformation.
In Python the operation is `hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()`.

The original hashes in `baseline.json` describe the original Windows working-copy
bytes; its two Python fixture hashes include CRLF line endings. Those observations,
the fixture contents and the frozen acceptance criteria remain unchanged. The
manifest retains the local byte hashes separately and supplies portable hashes
matching the committed LF bytes. This correction changes verification only, not
the experiment's results or criteria.
