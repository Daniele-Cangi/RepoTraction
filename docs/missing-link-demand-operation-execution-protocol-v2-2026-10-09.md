# Demand-to-operation native execution protocol, revision 2

This revision supersedes the preserved [revision 1](missing-link-demand-operation-execution-protocol-2026-10-09.md)
before any model prediction. Its PR93 P2 review exposed ambiguity between a
generation-schema failure and a post-schema local-normalizer rejection. Only the
validation-stage boundary changes; native bodies, policy, inputs/references,
slot order, limits and original allowance remain unchanged. The original
protocol/private preparation remain immutable, with zero outputs/calls.

## Preparation and authorization boundary

PR92 merged as `99064726996e6a2a150029c75d28efb8d792ef58`, with the same tree
as reviewed head `3a90a16b0e158f85b58974cc4f9409716045762b`. Its scoped Codex
review has no remaining findings. All four CI jobs passed; Windows/Python 3.13
needed a failed-job rerun after a local HTTP connection interruption. This is
baseline evidence, not conformance evidence for a future executor.

This document freezes a prospective execution contract and private native request
bodies. Preparation is offline: no credential lookup, account verification,
lease acquisition, model request, prediction or reservation. There is no paid
entrypoint in this change. Implement the opt-in owned executor separately, test
its gates with authored fixtures, obtain scoped review/CI and merge it, then
freeze a new owned run on that exact code before separately authorized calls.
Neither this preparation nor merging its documentation grants call authorization.

Use the unchanged [policy protocol](missing-link-demand-operation-policy-protocol-2026-10-09.md)
and its eleven retained development controls. These examples were inspected before
the policy was written; results cannot establish held-out accuracy, causal
improvement, live relevance or fresh Discover utility. No source execution,
additional acquisition, candidate compatibility assessment or production promotion
is part of this run. Existing qualified-lead requirements remain separate.

## Immutable inputs, order and native wire

Use all eleven packets in their original `inputs.json` order, exactly once each.
Keep original IDs only in the private operator mapping and accounting slot IDs;
send opaque policy IDs. Keep references outside all model-facing bodies.

- Exact input SHA-256:
  `c1311e56aebd31cd750c82d9a3f7192b5eb77ca9eadaef903b7d544aa44856dd`.
- Reference SHA-256, LF:
  `6cc171bc9e83130479156e71af09869c9bc6100240f28f69865da5fc95b6e9df`.
- Policy protocol SHA-256, LF:
  `14155abfccb0cc1f2bc09747de10c4fd3afea7cc683e4cb4b95712d52c27c3df`.
- Current v4 envelope manifest SHA-256:
  `7a893d49e4ee6f76df35702feebf8f5f487de2df4e01843a6d466ce05378cd50`.

Rebuild each experimental envelope from its frozen packet and match the v4 bytes.
Encode with the unchanged `Provider._encode_prompt`: instruction is envelope
`instructions`, data is envelope `context`, schema is envelope `schema`, phase is
`request`. Do not send the envelope itself as data, duplicate its schema, insert
reference text, or apply the older facet-reference decoder. Record both envelope
and exact native body hashes; they are different serialization boundaries.

The wire retains the existing provider SYSTEM instructions, followed by policy
instructions and the untrusted context. Pin the encoder, SYSTEM, policy/review,
receipt reader, budget, store, identity, lease and imported first-party code to
reviewed fingerprints. This preparation pins the PR92 baseline; a future owned
run must additionally pin the newly reviewed executor and its dependencies.
Changed bodies, settings or code require a separately named successor before
any output, preserving every earlier preparation. Never regenerate around a
failure or silently accept a changed input/reference/protocol.

Freeze these public settings without reading or persisting a credential:

| Setting | Frozen value |
| --- | --- |
| Endpoint | `https://api.openai.com/v1/responses`, redirects forbidden |
| Model | `gpt-6-luna` |
| API / format | Responses streaming, strict JSON Schema |
| Schema name / phase | `missing_link_request` / `request` |
| Reasoning / storage | `medium` / `store=false` |
| Output / native body bound | 6,000 tokens / 180,000 UTF-8 bytes |
| Calls / reservation per slot | 1 / USD0.02 maximum |
| Configured reservation rates | USD0.10 input and USD0.50 output per million |

Rates are the existing software reservation parameters, not verified current
provider prices or a billing estimate. All eleven exact native bodies fit:
maximum 26,383 bytes. Their full proposed conservative reservation is USD0.051305,
computed per slot as `((native_bytes + 2048) * 0.10 + 6000 * 0.50) / 1000000`.
No reservation is made by encoding or freezing these bodies.

## Original ledger, identity and ownership

Use account `Daniele-Cangi`, original database
`data/repotraction-daniele-cangi.sqlite3` and allowance
`missing-link-verification-2026-09-30`. The read-only baseline is 555 reservations
and USD8.0266132, with no active jobs. Keep the configured total at USD10.
The proposed segment cap is USD0.10 and its cumulative atomic ceiling is
USD8.1266132. A complete eleven-slot prefix would reach USD8.0779182.
Unused segment capacity does not authorize additional calls or replacement slots.
Never reset, refund, delete or move a reservation, or create another allowance.

