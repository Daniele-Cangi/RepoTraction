# Demand-to-operation execution preparation

The [native execution protocol](missing-link-demand-operation-execution-protocol-2026-10-09.md)
now fixes the next development experiment after PR92 merged as
`99064726996e6a2a150029c75d28efb8d792ef58`. Its tree matches reviewed head
`3a90a16b0e158f85b58974cc4f9409716045762b`. Scoped Codex review completed
without further findings and all four CI jobs succeeded; Windows/Python 3.13
passed after one failed-job rerun for a local HTTP transport interruption.

This is a prospective offline freeze, not execution machinery or authorization.
No credential was read, account check performed, lease acquired, provider contacted,
prediction obtained or reservation made. Production code/configuration and old
preparations remain unchanged. A future executor needs its own conformance tests,
scoped review/merge, exact-code owned successor and separate call authorization.

## Independent anchors and native requests

Private ignored preparation:
`data/missing-link-demand-operation-execution-preparation-2026-10-09/`.
Its exact inventory is `prepared.json`, `protocol.md`, `baseline.json`, unchanged
`inputs.json`/`references.json`, eleven `policy-envelope-*.json` files and eleven
`native-request-*.json` files. It contains no outputs, attempt/start markers or
paid entrypoint. Status is `offline_only_no_executor`.

Independent SHA-256 anchors retained outside that preparation:

| Artifact | SHA-256 |
| --- | --- |
| Execution protocol, UTF-8/LF | `ba56274b06c35eeb113251888d387f0b5246888f70943d2f6dd6fb710092fb81` |
| Private baseline, exact bytes | `b0845f7448e11c225802a2fb668682043377ad1aedbaf8304c9edd1c5ad603d7` |
| Private preparation manifest, exact bytes | `f759f36aa2c39a61e53ad73950ca4d2b21f8eb430e23641fe26ba716edf8c28d` |

The manifest pins the merged/reviewed policy tree, unchanged first-party code,
public settings, original input/reference digests, v4 envelope manifest, ordered
private accounting IDs and exact native body sizes/hashes/reservations. No
credential, operator reference card or descriptive control ID enters a native
request. Original IDs remain in the operator mapping. All eleven envelopes are
byte-identical to v4; native bodies use the pinned provider's SYSTEM/framing,
policy instruction, context-only data and closed schema under phase `request`.

All eleven native bodies fit within 180,000 bytes; maximum **26,383 bytes**.
The proposed conservative reservation sum is **USD0.051305**, with one request
per slot and a USD0.02 per-slot limit. The segment maximum is USD0.10, atomically
capped at cumulative USD8.1266132 within the original USD10 allowance. A complete
eleven-slot prefix would reach USD8.0779182. These are software reservation
calculations using frozen parameters, not current-price verification or billing.
No unused cap authorizes extra attempts, repair, substitution or a new allowance.

## Baseline and verification

Read-only preparation snapshots all twelve original `ml_*` tables, original
allowance rows/reservation prefix and **1,315 protected files**. The inventory
includes the previous 941 historical files, sealed paid-run evidence, subsequent
source/root audits, separate control inputs/references and all four earlier
policy preparations. Baseline remains **555 reservations / USD8.0266132**, with
zero active jobs. Non-accounting data, reservations and protected bytes reproduce
before and after preparation. Original paid-run receipt manifest remains
`da952e024c0356cf81ac39dfb301620aef9c2a6d80a91782eba413d64ce35df7`.

Offline verification rebuilds every envelope and native body from unchanged
inputs/settings, compares ordered hashes/costs, confirms exact inventories and
code fingerprints, and checks the read-only baseline again. The original
control provenance checker reproduces all eleven roots and 74 reference anchors.
The existing policy's 26 authored controls pass. The PR92 1,445-test suite and
matrix CI are baseline evidence; no new executor conformance suite exists yet.

The next implementation must enforce identity/leases, exclusive run/slot markers,
atomic original-ledger reservations and exact-prefix ownership; preserve native
terminals before parsing/validation; stop globally on transport, generation,
persistence or integrity failures; and permit continuation only for explicit
post-receipt policy-normalizer rejection. Freeze its new executable fingerprints
in a separate owned successor after review/merge. Retain every slot/failure and
unknown, and assess each field/constraint/context gap independently without
reference substitution, inferred truth or model-quality/qualified-lead claims.
