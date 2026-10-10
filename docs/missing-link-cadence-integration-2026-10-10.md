# Owned checkpoint cadence integration

## Scope and predecessor

PR107 merged as `65a066b35385b912491bb10e791b4807f710c725`, with the
`d997c25a4dc22bd277b9c3308478889fcdf4e7a6` reviewed tree unchanged, a clean
final scoped Codex review and successful CI run 38048311079. Its component
contract remains unchanged. This stage connects that controller to a separate
reader, executor, owned evidence writer and original-history audit.

All consumed code and evidence remain immutable. No production, UI, parser,
provider prompt, output schema, normalizer, timeout or budget setting changes.
The native stream scope already consumed its approval and cannot resume.
Original accounting remains 579 reservations / USD8.1408513 within USD10;
these are software reservations, not verified billed spending.

## Concrete adapter behavior

`missing_link_cadence_reader.py` uses the original response-ownership and
transport-error helpers, with a separately named loop. It polls the new engine
before and after every returned read, and uses real full barriers around native
terminal retention. There is no 128-line historical check and no placeholder
gate passed to the consumed reader. The wire limits remain 512,000 bytes per
line, 8,000,000 bytes total, socket timeout 55 seconds, 240 active stream seconds
and 600 observed wall stream seconds. There is one open and no retry.

`missing_link_cadence_checks.py` meters each actual fast, critical and historical
callback once, including callbacks invoked in forced barriers. Callback time
counts against wall time and is excluded from active time. Controller overhead,
parsing and receipt writing remain active time. Stream timing begins after
response entry and ends at the checked post-terminal barrier sample; later
usage/validation/sealing barriers are outside that stream interval but inside
the complete owned-workload measurement. Failed clocks invalidate seconds;
telemetry preserves fixed categories, null observations and bounded counters.

`missing_link_cadence_executor.py` reproduces all eleven ordered bodies before
any claim, then binds private immutable bytes for every slot and body. Callbacks
receive copies. Fast checks compare the small public provider configuration and
credential binding, check cancellation and held leases, and invoke the existing
three-second successful-identity cache. Account identity is forced again just
before opening. Request bodies are not rebuilt or all compared on every line.
Future accounting IDs use the distinct `demand-operation-policy-v3-cadence-owned-2026-10-10-`
prefix. The prospective manifest is an in-memory binding, not an owned freeze.

Full barriers surround claims, atomic reservation/journal transitions, job
checkpoints, native terminal writes, usage/call/output mutation, result writes,
summary/final-snapshot retention and sealing. The original Budget and atomic
ReservationBinding implementations remain in use. Missing usage is global,
not zero. Native/schema/transport/identity/lease/storage/integrity failures stop
the cohort. Only the existing post-schema normalizer's explicit local refusal
can advance to the next slot. Failed scopes are consumed and cannot replay.
Failure diagnostics cannot grant acceptance or a success seal.

## Compiled audits and trust boundary

`missing_link_cadence_history.py` verifies predecessor preparation relationships
once, then binds independent consumed native and assessment anchors. The old
1,714-file baseline extends to the sealed native 13 and assessment 13 files:
1,740 protected files. All 58 consumed fingerprints and the new adapter files
are pinned. The explicit sealed/prepared inventories remain checked at each
historical audit. Other historical entries keep their original file-pin scope.

Subsequent audits perform content hashing with the merged bounded reader,
inventory enumeration, Git/tree checks and a consistent read-only SQLite
transaction, followed by the unchanged exact-prefix comparison. They do not
recursively rebuild the preparation graph. Table hashes stream rows using
exactly the frozen `json.dumps(fetchall())` encoding, including separators and
Unicode; all tables, reservation rows, allowances and active jobs remain checked.
No mtime or stat cache replaces content checks. This remains the documented
1-second critical / 30-second historical detection window from callback
completion, subject to returned control, with unconditional acceptance barriers.

## Offline ownership and performance gate

`missing_link_cadence_owned.py` exposes only an offline owned rehearsal. It
exclusively creates a scratch directory and a new synthetic ledger there, holds
actual temporary leases, reserves against that ledger atomically, retains native
and interpreted evidence separately, and seals after final prefix checks. It
cannot be given an original database path. The original-history callback is
read-only. There is no paid prepare/run CLI or authorization constructor.

The full eleven-slot authored fixture verifies cohort behavior. For performance,
`missing_link_cadence_benchmark.py` runs the first slot of the exact owned adapter
with 10,000 and 60,000 authored nonterminal lines plus a valid authored terminal.
All eleven original request bindings are reproduced; slots 2–11 are explicitly
unattempted in each probe. Scratch usage and charges are authored, not native
provider observations. The original DB/history is audited throughout, while
identity uses an authored file and the real three-second cache. No CLI account
authentication, real credentials, network or original reservation is performed.

The measurement includes real code/history hashes, Git, inventories, temporary
leases, cancellation path checks, request binding, temporary atomic accounting,
native parsing, normalization, all persistence and final sealing. It reports
stream time separately from whole owned time, and breaks historical time into
Git, inventory, file and original-DB work. It does not estimate live identity or
provider latency and cannot establish model adherence or a useful lead.

Fixed gates, declared before this adapter's measurement: first three actual
critical samples each <=100 ms; first three full history samples each <=5 s;
complete first-slot owned probe <=30 s for 10,000 lines and <=120 s for 60,000.
The CLI exits nonzero if any fail. These are local performance gates, not CI
timing assertions. Neither a component pass nor an offline integration pass
authorizes a paid run.

```console
python -m unittest discover -s tests -p "test_missing_link_cadence_integration.py" -v
python scripts/missing_link_cadence_benchmark.py
```

Private actual-history measurements require the local immutable data and a clean
committed checkout. The benchmark only executes first-party authored control
code; acquired repository text is inert input. A separately reviewed paid
ownership binding, measured readiness, an unused owned freeze on the exact merged
tree, and concrete human call authorization remain prerequisites for any future
real attempt. No old preparation, approval, writer or native run is replayed.

## Validation and observed measurements

Authored regressions cover buffered streams, exact active/wall accounting,
unconditional terminal barriers, missing usage, SSE/size failures, cleanup and
primary exceptions, clock failures, immutable request binding, concrete config
types, whole-cohort/local-refusal behavior, atomic reservation failures, content
mutation with restored timestamps, foreign ledger changes, identity and lease
loss, inventory changes, finalization failure and replay rejection.

Actual read-only measurement results will be retained after the committed adapter
is measured. No execution-readiness claim is made by the implementation alone.