Before a future run, verify clean merged code, independent manifest anchors,
exact directory inventories, all request bodies and the unchanged original
database baseline. Require explicit call authorization bound to those identities.
Acquire the original database worker lease and an owned-run lease, deny active
jobs, and recheck integrity after lease acquisition. Force a fresh fixed-account
check before each attempt; uncertainty, account change or lease failure stops.
Checkpoint identity/cancellation during streaming, with at most the existing
three-second success cache. Recheck integrity around each forced identity check.

An exclusively created start marker consumes the owned run even if no request
reaches the provider. Each ordered slot has an exclusive attempt marker and a
unique private job ID. No resume, repeat, automatic retry, repair or substitution.
Persist the exact request metadata before reserving; bind its known cost and
slot ID to the original Store's atomic cumulative cap. Journal the committed
reservation immediately and verify the exact owned prefix. Any failure after
commit leaves the reservation retained and stops the run, including lost journals.
Never infer permission to continue from an apparently unused slot or missing file.

At every gate and finalization, compare all original non-accounting tables,
allowance identities/balances, prior reservation rows, protected historical files,
sealed native evidence, control inputs/references and earlier preparation folders.
Only the exact ordered owned reservation prefix may extend accounting. Runtime
lease locks are owned operational state, not historical evidence to rewrite.
No original jobs, matches, caches or source records are created by this experiment.

## Receipts, validation and stopping

Retain each complete decoded native terminal event privately **before** parsing,
usage accounting, shape validation or acceptance. This preserves native output
text, status, response ID and usage, including failed/incomplete/refused content.
Decoded terminal JSON is not a capture of SSE wire whitespace or earlier deltas.
Keep output text, parsed raw JSON, mechanical normalization and operator review
as separate artifacts; no reference substitution or prediction repair.

Use the existing bounded no-retry receipt reader: 55-second socket timeout,
240-second stream deadline, 8,000,000 received bytes and 512,000-byte line bound.
Transport/redirect/HTTP errors, absent or inconsistent terminals, native failure,
incompleteness/refusal, malformed JSON, generation-schema failure, identity,
budget, persistence or integrity errors stop the entire sequence. Record a bounded
diagnostic; never expose credentials, upstream error text or private roots in
public logs. A transport failure may have no terminal; preserve that absence.

The future executor must separate these validation stages:

1. Retain the native terminal and parsed raw prediction. Rebuild the envelope from
   the pinned original packet and verify code, input, context, schema and native
   body fingerprints outside any slot-local exception handler. Invalid packet,
   changed context or failed provenance checks are global integrity failures.
2. Require standalone `validate_shape(raw, frozen_schema)` success, using
   `missing_link.contracts.validate_shape`, outside the local handler, even if the
   receipt reader has already checked that schema. Any schema failure is a global
   generation failure and stops the sequence before normalization. Preserve the
   exact raw prediction and packet/context/schema snapshots or fingerprints.
3. Only after both prior stages succeed, invoke
   `normalize_prediction(raw, verified_context, packet=verified_packet)` in a
   narrow handler that catches **only `ValueError` from this call**. The policy
   normalizer repeats input/schema checks internally; its exception class alone
   therefore never establishes slot-local classification. On success or caught
   `ValueError`, recheck the unchanged raw/packet/context/schema and executable
   fingerprints, then rerun standalone schema validation, outside that handler.
   Any failed recheck is global. Only when all rechecks pass may the caught error
   be recorded as a post-schema slot-local rejection and permit the next slot.

Persist the unchanged prediction and rejection diagnostic before advancing, then
verify the owned reservation prefix and all run gates. Neither schema failures
nor integrity/persistence errors from any stage may be absorbed as local rejection.
Do not catch arbitrary exceptions or place multiple stages inside the narrow
normalizer handler. Future conformance must distinguish a shape-invalid prediction
(global stop before the next slot), a schema-valid but locally inconsistent card
(retained rejection and permitted next slot), and changed context/raw/code
(global stop even if `normalize_prediction` raises `ValueError`). These are
requirements for the separately reviewed executor, not claims that it exists.
Unknowns and mechanically valid misleading claims are retained, not repaired.

Record native usage separately from conservative reservations; missing usage is
unknown, not zero. Seal the complete owned receipt inventory, including failures
and final integrity checks, with a manifest whose digest is retained independently
outside the run directory. If finalization fails, keep evidence and stop; do not
claim a sealed/completed run. Verify the anchored inventory before reporting.

## Independent development assessment

Read every completed prediction against its original supplied roots and the
separate frozen references. Annotate request kind, all five fields, each constraint,
query relation and **each** context gap, with bounded independent reasons and
individual paths. Report supported/unsupported/unassessed claims, appropriate
unknowns, missed stated facts and omitted constraints without editing predictions.
Also describe semantic-layer confusions and whether concrete educational demand,
pending owner decisions and local facts survived incomplete context.

Report every slot disposition, failure and valid all-unknown output, including
unattempted slots after a global stop. Cite original coverage: ten full-root
assertions, one retained article gap, eleven incomplete-discussion assertions and
no independently verified acquisition. Review labels remain operator assertions;
exact citations prove provenance only. Mechanical acceptance and per-claim counts
are not useful triage, accuracy, eligibility, ranking or lead yield. Keep results
separate from any future fresh repository-only comparison and lead qualification.
