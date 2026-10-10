# Protected operation boundaries

## Reviewed predecessor and declared change

PR110 merged as `016d762782057e73434945055220865b8f2c3d4e`, with the
reviewed `d24342071660d0c4233a2b581b9a82acdd2f5514` tree unchanged. The final
scoped Codex review found no major issues and all four CI jobs passed in
38060527415. Its complete authored 10k/60k first-slot workloads took
52.338/73.931 seconds. The 10k gate still failed; each probe performed 43
complete original-history audits.

This stage declares a separate offline contract before measuring it. It assigns
full historical barriers to explicit operations instead of repeating them around
both an outer accounting method and its nested persistence callback. It changes
the historical detection boundary for internal provisional writes. It does not
claim the legacy per-callback guarantee. The default legacy executor and benchmark
retain their previous behavior.

The pure successor manifest has transport revision `checkpoint_operations_1`,
concrete integer `protected_operation_revision=1` and unused accounting IDs
`demand-operation-policy-v3-operation-owned-2026-10-10-01` through `11`.
The original eleven native request bodies, policy/schema, configuration, budget,
wire limits and 240/600-second deadlines remain bound by the existing verifier.
The new executor requires an explicit authored opener; there is no paid CLI,
retained live freeze or call authorization in this stage.

## Operation and acceptance ownership

`ProtectedOperations` owns fixed, single-thread operation bodies and exact ordered
commit steps:

| Operation | Required provisional writes |
| --- | --- |
| claim | attempt/request callback |
| reserve | atomic reservation and persisted job checkpoint |
| account | usage, call trace and output job checkpoints |
| validate | normalized result or explicit local refusal |
| telemetry | successful diagnostics |
| finish | cohort summary/final-integrity callback |

Every operation forces a complete barrier before entry and after its body,
regardless of audit age. Each inner commit forces immediate identity/configuration,
cancellation, code/content, held-lease, owned-evidence and fresh exact scratch-ledger
prefix checks before and after the callback. Polling still performs critical
checks at one second and complete historical checks at thirty seconds; overdue
history is checked inside the body before another commit. Ordinary explicit
barriers remain unconditional. The reservation binding also checks its fresh owned
prefix around the actual atomic commit and journal update.

Usage, trace, output and result files written within an operation are provisional.
An original-history mutation between internal writes can be detected at the
operation's final full barrier after later provisional files have been written.
No parsed value or accepted operation result returns across that boundary unless
the full audit succeeds. A failure consumes the owned scope, retains its charge,
blocks the next slot/transport and prevents publication of the success seal.
There is no rollback, retry or reinterpretation of a missing native usage report.
The existing stage-then-audit-then-promote final seal remains the last success write.

Cross-thread access, nested operations/commits, wrong/missing/extra ordered steps,
callback/storage failures and caught reentrant failures latch the first global
failure. A local normalization refusal remains local only when all enclosing
guards and the final full operation audit pass. Failure diagnostics cannot clear
the latch or grant acceptance. Response cleanup finishes before accounting entry;
native terminal receipt barriers remain complete on both sides.

## Validation and unchanged gates

Controls cover every operation boundary, immutable request/configuration binding,
due history inside an operation, concrete revision/unused IDs, prefix mutations
between accounting writes, response cleanup, local-refusal/global-failure ordering,
storage failures, reentrancy, response ownership, receipt publication and cohort
stop/no-replay. The same 28 integration controls also run against the legacy path.

The explicit benchmark switch is `--operation-units`. It measures the complete
owned first-slot workload against the actual read-only original history and an
authored identity/transport at a clean committed head. Compilation, including the
initial full logical database scan, remains separately reported. The first three
critical callbacks must each stay within 100 ms, the first three history callbacks
within five seconds, and whole 10k/60k probes within 30/120 seconds respectively.
No gate is relaxed. Passing authored gates would establish only offline timing;
review, merged exact-code ownership/freeze and concrete human authorization remain
separate before any new paid attempt.

All 58 consumed code fingerprints, 1,740 historical files, original database table
hashes and the consumed native/assessment scopes remain immutable. The original
579 reservations / USD8.1408513 within USD10 are preserved. Tests and the benchmark
create only temporary authored ledgers; they make zero provider calls and add zero
original reservations.

## Committed offline measurement

Implementation `b2ce8e048e089378462c135730282529ad9ef8a1` (tree
`c2459fc7c9da6b0789a0bd9d2bfd5fc7453110ab`) was measured on Windows / Python 3.13
against the actual original read-only history with authored identity/transport.
Compilation took 7.597 seconds, including initial complete logical validation,
outside the unchanged owned gates.

