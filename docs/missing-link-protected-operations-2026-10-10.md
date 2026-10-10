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
