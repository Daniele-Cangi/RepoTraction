# Policy-v3 stream successor adapters — 2026-10-09

Separate opt-in adapters implement the reviewed [stream successor contract](missing-link-policy-v3-stream-successor-protocol-2026-10-09.md).
PR105 merged as `55f4a6d676fccc4a204322e0080667c2ee154dd7`, with reviewed
`a3adfc1ace7163027eaaddb45f327f83a247a627` tree unchanged, clean scoped Codex
review and all four Windows/Ubuntu Python 3.10/3.13 CI jobs successful.
The original v3 failure subtype remains unknown. This implementation does not
establish a successful new provider attempt or change any consumed evidence.

## Separate code, unchanged interpretation

- `scripts/missing_link_stream_successor_receipts.py` reads one Responses stream
  with separate active/wall clocks and private bounded telemetry.
- `scripts/missing_link_stream_successor_executor.py` verifies every request and
  new accounting ID, supplies distinct stream/full checkpoints and reuses the
  unchanged v3 builder, schema/normalization gates and rejection boundary.
- `scripts/missing_link_stream_successor_run.py` explicitly prepares, verifies
  and runs an owned successor at its exact reviewed/merged tree, with original
  accounting, leases, exclusive markers and closed evidence inventories.

No production module imports these adapters. Imports read no configuration or
credentials and start no network calls or threads. The old Provider, receipt
reader, executors, policy modules, tests and all eleven request bodies remain
unchanged. Rebinding private accounting IDs does not alter model-facing data.

The [27-file source preparation](missing-link-policy-v3-stream-successor-preparation-2026-10-09.md)
remains immutable at manifest
`dd7d0f975d70f2f3fc2a5110a9111b881fea0053f2d493c0ad02f76bee38b1f7`.
Its historical status remains `offline_only_no_stream_successor_executor`;
this later adapter does not rewrite that prospective evidence.

## Stream behavior and detection boundaries

At each returned read, checks before and after it cover cancellation, fixed
account identity with its existing successful cache strictly below three seconds,
all executable fingerprints, immutable slots/public provider settings, anchored
owned metadata, held lease handles/inodes and owned evidence/journal state.
The light path performs no full original-table or historical-artifact snapshot.

After 128 nonterminal lines or 30 observed wall seconds since a successful full
checkpoint, run the full check. Blank/comment lines count. Full checks also guard
claims, atomic reservations/journals, job checkpoint and usage/call/output writes,
results and final sealing. A forced account check precedes every request with
full gates on both sides. These are synchronous returned-control observations,
not promises of cancellation or mutation detection while IO/checks block.

Retain a complete status-consistent decoded terminal privately before parsing
its semantic output or accounting usage. Then require a fresh full checkpoint.
A persistent original-history change stops before any usage/output processing,
while preserving the terminal as unaccepted evidence. Changes reverted between
full checks are not guaranteed to be detected. Full snapshots never rely on
cached table digests, mtimes or a lease alone as proof of unchanged history.

Clock measurements are nonoverlapping: opening is outside stream clocks; reads
and event handling count as active stream time; measured light/full checkpoint
callbacks are excluded from active time and included in wall time. Enforce 240
active and 600 observed wall seconds without resetting either clock. Equality
is allowed. The stream interval includes the fresh full post-terminal check;
later parsing/persistence/normalization is outside these stream timings. Socket
timeout remains 55 seconds, with no redirects/retries and unchanged 512,000-byte
line / 8,000,000-byte cumulative bounds. This is not a hard process timeout.

Invalid/backward/nonfinite clocks stop globally. Failed callback durations are
measured without replacing their original global exception with a clock error.
Only actual open/read HTTP/socket exceptions become transport failures; guard,
identity, cancellation, budget and storage errors cannot be converted by a broad
network exception handler. Wire/schema/native incomplete/failed/refused errors
remain global. Only the unchanged post-schema local normalizer rejection, with
independent immutable/schema/full checks succeeding, permits continuation.

## Private telemetry and failure retention

