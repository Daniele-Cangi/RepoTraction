# Checkpoint cadence prototype and integration contract — 2026-10-10

The [consumed stream successor](missing-link-stream-successor-outcome-2026-10-10.md)
spent 594.6 of its 600 observed seconds in local checks. Its light path reread
58 code files and owned bindings twice per checkpoint, with checkpoints before
and after every read. Every 128 nonterminal lines also triggered two complete
guards, including repeated traversal of historical preparation graphs, Git
subprocesses and full original DB/history snapshots. Fast arriving deltas and
blank lines therefore multiplied expensive local IO.

This change implements an **offline checkpoint component**, its fixed workload
benchmark and the contract for a future owned adapter. It does not yet wire a
paid reader/executor, create a source/owned freeze or authorize calls. The old
58 code fingerprints and all consumed records remain unchanged. The exact
original accounting remains 579 / USD8.1408513 within USD10.

## Design

The new single-owner `CheckpointCadence` has three explicit callbacks:

| Layer | Required checks in the future adapter | When |
| --- | --- | --- |
| Fast | Cancellation, held lease path/handle identity, bounded cached account identity, in-memory current-request/config bindings | Before and after each returned read, and around critical audits |
| Critical | Canonical code hashes, owned anchors, evidence inventory/content and reservation journal | At the next poll at least 1 second after successful completion; also every forced barrier |
| History | Original DB consistent snapshot and exact allowed reservation prefix; protected history and Git/tree checks | At the next poll at least 30 seconds after successful completion; also every forced barrier |

A full barrier executes **fast → critical → fast → history → fast → critical →
fast**. It always executes all callbacks regardless of their recent success.
`start()` performs that barrier once. `finish()` performs another fresh barrier
and permanently closes the controller. `barrier()` is available only during the
active lifecycle for mandatory write/acceptance boundaries. Any callback,
clock or lifecycle failure poisons the controller: even if caught by a caller,
subsequent operations rethrow the same failure without invoking checks again.
Reentrant operations fail globally, including when a callback catches that error.

The schedule depends on elapsed monotonic time, not line count. A due history
audit takes precedence and cannot be postponed by frequent critical checks.
Intervals begin at successful callback completion; this avoids a slow audit
immediately scheduling itself forever. Invalid/backward clocks fail globally.
Telemetry contains only fixed state/count/duration fields and explicit saturation;
invalid clock durations remain absent. Diagnostic snapshots do not read the clock.

`PinnedFiles` compiles independently trusted file pins into a fixed inventory.
It reads each distinct path once in an audit, verifying both raw and canonical-LF
hashes from those same bytes if required. At most eight file reads are submitted
at once; completed tasks replenish that bounded window. On failure, pending
reads are cancelled and running readers are joined before the audit raises.
Each reader hashes 64-KiB chunks, including incremental UTF-8 decoding and CRLF
normalization across chunk boundaries. File-content buffers are bounded by the
eight readers rather than the combined size of eight complete files. No threads
start on import or between audits. It deliberately has **no metadata-based
content cache**: same-size, restored-mtime edits still fail the next audit. It
checks content, not manifest trust, inventory completeness, leases or DB state.
Those obligations remain with explicit adapter callbacks.

## Changed detection boundary

This is a new contract, not an equivalent optimization of the consumed one.
Code/owned-file mutations that persist until the next critical check are detected
on the next poll due after 1 second; DB/history mutations on the next history
check due after 30 seconds. A blocking read or callback delays the next poll;
these are cooperative returned-control bounds, not hard real-time guarantees.
A transient mutation entirely between audits can escape detection. No promise
of atomic filesystem snapshots or protection against arbitrary host-process
compromise is made. The existing worker leases continue to exclude cooperating
workers; they do not make every historical file immutable.

Immediate guards still run for every read, including blank/comment lines. Full
fresh audits are mandatory at acceptance boundaries even if periodic audits are
fresh. Changes during a long history audit are followed by fast and critical
checks before the barrier succeeds. Filesystem metadata is never evidence that
content is unchanged. There are no watcher threads or background provider readers.
Bounded file-audit workers cannot outlive the callback that owns them or continue
a paid request after a foreground failure.

## Required adapter integration before any new paid attempt

1. Validate all predecessor manifests/seals and their relationships once against
   independent anchors, then compile immutable code/history pin inventories.
   Include the previous 1,714 protected files plus the consumed stream run and
   assessment (26 additional files), along with any new preparation files. Each
   periodic audit must hash every required protected path, but must not recursively
   reconstruct the same preparation graph or hash the same path repeatedly.
2. Use separate immediate, critical and history callbacks. Keep original account
   identity checks forced before a request and cached for at most the existing
   three seconds during reads. Do not compare or re-encode all eleven large
   packet bodies on each line: bind the immutable active request before opening,
   and check its required live configuration in the immediate guard.
3. Integrate scheduling in a separately named reader/executor. Reusing the old
   reader unchanged with cheap placeholder gates is forbidden: it would silently
   change the meaning of its 128-line checks and miss explicit barrier boundaries.
   Keep the existing SSE/shape/normalizer semantics, native-before-validation
   ordering and global-versus-local failure partition. Preserve response ownership,
   primary exceptions, usage-missing semantics and bounded diagnostics.
