# Independent output review — frozen

Reviewed the six actual outputs for indices **2, 7, 9, 12, 15 and 16**, separately against their visible payloads and the larger frozen discussions. All **79 requirements** and their selected quotes/inferences were read. No candidate implementation, source comparison, new acquisition or paid call was used. The previous demand review remains unchanged.

All six run rows report `validated`. Every returned citation ID and quote matches a supplied span. **That validation does not establish semantic support.**

## Findings

- **Index 7 / r12 — unrelated citation.** The requirement preserves W-A writer behavior, but citation `s9e06b2c657abd9af` discusses float-word differences around the Q default. The writer rule exists elsewhere in visible q1 and the full frozen discussion; the selected quote does not support it. This is a citation error, not an invented writer requirement.
- **Index 7 / several rows — incomplete selected fragments.** For example, r0 cites a sentence ending at “every continuous parameter gets one”; r10 cites only “points' `f32`s**, checked at validation.” Neighboring visible text supports the meaning, but the selected fragment alone does not establish the full requirement.
- **Index 16 / r2 — partial citation despite available supporting text.** The chosen span states why an item belongs to the owner. Placement in a separate list before batch 1 is in another selectable span, `sfa486f184575f7ec`.
- **Index 15 / r3–r7 — incomplete reconciliation of later status.** Historical SIGN design is retained, and r4 says implementation remains a proposal. Visible later q2 reports measured Sign attachments and rejects the two-argument variant as slower. This does not prove every SIGN behavior is completed, but the proposal-only framing is too broad. The output's caveats reduce the risk; they do not reconcile the later experiment evidence.

## What should not be counted as a semantic failure

Index 2's broad metrics scope is explicitly qualified as possibly retrospective; its outcome and prior attempts recognize completed work and the stop decision. It should **not** be scored as a newly invented unresolved assignment simply because the row says `mandatory=true`.

Index 9 captures the cleanup and acknowledges that the visible manager's census-baseline carveout has no selectable citation. The private removal list is absent even from the larger frozen record.

Index 12 reaches the **30-requirement cap** and explicitly lists uncovered behaviors. Its gallery/selection subset and group atomic Move/Removal/Undo are supported. The detailed transaction contract was removed from the payload's middle, but related API-test bullets survive in the tail without selectable spans. Missing finite-case details therefore involve citation coverage and the cap, not necessarily incorrect interpretation.

Index 16 correctly avoids treating ruled proposals as pending. Its payload contains 101 selected sources, of which **87 are empty**; 169 sources and 321 visible spans are omitted. The current pending set is legitimately uncertain.

## Coverage of the seven previously frozen cases

| Cases | What the baseline retains | Why detail is missing |
|---|---|---|
| I7-C1, I7-C2 | General integer lattice and exact decimal mapping | Exact example text is absent from visible payload. |
| I7-C3, I7-C4 | Escape distinctness partly retained; bound rejection/rank example absent | Exact examples are visible, but lack selectable citation spans. |
| I12-C1 | Atomic multi-source Move and one Undo | Mixed-destination test evidence is visible but uncitable; cap reached. |
| I12-C2 | General atomicity | Stale-version/no-mutation test bullet is visible but uncitable; detailed error/selection rules partly omitted; cap reached. |
| I12-C3 | No dedicated no-op row | All-no-op test bullet is visible but uncitable; cap reached. |

This is a bounded audit of baseline coverage and specific interpretation/citation defects, **not a universal semantic-accuracy score**. The JSON records per-index/rid evidence, availability categories and limits. No implementation or prompting fix is prescribed.
