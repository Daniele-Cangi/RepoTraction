# Policy-v3 stream successor offline preparation — 2026-10-09

This new private source preparation freezes the prospective [stream successor
protocol](missing-link-policy-v3-stream-successor-protocol-2026-10-09.md), following
the user request to try again after PR104's reviewed merge. The implementation
and actual one-shot execution still require their separate reviewed exact tree
and concrete owned authorization. No corrected live reader or paid entrypoint
exists in this phase. The [failed v3 run](missing-link-demand-operation-policy-v3-native-results-2026-10-09.md)
and all predecessors remain consumed and unchanged.

## Independent anchors

The new ignored directory is
`data/missing-link-demand-operation-policy-v3-stream-preparation-2026-10-09/`.
It contains **27 files**: manifest, baseline, original inputs/reference copies,
prospective protocol and eleven envelope/native-body pairs. Every write was
exclusive. Its manifest digest was retained independently outside the directory.
The protocol was committed prospectively as `4040c11` before preparation; this
commit is not an approved executable tree.

| Artifact | SHA-256 |
| --- | --- |
| Prepared manifest, exact bytes | `dd7d0f975d70f2f3fc2a5110a9111b881fea0053f2d493c0ad02f76bee38b1f7` |
| Protocol, UTF-8/LF | `c73a88721b9bab36f2a715012a202df1f22583c4ecaa6661e22f599d0d045fbe` |
| Original baseline, exact bytes | `f7d4d0ca0f9fe39f5996c84c1aa86bfdbb78b8c8825f99c6806bc37234c02c2b` |
| Inputs, exact bytes | `c1311e56aebd31cd750c82d9a3f7192b5eb77ca9eadaef903b7d544aa44856dd` |
| References, UTF-8/LF | `6cc171bc9e83130479156e71af09869c9bc6100240f28f69865da5fc95b6e9df` |
| Original v3 source preparation | `03bd97b6a26b74950ff5a6df921a9a92e37a2c298f6db2a5d556befb137ae741` |
| Failed v3 native prepared manifest | `15cd1bd3c0e82d89972ad42d6c5875c9f2912a753c80a82156daa878861c0411` |
| Failed v3 native receipt seal | `834d4a9ced59a7d23092fe0982aca97af11c2dd948b915cca76ddbd25e76a8b5` |
| Absence-assessment prepared manifest | `cd22d2e36e2dbddd1119bd3a41cf3a46ca1dfc1a092e4090a79ed343b9c08441` |
| Absence-assessment receipt seal | `f1c280a4e36f72ebf5253a1d00378753db228915c52c2c9e83ea2a55ffbfb5f7` |

The baseline protects **1,687 artifacts**: the existing 1,662, all twelve failed
v3 native files and all thirteen absence-assessment files. It pins the exact
current original `ml_*` tables and reservation/allowance rows with zero active
jobs. All **53** existing code fingerprints remain canonical-LF bound: the
previous 51 and the separate diagnostic harness/tests. The original v1/v2 seals,
assessments, protocols, policy modules, adapters and tests are unchanged. The
diagnostic report is pinned separately by its canonical digest.

## Identical inputs, distinct future scope

All eleven envelopes and native bodies were copied byte-for-byte from the
independently verified original v3 preparation. They reproduce through the
unchanged builder and Provider encoder using explicit key-free public settings.
Only private accounting IDs change to the new stream-successor namespace in
the protocol; those IDs are not model-facing data. No original packet, context,
strict schema, instruction, SYSTEM message, reference or policy is changed.

Settings remain `gpt-6-luna`, medium reasoning, Responses streaming, strict JSON
Schema, `request`, `store=false`, 6,000 output tokens and 180,000-byte prompt
bound. The maximum envelope/native sizes remain **27,318 / 29,597 UTF-8 bytes**.
New IDs are absent from the original ledger and distinct from all original
v3 IDs, including its ten unattempted ones. This is not resumption of that run.

Original accounting remains **578 / USD8.13614**, configured total **USD10**.
The proposed eleven-slot reservation sum is **USD0.0548404**; full execution
would reach **589 / USD8.1909804**. Segment cap is **USD0.10**, cumulative
ceiling **USD8.23614**, maximum per-slot reservation **USD0.02**. These are
software reservation bounds, not verified prices, usage or provider billing.
No budget increase, new allowance, refund, deletion or reset occurred.

## Required successor behavior

The protocol specifies separate monotonic measurements for reads/checkpoints,
a 240-second active stream limit and a 600-second wall stream limit. Continuous
returned-read checks cover cancellation, fixed identity, executable fingerprints,
slots and leases. Full DB/history checks run at side-effect boundaries and after
128 nonterminal lines or 30 observed wall seconds since the preceding completed
full checkpoint. A fresh full check after native retention is mandatory before
semantic parsing or accepting output. This changes the old detection cadence;
it does not promise detection of history changes reverted between full checks.

Typed failure codes, HTTP status, observed reservation/receipt state and bounded
timings must distinguish transport failure from callback failure without raw
upstream text or credentials. Authored tests must prove deadlines, detection
boundaries, global/local rejection rules, persistence and no-retry semantics.
The unchanged diagnosis cannot establish what caused the consumed v3 failure.

After protocol review/CI/merge, implement and review separate opt-in adapters.
Then exclusively prepare the actual owned run, extending the protected baseline
with all 27 new source-preparation files and pinning every new dependency at the
exact reviewed/merged tree. The prospective preparation remains
`offline_only_no_stream_successor_executor`, with **zero new calls,
reservations or predictions** and `call_authorization_granted=false`.
Never rewrite it to imply implementation or execution has occurred.

The user request records intent to try a successor, but this source preparation
does not bind or grant the later exact owned call authorization. No useful-lead,
semantic-quality, ranking or production-promotion claim follows from preparation.
