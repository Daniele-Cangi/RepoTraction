# Demand-operation policy v2 native execution protocol

This prospective protocol follows the [isolated instruction correction](missing-link-demand-operation-policy-v2-2026-10-09.md).
PR96 merged as `b95b1e2c2dcfb32769e80b88b2b4efeae73cd11b`; its tree
matches reviewed head `7ecd09913c01d941a6842f97e8ebb3168ff6379e`.
Scoped Codex review found no issues and all four Windows/Linux, Python 3.10/3.13
CI jobs passed. The 62 focused and 1,481 full tests establish baseline mechanics,
not instruction adherence or executor conformance for this new experiment.

## Separate preparation and authorization

The name **policy-v2** identifies changed policy instructions. The preserved
[older execution protocol revision 2](missing-link-demand-operation-execution-protocol-v2-2026-10-09.md)
used policy v1 and fixed a validation-stage boundary; it is not this experiment.
Keep both older protocols/preparations, original code/tests, frozen references,
the consumed eleven-call native run and its separate operator assessment immutable.
Never replay that run or use its paid-call authorization for these new bodies.

Prepare offline in the separately named private directory
`data/missing-link-demand-operation-policy-v2-execution-preparation-2026-10-09/`.
This freezes inputs, reference copies, protocol, baseline, new envelopes/native
bodies, public settings, ordered unused accounting IDs and first-party fingerprints.
Retain its manifest digest independently outside the directory. No credential
lookup, identity check, lease, reservation, model call or output is part of preparation.

The original executor remains explicitly bound to policy v1. Implement a separate
opt-in policy-v2 executor/run adapter with explicit dependencies, preserving every
old module and test. Obtain scoped review/CI and merge it, then freeze a new owned
run binding that exact merged/reviewed tree, this preparation and additional adapter
fingerprints. Require separate explicit call authorization bound to that owned
manifest, account, allowance, eleven bodies and limits. Preparation, merge and
schema compatibility grant no call authorization. No paid entrypoint is added here.

## Inputs, native differences and limits

Use all eleven retained development packets in their original order, one attempt
each. These controls were read before either policy; they are not held-out data.
Preserve the exact input and separate reference bytes:

| Artifact | SHA-256 |
| --- | --- |
| Inputs, exact bytes | `c1311e56aebd31cd750c82d9a3f7192b5eb77ca9eadaef903b7d544aa44856dd` |
| References, UTF-8/LF | `6cc171bc9e83130479156e71af09869c9bc6100240f28f69865da5fc95b6e9df` |
| Policy-v2 module, UTF-8/LF | `4a1692456492b509533a5c5db30f8fb19d8b1f60eb4e4f4abbbfb084859e48bc` |
| Pre-implementation v2 contract, UTF-8/LF | `9a146f7969a4c767d6b151c603587a60da24ec82bbb7a603e9f469614ab1fdec` |

Build envelopes with `scripts.missing_link_demand_operation_policy_v2.build_request`.
Context, opaque IDs, coverage/spans, schema and mechanical normalization remain
exactly the original policy's. Only instructions differ. Enforce the complete
180,000-byte envelope bound including the revised instructions. Keep references,
operator annotations, descriptive control IDs and previous predictions outside
all model-facing data. General instructions contain no per-control gold answers.

Encode using the pinned `Provider._encode_prompt(instructions, context, schema,
'request')`. Preserve SYSTEM/framing and compare every payload member with the
original body; only the user instruction text changes. Do not encode the envelope
as context, duplicate the schema or use a facet-reference decoder. Pin exact
envelope and native-body hashes separately, alongside all imported first-party
dependencies, unchanged old adapters and new policy/test fingerprints.

| Setting | Frozen value |
| --- | --- |
| Endpoint | `https://api.openai.com/v1/responses`, redirects forbidden |
| Model / reasoning | `gpt-6-luna` / `medium` |
| API / format / phase | Responses streaming / strict JSON Schema / `request` |
| Schema name / storage | `missing_link_request` / `store=false` |
| Output / native body bound | 6,000 tokens / 180,000 UTF-8 bytes |
| Calls / reservation per slot | 1 / USD0.02 maximum |
| Configured reservation rates | USD0.10 input and USD0.50 output per million |

Each new body is 2,005 bytes longer than its original. Maximum envelope/native
sizes are 26,109 / 28,388 bytes. The eleven-slot conservative reservation sum is
USD0.0535105, computed per slot as
`((native_bytes + 2048) * 0.10 + 6000 * 0.50) / 1000000`.
These are frozen software reservation parameters, not verified provider prices
or billing. Encoding does not reserve funds.

## Original accounting and evidence

Keep account `Daniele-Cangi`, database `data/repotraction-daniele-cangi.sqlite3`,
allowance `missing-link-verification-2026-09-30` and configured USD10 total.
Baseline is **566 reservations / USD8.0779182**, with zero active jobs. The
proposed segment cap is USD0.10, with cumulative atomic ceiling **USD8.1779182**.
A complete eleven-slot prefix would reach **577 / USD8.1314287**. No increase,
refund, reset, deletion, moved reservation or new allowance is permitted.
Unused capacity grants no additional slot, replacement, retry or repair.

