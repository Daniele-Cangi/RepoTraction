# Stopped Luna triage test

## Outcome

The first of nine planned extractions stopped with
`ai_stream_deadline_exceeded`. **No complete model response was retained, and
Luna's interpretation quality was not evaluated.** The other eight cases remain
unstarted. No outcome relation, citation success or reference agreement can be
reported from this attempt.

The [frozen protocol](missing-link-luna-triage-protocol-2026-10-04.md) required
stopping on a transport failure. No paid retry, replacement, model substitution,
refund, production ranking change or historical result rewrite occurred.

## Execution and accounting

Protocol commit `e09feb6` and its unpaid preparation clarification `62c063b` were
pushed before the actual call. Production executable code remained merged
`4039c311f81d02d639aabd91132c3e68ed482120`.

The first launch had already stopped before any reservation or provider request:
scan tuples and JSON lists failed a local equality assertion. The separate
canonicalized preparation retained exactly the same nine outbound request
hashes, sizes and USD 0.0553099 full-segment estimate. That unpaid preparation
failure was preserved and did not count as a model trial.

The actual launch sent only the first prepared request: Hermes demand versus
Path `only_newer`. Its request was 9,981 serialized bytes, with the declared
6,000 output-token cap and unchanged `gpt-6-luna` provider configuration. The
existing stream deadline guard stopped the attempt before a terminal response.

| Accounting item | Verified value |
| --- | ---: |
| Planned cases | 9 |
| Persistently reserved attempts | 1 |
| Complete response receipts | 0 |
| Evaluated model outputs | 0 |
| Conservative reservation added | USD 0.0042029 |
| Original allowance reservations | 462 |
| Original allowance reserved total | USD 7.2165095 |
| Original USD 10 allowance unreserved | USD 2.7834905 |

Reported token usage and provider invoice cost are **unknown**, not zero. The
private aggregate's zero usage accumulator only means that no usage event was
recorded; the supplementary diagnostic explicitly preserves unknown usage.
The attempt remains conservatively charged. It is inside the USD 0.20 segment
cap but is not a successful test or a measured model-quality failure.

## Harness defects and diagnostic limits

The one-shot evaluation supplied `verify_cli_account` directly as its checkpoint
callback. `Provider.complete` invokes checkpoints while reading streamed events,
so the harness could launch a bounded GitHub CLI check for every event. The
normal application's verification callback instead reuses recently verified
success, invalidates it before a fresh check and timestamps success after CLI
latency. This evaluation did not reuse that pacing behavior.

A symbolic-time fixture reproduces the sensitivity: 150 streamed events with
a two-second checkpoint cost exhaust the unchanged 240-second deadline. A fast
checkpoint reaches the same simulated terminal response. This proves a possible
harness-induced timeout, **not the full cause of the live failure**: per-event
live timing and the missing terminal response were not captured. Do not blame
GitHub, network conditions or Luna's reasoning from these observations alone.

The offline fast-stream fixture also exposes a separate preparation defect:
the frozen schema uses nullable `type: ["string", "null"]`, while the existing
local `validate_shape` supports only simple object, array, string and boolean
types. A completed synthetic response reaches that validator and raises
`TypeError`. This second issue did **not** cause the observed live timeout,
which happened earlier. No live model output was recovered through the fixture.

Both are evaluation-harness integration defects, not demonstrated regressions
in production discovery or the model's relevance decisions. No production
validator, account guard or stream timeout was changed.

## Offline repair checks

A separate private, unwired prototype under
`data/luna-triage-repair-2026-10-04/` checks a future harness design:

- Bounded reuse of successful identity checks, including expiry, forced failure
  invalidation and success timestamps after CLI latency. Failed identity is never
  treated as cached success; the fixed expected account is still verified.
- An explicit string-only wire format for unknown references, with empty strings
  mapped to null by a declared transport adapter. The adapter preserves raw
  responses and every relation; it does not repair quotes or semantic judgments.
- A fully simulated `Provider.complete` stream produces a receipt, passes the
  unchanged local schema validator and normalizes to `context_required`.

Seven offline repair tests pass. They are not an installed fix, a new frozen
live schema or a successful paid retest. The earlier nullable protocol remains
unchanged as the record of the failed attempt.

In total, seven initial harness checks, two canonicalization checks, three
post-failure diagnostics and seven repair checks pass without paid calls.
Fixture coding errors were corrected before interpreting those fixture results.
These checks do not replace real model predictions. Production code is unchanged;
the full application suite was not rerun for this documentation-only experiment.
The preceding merged baseline had 994 passing local tests.

## History preservation and next action

All ten non-accounting Missing Link tables retain their baseline hashes.
All 461 earlier reservation rows, every other allowance row and 383 protected
prior artifacts are unchanged. Only one new reservation and the corresponding
original allowance increment exist. No production job, match, snapshot or proof
was added or changed; no investigation is running. The lease was released.

The failed attempt and original preparations are retained privately; source
text, credentials and local receipts are not committed. This report separates
operational failure from model evaluation, rather than assigning missing
predictions an accuracy score.

Before another paid attempt, integrate and validate the offline repair in a
separately fingerprinted harness and freeze its revised wire format/prompt.
An explicit go-ahead is required for a fresh paid segment after this protocol's
stop. Keep the original unknown attempt charged and the combined spend within
the authorized cap. Do not expand ranking, parser or UI scope from this failure.
