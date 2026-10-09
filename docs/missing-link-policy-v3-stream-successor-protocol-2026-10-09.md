# Policy-v3 stream successor protocol — 2026-10-09

This prospective transport successor follows the reviewed [offline diagnostics](missing-link-policy-v3-stream-diagnostics-2026-10-09.md).
PR104 merged as `61c90872db8308758d6f6994203cf37a550ac6e0`, with the
`18970ea968cbf9018ad0e6bec31c84717303df57` reviewed tree unchanged, clean scoped
Codex review and all four Windows/Ubuntu Python 3.10/3.13 CI jobs successful.
The diagnostic reproduces local-checkpoint deadline exhaustion but does not
identify the actual failed run's subtype. Its 1,598 passing tests establish
offline mechanics, not successful transport or model quality.

The user requested another attempt. Preserve that intent, but never restart the
consumed v3 run or reuse its unused accounting IDs or authorization. This phase
specifies and prepares the successor offline; it adds no paid entrypoint.

## Unchanged interpretation and new ownership

Use the same eleven development packets in original order and the unchanged
policy-v3 builder, context, strict schema, SYSTEM framing and normalization.
Every complete envelope and native body must be byte-identical to the original
v3 preparation. References and prior predictions remain outside model input.
This is a transport revision, not a new semantic policy or held-out evaluation.

Freeze exclusively in the new ignored directory
`data/missing-link-demand-operation-policy-v3-stream-preparation-2026-10-09/`.
Copy original inputs/references, this protocol, public configuration, eleven
envelopes/native bodies and an exact read-only baseline; retain its manifest
digest independently. Preserve every consumed preparation/run/assessment and
existing module/test. No credentials, account verification, lease acquisition,
reservation or model call belongs to preparation.

Implement separate opt-in reader, executor and run adapter only after this
contract's review/CI/merge. Keep all consumed adapters byte-bound to their old
fingerprints. Later freeze a new owned run at
`data/missing-link-demand-operation-policy-v3-stream-owned-run-2026-10-09/`
on the exact reviewed/merged executable tree, pinning all new dependencies.
Separate human authorization must bind that concrete owned manifest, bodies,
account, allowance, IDs and limits. This prospective manifest is not an executable
freeze or call authorization; neither available funds nor merge authorizes calls.

## Accounting and original evidence

Keep account `Daniele-Cangi`, original database
`data/repotraction-daniele-cangi.sqlite3`, allowance
`missing-link-verification-2026-09-30` and configured total **USD10**.
Current baseline: **578 reservations / USD8.13614**, zero active jobs. The
eleven identical bodies imply **USD0.0548404** conservative reservations;
complete execution would reach **589 / USD8.1909804**. Segment cap is **USD0.10**,
atomic cumulative ceiling **USD8.23614**, per-slot maximum **USD0.02**. These are
software reservation parameters, not verified provider billing or prices.

Use new ordered IDs `demand-operation-policy-v3-stream-owned-2026-10-09-01`
through `-11`; reject any already present. Never charge or resume any old v3 ID.
An exclusive start marker consumes the entire new run even with zero calls.
Each slot permits one attempt, no retry, repair, replacement or later resume.
A global failure leaves remaining slots unattempted. A committed reservation
remains charged even if journal/persistence/transport subsequently fails.
No increase, reset, refund, deletion, moved reservation or new allowance.

The baseline extends the old 1,662 protected artifacts with all **12** failed
v3 native-run files and **13** absence-assessment files: **1,687** protected
artifacts. Verify all three native seals and assessments statically against
independent anchors; do not run earlier historical live-prefix verifiers.
Pin all **53** existing code fingerprints (the old 51 plus the two diagnostic
files), the diagnostic report and this protocol. Preserve exact original
`ml_*` tables, old reservation rows, allowance identities, matches, caches and
source rows. Only the original Store's atomic reservation may extend accounting.

## Stream checks and their explicit detection boundaries

The current reader does full history/DB checks at every nonterminal line.
The successor deliberately changes this cadence. It must not claim identical
per-line DB/history detection or reuse the old transport protocol.

Hold the original-DB and owned-run worker leases throughout. Before every
attempt, force a fresh fixed-account check with full integrity checks on both
sides. Validate all eleven request bodies/settings/IDs before any reservation.
Full checks remain mandatory around every claim, reservation and journal,
checkpoint persistence, usage/call/output persistence, result and final seal.

During streaming, check cancellation, fixed-account identity (successful cache
strictly under three seconds), all pinned executable fingerprints, immutable
slot/request metadata and held lease state before and after each returned read.
These checks use no acquired-code execution or original DB writes. Callback
failures escape globally; do not disguise them as provider transport errors.

