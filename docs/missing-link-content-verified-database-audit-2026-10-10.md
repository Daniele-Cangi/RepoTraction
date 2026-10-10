# Content-verified original database audits

## Predecessor and scope

PR108 merged as `3db6002201dd18ea44fdecc7a5487c266bd4b7ad`, with the reviewed
`77d1523ab6dd6af43ea164dfc906ada6b10f2625` tree unchanged, a clean final Codex
review and four successful CI jobs in run 38053670199. The offline owned adapter
retains its provisional seal, mandatory write/acceptance barriers, detection
intervals, accounting and failure boundaries.

The previous owned measurements failed the fixed gates: 10k/60k authored streams
took 249.761/224.065 seconds for the complete first slot. The first probe spent
195.252 seconds in 43 original database audits. Large historical JSON payloads
were repeatedly decoded into SQL rows and re-encoded for the same table hashes.
This change targets that work. No consumed reader, code pin, evidence, prompt,
schema, normalizer, production path, timeout or budget setting changes.

## Exact content reuse

`missing_link_database_audit.py` owns the same row-by-row logical snapshot
encoding previously used by the cadence adapter. Each table digest is byte-exact
with the frozen `json.dumps(fetchall())` representation. Reservation rows,
allowances, active jobs, table inventory and missing aggregates remain included.
Ordinary `database_snapshot` still performs the full logical scan.

Only the compiled original-history audit uses `ContentVerifiedSnapshot`:

1. Open a new `mode=ro` SQLite connection, begin a transaction, and finish a
   schema SELECT to establish the current read snapshot.
2. On supported runtimes, obtain that connection's complete SQLite serialization
   and hash every returned byte with SHA-256. This includes WAL-backed pages;
   the main file alone is not a cache key.
3. The first image or any changed image gets the entire logical scan in the same
   transaction. Only a byte-identical image can reuse the previously computed
   logical result. Path identity and connection cleanup must also succeed.
4. Return a fresh copy. The caller still performs its independently anchored
   exact-prefix comparison, alongside real file hashes, inventories and Git
   checks on every full barrier. No barrier is removed or coalesced.

The cache holds one image digest and private immutable logical JSON, bound to one
database and allowance. It retains no image or open connection between audits,
and creates no persistent cache. Errors latch the first failure; caught nested
or overlapping audits cannot let the outer audit accept a result. No failed
refresh can return an older cached result or silently select a weaker fallback.
Metadata is used for path safety only, never to skip content reads.

The mechanism uses SQLite's own connection image rather than opening/closing raw
database file descriptors. SQLite documents that POSIX closes on another raw
descriptor can release its locks. Its serialization API returns the database
image from the supplied connection; a WAL read transaction retains its snapshot
even while another writer commits. See [SQLite serialization](https://www.sqlite.org/c3ref/serialize.html),
[WAL concurrency](https://www.sqlite.org/wal.html#concurrency), and
[POSIX descriptor hazards](https://www.sqlite.org/howtocorrupt.html#posix_advisory_locks_canceled_by_a_separate_thread_doing_close_).

## Runtime and resource boundary

Python 3.10, or a SQLite build without `Connection.serialize`, retains a complete
logical scan on every audit. Images larger than the fixed 512 MiB bound also
select that complete scan. This is a compatibility/resource fallback, with no
performance claim. Serialization/read/corruption/memory failures are global.

On supported runtimes the image is transient and bounded by 512 MiB. The SQLite
buffer and returned Python bytes can coexist during copying, so peak image
memory can approach twice that bound, plus normal interpreter/page/row overhead.
The actual original database image is 251,498,496 bytes. No original journal mode,
checkpoint, ledger, allowance or database file is modified by the audit.

SQLite coordinates normal writers, while each new transaction observes a fresh
snapshot. Host compromise, broken filesystems/locks and transient mutate/restore
between observation points remain outside the predecessor contract. A changed
physical image whose logical contents still satisfy the original contract may
pass only after a full logical scan; image identity is not a new baseline.

## Validation and measurement

Authored controls cover canonical digests, detached cache results, real content
changes with restored metadata, foreign accounting, table/active-job changes,
physical-only changes, unsupported runtimes and image size bounds, read-only
enforcement, missing-versus-zero aggregates, serialization/refresh failures,
reentrancy, path replacement, and WAL commits before/during audits. The
integration and complete suite must also pass before this stage is published.

The unchanged owned benchmark declares the same gates: first three critical
samples <=100 ms, first three history samples <=5 seconds, whole first-slot
10k probe <=30 seconds and 60k probe <=120 seconds. It now reports image reads,
logical scans and cache hits per probe, plus compilation time separately.
Compilation performs the first full logical audit before either owned probe;
that time was already outside the predecessor's owned gates and is now explicit.
An unchanged-history probe therefore starts with a validated warm image.

Measurements require a clean committed implementation, the original read-only
history, actual temporary leases/reservations and explicit authored identity and
transport. Retained metrics must name their exact measured commit; later changes
are not retrospectively certified. No component result or gate pass authorizes
provider calls, a new paid freeze, or a model-quality claim.
