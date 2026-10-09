# Demand-operation policy v3 execution preparation

The [separate v3 execution protocol](missing-link-demand-operation-policy-v3-execution-protocol-2026-10-09.md)
specifies an eleven-slot development experiment after PR100 merged as
`2c6fe347b2ff7df31868f385ac42d2a9e34b7e73`, with the exact reviewed
`2485cdf0f24197560abfe13598308f2907e3e3ba` tree. Scoped review was clean and
all four CI jobs passed. The 113 focused and 1,532 full local tests passed on
that policy head; they establish mechanics, not v3 instruction adherence.

This stage changes public documentation only. Offline preparation and read-only
verification made no credential lookup, identity check, lease acquisition,
reservation, provider call or prediction. Existing executors remain bound to their
own policies; there is no v3 executor, paid entrypoint or call authorization.
Production behavior remains unchanged.

## Independent anchors and exact inventory

New private ignored directory:
`data/missing-link-demand-operation-policy-v3-execution-preparation-2026-10-09/`.
Its 27 files are `prepared.json`, `protocol.md`, `baseline.json`, unchanged
`inputs.json` and `references.json`, eleven `policy-envelope-*.json` and eleven
`native-request-*.json`. There are no predictions or start/attempt markers.
Status is `offline_only_no_policy_v3_executor`; creation was exclusive and must
not be replayed or overwritten.

Digests retained independently outside that directory:

| Artifact | SHA-256 |
| --- | --- |
| V3 execution protocol, UTF-8/LF | `a84a8e039ef8e91cd6bb135305f69dce4431306ab3772c60ddf0c6fe7c28bb31` |
| Private baseline, exact bytes | `247aaf5cc1bd3ebf6cced744b29c6ed830c42d3db53449f7ae3678489466edd8` |
| Private preparation manifest, exact bytes | `03bd97b6a26b74950ff5a6df921a9a92e37a2c298f6db2a5d556befb137ae741` |

The manifest binds merged/reviewed policy code, protocol commit `2cb10b8`, all
48 existing first-party LF fingerprints, public settings, both consumed native
and assessment anchors, unchanged inputs/references, unused accounting slot order
and every new envelope/body. A future owned freeze must additionally bind the
new v3 adapters and their reviewed merged tree. This is an offline source
preparation, not an approved execution tree or an owned run.

Every new envelope has exactly the original context/schema, with changed
instructions only. Independent re-encoding reproduces all eleven frozen native
bodies; replacing only the v2 user instruction text reproduces every new payload.
SYSTEM/framing, model/settings, strict schema name, phase, storage and streaming
remain unchanged. References, annotations, descriptive control IDs and previous
predictions stay outside model-facing inputs.

Maximum envelope/native sizes are **27,318 / 29,597 UTF-8 bytes**, within their
180,000-byte bounds. Each native body adds **1,209 bytes** to v2. The prospective
eleven-slot conservative reservation sum is **USD0.0548404**, with one call and
USD0.02 maximum per slot. Settings remain `gpt-6-luna`, Responses streaming,
strict JSON Schema, `medium`, 6,000 output tokens, `store=false`, phase `request`.
These software calculations do not establish current provider prices, billing
or native usage, and encoding does not reserve funds.

## Historical evidence and original accounting

Read-only verification confirms both consumed native inventories, both independent
assessments, their unchanged checked predictions/review paths and previously
protected history. The current v2 verifier checks the exact original reservation
extension; the older v1 receipt seal is checked statically, without replaying its
historical live-prefix verifier. Both old policies, adapters, tests, protocols,
frozen requests and reference bytes remain unchanged.

The new baseline contains **1,635 protected files**: the previous 1,515, all
107 consumed v2 run files and all 13 v2 assessment files. It retains all twelve
original `ml_*` table hashes, prior reservation rows, allowance identities and
zero active jobs. Before/after preparation and verification, accounting remains
**577 reservations / USD8.1314287** under the original account, database and
allowance. The configured total remains USD10; no increase, refund, reset,
deletion, moved reservation or replacement allowance occurred.

The prospective segment cap is USD0.10 and cumulative atomic ceiling
**USD8.2314287**. All eleven reservations, if separately authorized and executed,
would reach **588 / USD8.1862691**. The distinct private IDs
`demand-operation-policy-v3-owned-2026-10-09-01` through `-11` are unused;
neither those IDs nor unreserved capacity authorize calls.

Verification checks exact inventory, independent digests, all old/new pinned code,
protected bytes, unchanged input/reference copies, every envelope/native body,
public settings, unused slot order, sizes and per-slot/total reservation arithmetic.
The original provenance checker also reproduces eleven roots and 74 reference
anchors. These checks validate bytes/offsets and mechanics, not semantic truth,
acquisition completeness or model quality. Public scope is four documentation files;
no application implementation changed or required new unit tests in this phase.

## Required next stage

After scoped review/CI/merge of this protocol, implement a separate opt-in v3
executor/run adapter with authored conformance for policy binding, identity/leases,
original accounting prefixes, exclusive consumption, native retention and strict
three-stage validation. Match frozen slots with concrete JSON types before any
reservation. Schema/integrity failures stop globally; only a retained post-schema
local rejection with successful independent rechecks may permit continuation.
Old executor tests alone do not prove this new binding or inventory handling.

After that adapter's review/CI/merge, freeze a new owned run on its exact code
and obtain separate explicit human authorization for these eleven bodies and
limits. Future predictions and an independent per-path assessment stay separate
from both consumed runs. Known retrospective controls cannot establish held-out
accuracy, causal improvement, fresh Discover utility or qualified external leads.
Acquisition, acquired-code execution, UI/key entry and production promotion remain
deferred.
