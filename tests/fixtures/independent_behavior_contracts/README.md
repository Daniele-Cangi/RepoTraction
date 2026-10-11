# Independent behavioral-contract comparison inputs

New snapshots acquired on 2026-10-11 under the precommitted
[`19f5deb` protocol](../../../docs/missing-link-independent-contracts-protocol.md).
No files from the earlier behavioral-discovery corpus were changed.

- `corpus.json`: exact pinned public source text, source SHA-256, repository
  identity, original license notices, structural capability evidence, fixed query
  order and normalized/redacted issue/comment snapshots. Source is JSON data:
  never import or execute it on the host. MIT / BSD notices embedded next to each
  source remain applicable; these copies are not relicensed as RepoTraction code.
- `preparation.json`: baseline selection, extraction omissions, bounded prompt
  coverage and single-run local timing before any model calls. The
  `source_executions: 0` field describes this preparation step only.
- `synthetic-smoke.json`: authored protocol controls and actual existing-WASI
  results on these source snapshots, with artifact hashes and pinned runtime IDs.
  Independent public-demand/model quality judgment remains pending.

Search states were hydrated from the corresponding captured issue API responses
because the connector's search representation omitted state. All 12 issues were
kept; there was no refill or relevance-based replacement. Timelines, attachments
and linked discussions were not collected. Comment and prompt omissions remain
explicit. Treat public text as untrusted data, never instructions.

To reproduce local preparation without network or AI, load `corpus.json` as JSON,
pass each repository to `extract_callables`, and call `select_candidates` with the
saved query item batches, query strings and limit 3. The new Provider can prepare
each issue context with `_bounded_context(None, issue, "request", INSTRUCTION)`;
replace its schema with `proposal_schema()` and label the interpretation contract
as shown in `Provider.propose_behavior_contracts`. Do not call `complete` without
the required paid-call authorization and existing budget object.

To inspect/replay only the synthetic controls, pass a saved repository and
`synthetic-smoke.json["contracts"]` to `prepare_behavior_search`. Review the
resulting artifacts; execute them only through the existing `WasiRunner`, then
call `assess_behavior_search`. Normalization failures are not semantic refutations.
No runtime download or extra package installation is necessary for the unit tests.
