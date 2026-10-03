# Missing Link — contract-25 offline corrections

Date: 2026-10-03. Follow-up to the
[contract-24 three-source test](missing-link-contract24-remaining-result-2026-10-03.md).
This is a retained-output replay and fixture verification, **not a new model test**.
No acquired source or generated bridge was executed.

## Scope

Three independent corrections, outside `app.py`:

1. A Python class citation spanning its own assignments **and a nested operation's
   body** cannot establish that nested operation's behavior. Precise class-owned
   initialization and separately selected method bodies remain supported. A
   truncated prefix cannot bypass the mixed-range rejection.
2. Keep the existing 1,600-character quote limit, but retain a body-bearing
   contiguous subspan when the original valid, supplied citation already contains
   that body and prefix clipping would hide it. Preserve the original source ID;
   update display lines/URL and include `quote_selection` with the original range.
   Do not expand signature-only, omitted, out-of-operation or mixed class citations.
3. Persist a safe identity observation before the HTTP investigation driver's
   unverified-state guard fails. `Report.observe_identity` can also be used before
   an owned verification assertion. Save only typed flags and reconstructed known
   diagnostic codes; never raw CLI output, account/provider data, messages or keys.
   Keep the acknowledged job and its last observed snapshot; do not replace,
   retry, resume or cancel it because observation failed.

The analysis contract is now **25**. Contracts 21–24 remain historical/stale;
they are not migrated or rewritten. Provider context remains bounded to
180,000 encoded request bytes. No parser/resolver completeness expansion,
larger prompt, larger export limit or semantic-truth certificate is introduced.

## Retained public-output replay

Replayed the nine comparison responses / 15 stored comparisons from Filelock,
Psutil and Ws with a mocked provider completion and explicitly blocked HTTP and
subprocess calls. The real database was opened with SQLite `mode=ro`. Inputs and
raw provider outputs remained immutable. This exercises the current packing,
source-scope validation, normalization and export paths, not a fresh model decision.

| Reproduced case | Contract-25 outcome |
| --- | --- |
| `BaseAsyncFileLock`, match `e72f5f6d33154cd84350a7591c8a7968` | `r0`: satisfied / existing behavior → undetermined / not demonstrated. The citation mixes class assignments with the claimed method's body. The missing method ID is not invented. |
| `lock_descriptor`, match `dff2a683d6a07b845c6dce9c666196b6` | The original supplied range 16–50 retains the actual body at 43–50, a 336-character quote. The verdict remains unchanged: a separate selected-operation attribution gate still fails. Body visibility alone does not confer partial credit. |

Only the class case changes a check's status/contribution. All 15 overall
discovery assessments remain unchanged: seven `not_a_fit`, two `similarity_only`,
two `known_reference`, four `partial_contribution`; **zero eligible follow-ups**.
This does not establish a newly discovered useful integration or improve recall.

The nine locally encoded Responses-format comparison requests range from
154,043 to 178,061 bytes, all below the unchanged 180,000-byte cap. The replay
uses explicit non-secret provider settings, not the local `.env` or a paid client.
Every retained quote is at most 1,600 characters; focused quotes are substrings
of their original supplied citations with contained line bounds.

All 15 original ZIP exports remain byte-identical when rebuilt from their pinned
historical snapshots. All 15 newly normalized inspection packages reconstruct
their full JSON handoff, including multipart packages, with existing per-file
128,000-byte and total 2,000,000-byte limits. No stored package/result is replaced.

## Fixture and installation verification

Regression fixtures cover:

- Full and partial claims from mixed class/method excerpts, nested classes,
  precise initializers, selected methods and prefix clipping.
- Long docstrings, fake body words/default arguments, CRLF, Unicode, oversized
  body lines, documentation-only spans and whole-file/sibling citations.
- Provider source-scope rejection when the acquired body was not supplied;
  temporary-store round trips retain the focused quote and audit metadata.
- Preflight/poll diagnostic retention, known/unknown code redaction, typed flags,
  assertion-time report preservation and no observer-triggered replacement job.
- Contracts 21–24 stay stale while historical payloads remain unchanged in a
  temporary store, without GitHub requests or AI reservations.

The first full run caught a fixture still asserting contract 24; the expectation
was updated to 25 and contract-24 history was added to the stale-history test.
The final full run passes **948 tests** on Windows / Python 3.13.
Source and installed `app.py --help` pass. A separate ignored Windows installation
includes the new modules and preserves its fixture history and `.env` on update.
The user's installed configuration and running server were not replaced/restarted.

## History, cost and diagnostic limits

Before/after verification: all **12 Missing Link table hashes** and **150 protected
historical JSON artifact hashes** are identical. There are no queued/running jobs.
Freezegun/Babel remain paused. Original allowance
`missing-link-verification-2026-09-30`: **440 reservations / USD6.8468383**,
unchanged; remaining allowance USD3.1531617. New paid calls/reservations: **zero**.
No unknown reservation was refunded.

This does not retrospectively recover the diagnostic response lost by the old
post-restart assertion. Its exact cause remains unknown. A later successful CLI
identity check is not evidence of an expired key, nor a clean rerun of that
operational check. The frozen old experiment/helpers and report remain unchanged;
future assertion-based checks should use the safe observation helper before
asserting verification. Account isolation, cache policy and the ten-second
CLI-verification timeout are unchanged.

## Next boundary

Review this bounded correction before another separately scoped real-model test.
Do not resume the paused historical jobs or execute a bridge until a genuinely
grounded eligible lead has been established. Typed callable JS/TS coverage remains
a separate planned task, not an implicit parser extension in this patch.