| Authored lines | Stream wall | Whole owned | First 3 critical max | First 3 history max | Full history audits | Gate |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 10,000 | 6.801 s | 30.545 s | .039 s | 1.254 s | 21 | **Fail:** whole >30 s |
| 60,000 | 34.895 s | 61.646 s | .042 s | 1.221 s | 22 | **Pass:** all fixed gates |

Both probes complete with a native authored terminal and result, one attempted
slot, ten explicit unattempted slots and a final audited seal. The 60k stream
exceeds the thirty-second interval and performs an additional full historical
audit during the stream. There is no fixed audit-count cap or suppression of
overdue work. Every full audit reads and hashes a new complete database image;
the owned probes reuse exact logical snapshots with zero repeated logical scans.

In the 10k probe, complete history callbacks total 24.076 seconds, including
13.110 seconds in original database auditing, 5.896 in Git and 4.430 hashing
historical files. Critical callbacks total 1.675 seconds across 72 invocations,
including the fresh owned-prefix checks. The earlier PR110 10k observation was
52.338 seconds with 43 full audits. These are individual retained observations,
not controlled percentile or cache-flushed speedup estimates.

That benchmark exits 1 because 30.545 exceeds the fixed thirty-second whole-owned
gate. At that measured revision, performance and paid readiness remain false. No retry
or threshold adjustment is used to turn this observation into acceptance. A
subsequent documentation-only commit is not retrospectively the measured head.

Validation passes 131 focused controls (130 passes and one existing POSIX-only
skip), including 63 legacy/new integration tests in 149.044 seconds. The complete
1,787-test suite passes in 845.590 seconds with the same single Windows skip.
Startup `--help` passes. Initial publication `375dae2` changed documentation only
after measurement; its scripts/tests were byte-identical to that measured code.

Independent final read-only verification after the full suite confirms all 58
consumed code fingerprints, 1,740 historical files and original table hashes
unchanged: 579 reservations / USD8.1408513, zero added original reservations and
zero provider calls. The task-owned temporary root is removed only after checking
its exact resolved path and empty inventory, without recursive deletion. Fresh CI
and scoped Codex review must cover the final published head and this explicitly
changed historical detection boundary before merge.

## Scoped review corrections

Codex reviewed `375dae2` and reported two P2 findings. Foreign `poll`, `barrier`,
`start`, `finish` and `write` already reach the overridden `_perform` through
dynamic dispatch; explicit regressions confirm that they reject before any audit.
The inherited `stream` context and `abort` did bypass ownership. They now verify
the thread before timer attachment/detachment and failure installation, including
exceptional context exit. A private lock serializes first-failure installation.
Owner cleanup still detaches its timer after a failure; a caught foreign attempt
poisons subsequent owner operations and cannot replace the first exception.

Historical/critical failures at telemetry operation entry/exit now escape as the
original latched exception. Conversion to `TelemetryPersistenceError` is confined
to actual storage callbacks; an actual failed diagnostic write retains the prior
bounded transport projection. Diagnostic projection failures and failed diagnostic
guards preserve the global primary rather than claiming a storage failure.
The legacy reader's exception behavior is preserved.

Regressions reproduced three ownership failures and both telemetry audit failures
on `375dae2` before the corrections. They also cover genuine telemetry storage
failure, failed-transport diagnostic storage, context cleanup and diagnostic
projection failure. The retained benchmark and full-suite timings above precede
these code corrections and are not attributed to the corrected revision. The
original four CI jobs passed on `375dae2`; fresh CI/review cover the fix.

Review-fix validation passes 18 ownership unit controls, 29 cadence controls and
40 successor / 28 legacy integration controls (115 distinct tests). The main
114-test run passes in 204.806 seconds; the final exceptional foreign-exit
regression and all 18 ownership controls pass separately. Startup passes.
Independent final read-only verification again confirms all 58 consumed code
fingerprints, 1,740 historical files and original tables unchanged, with zero
added original reservations or provider calls. The empty resolved task temporary
root is removed without recursive deletion. The complete suite runs in fresh CI
on the corrected head; the local full-suite timings above remain pre-fix evidence.

### Owner cleanup after a rejected foreign exit

The next scoped review of `e753ce9` found that checking ownership inside a
generator context's `finally` exhausts the generator on a rejected foreign exit.
Two regressions reproduced the subsequent owner exit doing nothing and leaving
the timer attached, for both normal and exceptional foreign exits.

The stream now uses an explicit context with new/active/closed states. Exit checks
ownership before changing context state or the timer, so the rejected foreign
exit leaves the context available for owner cleanup. The owner detaches its timer
even with a latched failure, then raises the identical primary exception. An
unentered context cannot detach another active context's timer, and rejected
reentry also leaves owner cleanup available. These are lifecycle corrections;
the operation audit boundaries and legacy context remain unchanged.

