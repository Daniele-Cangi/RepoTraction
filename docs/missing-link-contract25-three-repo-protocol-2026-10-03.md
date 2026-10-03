# Contract 25: new repository-only Luna segment

## Frozen before generation

- Executable code: `123fe347d2436e4a448fdb7e4144148fec70ecd2` (merged PR #49), analysis contract 25. Only this protocol and the later result report may change during this segment.
- Provider: OpenAI Responses API, `gpt-6-luna`, streaming, medium reasoning, JSON schema. Existing settings remain unchanged: 180,000 prompt bytes, 12,000 output tokens, at most eight calls and USD 2 reserved per job.
- Inputs, in order: `jaraco/path`, `pallets/itsdangerous`, `d3/d3-array`. Supply only the repository, `max_candidates=3`, and AI enabled. No issue URL, demand query, manually imported analysis, or selected positive control.
- Python classes/methods are in scope. JavaScript coverage remains partial; structural acceptance does not prove semantic correctness. ItsDangerous is analyzed read-only, not subjected to security testing.

The first unpaid preparation draft contained `python-humanize/humanize` and `sindresorhus/p-limit`. The historical-input check rejected those already-used repositories before baseline creation, protocol registration, server restart, or AI generation. That draft and its failure record are preserved. The final three inputs were fixed without inspecting their issues, then passed the unused-source check. This is a preparation correction, not replacement of a failed live job.

## Budget and evidence baseline

The original cumulative allowance `missing-link-verification-2026-09-30` remains USD 10. The starting ledger contains 440 reservations totaling USD 6.8468383; USD 3.1531617 remains unreserved. There is no reset or refund.

This segment has an additional USD 0.60 conservative-reservation ceiling. The worst-case bound is 24 calls × USD 0.0242048 = USD 0.5809152, giving a cumulative bound of USD 7.4277535. Reservation accounting is not an invoice or measured token cost.

The private baseline freezes the provider identity/settings (excluding the key), hashes of five owned harness files, all historical jobs/matches/snapshots and reservation rows, and 157 prior private JSON artifacts. Seven offline harness checks passed. The merged source had 951 passing local tests and four successful Ubuntu/Windows CI jobs. Old paused jobs stay paused.

## Actual workflow and stop rules

1. Commit and push this protocol before generation. Verify the full Missing Link table hashes, GitHub account, localhost API identity, model availability, source public/canonical/non-archived metadata, and unchanged provider/harness settings. Persist only the safe identity projection before verification assertions.
2. Restart only the identified owned localhost server on the frozen code. Use the production HTTP handler without the analytics scheduler or automatic job resumption. Immediately verify the page and browser errors.
3. Run the normal investigation CLI sequentially through production HTTP, GitHub retrieval, provider responses, normalization, persistence, and export. A transparent observer records sanitized retrieval-pool metadata without changing selection or injecting demands.
4. Stop the entire segment on an unavailable input, observation/identity failure, failed/paused/partial job, candidate error, or missing receipt. Do not retry, resume, replace an input, or repair the frozen code during this segment. Retain every acknowledged job and reservation even when its outcome is unknown.
5. Reconcile reservation rows, logical provider attempt receipts, raw outputs, pinned snapshots, selected candidates, and JSON/ZIP exports. Review retained and rejected comparisons, operation-level evidence, and false positives. Separate lexical relevance, structural grounding, semantic usefulness, and execution eligibility.
6. Verify historical records/artifacts are unchanged. Restore a normal server on the same frozen code, without collector/job-resume side effects, and verify the browser/API again. Do not execute a bridge or change the interface/key workflow in this test.

Zero eligible leads is a valid result. A useful correspondence or correctly rejected false positive must be demonstrated from actual evidence, not inferred from a completed status. Different inputs do not establish an accuracy improvement over earlier cohorts.

## Private artifacts

Owned harness, baseline, safe observations, receipts, retrieval pools, screenshots, and export bundles live in ignored `data/luna-discovery-contract25-2026-10-03/three-new-02/`. The rejected preparation is retained under `three-new-01/`. Raw private artifacts and credentials are not published; the later report will summarize reproducible conclusions and public issue links.
