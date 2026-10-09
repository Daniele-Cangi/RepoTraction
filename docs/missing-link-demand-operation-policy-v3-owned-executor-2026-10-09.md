# Demand-operation policy v3 owned executor

PR101 merged as `d399203339fcf09acbffc865551952c9a7bc4569`, matching reviewed
`112bbd124ea7cf85fe0214a6cfc893c9fad7696c` and tree
`df4bae38f1b12f6f386b051139fdc39c10b59068`. Scoped Codex review was clean
and all four CI jobs passed. The [v3 protocol](missing-link-demand-operation-policy-v3-execution-protocol-2026-10-09.md)
and [offline source preparation](missing-link-demand-operation-policy-v3-execution-preparation-2026-10-09.md)
remain immutable. This stage adds separately named adapters and authored temporary
conformance. No actual owned freeze, authorization record, model output or call occurs.

## Explicit policy and ownership binding

`scripts/missing_link_demand_operation_policy_v3_executor.py` imports the v3
builder and unchanged original normalizer. It reproduces all eleven ordered
envelopes/native bodies, settings, hashes, lengths, costs and the distinct v3
accounting namespace before attempts. A direct caller supplies its independently
anchored source manifest and frozen-body reader; the entire supplied slot structure
must match verified frozen data with concrete JSON dict/list/scalar types.
Self-supplied hashes, old policy bodies/revisions/IDs and JSON-equivalent type
changes cannot substitute for the frozen manifest.

Typed immutable slot checks repeat around identity/claim, immediately before and
after reservation, during validation and after receipt/record callbacks. A late
slot mutation blocks even an earlier payment; a mutation after a committed charge
stops without refund or transmission. Raw/slot snapshots are also compared with
concrete types around the narrow local-normalizer handler.

`scripts/missing_link_demand_operation_policy_v3_run.py` provides explicit
`prepare`, `verify` and `run` actions. Import performs no I/O or background work.
Both old policy modules, executors, runners, tests, protocols, references, native
predictions and assessments remain unchanged. The bounded copy of execution
mechanics preserves those frozen old fingerprints; this stage does not refactor
historical adapters or change production imports, parser/schema/normalizer,
acquisition, ranking or UI.

The source-preparation digest is
`03bd97b6a26b74950ff5a6df921a9a92e37a2c298f6db2a5d556befb137ae741`;
the protocol LF digest is
`a84a8e039ef8e91cd6bb135305f69dce4431306ab3772c60ddf0c6fe7c28bb31`.
The runner requires exact source inventory/bytes, all 48 source-code fingerprints,
both consumed run/assessment prepared and receipt anchors/inventories, and both
older execution preparations. Each historical seal/preparation must match its
baseline binding. These are static historical checks: neither consumed runner's
earlier live reservation prefix is reused for future v3 accounting.

## Reviewed freeze and separate authorization

After adapter review/CI/merge, `prepare` requires clean current merged main with
the full reviewed tree, unchanged original baseline, zero active jobs and unused
v3 IDs. It reproduces every body using public settings without credential lookup.
A new exclusive owned directory adds the 27 source-preparation files to the 1,635
historical artifacts: **1,662 protected files** and **51 code fingerprints**,
including the three new adapter/test files. These counts are prospective; no such
owned directory is created in this implementation phase. Retain its manifest
digest independently outside the output directory; existing outputs are never replaced.

`verify` checks owned/source/receipt anchors, exact inventories, reviewed/merged
tree binding, executable fingerprints, the precise source-to-owned baseline
extension and original reservation prefix. It reads no credentials and starts
no execution. Dropping historical evidence fails even with a newly computed owned
manifest digest.

