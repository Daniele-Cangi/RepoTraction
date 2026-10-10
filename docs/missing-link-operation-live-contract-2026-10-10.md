# Separate authorized operation one-shot adapter

PR112 retained the final merged offline measurement: whole-owned 10k/60k probes
took 29.145/62.573 seconds on `876033e`, preserving the earlier 10k failure and
the narrow single-observation margin. Those authored transports did not establish
live latency, provider readiness, useful leads or execution authorization.

This stage adds `scripts/missing_link_operation_run.py` and explicit owned
wiring in `scripts/missing_link_operation_owned.py`. It does not prepare an
actual private run, reserve funds or make calls as part of implementation/CI.
The existing offline runner remains an authored scratch-database entry point.
The shared executor now names its injected transport explicitly; it still has
no implicit network transport or credential loading.

The only prospective output is
`data/missing-link-demand-operation-policy-v3-operation-owned-run-2026-10-10`.
Preparation must follow this adapter's review, successful CI and human merge.
It requires clean exact merged main with the reviewed tree, independently
verified consumed anchors, all 58 consumed fingerprints and 1,740 historical
artifacts. It freezes every compiled executable pin, the new adapter/test/contract
pins, the original database baseline and the eleven unchanged native bodies.
The independently retained prepared-manifest SHA-256 is required for verification
and execution; a checksum beside the files is not an independent trust anchor.
Preparation/verification read no live credentials and make no provider requests.

The original account is `Daniele-Cangi`, allowance
`missing-link-verification-2026-09-30`, accounting 579 reservations / USD8.1408513.
The configured total remains USD10. The new segment remains USD0.10 and the
atomic cumulative ceiling is USD8.2408513. Eleven unused operation accounting
IDs end in `01` through `11`; each slot permits exactly one call.
The unchanged bodies require USD0.0548404 in planned software reservations,
with a maximum slot reservation of USD0.0061645, below the segment ceiling.
No allowance reset, retries, automatic repair, resume or new production job/cache writes are
allowed. Accounting reservations are not independently confirmed billed spend.

Before reading live credentials, `run` requires a separate human-approved record
equal in concrete JSON types and values to `authorization_scope`: prepared
anchor, exact merged head/tree, source anchor, owned output, account/allowance,
eleven bodies/job IDs, public provider configuration, streaming deadlines and
revision, and both budget limits. Approval for the consumed stream run cannot
authorize this scope. The adapter itself cannot determine whether a human
actually granted approval; the record must be created only after that grant.
The original frozen Responses configuration remains gpt-6-luna, medium reasoning,
strict schema, `store:false`, streaming, maximum 6,000 output tokens and one call
per slot. Configuration/readiness/body reproduction must pass before an attempt.
The explicit live opener rejects redirects and has no retry path.

Execution holds both the original database worker lease and owned output lease.
It invokes only the existing atomic `Store.reserve_ai_allowance` on the original
database, without the constructor's DDL/identity writes. The reservation journal
must match both the in-memory binding and the exact original accounting prefix.
Immediate checks include identity, cancellation, held lease identity and provider
configuration. Critical checks freshly read code, owned evidence and accounting,
identity and active jobs at each one-second boundary and around each protected
commit. Other original tables and all historical files are fully audited at
every operation entry/exit and at the due thirty-second audit. The narrow
critical prefix read is not represented as a full database audit or a cached
proof of nonaccounting tables. Full audits retain fresh complete image hashing
and independent prefix comparison; image changes force a logical scan.

The reviewed protected reader still owns response cleanup before accounting,
native terminal retention/validation and acceptance barriers. Its 240-second
active stream and 600-second observed wall deadlines remain unchanged. Any
transport, identity, integrity, persistence, budget or cleanup failure stops
the cohort. Only the existing post-schema semantic normalization refusal is
candidate-local. Results are provisional until all eleven slots and final gates
complete; no next-slot attempt or success seal follows a latched failure.

Summary/final integrity and a provisional receipt must pass fresh final audits.
Promotion to `owned-artifacts.json` is the last success write. The returned
receipt digest must be retained independently. Lease cleanup is attempted for
every acquired lease and cannot replace an earlier primary failure. A cleanup
failure after promotion raises without issuing a success digest and retires the
success filename when storage permits. File existence alone never proves a
successful independently anchored run. Failure evidence is best effort and the
directory remains consumed, including pre-start failures after lease creation.
Failure writes require ownership of the output lease; a rejected competing
lease acquisition cannot add failure evidence to another owner's directory.

After this adapter is merged, prepare and retain the actual scope, present its
requests and concrete costs to the human, and obtain fresh exact authorization.
This feature merge supplies neither that freeze nor approval for a paid call.