Use unique private job IDs `demand-operation-policy-v2-owned-2026-10-09-01`
through `-11`, in frozen order, and reject any already present in the ledger.
Before freezing, independently verify the consumed policy-v1 prepared/receipt
anchors and operator-assessment anchor. Preserve their exact directory inventories
and all original historical bytes. The new baseline includes all 1,369 previously
protected artifacts, all 106 consumed-run files and all 13 assessment files:
**1,488 protected files**, with original twelve `ml_*` tables, allowance identities,
all prior reservation rows and non-accounting hashes unchanged.

The future executor must require clean reviewed merged code, independent digests,
exact inventories, all native bodies/public settings and the original baseline
before calling. Hold the original database worker lease and an owned-run lease;
deny active jobs and recheck after acquisition. Force a fresh fixed-account check
before every attempt, with integrity gates around it. Check identity/cancellation
during streaming using at most the existing three-second success cache.

An exclusive start marker consumes the run even with zero calls. Each ordered
slot has an exclusive attempt marker. Persist its exact request metadata before
the original Store's atomic reservation, binding cost/ID to the cumulative ceiling.
Journal each committed reservation immediately and verify the exact owned prefix.
Any failure after commit retains the reservation and stops, including a lost journal.
No resume or repeat; no original jobs, matches, caches or source rows are created.
At every gate/finalization preserve original non-accounting tables, prior rows,
allowance identity and protected history. Operational lease locks remain separate.

## Retention, validation and stopping

Retain the complete decoded native terminal privately before parsing, shape checks,
normalization or usage reporting. Preserve native status/output/response ID/usage,
including failure, incompleteness and refusal. Decoded JSON does not preserve SSE
whitespace or preceding deltas. Keep native terminal, raw parsed prediction,
mechanically checked card and independent operator annotations separate.

Reuse the unchanged bounded no-retry receipt reader: 55-second socket timeout,
240-second stream deadline, 8,000,000-byte total and 512,000-byte line bounds.
Transport/redirect/HTTP errors, absent/inconsistent terminals, native failure,
incompleteness/refusal, malformed JSON, schema, identity, budget, persistence or
integrity failure stop the sequence globally. Preserve missing terminals as absence.
Public diagnostics are bounded and exclude credentials, upstream text/private roots.

The new executor must reproduce the reviewed three-stage validation boundary:

1. Rebuild with the pinned **policy-v2** builder and verify original packet,
   context, schema, native body and executable fingerprints outside local handlers.
   Keep immutable snapshots of raw prediction/packet/context/schema.
2. Run standalone `missing_link.contracts.validate_shape(raw, frozen_schema)`
   outside the local handler, even after receipt-reader shape validation. Failure
   is global and stops before any next slot.
3. Invoke the unchanged `normalize_prediction(raw, context, packet=packet)` in a
   narrow handler catching only its `ValueError`. After success or that exception,
   recheck immutable raw/packet/context/schema and code fingerprints, and repeat
   standalone shape validation outside the handler. Failed rechecks are global.
   Only a retained post-schema local inconsistency with all rechecks/gates passing
   permits continuation. Persist prediction/rejection before advancing.

Authored conformance must distinguish global schema failure, schema-valid local
rejection, and changed raw/context/code even when the normalizer raises `ValueError`.
Never catch arbitrary errors as local, repair a card, substitute references or
classify semantics automatically. Mechanically valid misleading claims and unknowns
remain retained. Native usage is separate from conservative reservations; missing
usage is unknown, not zero. Seal the entire owned evidence inventory, failures and
final integrity checks with an independently retained digest. Failed finalization
retains evidence and stops without a claim of sealed completion.

## Independent development comparison

Read every completed v2 prediction against the original supplied roots and
separate frozen references. Annotate kind, five fields, each constraint, relation
and each context gap with bounded independent reasons and individual paths;
record unsupported claims, appropriate unknowns, missed facts, omitted constraints
and unassessed paths. Keep predictions unchanged. Read v2 cards independently
before using prior annotations for a descriptive per-slot comparison; preserve
both assessments without overwriting the consumed policy-v1 assessment.

Report all eleven dispositions, failures, unattempted slots and all-unknown cards.
Describe operation/mechanism distinctions, partial known facts, declared/reported
context, pending owner choices/local consistency, explicit constraints, identifier
fidelity and gaps from the pre-implementation contract. Do not change references
to fit either policy. Different constraint/gap counts cannot be treated as identical
paired assertions; compare meaning/path and report denominators separately.

Coverage remains ten full-root assertions, one retained article gap, eleven
incomplete-discussion assertions and no independently verified acquisition.
Operator labels are assertions, not automatic truth. These retrospective known
controls cannot establish held-out accuracy, causal improvement, fresh utility,
compatibility, ranking, external adoption or qualified leads. No new acquisition,
source execution, production promotion or UI/key-entry work belongs to this stage.
