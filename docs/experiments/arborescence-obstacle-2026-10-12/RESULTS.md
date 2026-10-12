# Ordinary direct result: local success, no Missing Link attribution

The separately authorized ordinary agent stopped at 14:31:04 UTC after 689.96
seconds, within its 15-minute limit. The exact frozen patch passes independent
parent replay of the original criteria. **Stop this assistance case as a direct
success.** There is no residual failure in the frozen controls to justify a donor
search or an assisted continuation. No paid API call ran.

This is a useful native software improvement on the specified synthetic inputs.
It does not demonstrate Missing Link discovering an external technique or helping
a blocked agent. The historical human block in #3825 did not become a fresh agent
block. A bounded fresh attempt was sufficient; this says nothing about whether
other technical obstacles require assistance.

## Independent replay

The parent applied [the complete frozen patch](direct-attempt/complete.patch) to
a separate clean checkout of NetworkX `6da4704cbf32ba6f50f6d9c46cc0a071e3a87985`.
Original and candidate use separate checkouts, the same corrected Python
environment, unchanged measurement fixtures and the original 30-second process
cap. Three fresh original/candidate pairs ran per prescribed case; all 30 exited
successfully, with equal original/candidate weights and input hashes, preserved
inputs, and spanning arborescences. No candidate or criterion was repaired.

| Nodes / seed | Original median algorithm time | Candidate median | Speedup |
| --- | ---: | ---: | ---: |
| 50 / 20261012 | 0.2730 s | 0.01357 s | 20.12x |
| 100 / 20261012 | 2.0737 s | 0.09741 s | 21.29x |
| 200 / 20261012 | 17.1463 s | 0.77715 s | 22.06x |
| 75 / 20261013, fixed assessment | 0.8831 s | 0.04185 s | 21.10x |
| 150 / 20261013, fixed assessment | 7.2109 s | 0.34985 s | 20.61x |

These are Windows medians on the frozen synthetic family, not the unavailable
original user matrix, a representative workload, or an asymptotic proof. Startup,
graph construction, checks and teardown are outside algorithm timing; total
process time is recorded separately. The residual is not isolated startup cost.
Raw observations and all gates are in [independent-assessment.json](independent-assessment.json).
The additional seeds were disclosed before the attempt; they are not a blind
holdout. Large-case optimum equality is comparison with the native exact solver;
independent exhaustive optimum enumeration applies to the small controls only.

[The independent oracle](independent-acceptance.log) passes seven methods,
including 12 seeded subcases. [The native directory](independent-native-tests.log)
passes **302 tests**: the original 219 plus 83 new regressions. Two existing slow
tests remain skipped and the existing self-loop centre case remains xfailed.
Existing upstream tests are unchanged. The agent's own separate observations,
report, checks and freeze are retained under [direct-attempt](direct-attempt/report.txt).

## Changed scope and limits

The patch adds a private batched Edmonds implementation inside the actual existing
API, using compact edge records and contraction membership instead of retained
NetworkX graph copies. A synthetic root handles root choice with an exact integer
penalty; original edges/weights are reconstructed after expansion. It adds no
dependency, public API, product module, provider, store or runner.

The fast path covers built-in integer edge weights on directed graphs without
partition constraints. Floats, custom numeric types, partitions, empty graphs and
undirected inputs retain the original path. Missing integer weights can remain
absent in the input, explicitly allowed by the frozen default-normalized control;
this differs from the original default-fill side effect. Returned optimal tied
edges may differ. This is not a complete Tarjan/Gabow implementation and does not
resolve the entire public performance request for arbitrary matrix types.

The helper's classical complexity comment is retained as part of the frozen
candidate; these tests do not independently establish a general implementation
bound or an improved asymptotic bound. The demonstrated claim is the measured
local benefit with the stated scope and regressions.

The already disclosed unfinished fork and open PR #2117 were inspected normally.
Neither was executed, adapted or benchmarked. Their current performance remains
unknown, and the current baseline is not claimed to be the best possible direct
implementation. The agent reports no copied donor code or other source search;
ordinary Edmonds reasoning and disclosed direct context produced this patch.

## Portability and review

The existing native CI workflow now replays this exact patch, independent oracle,
unchanged native tests plus new regressions, and paired observations on both
Windows and Linux. Hosted timings are retained as platform evidence; the frozen
2x performance gate is the local one above. Complete product CI remains required.
Hosted results are pending at this result freeze; the PR records their actual
conclusions against the resulting head. Preparation CI/review applies only to
`172beae`, and is not reported as review or CI of this later result commit.

The agent's raw Windows file hashes are preserved in freeze.json. Git replay can
change CRLF/LF bytes; [candidate-replay.json](candidate-replay.json) adds canonical
source hashes without rewriting that freeze. The parent corrected an initial
CI assertion that compared canonical bytes with the raw Windows hash; no native
implementation changed. YAML and embedded CI Python parse locally.

No upstream issue, comment or PR was submitted. Native portability/CI success
would support this local study, not personal upstream contributor approval or
user deployment. Product functionality and earlier frozen experiments remain
unchanged. There is no new donor search, harder replacement threshold, retry,
second agent or further cohort implied by this direct success.
