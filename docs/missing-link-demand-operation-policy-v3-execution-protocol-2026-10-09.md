# Demand-operation policy v3 native execution protocol

This prospective protocol follows the [isolated v3 correction](missing-link-demand-operation-policy-v3-2026-10-09.md).
PR100 merged as `2c6fe347b2ff7df31868f385ac42d2a9e34b7e73`, matching reviewed
head `2485cdf0f24197560abfe13598308f2907e3e3ba` and tree
`1f88d20b8cdb01a6c29839a867bb5da8d27885ab`. Scoped Codex review was clean;
all four Windows/Linux Python 3.10/3.13 CI jobs, 113 focused and 1,532 full
local tests passed. These checks establish mechanics, not v3 model adherence.

## Offline preparation and separate authorization

Policy-v3 means changed instructions, not the revision number of an older
execution protocol. Preserve both consumed native runs, separate assessments,
reference cards, prior protocols/preparations, policy modules, executors and tests.
Never replay a consumed run or reuse its authorization for changed bodies.

Prepare exclusively in the new private ignored directory
`data/missing-link-demand-operation-policy-v3-execution-preparation-2026-10-09/`.
Freeze unchanged inputs and separate reference copies, this protocol, original
baseline, eleven new envelopes/native bodies, public settings, ordered unused
accounting IDs and first-party LF fingerprints. Retain the manifest digest
independently outside the directory. No credentials, account check, lease,
reservation, provider call or prediction belongs to preparation.

The old executors remain bound to their own policies. Implement a separate opt-in
v3 executor/run adapter later with explicit dependencies and authored conformance,
preserving every previous module/test. Review, CI and merge must precede a new
owned run binding the exact reviewed/merged executable tree, this preparation and
all additional adapter fingerprints. Separate human call authorization must bind
the owned manifest, original account/allowance, eleven bodies and limits.
Preparation, merge, available capacity and schema compatibility authorize no calls.
No paid entrypoint is added in this phase.

## Inputs, encoding and settings

Use all eleven retained development packets in original order, one attempt each.
They are known development controls, not held-out data. Keep these bytes unchanged:

| Artifact | SHA-256 |
| --- | --- |
| Inputs, exact bytes | `c1311e56aebd31cd750c82d9a3f7192b5eb77ca9eadaef903b7d544aa44856dd` |
| References, UTF-8/LF | `6cc171bc9e83130479156e71af09869c9bc6100240f28f69865da5fc95b6e9df` |
| Policy-v3 module, UTF-8/LF | `c82e06f39a5e291c4ca458fe41df3caed76f9ab1364e1bf4794c90482a009050` |
| Pre-implementation v3 contract, UTF-8/LF | `7bea9a72f37fc9d2c0629d0db07a1b74997becf93f60caabdd6da2f99486eccf` |

Build only with `scripts.missing_link_demand_operation_policy_v3.build_request`.
Keep the original context, opaque IDs, exact spans/coverage, schema and mechanical
normalization. References, annotations, descriptive control IDs and previous
predictions stay outside model-facing data; no per-control expected answers enter
the general instructions. Enforce the 180,000-byte complete-envelope UTF-8 limit
including v3 instructions, with no truncation.

Encode through the pinned `Provider._encode_prompt(instructions, context, schema,
'request')`. Compare every payload member with frozen v2: only user instruction
text changes. Preserve SYSTEM/framing and schema naming; do not encode an envelope
as context, duplicate the schema or use another decoder. Pin exact native and
envelope hashes independently alongside all imported first-party dependencies.

| Setting | Frozen value |
| --- | --- |
| Endpoint | `https://api.openai.com/v1/responses`, no redirects |
| Model / reasoning | `gpt-6-luna` / `medium` |
| API / format / phase | Responses streaming / strict JSON Schema / `request` |
| Schema / storage | `missing_link_request` / `store=false` |
| Output / native body bound | 6,000 tokens / 180,000 UTF-8 bytes |
| Calls / reservation per slot | 1 / USD0.02 maximum |
| Configured reservation rates | USD0.10 input and USD0.50 output per million |

Each native body adds 1,209 bytes to its frozen v2 counterpart. Maximum envelope
and native sizes are **27,318 / 29,597 UTF-8 bytes**. The eleven-slot conservative
reservation sum is **USD0.0548404**, computed per slot as
`((native_bytes + 2048) * 0.10 + 6000 * 0.50) / 1000000`.
These are software reservation parameters, not verified provider prices, actual
billing or usage estimates. Offline encoding reserves nothing.

## Original accounting and immutable evidence

Retain account `Daniele-Cangi`, database `data/repotraction-daniele-cangi.sqlite3`,
allowance `missing-link-verification-2026-09-30` and original configured USD10 total.
Baseline is **577 reservations / USD8.1314287**, with zero active jobs. The proposed
segment cap is USD0.10 and cumulative atomic ceiling **USD8.2314287**. Eleven
complete new reservations would reach **588 / USD8.1862691**. No increase, reset,
refund, deletion, moved reservation or new allowance is permitted. Unused capacity
grants no additional slot, retry, replacement or repair.

