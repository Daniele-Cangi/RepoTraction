# Demand-operation policy v2 execution preparation

The [new policy-v2 execution protocol](missing-link-demand-operation-policy-v2-execution-protocol-2026-10-09.md)
freezes a prospective eleven-slot development experiment after PR96 merged as
`b95b1e2c2dcfb32769e80b88b2b4efeae73cd11b`, with the same tree as reviewed
head `7ecd09913c01d941a6842f97e8ebb3168ff6379e`. Its Codex review has no
findings and all four CI jobs passed. The 62 focused and 1,481 full tests passed
on that policy head; those results do not prove semantic instruction adherence.

This stage changes documentation only. Offline freezing and independent read-only
verification performed no credential lookup, account check, lease acquisition,
reservation, provider call or prediction. The original executor remains bound
to policy v1. No new policy-v2 executor, paid entrypoint or call authorization
exists yet; production behavior remains unchanged.

## Independent anchors and inventory

Private ignored preparation directory:
`data/missing-link-demand-operation-policy-v2-execution-preparation-2026-10-09/`.
Its exact 27-file inventory is `prepared.json`, `protocol.md`, `baseline.json`,
unchanged `inputs.json` and `references.json`, eleven `policy-envelope-*.json`
files and eleven `native-request-*.json` files. There are no outputs or attempt/start
markers. Status is `offline_only_no_policy_v2_executor`.

Independent digests retained outside that directory:

| Artifact | SHA-256 |
| --- | --- |
| Policy-v2 execution protocol, UTF-8/LF | `c60fc910194f5ceb38c90a3ed1412847d32543a28b21cee5e758100647a05e56` |
| Private baseline, exact bytes | `e99ad7a947ff4adefa1b9cd026f702bf09051c12115735c4fc6d67df38c33f71` |
| Private preparation manifest, exact bytes | `4ebbbb80c708eaf3531540679211bac18f7c4443a1351a51751cf97bb334390d` |

The manifest binds the merged/reviewed policy tree, protocol commit `388c475`,
43 first-party LF fingerprints including the unchanged original adapters and
new policy/tests, public settings, old independent native/assessment anchors,
exact input/reference copies, ordered unused accounting IDs and every new body.
A future owned freeze must additionally bind its newly reviewed policy-v2 adapter
and dependencies. This preparatory tree is not a reviewed execution tree.

All eleven new envelopes have byte-identical original context/schema and changed
instructions only. Re-encoding reproduces all exact new native bytes. Replacing
only the original payload's user instruction text produces each new payload;
SYSTEM, framing, model/settings, schema name, phase, storage and streaming remain
unchanged. Original reference cards, annotations, descriptive control IDs and
previous predictions are absent from model-facing inputs.

Maximum envelope/native sizes are **26,109 / 28,388 UTF-8 bytes**, both within
180,000-byte limits. Each native body adds exactly 2,005 bytes to its original.
The proposed eleven-slot conservative reservation sum is **USD0.0535105**,
with one call per slot and USD0.02 maximum per slot. Original settings remain
`gpt-6-luna`, Responses streaming/strict JSON Schema, `medium`, 6,000 output tokens,
`store=false`, phase `request`. These are software reservation calculations,
not verified provider prices, invoice amounts or native usage estimates.

## Preserved history and accounting

Independent verification reproduces the consumed policy-v1 run using its original
prepared and sealed-receipt digests:
`f1ae64dae8c73429bbe923a0fed5d8e482020d6af6ac682a995df51cea28122e`
and `65ff6142a6ceb2a1096975281d0bf564c12fcbfdca10738775cedc912b2c15d3`.
Its separate operator assessment remains anchored by
`1222afe56697d5a43cd143d46a3be45b1a14166ebf380ffd7a3a3164cb88e586`;
each checked prediction and per-path review still reproduce. Earlier preparations,
original code/tests/protocols and reference bytes remain unchanged.

The new read-only baseline preserves all twelve original `ml_*` table hashes,
allowance identities, prior reservation rows and **1,488 protected files**:
the previous 1,369 artifacts, 106 consumed-run files and 13 assessment files.
There are zero active jobs. Before/after freezing and independent verification,
the original ledger remains **566 reservations / USD8.0779182** under account
`Daniele-Cangi`, original database and `missing-link-verification-2026-09-30`.
Configured total stays USD10; no increase/reset/refund/new allowance occurred.

Prospective limits are a USD0.10 segment and cumulative atomic ceiling
**USD8.1779182**. Eleven complete reservations would reach **577 / USD8.1314287**.
The distinct accounting IDs `demand-operation-policy-v2-owned-2026-10-09-01`
through `-11` are currently unused. Neither those IDs nor unused cap authorize calls.

Read-only verification compares exact inventories/independent anchors, all protected
bytes, code fingerprints, unchanged inputs/references, every envelope/native body,
public settings, unused slot order, lengths and per-slot/full reservation math.
The original provenance checker reproduces all eleven retained roots and 74
reference anchors. It verifies offsets/digests, not semantic truth or acquisition.

## Required next stage

Implement the separate opt-in policy-v2 executor/run adapter against this frozen
protocol, preserving the old executor and consumed run. Authored conformance must
cover instruction-builder binding, identity/leases, exact original accounting
prefixes, exclusive consumption, terminal retention and three-stage validation:
schema/integrity failures stop globally; only a retained post-schema local rejection
after successful independent rechecks can permit the next slot. Do not infer that
old executor tests already cover new binding or successor inventory handling.

After scoped review/CI and merge, freeze a separate owned run on its exact code
and obtain explicit authorization for these eleven bodies and limits. Later native
outputs and independent per-path assessment must remain separate from old outputs,
with all failures/unattempted slots reported. Known retrospective controls cannot
establish causal improvement, held-out accuracy, fresh utility or qualified leads;
production promotion, new acquisition, source execution and UI/key-entry remain
deferred.
