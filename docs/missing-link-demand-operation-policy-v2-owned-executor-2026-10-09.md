# Demand-operation policy v2 owned executor

PR97 merged as `5d6449bb7659f7eab2294b3dfd8cd2e7422bb044`, with the same
tree as reviewed head `d7424f1427be976c40ecd4b80d43d62f38fc6751`.
Scoped Codex review has no findings; all four CI jobs passed. Its
[policy-v2 protocol](missing-link-demand-operation-policy-v2-execution-protocol-2026-10-09.md)
and [offline preparation](missing-link-demand-operation-policy-v2-execution-preparation-2026-10-09.md)
remain unchanged. This stage implements separately named adapters against them,
with authored temporary-data conformance; no actual owned freeze or calls occur.

## Explicit isolated adapters

`scripts/missing_link_demand_operation_policy_v2_executor.py` explicitly imports
the policy-v2 builder and unchanged mechanical normalizer. It verifies all eleven
ordered envelopes/native bodies, settings, hashes, lengths, costs and the distinct
`demand-operation-policy-v2-owned-2026-10-09-01` through `-11` accounting IDs
before attempts. Direct execution callers must supply the caller's independently
anchored source manifest and frozen-body reader. The executor rebuilds all eleven
requests and recursively compares complete slots with those verified manifest entries,
requiring identical concrete dict/list/scalar types without JSON serialization,
before claiming any slot or paying, including identifiers, phase, paths, lengths,
costs, envelope and native hashes. A slot's own hash is not a trust anchor. Policy-v1 bodies,
IDs or preparation revision cannot silently enter the new executor.

`scripts/missing_link_demand_operation_policy_v2_run.py` owns explicit
`prepare`, `verify` and `run` actions. Import performs no I/O. Production imports,
parser/schema/normalizer, provider settings, ranking, acquisition and UI remain
unchanged. The original executor, runner, authored tests, protocols, prepared
bodies, consumed run and independent assessment retain their original bytes.
The new adapters retain a bounded copy of the original execution mechanics to
keep those historical executable fingerprints reproducible; this is not a
refactor of the frozen original modules.

The source-preparation independent digest is
`4ebbbb80c708eaf3531540679211bac18f7c4443a1351a51751cf97bb334390d`;
the protocol LF digest is
`c60fc910194f5ceb38c90a3ed1412847d32543a28b21cee5e758100647a05e56`.
The adapter requires exact source inventory/bytes, original 43 code fingerprints,
sealed policy-v1 run and operator-assessment anchors/inventories, and preserved
older execution preparation. These historical checks read sealed bytes rather
than applying the old live-ledger verifier after a new accounting extension.
The old verifier remains unchanged and correctly expects its own 566-row endpoint.

## Freeze, authorization and accounting

After this adapter's scoped review/CI and merge, `prepare` requires clean current
merged main, equality with the full reviewed tree, unchanged source baseline,
zero active jobs and unused new accounting IDs. It reproduces all eleven bodies
using public settings without credentials. A newly named exclusive owned directory
adds this source preparation's 27 files to the 1,488 protected artifacts:
**1,515 protected files** and **46 first-party fingerprints**, including the three
new adapter/test files. Its manifest digest must be retained independently outside
that owned directory. Existing output directories cannot be overwritten.

`verify` checks independent owned/source/receipt digests, exact inventories,
reviewed/merged bindings, executable fingerprints, the precise source-to-owned
baseline extension and original accounting. It does not read credentials or call
the provider. A changed or omitted historical file fails even if someone supplies
a newly computed digest for a different owned manifest.

Only `run` can read provider credentials. Before lookup it requires clean main
with current HEAD at the owned manifest's exact frozen merged commit and its
reviewed tree, and current `origin/main` still at that commit. Repeat that exact
execution-tree check at every integrity gate; a later main commit cannot inherit
the owned run's authorization even with unchanged pinned code. Read-only receipt
verification retains the independent historical binding without starting execution.
The credential boundary also requires an independent owned anchor,
source/history integrity, unused inventory, original
baseline and exact authorization-scope checks. It requires an explicit
`--call-authorization` JSON record matching `authorization_scope(anchor, source)`:
the owned/source digests, account, original allowance, all eleven ordered native
hashes and job IDs, eleven one-shot calls and exact limits. The record must follow
separate human authorization; it records scope and is not an authentication proof.
Neither `prepare` nor the helper creates that record or grants authorization.
The run retains a copy in its owned inventory before the exclusive start marker.
No real policy-v2 call-authorization record is created in this implementation stage.

