# Policy-v3 stream diagnostics — 2026-10-09

Authored offline controls reproduce a concrete mechanism: local checkpoint work
can exhaust the frozen receipt reader's 240-second wall-clock stream deadline,
even when all stream lines are immediately available. This **does not identify
the actual cause** of the [consumed v3 stop](missing-link-demand-operation-policy-v3-native-results-2026-10-09.md).
Its sealed summary retains only `ProviderTransportError`, with no subtype, HTTP
status, stream counters or timing breakdown. Neither that run nor its ten
unattempted slots may be resumed or retried.

## Reproducible authored experiment

```console
python scripts/missing_link_stream_checkpoint_diagnostics.py
python -m unittest discover -s tests -p test_missing_link_stream_checkpoint_diagnostics.py -v
```

The standalone harness uses the unchanged `complete_with_receipt` reader and
real `Budget`, a literal loopback-only authored provider configuration, an
in-memory reservation list, a mocked opener and a virtual monotonic clock.
Socket construction is forbidden. No credentials, source roots, original DB,
owned run, CLI identity or provider configuration are read. There are no CLI
arguments for endpoints, keys, inputs or execution. Import performs no IO.
Process-wide mocks make this a standalone diagnostic, not a concurrent worker.

Each simulated checkpoint invokes two guards, matching the v3 executor's
`guard(); identity(); guard()` structure while omitting identity time. Guard
durations are authored parameters, not measurements from the failed run. The
fixture omits other persistence/reservation guards: it isolates the stream
deadline mechanism rather than replaying the full executor. A delta and its
following blank line each cause a checkpoint. The reader checks elapsed time
after reading a line, before interpreting or retaining a terminal event.

| Authored fixture | Virtual time at last read | Result | Terminal retained |
| --- | ---: | --- | --- |
| 61 delta/blank pairs, zero guard/read time | 0 s | Completed and parsed | Yes |
| 60 pairs, 1 s per guard | 240 s | Completed and parsed | Yes |
| 61 pairs, 1 s per guard | 242 s | `ai_stream_deadline_exceeded` after 121 stream checkpoints | No |
| 13 pairs, 5 s per guard | 250 s | `ai_stream_deadline_exceeded` after 25 stream checkpoints | No |
| Terminal-only, 241 s simulated read | 241 s | `ai_stream_deadline_exceeded`, zero stream checkpoints | No |
| EOF without terminal | 0 s | `ai_stream_missing_terminal` | No |
| Malformed JSON event | 0 s | `ai_stream_invalid_event` | No |
| Opener raises timeout | 0 s | `ai_transport_timeout` | No |
| Opener raises HTTP 503 | 0 s | `ai_transport_http_error`, status 503 | No |

Every scenario has one mocked open and one **synthetic in-memory reservation**;
these are not provider attempts or original ledger rows. Failure fixtures retain
no terminal, parsed output or usage record. The timeout/HTTP/malformed/EOF cases
demonstrate why the exception class alone cannot distinguish causes. Even the
deadline code would need a timing breakdown to distinguish slow reads from
local checkpoint work. Cancellation and integrity exceptions still propagate;
the experiment adds no retries or guard bypasses.

## Read-only local component measurements

Before authoring this change, five sequential samples on the local Windows
checkout measured two existing components using `time.perf_counter()`:

1. `frozen(out, anchor)` followed by all eleven `verify_requests` encodings with
   `readiness=False`, using a key-free explicit provider configuration.
2. `snapshot(before)`, `journal(out)` and `verify_prefix` against the exact
   current original ledger and sealed baseline.

The first component checked the 51 frozen code fingerprints and historical
preparation/seal bindings. The second used the existing SQLite `mode=ro`
snapshot and hashed all 1,662 protected artifacts. Both native and assessment
seals were verified independently before the samples; a final exact snapshot
comparison confirmed unchanged original accounting and history.

| Sample | Frozen/encoding component | Snapshot/prefix/journal component | Sum |
| --- | ---: | ---: | ---: |
| 1 | 0.457 s | 4.832 s | 5.288 s |
| 2 | 0.457 s | 4.502 s | 4.960 s |
| 3 | 0.558 s | 4.662 s | 5.220 s |
| 4 | 0.477 s | 4.489 s | 4.966 s |
| 5 | 0.460 s | 4.414 s | 4.874 s |

Median sum: **4.966 seconds per sampled component pair**. These are local
observations, not a portable benchmark or failed-run timings. They exclude
identity, exact execution-tree assertions, lease checks, owned evidence checks,
persistence and stream reads. The sampled descendant checkout could not pass
the consumed run's exact execution-tree gate; no execution gate was invoked,
relaxed or replaced. No full checkpoint was timed. Two full guards per stream
checkpoint would repeat these components, making local overhead a plausible
failure mechanism, but actual delta counts and timings remain unavailable.

## Bounded observability contract for a future successor

The frozen adapters, receipt reader, protocols, bodies, native runs and
assessments remain byte-bound to their independent anchors. This diagnostic
adds no live instrumentation or change to transport behavior.

A separately reviewed successor should retain a bounded transport projection:
allowlisted error code and phase, typed HTTP status only for HTTP errors,
observed committed reservation and terminal-retention state, line/byte counts,
and separate monotonic durations for stream reads and local checkpoints. Raw
exception messages, response bodies, headers, credentials, root excerpts and
private control metadata must stay out of public diagnostics. Missing telemetry
must remain absent rather than becoming zero or a guessed cause. Instrumentation
must not mask cancellation, identity, persistence or integrity failures.

Before choosing any checkpoint optimization, its new protocol must specify
which protections run at each boundary and how changes during streaming are
detected before accepting output. Simply caching/skipping integrity guards or
raising the deadline would weaken or change the reviewed contract. No such
change is implemented here. A new exact tree, unused owned/accounting scope and
separate human call authorization are still required for any future execution.

Original accounting remains **578 / USD8.13614 within USD10**, with no active
jobs, new reservations, provider calls or budget changes during this diagnostic.
No semantic quality, causal model improvement or fresh useful lead is established.
