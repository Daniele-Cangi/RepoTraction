# Consumed stream successor outcome — 2026-10-10

PR106 merged as `098378004caed2882412f83afd67ce64d33b668c`, with reviewed
`32ed88526c6567025a3eda2d12c544d3a9d58776` tree unchanged, clean scoped Codex
review and all four CI jobs successful. A new owned freeze was prepared on that
exact merged tree. The user separately authorized its eleven one-shot slots.

The actual invocation stopped globally at slot 1 with
`ai_stream_deadline_exceeded`, phase `request`, deadline kind `wall_stream`.
One reservation was committed; no terminal, output or native usage was retained.
Slots 2–11 were unattempted. No retry or resume occurred, and the entire owned
scope is consumed. A separately sealed assessment records absence for all eleven
slots; it supplies no predicted claim paths or semantic judgments.

| Native observation | Value |
| --- | ---: |
| Observed stream wall time | 600.048269 s |
| Active stream time | 5.411616 s |
| Time inside returned reads | 5.324723 s |
| Opening, outside stream interval | 1.677955 s |
| Light checkpoints | 3,877 / 356.867779 s |
| Full checkpoints | 15 / 237.768874 s |
| Total checkpoint time | 594.636653 s / 99.098% of wall |
| Observed lines / bytes | 1,938 / 195,467 |

The trace reports a valid clock and no saturation. These observations establish
local checkpoint overhead in this run. They do not establish how long the
provider would have needed without that overhead, nor the cause of the older
v3 run's untyped transport failure. Stream reads can return already-buffered
data; their measured duration is not the model's generation time.

Original accounting extends from 578 / USD8.13614 to **579 / USD8.1408513**,
including the retained USD0.0047113 reservation, within the original USD10
allowance. This is software accounting, not verified billed spend; absent usage
does not mean zero tokens. No original jobs are active. Independent read-only
verification reproduced all 58 executable fingerprints, all 1,714 protected
artifacts, the exact reservation prefix and the closed native receipt inventory.
The native run and separate absence assessment each contain 13 sealed files.

Independent anchors retained outside the owned directories:

- Prepared: `e9f3b1ee61c97e944a3ba4fe6e9ef5c55db8f70d37a72f8b2bc830ac5a862394`.
- Native receipt: `30441938e0974e6ed44c95aa094af267a946aa873beed143a26e44fae4e741c1`.
- Assessment prepared: `e5344edf26891c54eb05ed3f6fc786cac112c659636e1975cc9db0871d86662c`.
- Assessment receipt: `3d5f594ff23bcfae2452da57b3a4e387e849e38bac493ff2c90125bfeb8094b8`.

The next step is the separate [checkpoint cadence prototype and integration
contract](missing-link-checkpoint-cadence-2026-10-10.md). All consumed code,
requests, native evidence and assessments remain immutable. No timeout increase,
budget increase, production promotion or new paid invocation follows from this
report or from the offline prototype.
