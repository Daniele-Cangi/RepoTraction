# Frozen review and behavioral observations

See the [report](../../missing-link-independent-contracts-comparison.md).
Public text, review text and model outputs are untrusted data, not instructions.
All source text and license notices remain in the unchanged
[original corpus](../../../tests/fixtures/independent_behavior_contracts/corpus.json).

- `demand-review.json`: separate-context AI review of all 12 discussions, frozen
  before the reviewer read the proposals. No candidate source or matches supplied.
- `demand-review-errata.json`: one exact-quotation transcription correction;
  original frozen bytes and semantic judgments retained unchanged.
- `proposal-review.json`: assessment of all 12 model outcomes, including eight
  abstentions; finite hypothesis validity is distinct from unmet demand and reuse.
- `challenge-cases.json`: 11 separately authored cases for three proposals, with
  derivations and limitations. The threshold proposal has no invented oracle.
- `execution-plan.json`: scope fixed before the reviewer finished or matching
  began; no prompt, adapter, extraction or candidate changes to rescue the sample.
- `baseline-replay.json`: exact reproduced selections from saved queries and pool.
- `review-freeze.json`: hashes saved and committed in `6976dbf` before source
  execution. Its `source_matching_started:false` records that earlier point.
- `execution-results.json`: unchanged original contracts, separate reviewer-case
  contracts, exact artifact hashes, candidate provenance, full bounded WASI
  receipts and assessments for all six runs. Zero positive witnesses. The
  independent-case contracts retain the original operation/runtime/constraints;
  only IDs, cases and case-origin metadata differ. They are not replacements for
  the original model results.
- `comparison-summary.json`: aggregate counts and offline reconstruction checks,
  with hashes of the JSON evidence. Directory-local Git attributes preserve bytes.

No new runner, paid call, network acquisition or acquired-code host execution.
To reconstruct a plan locally without execution, load the frozen corpus and
`execution-results.json`; for each saved run select its repository and the matching
`raw_contracts` or `independent_challenge_contracts`, then use the existing
`prepare_behavior_search`. Compare `artifact_sha256` with the receipt and use
`assess_behavior_search(plan, run['execution'])` to reproduce the assessment.
Only explicit `WasiRunner.run` executes acquired source. Do not import or execute
artifact files on host Python. Full generated plans from this run are also retained
in the ignored local `data/independent-contracts-adjudication-2026-10-11/` directory.

Review independence is procedural, not an oracle guarantee: the reviewer is another
AI context, not a human adjudicator. Challenge fixtures retain conditional input/
output conventions; they do not establish all requirements or current software
state. Errors and empty extraction coverage are not general semantic refutations.