4. Force full barriers around claims, atomic reservations/journals, checkpoints,
   terminal retention, usage/call/output writes and final sealing. A retained
   terminal alone cannot grant acceptance. A failed barrier prevents usage/output
   acceptance and further slots. Every failure consumes the owned scope.
5. Keep observed active/wall limits at 240/600 seconds, socket timeout at 55,
   512,000-byte line and 8,000,000-byte total bounds. Meter each actual callback
   once, including forced barriers; do not charge audits as active stream time.
   No audit optimization grants a retry, timeout increase or extra allowance.
6. Before authorization, run the exact new adapter offline with an injected
   authored stream, actual read-only original DB/history checks and no credentials,
   CLI authentication, reservations or network. Reject readiness if the full
   integration exceeds its declared performance budget or fails fault injection.
   Freeze only the reviewed/merged tree in a distinct unused owned directory,
   with original allowance and exact-scope human authorization before real calls.

## Verification and reproducible measurements

```console
python -m unittest discover -s tests -p "test_missing_link_checkpoint*.py" -v
python scripts/missing_link_checkpoint_benchmark.py
python scripts/missing_link_checkpoint_benchmark.py --filesystem
```

The tests exercise 10,000 buffered line boundaries, exact periodic deadlines,
slow/blocked reads, unstarvable history checks, forced terminal audits inside a
fresh interval, code/history mutation, same-size/restored-mtime edits, deletion,
replacement, cancellation/lease failures, fail-stop reuse, reentrancy and clocks.
Parallel-audit controls verify the eight-read bound, one read per distinct path
and joining every running read before a failure returns. Chunked-hash controls
cover split UTF-8/CRLF, trailing CR, invalid UTF-8 and mid-file read failure/close.
A virtual-time control with 12,000 reads / 240 seconds of authored read time,
46 ms critical checks and 15.85 s history audits remains below 600 seconds. It is
a schedule control, not a prediction about the provider or real adapter.

The optional filesystem benchmark creates 58 synthetic 16-KiB code files,
1,740 synthetic 32-KiB historical files, a 579-row temporary SQLite ledger and
an actual temporary worker lease. It hashes all content, enumerates inventories,
compares ledger rows in read-only transactions and checks handle/path identity.
It drains 10,000 and 60,000 buffered comment lines (under the 8-MB wire bound),
calling the controller before and after every read and forcing both barriers.
No provider response parsing, original DB, acquired source, Git subprocess or
real identity lookup belongs to this component measurement.

The fixed local component gates are: maximum of three critical samples ≤100 ms,
history samples ≤5 s, total including barriers ≤30 s for 10,000 lines and ≤120 s
for 60,000. The CLI exits nonzero if any gate fails. Timing gates are not unit-test
assertions across arbitrary CI hardware. Passing this component benchmark is
explicitly **insufficient for live-run readiness**; step 6 remains mandatory.

Local measurements on Windows / Python 3.13, 2026-10-10:

| Component / filesystem | Critical samples (s) | History samples (s) | 10,000 lines (s) | 60,000 lines (s) |
| --- | --- | --- | ---: | ---: |
| Synthetic, sequential hashing, D: | .685 / .013 / .013 | 28.333 / 1.448 / .877 | 2.482 | 11.631 |
| Synthetic, bounded 8-reader hashing, D: | .189 / .017 / .016 | 6.251 / .607 / .540 | 6.043 | 17.752 |
| Actual pinned content + original DB, read-only C: | .220 / .018 / .017 | 13.778 / 6.130 / 5.945 | 16.346 | Not run |
| Final 8-reader / 64-KiB chunks, synthetic C: | .303 / .101 / .081 | 6.716 / 1.486 / 1.261 | 6.153 | 29.685 |

The first three rows preceded the final bounded-buffer implementation and remain
historical component observations. All three synthetic benchmark runs **failed the strict
calibration gate**, despite completing the long streams inside their time
budgets. Eight readers reduced the first scan's observed cost but did not make
every workload faster. These are individual observations, not a controlled
speedup estimate or a percentile distribution; no OS caches were flushed.

The original C: volume had approximately 13 MB free and could not hold the
synthetic fixture. Its failed creation cleaned up its own temporary directory;
the next workload measurements used temporary files on D:. C: later reported
approximately 4 GB free, allowing the final bounded-buffer measurement there.
No original artifact was removed or relocated by this work. The low-space
observation is not established as the cause of the earlier native timeout.

The additional private read-only C: measurement bound all 58 code fingerprints
and the consumed owned evidence, hashed all 1,740 protected files and compared
every original `ml_*` table against the independently sealed final snapshot.
All hashes and table contents matched before/after; reservations remain 579 /
USD8.1408513. Its stream's immediate callback was empty: lease, Git and live
identity costs are excluded. It is therefore also **not** full-adapter readiness.
The 16.346 seconds include 16.099 seconds in two history audits, which identifies
the full DB/history callback as the remaining component to profile during
integration. These measurements establish that audits need not scale with every
delta; they do not establish that the provider would complete or that every
performance gate passes. No threshold was relaxed after observing a failure.