Additionally run the complete history/DB/owned-evidence integrity checkpoint
after **128 nonterminal lines** or **30 wall seconds since its last successful
completion**, whichever threshold is observed first. Count blank/comment lines
as well as deltas. Check thresholds on returned reads; do not promise detection
while a blocking read or guard is in progress. Reset counters/time only after
the full checkpoint succeeds. No mtime-only cache, cached table hashes or
assumption that a held lease proves unchanged history is permitted.

Retain a status-consistent complete decoded native terminal privately before
semantic parsing, usage reporting, normalization or acceptance. Then require
a fresh full integrity checkpoint before any such processing. If that check
fails, preserve the terminal as unaccepted evidence and stop. Thus a persistent
DB/history change during streaming is detected before accepting any result;
the interval does not prove detection of a change reverted between full checks.
That limitation must remain explicit in implementation and reports.

## Separate active and wall deadlines

Preserve no redirects, one opener invocation, **55-second socket timeout**,
**512,000-byte line** and **8,000,000-byte cumulative** limits. A separate reader
must not monkeypatch the consumed reader or production Provider.

After opening the response, measure monotonic wall elapsed and completed local
checkpoint durations separately. Active stream elapsed is wall elapsed minus
those measured checkpoint durations; it includes reads and event handling.
Enforce **240 active stream seconds** and separately **600 wall stream seconds**.
The latter prevents arbitrarily expensive checks from making execution unbounded.
Do not restart either clock after progress, gaps or checkpoints. The socket-open
duration is measured separately, outside both stream clocks.

Check both deadlines before and after returned reads and checkpoint callbacks.
Equality at a limit is permitted; exceeding either stops globally. No terminal
arriving after an exceeded deadline may be retained as a complete valid receipt.
As with the existing synchronous adapter, checks run after control returns:
socket/CLI timeouts bound their operations, but a callback is not asynchronously
interrupted at the wall limit. Do not advertise a hard 600-second process timeout.
Do not subtract arbitrary delays or estimates: measure each actual callback,
including failed callbacks, with a monotonic clock. Invalid/backward/nonfinite
clock observations stop globally rather than granting more time.

## Bounded failure and timing evidence

Retain private per-attempt telemetry on success or failure: observed line/byte
counts, light/full checkpoint counts, opening/reading/checkpoint durations,
active/wall elapsed and exceeded deadline kind (`active_stream` or `wall_stream`).
Use primitive typed values with documented finite bounds. Before opening, absent
stream measurements are null, not guessed zero. Record a terminal-retention or
reservation flag only from the corresponding successful storage/commit observation;
uncertain state stays null. No provider usage without its native report.

For a typed provider transport failure, project only an allowlisted code and
phase and a concrete integer HTTP status 100–599 for HTTP errors. Do not trust
arbitrary exception `.diagnostic()` methods or stringify raw exceptions. Existing
`ai_stream_deadline_exceeded` may be distinguished by the typed deadline kind.
Do not translate identity, cancellation, budget, guard or persistence failures
into transport failures: catch HTTP/socket exceptions only around open/read IO.
Telemetry-storage failure is itself global; it must not authorize continuation
or a claimed complete seal. Preserve the original bounded failure category if a
secondary finalization failure prevents sealing; never log upstream messages,
headers, credentials, root excerpts or private control metadata publicly.

## Acceptance controls and next execution gate

Authored offline tests must prove buffered deltas with expensive guards reach
their terminal within the new clocks, slow reads still expire active time,
excessive guards expire wall time, equality boundaries work, failed callbacks
are measured without masking their exception, and blank lines count toward
both size and checkpoint limits. Mutation of code, slots, lease or original
history must stop at its declared boundary before accepting output. Test missing,
malformed/inconsistent, incomplete/failed/refused terminals, HTTP/redirect/timeout,
receipt/telemetry storage failure, cancellation, account changes and no retry.
No real sockets, credentials or original accounting may be used in those tests.

Keep native-before-validation, standalone schema gates and the narrowly caught
post-schema normalizer `ValueError` boundary from the existing v3 contract.
Only a retained local rejection with independent immutable/schema/integrity
rechecks passing can allow the next slot. Seal all native evidence, dispositions,
bounded diagnostics and final exact accounting extension with an independent
digest. Missing receipt/usage/prediction is absence, never an all-unknown card.

Review/CI/merge and the actual exact-tree owned freeze must precede the separately
authorized new one-shot sequence. Assess any new completed cards against original
roots and references before consulting earlier assessments, keeping annotations
separate. No acquired-code execution, production/UI/key-entry work, quality gain,
fresh useful lead or ranking claim follows from a transport correction.
