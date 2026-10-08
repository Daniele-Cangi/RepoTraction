# Owned repository-only evaluator

The [frozen four-source protocol](missing-link-repository-only-fresh-protocol-2026-10-08.md)
requires a caller-owned evaluator before its initial Discover investigations.
`scripts/missing_link_repository_only_evaluator.py` and
`scripts/missing_link_repository_only_run.py` implement that boundary without
changing production prompts, schemas, source sampling, query generation, selection,
normalization, qualification, application configuration or analysis contract 25.
No production module imports either script.

The runner uses the unchanged synchronous `Service.start` on a newly claimed
private database. Its Store reservation method delegates to the original Store's
atomic reservation with USD8.4904081 as the ceiling, despite the provider retaining
the configured USD10 total. The original worker lease covers the entire cohort;
Service retains its own private database lease. Source branch resolution alone is
redirected to the frozen commit and checked against its complete tree SHA. Target
retrieval and source-file selection remain the existing production behavior.

The Provider subclass overrides only `complete`. It retains the exact production
payload, supplied data, schema and full decoded native terminal before parsing.
Readiness, fresh account identity, reviewed-main ancestry, executable/configuration
fingerprints, original historical artifacts and the dynamic owned reservation
prefix are checked before each call. Each native/generic wire failure latches a
global stop; it cannot enter Service's candidate-local validation catch. Semantic
and provenance failures raised by unchanged interpretation after `complete` returns
retain their existing charged candidate-local continuation. Neither kind is evidence
of a sound semantic rejection.

Preparation is explicit and does not read credentials or perform acquisition/model
calls. After scoped review, CI and merge, `prepare --reviewed-head FULL_SHA --output
PRIVATE_DIRECTORY` requires a clean main identical to origin/main and the reviewed
tree, then freezes a separately owned baseline, code hashes, cohort and public knobs.
`verify --output PRIVATE_DIRECTORY` is read-only before execution. After spending,
it also requires `--receipt-manifest-sha256 DIGEST`, using the digest printed to
the independent execution log and subsequently retained in the reviewed report.
An adjacent, editable checksum is never accepted as the audit trust anchor.
`run --output PRIVATE_DIRECTORY` reads credentials only for that explicit execution;
it first requires exactly the two frozen preparation files, then claims exclusive
cohort/slot/receipt files and executes each ordered initial job
once. There is no resume, replacement, retry, query adjustment or copied allowance.
Every non-completed job stops the cohort and records remaining unattempted sources.
Acquired source is read and parsed as data, never imported or executed.

Private evidence includes redacted acquisition receipts, generated search queries,
complete acquired retrieval pools, selected/skipped candidates, supplied request
contexts, native terminal usage details, parsed attempts, job checkpoints, matches,
reservation journals and final integrity. Native usage and byte-based local
reservations remain separate from billing and semantic judgments. The runner checks
each file it has saved and rejects unexpected files before further attempts. After
execution it seals the exact inventory, including the private database, and prints
the manifest digest for independent retention. Post-run audit rejects altered,
deleted or added evidence, and changed/deleted manifest entries.

Seventeen authored offline tests cover unchanged production payload serialization,
all three interpretation phases across four initial synchronous Service jobs,
private storage/original-only atomic spending, tighter-cap failure before transport,
two leases, pin/tree/identity drift, original prefix tampering, retained charges on
journal failure, native refusal/incomplete/failed/malformed output and receipt
failure stopping subsequent calls. A schema-valid but semantically inconsistent
request confirms that production candidate-local continuation remains possible.
Consumed markers, pre-existing receipt/job files, and code/configuration/readiness
gates are checked before payment; stale directory entries block before credential
lookup. Reviewed-main ancestry is explicitly required. The independently anchored
manifest tests cover receipt-plus-hash replacement, deleted entries/files, extra
files and incomplete/unowned inventories. These address the two scoped PR88
review findings before execution.
These are mechanical checks with mocked acquisition/transport, not evidence of
model compliance or useful external leads. No model call or reservation occurs
while implementing or testing this evaluator.

Source-grounded assessment after the authorized one-shot execution must still read
every selected comparison and abstention/rejection, inspect retained query/pool
omissions separately, distinguish partial mechanisms from actionable external
leads, and keep missing prior-use/context evidence unknown. Execution/isolation,
UI/key-entry work and production promotion remain contingent on a supported lead.