Original account is `Daniele-Cangi`, database
`data/repotraction-daniele-cangi.sqlite3`, allowance
`missing-link-verification-2026-09-30`. Baseline remains **566 / USD8.0779182**;
configured total remains USD10. Per slot: one call, USD0.02 maximum. Proposed
eleven-slot software reservations total **USD0.0535105**, under a USD0.10 segment
and cumulative atomic ceiling **USD8.1779182**. A complete prefix reaches
577 / USD8.1314287. These are software reservations, not verified billing.

The runner acquires original-database and owned-run leases, rechecks all gates,
forces fresh fixed-account identity before each attempt and checkpoints during
streaming. Exclusive start/attempt/request files, original Store atomic reservation
and immediate journal precede provider execution. It uses only the original
Store reservation method without constructor migrations or job/cache writes.
Only the exact new ordered reservation prefix can extend the frozen original
ledger; all old rows, non-accounting tables, allowance identity and protected
bytes remain intact. Failed journaling retains a committed reservation and stops.
No refund/reset/new allowance, resume, retry, repair or replacement is implemented.

## Receipts, validation and sealing

The unchanged bounded receipt reader retains decoded native terminal JSON before
parsing, usage reporting or acceptance. Parsed raw output is retained in exclusive
private checkpoints before generation-schema validation, including schema-invalid
JSON values. Malformed output remains in the native terminal without inventing
a parsed prediction. Output/status/ID/usage, raw values, checked cards and later
operator annotation remain separate; missing terminals or usage are absence,
not zero. SSE whitespace and preceding deltas are not captured.

Transport, native status/refusal/incompleteness, parsing, schema, identity, budget,
persistence and integrity failures stop globally. Independent shape/provenance
guards run outside the local handler before and after normalization. Only
`ValueError` from the unchanged normalizer may become a retained local rejection,
and only after successful postchecks. Changed raw/context/code and exceptions
from those guards cannot be downgraded. Unknowns or misleading mechanically valid
assertions are retained without reference substitution or semantic rejection.

The runner retains every attempted slot, bounded failure type/slot, and unattempted
slots. Finalization checks original accounting/history and seals exact owned
inventory with a returned digest for independent retention. On Windows the held
lease handle supplies its lock checksum without opening a second locked handle.
Failed finalization leaves evidence and stops without claiming sealed completion;
leases release in every exit path. Any evidence of prior execution blocks replay.

## Authored conformance and next boundary

Forty-three authored offline controls use temporary original databases, fake
public identity, temporary historical seals/scope records and synthetic native
streams. They cover v2 versus v1 body binding, ordered IDs/settings/costs, standalone
schema versus local rejection, raw/context/code mutation, receipt/usage/raw retention,
fixed-account/lease/cancellation gates, atomic caps/committed-journal failure,
scope mismatch before credentials, history mutation and exact inventories,
source-to-owned baseline preservation, seals/replay prevention and credential-free
freeze on an authored 566-row baseline. Previous native/assessment bytes remain
identical after the authored owned accounting extension.
The four review regressions reject changed metadata in the first/middle/last slot,
an internally consistent changed body with a self-supplied new hash, a descendant
main before credentials, and a tree change during receipt handling after one
retained reservation. Both original P1 failures were reproduced before correction.
Another reproduced review regression rejects JSON-equivalent tuple/list changes
in nested envelopes, coverage and native payloads before any claim/payment;
numeric metadata types must also match the verified slot exactly.

These are execution-mechanics tests, not model outputs or proof the revised
instructions work. Independently recheck the actual source preparation, consumed
native/assessment anchors and unchanged original ledger before publishing.
After review/CI/merge, freeze the actual separately owned successor and obtain
new explicit authorization before eleven real calls. Then retain all native
outcomes and perform a new independent per-path assessment. Retrospective known
controls cannot establish causal improvement, held-out accuracy, fresh utility
or qualified leads. Source execution, new acquisition, production promotion and
UI/key-entry remain deferred.