All four CI jobs passed on `e753ce9` before this follow-up fix. All 117 focused
controls pass in 145.916 seconds: 20 ownership, 29 cadence and 40 successor / 28
legacy integration controls. Startup and independent read-only verification pass,
with all consumed fingerprints, historical files and original tables unchanged,
zero new original reservations and zero provider calls. Fresh scoped CI/review
cover the new published head. The earlier benchmark and local full-suite timings
remain evidence only for their declared pre-correction revisions.

### Rollback when stream entry fails after attachment

The scoped review of `2fb37f4` found a foreign failure can be latched after the
entry callback attaches the timer but before `_perform` checks its result. Entry
then raises, and Python does not invoke context exit. A deterministic regression
inserts a real foreign-thread abort at that boundary and reproduced the attached
timer without entering the context body.

Entry now takes responsibility for rollback before its first attachment mutation.
If that entry fails, it closes its context and detaches the timer, then rethrows
the identical primary exception. A failure before this attempt starts attachment,
including overlapping entry or reentry, leaves the already active context's timer
and owner cleanup intact. Existing normal/exceptional foreign-exit and owner
cleanup controls remain in place. All four CI jobs passed on `2fb37f4` before this
follow-up; the new correction requires fresh validation, CI and scoped review.

All 119 focused controls pass in 188.687 seconds: 22 ownership, 29 cadence,
40 successor and 28 legacy integration controls. Startup and whitespace checks
pass. Independent final read-only verification again confirms 58 consumed code
fingerprints, 1,740 historical files and original table hashes unchanged, with
579 reservations / USD8.1408513 and zero new reservations or provider calls.
The temporary authored root is removed only after verifying its exact resolved
path and empty inventory, without recursive deletion. Retained benchmark and local
full-suite timings remain bound to their earlier pre-correction revision.

## Final merged revision and retained measurement

PR111 merged as `876033e1bb2ca32a9e49417306f65f016a7ed83d`, with tree
`dbf4c31ecda90c0c4907e965825c59a48d1e7e0a` identical to the final reviewed
`f98758e96d5aed2daebce58d42425c31bfef50fd`. The final scoped Codex review found
no major issues, all four CI jobs passed in run 38081270536, and all four review
threads are resolved. Final focused validation is the 119-control run above;
the full CI covers the corrected code. The earlier local 1,787-test timing still
belongs to the original pre-correction implementation.

The clean merged revision was measured once on Windows / Python 3.13.5, using
the existing `--operation-units` benchmark, actual original read-only history
and authored identity/transport. The [bounded JSON report](fixtures/missing-link-protected-operations-merged-measurement-2026-10-10.json)
retains the exact measured head/tree, callback profiles, trace and unchanged gates.
Compilation took 6.108 seconds, outside the owned gates.

| Authored lines | Stream wall | Whole owned | First 3 critical max | First 3 history max | Full history audits | Fixed gates |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 10,000 | 6.805 s | 29.145 s | .035 s | 1.112 s | 21 | **Pass** |
| 60,000 | 38.143 s | 62.573 s | .040 s | 1.133 s | 22 | **Pass** |

Both workloads complete with one authored result and audited final seal, one
attempted slot and ten explicit unattempted slots. Each full audit reads and
hashes a fresh complete original database image; 21/22 exact logical cache hits
avoid repeated logical scans. The 60k stream still performs its overdue full
history audit. Complete history callbacks total 22.823/26.391 seconds; the 10k
profile includes 12.632 seconds in database audits, 5.483 in Git and 4.096 in
historical file hashing. No audit, acceptance barrier or gate is removed.

The benchmark exits 0 and its offline performance gate passes on this measured
revision. The 10k margin is only .855 seconds (about 2.85% of the thirty-second
limit). This is one observation, not a percentile, reliability margin or controlled
comparison with the earlier 30.545-second failure, which remains retained above.
The difference is not attributed to the review fixes. The critical gate applies
to the first three callbacks; a later 60k critical callback takes .208 seconds,
so this report does not establish a bound on every critical invocation.

Independent final read-only verification confirms the same 58 consumed code
fingerprints, 1,740 historical files and original database table hashes, with
579 reservations / USD8.1408513, zero added original reservations and zero
provider calls. The exact resolved temporary root is removed after checking its
empty inventory, without recursive deletion. This documentation publication is
not the measured head. There is no paid entry point or new live freeze; paid
readiness and call authorization remain false. Separate owned preparation tied
to reviewed/merged code and concrete human approval are still required before
a new one-shot provider attempt. Authored timing supplies no live latency or
semantic-quality evidence, and the consumed native run remains closed.
