# Acceptance frozen before any development agent or external source search

Target: pytest `aec0291ed14c724873bfcea99d5dfd739f75a68f`.
Need: the ordinary pytest error-reporting path should produce a useful diagnostic
for the original #8482 example without spending quadratic work on expensive locals.
The criteria derive from that report, the withdrawn direct proposal's acknowledged
counterexample, and existing target semantics. They do not prescribe a donor,
hashing method, data structure or target implementation.

1. On the preserved original reproduction, ordinary formatting must finish within
   the same 15-second observation cap, report `RecursionError` with the relevant
   filename/frame information, and retain the collection-error exit status (2).
   Verify in three fresh candidate processes, paired with the disclosed native
   traceback workaround. The cap is an experimental resource boundary, not a
   maintainer latency requirement. No exact speedup is inferred from a censored
   baseline. A future different platform needs its own measured baseline.
2. Preserve the first repeated state for equal locals at the same code identity
   and line in the six small native controls: immediate repetition, repetition
   before a distinct tail, no repetition, equal-but-distinct unhashable values,
   unavailable equality, and equal-but-distinct code objects. Do not use only the
   last frame or compare code objects by value. Unknown origin must remain an
   explicit uncertainty; it must not be labelled a detected cycle.
3. Keep the existing native exception/traceback regressions passing, especially
   origin index, no-index fallback, equality errors, hidden frames and full-trace
   behavior. Report optional skips and environment limits. Run the full relevant
   module before claiming an advance; broader tests and Windows/Linux CI are
   required for any future implementation before merge.
4. Measure equality calls at 20/40/80/160 native frames, wall time on the original
   workload, changed source size and dependencies. A lower toy-operation count
   alone is not evidence of practical benefit. Linear behavior for all arbitrary
   custom equality semantics is not required or claimed. If a candidate bounds
   work by conceding origin precision on expensive/large inputs, record that
   changed guarantee and its warnings explicitly; do not call it equivalent.
5. No improvement by changing the reproduction, lowering the global recursion
   limit, deleting/skipping original tests, globally switching to native output,
   suppressing diagnostics, or special-casing fixture names or MagicMock. Target
   modifications stay in the actual pytest reporting path. No donor-only or
   standalone replacement test counts as recipient-software evidence.

Useful partial progress must overcome at least one previously failed criterion
while preserving the relevant correctness controls, and retain any remaining
failures. Success of an ordinary first attempt ends the assistance experiment.
An assisted improvement needs a trace from a source-owned idea to the actual
target modification, plus an ordinary continuation comparator. One pair cannot
establish population-wide effectiveness or isolate causation from agent variation.
