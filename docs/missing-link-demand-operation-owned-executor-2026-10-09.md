# Owned demand-operation executor

The [revision 2 execution protocol](missing-link-demand-operation-execution-protocol-v2-2026-10-09.md)
merged in PR93 as `e843aa0227c4031428c247c0796238ece56c28e5`. Two opt-in
scripts now implement its execution boundary; production imports, prompts,
schemas, normalizers, ranking and `app.py` remain unchanged. No provider request
or real reservation was made while developing/testing them. The original ledger
remains 555 reservations / USD8.0266132 within the original USD10 allowance.

## Implementation

`scripts/missing_link_demand_operation_executor.py` reproduces every frozen
envelope, exact native body, ordered slot identity, setting and reservation before
execution. Its one-shot loop preserves terminal receipts through the existing
no-retry stream reader and keeps schema/integrity gates outside the narrowly
caught policy normalizer call. Schema-invalid cards stop globally; schema-valid
local inconsistency can be retained as rejection and permit the next slot only
after successful immutable-input/schema rechecks and persistence/prefix gates.
Unknowns and unsupported interpretations remain unchanged.

`scripts/missing_link_demand_operation_run.py` exposes explicit `prepare`, `verify`
and `run` actions. Import performs no configuration lookup or execution.
Preparation requires clean merged main whose tree matches the reviewed head;
it uses public settings with no credential to reproduce exact native bytes.
It preserves the [v2 private preparation](missing-link-demand-operation-execution-preparation-2026-10-09.md)
and adds its 27 files to the original protected inventory in a separately named
owned successor. The new preparation pins all previous dependencies plus both
executor modules and their authored tests, original ledger/allowance rows,
reviewed/merged trees and a fresh baseline. Its independent manifest digest must
be retained outside the output directory.

Run requires that digest and clean merged main, unchanged code/protocol/input/
configuration/ledger, no active jobs, fixed account checks and both the original
database worker lease and an owned-run lease. It exclusively claims a start marker
and each ordered attempt; any started run is consumed even if it stops before
payment. No resume, retry, repair or substitution is implemented. An optional
external cancellation marker at `<output-directory>.cancel` stops checkpoints;
it does not delete reservations or authorize replay.

The original Store's reservation method is used without invoking its constructor
or adding original jobs/caches/matches. Known exact costs and unique slot IDs are
bound to the original atomic USD8.1266132 ceiling (USD0.10 maximum segment).
All eleven planned costs still sum to USD0.051305. The original allowance stays
`missing-link-verification-2026-09-30`; reservations are never reset or refunded.
Usage, including absent usage, remains distinct from reservation estimates and
verified billing. Configuration is checked without serializing credentials.

Private requests, complete decoded native terminals, successive job checkpoints,
unchanged predictions/normalization results, reservation journal, slot summary and
final integrity snapshot are saved exclusively. Native terminal retention precedes
parsing/validation. Stream whitespace/prior deltas are not claimed as retained.
Transport, native/schema, identity, budget, storage or integrity failures stop
globally. A failed journal after atomic commitment leaves the charge retained and
prevents sealing or continuation. Every actual file must match the owned inventory
before sealing; the independent receipt-manifest digest is emitted for retention
outside the run directory. Verification after execution requires both anchors.

The leases remain held through finalization. On Windows, the owned lock's checksum
is read from its existing locked handle; opening a second read handle would fail.
The finalized summary lists completed/local-rejected slots, the stopped slot and
unattempted slots. Failure to finalize is reported as failure, never as a complete
sealed run. Raw private evidence and upstream exception text are not printed.

## Offline conformance and next boundary

Twenty-eight authored controls use synthetic packets/terminal events and temporary
account databases, never actual model output or acquired-code execution. They cover
exact body/config/order/cost checks, independent anchors and complete code inventory,
schema-versus-local rejection, mutable raw/context/code failure, original-prefix
preservation, atomic cap denial, missing reservation journals, receipt persistence,
native incomplete/failed/refused/malformed content, transport interruption,
fixed-account uncertainty, active jobs, leases, cancellation, replay prevention,
sealed inventory tampering and credential-free prepare/verify. They also exercise
the full eleven-slot owned path with simulated HTTP streams. Their assertions are
mechanical conformance evidence, not policy predictions or semantic quality.

All 28 focused controls pass; the final complete application suite passes
**1,473 tests**. The PR records scoped review/CI on the final head. Both frozen native preparations
and original owned paid-run receipts are verified separately against independent
anchors. This implementation does not rewrite them or allocate calls.

After this executor's scoped review/CI and merge, freeze the owned successor on
that exact reviewed code and retain its independent digest. Verify it offline
before separately authorized calls. Merely supplying a digest, merging code or
preparing files does not establish human authorization. No owned successor or
provider execution has been performed in this implementation phase. Assess every
eventual slot independently against original evidence/references, including each
context gap, without prediction repair, inferred semantic truth, accuracy claims
or production/qualified-lead promotion.
