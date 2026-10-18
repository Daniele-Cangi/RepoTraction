# Conditional RF prediction: unresolved native comparison

Preparation only. No paid call, donor search, source selection or external
adaptation has run. The #130 allowance is closed. A new USD 0.15 cap is proposed,
with dispatch only after distinct user approval, review and Windows/Linux CI.

## The actual obstacle

Satellite's joint source model reduces training residuals but transfers badly to
excluded reference links. The earlier source-separation experiment documented
this failure. We repeated prediction with the stable differential rows on current
main `660cc7696f4b6730c8689a2c06fdf497625422ae`, after #236 merged. It persists.

Two further direct alternatives were executed before any donor search: the
native free segment-drift model and predictive Euclidean source shrinkage with
a bounded training-only GCV choice. Neither beats the strongest simple primary
comparison. This is a documented algorithmic generalization problem on real RF
data. It is an operator-formulated task, not a public issue or a live blocked-agent
checkpoint, and does not prove every reasonable direct method must fail.

The existing hash-selected links and last-third exclusion remain unchanged.
Across the five overlapping folds, the identical support across all five methods
contains 1,248 increment pairs at 30 s and 874 at 300 s:

| Direct method | 30 s phase RMS, mm | 300 s phase RMS, mm | 300 s code RMS, m |
| --- | ---: | ---: | ---: |
| Clock only | 9.2850 | 15.1054 | 1.333459 |
| Wet only | 9.3104 | **14.5673** | 1.333436 |
| Complete source fit | 15.9750 | 111.8983 | 1.346885 |
| Native free drift | **9.2506** | 14.7668 | **1.333192** |
| Complete source fit, training GCV | 15.7174 | 109.7871 | 1.346464 |

GCV here is one bounded numerical training criterion, with the original identified
source basis and native residual degrees of freedom. It neither establishes a
global GCV optimum nor qualifies independent errors, a physical source prior or
uncertainty. Its poor transfer is retained. Native comparisons took 39.030 and
34.185 seconds; no candidate trajectory was refitted or CODE score recomputed.

## What Missing Link would have to improve

The benchmark is **wet-only's 14.5673 mm**, not the adverse complete model. The
fixed practical pilot criteria in `request.json` require:

- At least 10% lower pooled 300 s phase RMS on all 874 common pairs.
- Retain all 1,248 short-lag pairs. Both code RMS values and short-lag phase RMS
  may be no more than 2% above their respective best direct metric.
- At least four of five folds improve the primary metric versus the same globally
  selected wet-only baseline; no fold worsens it by more than 10%.
- Keep all original missing/unknown terminals, support and worsening outcomes.
  No withheld measurements, future-link continuity witness or held score may
  choose a parameter, source, threshold or replacement attempt.

These criteria were chosen after observing the direct baselines and **before
donor search**. They are practical exploratory criteria, not physical accuracy
thresholds, preregistered blindness or a significance test. The folds share data.

The model may choose whether and where to search, up to three phrases and one
source, with five Provider calls maximum and no retry/replacement. It may stop.
The two target excerpts are explicitly selected by the operator, with exact Git
blobs and original line ranges; there is no autonomous target-file selection
claim. They must not become ordinary complete-file citation IDs in evaluation.

After a defensible packet, one bounded adaptation would be exercised in the native
prediction path against every comparison above. Any parameter-selection rule must
be decided from training only. No held-score weight search or rescue iteration.
A donor-only example would not satisfy the test. A justified code modification
would require native regressions and Windows/Linux CI before integration.

## Scope and retained evidence

Other reference RF at the excluded times remains available. This is conditional
missing-link transfer, not whole-network future clock prediction. Nominal timing,
geometry and masks already condition the archive; the archive is exposed.
Improved prediction would not identify physical source amplitudes, qualify a
covariance, reveal G12, establish orbital accuracy, close S2 or rescue a blind
agent. Those claims remain separate.

`predictions-before-scoring.json.gz` retains every native forecast extracted
unchanged from the two pre-scoring receipts. `scores.json.gz` retains every native
score/terminal without duplicated forecasts. Large fitted source/null matrices
are omitted: the pinned original input artifact and native routines retain their
definition. `direct-comparison.json` derives pooled and per-fold metrics only on
the explicit intersection. Original private receipt hashes are recorded without
claiming those compact exports are byte-for-byte copies of the larger receipts.

The source texts document the executed one-off calculations. They add no product
runner, transport, model framework or new authority. The existing 15 native
geometry, null, holdout and historical-receipt tests passed; raw log/JUnit and
source/input hashes are retained. The offline Provider preflight replaces remote
completion with an unconditional stop, so its API-call count is zero.

Preparation correction after review: both compact exports now retain the executed
source hashes from the original pre-scoring and scored receipts. Packaging checks
those hashes against the copied source bytes and checks the shared target/input
identity. `provenance-correction.json` records this metadata correction against
`4f7e4b2`; all forecasts, scores, comparisons and numerical source bytes are unchanged.

If no native gain emerges, keep the outcome and stop this cohort. Do not change
the comparison, add donors or reclassify predictive scores as physical evidence.
