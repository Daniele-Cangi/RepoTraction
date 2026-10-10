# Fresh file and Git audit scheduling

## Reviewed predecessor and scope

PR109 merged as `fb06bbd3b2a97c208aac723beca7a7d098963025`. Its tree matches
reviewed `15653174ccd5c7b97ba225fbf0ea8ada270a5bbb`, including the final SQLite
path identity check after connection cleanup. The final scoped Codex review
found no major issues; all four CI jobs passed in run 38057767044.

The retained pre-review measurement on `548929c` took 65.932/84.557 seconds
for the complete authored 10k/60k first-slot workloads. The 10k gate still failed.
Its 43 historical audits spent 15.935 seconds hashing files and 16.534 seconds
in Git checks. This stage reduces scheduler and subprocess overhead while
preserving the existing observations, barriers and detection intervals.

## File reads and failure ownership

`PinnedFiles` still groups duplicate paths and computes every required raw and
canonical-LF SHA-256 digest from one new bounded-chunk read per distinct file.
Every invocation reads the complete immutable pin inventory again. The encoding,
digest comparisons, 64 KiB chunk bound and maximum eight simultaneous readers
are unchanged.

An audit now submits at most eight fixed batches, distributed across the pin
inventory. Each worker processes its batch one file at a time. This removes
one future submission/result exchange per file in the 1,740-file workload.
There is no persistent pool, cached file body or metadata-based read shortcut.

A worker sets a shared stop event before propagating any failure. Other workers
finish their current reads, stop before opening subsequent files, and all join
before the audit can return or raise. Pending batches are cancelled on failure.
The outer cadence controller retains its original global failure latch; no
failed read or partial batch can yield acceptance.

## Git observations

The benchmark's immutable `GitTreeAudit` resolves `HEAD` and `HEAD^{tree}` in one
fresh Git process and compares exactly two result lines with the bound commit
and tree. A separate fresh `status --porcelain` must be empty. Both observations
are repeated before and after each historical audit, in their existing order.
This reduces three subprocesses per Git gate to two while retaining explicit
commit, tree and clean-worktree checks. Command failures and malformed outputs
remain failures. No Git output is cached.

The new Git helper and its tests, plus the changed file-scheduler tests, are
included in the adapter's code pins. All 58 consumed code fingerprints and
1,740 historical file pins remain independently anchored and immutable.

## Calibration and acceptance

Read-only calibration on merged `fb06bbd` compared the old scheduler with an
authored batch prototype over the same protected files. Three observations were
0.355–0.370 seconds for the old scheduler, 0.186–0.201 for eight batches and
0.402–0.432 for serial reads. The Git gate observed 0.179–0.204 seconds with
three commands and 0.121–0.146 with two. These are feasibility observations,
not end-to-end measurements of the committed implementation or speedup estimates.

Focused controls cover every file in uneven batches, late-round failures,
bounded readers, worker joins, complete raw/canonical digests, restored-metadata
mutations, fresh Git checks, changed head/tree/status, malformed output, command
errors and immutable Git bindings. Integration, the full suite, startup and
independent original-history verification are required before publication.

The unchanged owned benchmark must measure a clean committed implementation.
It retains the first-three critical <=100 ms, first-three history <=5 seconds
and whole-first-slot 10k <=30 / 60k <=120 seconds gates. Each full barrier still
performs fresh file/inventory/Git checks, a new complete SQLite transaction-image
hash, exact ledger-prefix verification and the final critical checks. The
resource fallback and post-cleanup SQLite path check remain in force.

There is no barrier coalescing, changed timeout, provider call, original
reservation or new paid freeze. Measurements are tied to their exact commit.
Performance results alone grant no live execution authorization or model-quality
claim; a separately owned reviewed/merged freeze and concrete approval remain
necessary for any new paid attempt.

## Retained owned measurement

The clean implementation `72c07b5ab3612d8c25f9d61bbb242bc0e1f3cfb9` (tree
`b8a11205ccac1895c4fb877bfc627529c3c3be94`) was measured on Windows / Python 3.13
against the actual original read-only history and authored identity/transport.
Compilation took 5.483 seconds, including initial complete logical validation,
outside the same owned gates as before.

| Authored lines | Stream wall | Whole owned | First 3 critical max | First 3 history max | Gate |
| ---: | ---: | ---: | ---: | ---: | --- |
| 10,000 | 6.541 s | 52.338 s | .034 s | 1.078 s | **Fail:** whole >30 s |
| 60,000 | 27.727 s | 73.931 s | .036 s | 1.120 s | **Pass:** all three fixed gates |

Both probes complete with a native authored terminal and result, one attempted
slot and ten explicit unattempted slots. Each retains 43 full history audits,
43 new complete database-image reads/hits and zero repeated logical scans in
the owned phase. Initial logical validation is in compilation above.

In the first probe, historical file reads take 8.276 seconds and Git takes
10.917 seconds, compared with the earlier observations of 15.935 and 16.534.
DB auditing takes 25.714 seconds and remains the largest component. The
complete historical callback totals 46.131 seconds. Counts, barriers and
original accounting remain unchanged. These are separate observations, not
controlled percentile or cache-flushed speedup estimates.

The benchmark exits 1 because the fixed 10k gate still fails. Overall
performance readiness and paid readiness remain false. No subsequent
documentation-only commit is retrospectively treated as the measured head.

Validation on this implementation passes 57 focused cadence/file/Git/DB tests
(56 passes and one existing POSIX-only skip), all 28 integration controls in
62.219 seconds and the complete 1,741-test suite in 654.940 seconds (one
POSIX-only skip on Windows / Python 3.13). Startup `--help` passes. Independent
final read-only verification after the full suite confirms all 58 consumed code
fingerprints, 1,740 historical files and original table hashes unchanged:
579 reservations / USD8.1408513 within USD10, zero added original reservations
and zero provider calls. Fresh CI and scoped Codex review must cover the final
published head, whose changes after measurement are documentation only.