Use distinct private accounting IDs `demand-operation-policy-v3-owned-2026-10-09-01`
through `-11`, in frozen order; reject any already present. Independently verify
both consumed prepared/receipt anchors and assessment anchors, exact sealed
inventories, predictions/reviews and old code. Check the old v1 seal statically;
its historical live-prefix verifier is not valid after the v2 reservation extension.
Use the current v2 verifier to check that exact original accounting extension.

The baseline extends the **1,515** protected files with all **107** consumed v2
native-run files and **13** v2 assessment files: **1,635 protected artifacts**.
Preserve all twelve original `ml_*` table hashes, prior reservation rows, allowance
identities, matches, caches and source rows. Pin all **48** existing first-party LF
fingerprints, including both unchanged executors and the v3 pure policy/tests.
Later owned preparation adds this new 27-file preparation and new adapter code;
this preparatory tree is not an approved execution tree.

Before calling, the future runner must require clean exact reviewed merged code,
independent digests, exact inventories, all native bodies/settings and baseline.
Hold the original database worker lease and an owned-run lease, deny active jobs
and recheck after acquisition. Force a fresh fixed-account check before every
attempt with integrity gates around it. Check cancellation/identity during streaming
with at most the existing three-second identity-success cache.

An exclusive start marker consumes the run even with zero calls. Use one exclusive
attempt marker per ordered slot. Persist exact request metadata before the original
Store's atomic reservation; bind cost/ID to the cumulative ceiling. Journal each
committed reservation immediately and verify its exact owned prefix. A failure
after commit retains the reservation and stops, including a lost journal. No resume,
repeat or original job/match/cache/source creation. Recheck original tables, old rows,
allowance identity and history at every gate/finalization; operational locks stay separate.

## Native retention, validation and stopping

Retain the complete decoded native terminal privately before parsing, shape checks,
normalization or usage reporting. Preserve native status/output/ID/usage, including
failure, incompleteness and refusal. Decoded JSON does not preserve SSE whitespace
or prior deltas. Keep terminal, parsed prediction, mechanically checked card and
independent operator annotations separate; missing usage is unknown, not zero.

Reuse the bounded no-retry receipt reader: 55-second socket timeout, 240-second
stream deadline, 8,000,000-byte total and 512,000-byte line bounds. Transport,
redirect/HTTP, missing/inconsistent terminal, native failure/incompleteness/refusal,
malformed JSON, schema, identity, budget, persistence or integrity failures stop
globally. Preserve absent terminals as absence. Bounded public diagnostics exclude
credentials, upstream text and private roots.

The future v3 executor must preserve the reviewed three-stage boundary:

1. Rebuild through the pinned v3 builder and verify packet/context/schema/native
   body and code outside local handlers. Match the entire execution slot structure
   to frozen data with concrete JSON types, so booleans cannot impersonate integers.
   Keep immutable snapshots of raw prediction, packet, context, schema and slots.
2. Run standalone `missing_link.contracts.validate_shape(raw, frozen_schema)`
   outside the local handler, even after receipt-reader validation. Failure is
   global and stops before any next slot.
3. Call unchanged `normalize_prediction(raw, context, packet=packet)` in a narrow
   handler catching only its `ValueError`. After success or that exception, recheck
   immutable inputs and code, and repeat standalone shape validation outside the
   handler. Failed rechecks stop globally. Only a retained post-schema local
   inconsistency with every independent recheck/gate passing can permit continuation.
   Persist prediction/rejection before advancing.

New authored conformance must distinguish global schema failure, schema-valid local
rejection and changed raw/context/code even when normalization raises `ValueError`.
Preserve exact slot metadata/types before reservations. Do not assume old tests prove
v3 binding, catch arbitrary errors locally, repair outputs, substitute references or
classify semantics. Seal the entire owned evidence inventory, failures and final
integrity checks with an independent digest; failed finalization retains evidence
and stops without claiming sealed completion.

## Independent development comparison

Read each completed v3 card against original supplied roots and separate frozen
references before consulting either previous assessment. Annotate kind, five fields,
each constraint, relation and each context gap with bounded independent reasons and
individual paths. Record unsupported claims, appropriate unknowns, missed stated
facts, omitted conditions and unassessed paths; preserve the prediction unchanged.
Retain the new assessment separately from both consumed assessments.

Report all eleven dispositions, failures, unattempted slots and all-unknown cards.
Assess minimum/preferred outputs versus open owner choices, requirements versus
reported context, semantic roles, delivery conditions, gaps and identifier fidelity
against the prospective v3 contract. Do not change references to fit any policy.
Different constraint/gap arrays have different denominators and cannot be treated
as identical paired assertions; any per-slot comparison is descriptive.

Coverage remains ten full-root assertions, one article gap, eleven incomplete
discussions and no independently verified acquisition. Operator judgments are
assertions, not automatic truth. Known retrospective controls cannot establish
held-out accuracy, causal improvement, fresh utility, compatibility, ranking,
adoption or qualified leads. No acquisition, acquired-code execution, production
promotion or UI/key-entry work belongs to this stage.
