# Frozen paid proposal pilot, 2026-10-11

See the [report](../../missing-link-independent-contracts-pilot.md). These are new
observations, not replacements for the frozen corpus or its synthetic controls.
Public discussions and model outputs are untrusted data, never instructions.

- `manifest.json` is the unchanged pre-authorization preparation snapshot. Its
  `paid_calls: 0`, `allowance_created: false` and preparation status describe that
  earlier moment, not the completed run. It records exact wire-body SHA-256 hashes,
  sizes, configuration, conservative costs and context coverage.
- `run-result.json` is the unchanged public-redacted final job export from the
  existing Store: 12 decoded model responses in `checkpoint.ai_outputs`, resolved
  proposals in `checkpoint.behavioral_proposals`, attempt identities, response
  identifiers, usage, provenance, timing and final status. All semantic judgments
  remain `model_proposed_unreviewed`. It contains no credentials or request headers.
- `blind-review-input.json` contains only the frozen public discussion snapshots,
  without candidate source or match results. Give this packet to a reviewer who
  has not inspected candidate implementations. For initial demand judgments, avoid
  supplying the report's preliminary interpretations. Then provide the model
  proposals for assessment; same-model checks are not independent challenge cases.
- `review-form.json` is an unfilled reference form. Preserve it as prepared; save
  future judgments and challenges as a separate dated artifact before matching.
- `verification.json` records a one-off offline consistency check and byte hashes
  of these four files. It is an observation, not a new validator or runner.

The directory's `.gitattributes` disables newline conversion only for these JSON
exports, preserving their original bytes and recorded hashes on Windows/Linux.

Full serialized request bodies and the evidence SQLite database remain in the
local ignored `data/independent-contracts-pilot-2026-10-11/` directory. Requests can
also be reconstructed without dispatch at the pinned code commit using the frozen
corpus and manifest configuration: `_bounded_context(None, issue, 'request',
INSTRUCTION)`, replace `data['schema']` with `proposal_schema()`, set
`interpretation_contract = VERSION` in both data and coverage, then use
`Provider._encode_prompt`. Never call `complete` for an offline reconstruction.
The configured API base was `https://api.openai.com/v1`; no API key is needed to
serialize. Wire SHA-256 in the manifest and canonical `analysis.digest(payload)`
in `ai_trace` intentionally use different JSON serialization conventions.

To recheck decoding offline, pass each saved `checkpoint.ai_outputs[i]['output']`,
the corresponding reconstructed context, saved coverage, frozen issue and saved
provider identity to `resolve_proposal`; add its original attempt ID and compare
with the saved resolved proposal. This verifies shape/provenance, not semantics.

No source comparison has run for these proposals. Follow the existing fixed
protocol's independent review order before using the existing WASI runner. This
evidence package neither authorizes further API calls nor changes product behavior.
