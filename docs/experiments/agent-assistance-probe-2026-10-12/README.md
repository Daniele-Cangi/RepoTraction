# Native agent-assistance probe: preparation

This study asks whether an independently selected source mechanism helps a
development agent solve an actual target defect. It does not require a drop-in
library. No development agents, Missing Link donor search or paid calls have run
for this cohort. Product code and historical experiments are unchanged.

## Actual demand and direct comparator

[pytest #15099](https://github.com/pytest-dev/pytest/issues/15099) reports that
`monkeypatch.setattr` fails to restore custom attribute storage. The public
reproduction fails in native pytest at
`587ebc501ba292539202a1aac3a7f5b0112a08ec`, including teardown failure and leaked
state. The report already proposes a direct correction. The open
[upstream PR #15118](https://github.com/pytest-dev/pytest/pull/15118), head
`68cb1befd6baf84432b046fe9d703315e5f7221d`, is disclosed to all agents and tested
as a strong direct comparator. No upstream patch is submitted by this study.

| Native check | Pinned target | Target with exact direct PR patch |
| --- | --- | --- |
| Public two-test reproduction | 1 passed, 1 failed, 1 teardown error | 2 passed |
| Existing monkeypatch module | 44 passed, 2 skipped | 45 passed, 2 skipped |
| Eight assessor controls | 4 passed, 4 errors | 6 passed, 2 failed |

The two direct-proposal failures concern passthrough and mixed custom setters
leaving an instance shadow after undo. These are **assessor generalizations** of
the target's existing inherited-attribute restoration invariant, not requirements
explicitly added by the issue author. They do not show that maintainers reject the
proposal. The original reported defect is fixed by that proposal. Acceptance was
frozen before acquiring/applying its patch and before agents or source search.
Report these three check groups separately throughout the study.

The [preparation record](preparation-result.json) includes exact revision, source
and patch hashes, commands, environment and six retained logs. Tests use actual
`_pytest.monkeypatch`, not a replacement implementation. The shallow clone needs
an explicit packaging-version override for pytest's minversion check; this changes
generated version metadata, not pinned implementation. Failed setup attempts and
earlier unpatched direct-labelled results are explicitly excluded. This is a
Windows preparation result, not a full upstream pytest CI result.

## Selection history and its limits

[Protocol](protocol.md) was committed before issue search. The initial three-issue
2025 pool did not establish a still-failing bounded reproduction; the tentative
#13479 selection is retained, not rewritten. Its native fixture controls now pass
(3 passed). The [selection amendment](selection-amendment.md) explicitly permits
one additional 2026 pool before agents, donors or paid calls. That pool's first
result, #15099, is the actual selected demand. Full discussions, both pools and
the tentative selection remain available. This is purposive selection, not an
unbiased discovery-success estimate.

## Bounded comparison, pending authorization

1. One isolated agent receives the complete demand, public semantic acceptance,
   pinned target and native tools. It has 15 minutes for the strongest direct
   correction. Freeze its patch, commands and outcomes. Stop if it passes all
   frozen criteria; do not invent a harder task.
2. If it remains blocked, run the existing request-led Service once, with targeted
   inquiry, at most three searches and one inspected source. The experiment-local
   [strategy](strategy.py) changes only planner/selector instructions and supplies
   the recorded failure separately from public demand. Existing transport,
   interpretation, resolution, budgets, source inspection and handoff are reused.
   No operator-selected donor, source substitution or retry is allowed.
3. Two isolated continuation agents receive the same checkpoint and observed
   feedback, same inherited model/settings, tools and 15-minute limit each. Assign
   arm A to ordinary investigation and arm B to ordinary investigation plus the
   first returned source-inspection packet. The control may investigate public
   sources and upstream proposals. Neither sees concrete assessor controls or
   the other arm. The packet omits generated target bridge code, so any source
   mechanism must actually be reconstructed in the target. Stop if no packet.
4. Compare native outcomes, residual failures, source-to-implementation trace,
   code/dependency changes and time. Preparation overhead is additional treatment
   cost. One pair is confounded by agent variation; successful tests alone do not
   establish novelty, causation, economic gain or a general capability. Record
   equal success or no improvement honestly, without searching for better weights
   or replacing the case.

The frozen [prompts](prompts.json), [acceptance](acceptance-before-source-search.md)
and [bounds](execution-bounds.json) are reviewable before dispatch. The proposed
new allowance is USD 0.25 for at most six gpt-6-luna calls; configured conservative
maximum reservation is USD 0.1452288. This is not a provider invoice or a verified
current tariff. Three isolated development agents also require explicit approval.
No previous cohort allowance is reused. Paid dispatch requires that authorization,
review and the existing complete Windows/Linux CI. There is no automatic merge,
resume or follow-up cohort.

Four offline contract regressions protect demand/attempt separation, public
provenance, existing budget delegation, unknown requirement/source rejection and
the existing redaction/bounds policy. They replace provider completion with a
local mock. There is no new runner, store, framework or product mode.