Only `run` can load provider credentials. Before lookup it requires clean main,
HEAD and `origin/main` at the owned manifest's exact frozen merged commit/tree,
independent owned/source anchors, unused inventory, original baseline and a
separate `--call-authorization` record matching `authorization_scope(anchor, source)`
with identical concrete JSON types. The scope binds owned/source digests, original
account/allowance, all eleven ordered body hashes and job IDs, eleven one-shot
calls and exact limits. The runner retains that scope before its exclusive start
marker. The JSON record follows human authorization; it is not authentication
proof, and no prepare/helper/merge grants permission or creates a real record here.
Exact execution-tree checks repeat at every gate; later main cannot inherit approval.

Retain account `Daniele-Cangi`, original database and allowance. Accounting remains
**577 / USD8.1314287** within configured USD10. The frozen plan is one call and
USD0.02 maximum per slot, **USD0.0548404** total software reservations, a USD0.10
segment and atomic cumulative ceiling **USD8.2314287**. A separately authorized
complete eleven-slot prefix would reach **588 / USD8.1862691**. These parameters
are conservative reservations, not verified provider billing.

The runner holds original-database and owned-run leases, checks active jobs,
forces fresh fixed-account identity before each attempt and checkpoints during
streaming. Exclusive start/attempt/request markers and immediate atomic original
Store reservation/journal precede requests. No Store constructor migrations,
original job/cache/source writes, reset/refund/new allowance, replay, resume,
retry, repair or replacement occur. Any post-commit failure preserves the charge
and stops, including a lost journal.

## Receipts, validation and sealing

The unchanged bounded reader retains decoded native terminal JSON before parsing,
usage reporting or validation. Parsed raw output is retained in private checkpoints
before schema validation. Malformed output stays in the native terminal; missing
terminal/usage is absence, not zero. SSE whitespace and preceding deltas are not
retained. Native output/status/ID/usage, parsed predictions, checked cards and
future independent annotations remain separate.

Transport/native status/refusal/incompleteness, parsing, schema, identity, budget,
persistence and integrity errors stop globally. Independent shape/integrity checks
run outside the handler before and after normalization; only the normalizer's
`ValueError` can become a retained post-schema local rejection after successful
rechecks. Arbitrary errors, guard failures and changed inputs/code remain global.
Mechanically valid unknown or misleading claims stay visible without semantic
classification, reference substitution or repair.

Finalization retains attempted/unattempted slots and bounded failure type/slot,
rechecks accounting/history and seals the exact owned inventory with an independent
digest. On Windows the held lease handle supplies its lock checksum. Failed
finalization retains evidence without claiming a complete seal; leases always
release. Prior execution evidence blocks replay, including a zero-call consumed run.

## Offline conformance and next boundary

Fifty-three authored controls use temporary databases, fake identity, temporary
historical seals and synthetic Responses streams. They cover policy/ID/body
binding, exact settings/costs/typed slots, schema versus local rejection,
raw/context/code/tree mutation, native/raw/usage retention, fixed identity,
leases/cancellation, atomic caps/journal failure, exact scope before credentials,
historical inventories/baselines, seals/replay and credential-free preparation
on an authored 577-row baseline. V3-specific controls reject v2 binding, v2
native/assessment changes, concrete authorization-type changes, callback type
mutations at identity/payment/normalization, and dropped v2 assessment evidence.
They verify execution mechanics, not model adherence or semantic improvement.
All **166 focused controls** pass in 176.032 seconds. The full application suite
passes **1,585 tests** in 363.988 seconds; CLI `--help` also exits successfully.

Read-only checks reproduce all eleven actual frozen v3 bodies, independent
source/history/assessment anchors, all 48 frozen code fingerprints and unchanged
accounting, without keys, leases, owned preparation or calls. The scope is six
public files; old code and historical evidence remain unchanged.

After scoped review/CI/merge, freeze the separately named actual owned successor
against its exact merged/reviewed executable tree. Obtain new explicit human call
authorization before any real request. Future native outcomes and an independent
per-path assessment remain separate from both consumed runs. Retrospective known
controls cannot establish held-out accuracy, causal improvement, fresh utility
or qualified leads; acquisition, acquired-code execution, UI/key entry and
production promotion remain deferred.