Each reader attempt retains a separate `diagnostics-NN.json`. It contains typed
line/byte and light/full checkpoint counts, separate opening/read/checkpoint
durations, active/wall elapsed, exceeded deadline kind, observed reservation and
terminal-retention states, clock validity and a fixed failure projection.
Durations are capped at 86,400 seconds, counts at the wire-bound maximum plus
one read; `saturated=true` explicitly identifies capped observations. Missing
pre-open stream metrics remain null. Invalid-clock durations remain null.

Reservation state comes from the caller's observation of the original atomic
commit, not a static error message. Receipt state becomes true only when the
exclusive writer returns successfully; a failing writer leaves it null because
partial persistence is uncertain. A missing terminal on an opened stream is
false; before opening it remains null. Missing native usage is never zero usage.
Opened-stream absence and zero observed counters are initialized immediately
when the opener returns, before its post-open timing sample or context entry.
The reader owns that response at return and closes it if timing or context entry
fails before the response context takes ownership. A failed cleanup cannot
replace the primary global error. Normal response-context exit closes it once.
Invalid-clock durations remain null even when opened-stream absence is known.
Both native `input_tokens` and `output_tokens` must be present as concrete
nonnegative integers before usage, call metadata or semantic output processing.
Missing/null/incomplete usage, booleans, fractional/negative counts and strings
stop globally after native retention and the fresh full check. Explicit integer
zero is valid and retained as reported usage. A closed failed-run receipt can
record the stopped attempt and remaining absence; it cannot report an accepted
prediction or allow continuation/replay.

Error projection accepts only fixed categories, allowlisted transport code/phase
and concrete HTTP status 100–599 for HTTP errors. It ignores arbitrary exception
diagnostic methods, unknown keys and raw messages/bodies/headers/credentials.
Telemetry persistence failure stops globally, preserves the bounded primary
failure and explicitly prevents a complete seal. Finalization failure likewise
retains a bounded primary/secondary record when storage permits, releases leases
and never reports a sealed complete run. Failure evidence can be saved after a
full DB/history check fails; it cannot authorize output acceptance or sealing.

## Owned directory and execution authorization

Only `data/missing-link-demand-operation-policy-v3-stream-owned-run-2026-10-09/`
inside the repository can be prepared, verified or run. Its path is part of both
the owned manifest and exact call-authorization scope. A cloned directory cannot
reuse an identical zero-call manifest/authorization. An exclusive start marker
consumes the named run even with zero calls; each slot has one exclusive attempt
marker. There is no replay, resume, replacement, repair or automatic retry.

Before keys or identity lookup, require the independent owned digest, exact
prepared/code/history inventories, current original prefix, clean frozen main
tree and concrete typed authorization. The actual prepare action is key-free and
requires reviewed/merged main. The actual run holds original-DB and owned leases,
denies active workers, reserves only through the original Store method and
journals the exact committed prefix. Lost journals leave charges retained and
prevent sealing. No original job/match/cache/source or allowance creation occurs.

The future actual owned freeze must protect **1,714 artifacts** (1,687 historical
plus the 27 source-preparation files) and **58 code fingerprints** (53 unchanged
plus the three adapters and two new test files). This stage creates no such
actual freeze or call authorization. Original accounting remains **578 /
USD8.13614 within USD10**, with no active jobs or new reservations/calls.
The planned eleven-slot sum remains USD0.0548404, segment USD0.10 and cumulative
ceiling USD8.23614, using distinct unused stream-successor IDs.

Authored offline controls exercise buffered/slow streams, timing boundaries,
blank lines, wire/native/schema failures, identity/cancellation, callback timing,
tampering, leases, journal loss, concrete scope/body bindings, native-before-
validation, local/global rejection, finalization and replay prevention. They use
temporary original-account fixtures and mocked openers with real sockets forbidden.

Adapter review/CI/merge and an actual exact-tree owned freeze precede the separately
authorized one-shot provider sequence. Existing source/native/assessment anchors
remain unchanged. No semantic quality, billing, causal improvement, fresh useful
lead, ranking or production/UI/key-entry claim follows from offline conformance.
