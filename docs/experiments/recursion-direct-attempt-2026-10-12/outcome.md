# The ordinary attempt overcomes the selected obstacle

One fresh-context agent produced the frozen [patch](agent.patch) within the
authorized 15-minute attempt. The manifest records the reported freeze and the
parent's observation before the deadline; the [report](agent-report.md) is the
agent's account, not independent evidence. No continuation, second agent or paid
API call was used. Isolation was instructional, not a filesystem security boundary.

The parent replayed the exact patch into a second, clean checkout of pytest
`aec0291ed14c724873bfcea99d5dfd739f75a68f`, using Python 3.13.5 on Windows,
the same local dependencies and the unchanged public reproduction. Complete
outputs, commands, measured wall times and output hashes are retained in
[parent-assessment.json](parent-assessment.json). The source and patch hashes are
in [candidate-manifest.json](candidate-manifest.json); line-ending normalization
is CRLF pairs to LF only. Historical preparation, fixtures and results are unchanged.

## Observed recipient-software improvement

| Process | Ordinary output | Disclosed `--tb=native` workaround |
| --- | ---: | ---: |
| Original pinned implementation | Timeout at 15.040 s | 1.784 s |
| Frozen candidate, pair 1 | 1.755 s | 1.632 s |
| Frozen candidate, pair 2 | 1.718 s | 1.641 s |
| Frozen candidate, pair 3 | 1.717 s | 1.604 s |

These are fresh subprocess wall times including startup, collection and reporting;
they are not isolated algorithm timings. The original ordinary observation is
censored, so it does not yield an exact speedup. Every completed reproduction
retained exit status 2, `RecursionError`, the relevant filename and `func` frames.
Candidate ordinary output explicitly says the origin could not be found within
the comparison limit and a repeated state may have been missed. It does not
claim a detected equal-locals cycle.

All six frozen small semantic controls passed on the candidate. The complete native
`testing/code` directory passed: **280 passed, 11 skipped** (one missing `decorator`,
one missing `jinja2`, nine missing `exceptiongroup`). These skips are environment
limits, not removed tests. The directory includes the agent's 15 added regressions.
No existing test, reproduction, global recursion limit or dependency was changed.

## Changed guarantee and remaining limits

The candidate indexes only exact builtin scalar/function values, retaining code
identity, line grouping and original comparison order, including custom equality
against simple values. Arbitrary objects retain dictionary equality. A global
limit of **500 dictionary comparisons per traceback** stops expensive searches;
the formatter then reports unknown origin and normally retains the first and last
ten frames. `--full-trace` retains all frames. An explicit
`recursionindex(max_comparisons=None)` keeps an unlimited search available.

| Native frames with distinct custom values | Original equality calls | Candidate equality calls | Candidate conclusion |
| --- | ---: | ---: | --- |
| 20 | 190 | 190 | Search completed, no repetition |
| 40 | 780 | 500 | Origin unknown |
| 80 | 3,160 | 500 | Origin unknown |
| 160 | 12,720 | 500 | Origin unknown |

The original full probe fails on the candidate at 40 frames with
`_RecursionSearchLimitExceeded`: its large exact no-match expectation is no longer
satisfied. That failure is retained. The six original control statements were
run separately with their assertions unchanged, excluding only the preceding
scaling loop. The second scaling observation records uncertainty explicitly.
Passing the controls therefore does **not** mean the entire frozen probe passed.

A true repeated state after the limit can be missed; an added regression verifies
that the unlimited path finds it. This is a different guarantee from the original
algorithm, expressly allowed by the pre-frozen acceptance when disclosed. It is
not an equivalent optimization. The value 500 is the agent's policy choice,
not a maintainer requirement or a generally validated optimum. One comparison,
hashing large builtin values or full-trace rendering can still be expensive.
There is no universal wall-time bound or linearity claim.

The patch changes one native implementation file (+57/-6 lines) and adds one
120-line test file; it adds no dependency. No fixture-name or MagicMock special
case, donor transfer or operator-proposed implementation was used. The existing
native CI workflow now replays this exact frozen patch on Windows and Linux with
a separate original baseline on each platform, three paired processes, the six
controls and the full native code directory. Product CI remains unchanged.
Cross-platform results are pending at the time of this local outcome record.
Broader upstream suite, typing/lint checks and maintainer agreement on the changed
default remain necessary before an upstream implementation could be proposed.
This PR retains experiment artifacts; it does not install the patch into a product.

## Consequence for Missing Link

The ordinary attempt satisfies the measured local acceptance with an explicit
precision tradeoff. Under the frozen stop rule, assistance stops here; CI verifies
portability without extending the agent's attempt. This is practical progress in
the recipient software, **not a Missing Link discovery or assistance result**.
The native workaround also already existed and remains comparable in runtime.

This case cannot establish that another agent was blocked or that an external
technique changed its work: the first ordinary agent found a direct solution.
Do not search a donor, invent a harder criterion or spend another allowance to
turn this result into an assistance win. A future assistance experiment needs
an independently observed unresolved technical obstacle and a changed recipient
invariant after a concrete source-owned contribution, with an ordinary continuation
comparison. This result selects out the present case; it does not refute that
possibility or demonstrate it.
