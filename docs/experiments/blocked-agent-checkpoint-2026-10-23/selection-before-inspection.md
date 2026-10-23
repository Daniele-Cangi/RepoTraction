# Checkpoint selection rule, before inspecting candidate attempts

Purpose: acquire one independently recorded failed development-agent attempt,
not manufacture a failure by extending an issue's requirements. No solution-source
search, donor selection, new agent dispatch or paid AI call is authorized here.

The preliminary read-only chat inventory did not establish a suitable preserved
failed patch: one project is actively progressing, another has residual work
without an associated failed correction, and another's latest turn concerns file
transfer. Private chat text will not be published. Satellite is excluded entirely.

Use the official SWE-bench Verified submission
`20260219_mini-v2.0.0_gpt-5-2-codex`, from the observed experiments repository
`40f164d5b8f1d249bf95a6df8b74b577fd8e519d`. This is the latest submission explicitly
named Codex in the inspected directory inventory. Its contents and per-instance
outcomes have not yet been inspected. Historical failure does not establish that
a present-day agent is blocked or that the upstream problem remains open.

Within that one submission, consider failed `sympy__sympy-*` instance IDs in
lexicographic order, requiring a nonempty submitted patch, a preserved trajectory,
and recorded semantic test failure rather than only installation, timeout,
credentials or infrastructure failure. SymPy is chosen for an existing local
scalar-Python test environment, not a known donor or a predicted success.

Inspect at most three candidate attempts in this order. Select the first for
which the base revision, submitted patch, independent task/test contract and
local failing behavior can be reproduced. Record skipped candidates and reasons.
Do not read reference implementation patches, hints containing solutions,
successful trajectories, upstream fixing PRs or external mechanism sources.

If none qualifies, retain an honest selection failure rather than inventing a
blocked checkpoint. A selected historical benchmark case remains a benchmark
checkpoint with contamination limits, not evidence of a live unresolved request.

All new tracked artifacts belong to RepoTraction. Target snapshots and test
dependencies may be acquired only under its ignored data directory; no other
repository is modified. Freeze the failed state, baseline and independent tests
before any future source search. Do not run an assistance comparison in this PR.
