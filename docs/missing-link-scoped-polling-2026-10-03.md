# Missing Link: lossless, repository-scoped dashboard polling

## Outcome and boundary

The dashboard now requests complete saved evidence for its selected repository
instead of repeatedly transferring all account history. On the existing local
dataset, the D3 response falls from **31,318,927 to 833,960 bytes** (97.3% smaller).
The legacy full response, saved comparisons, exports and analysis contract 25
remain unchanged. This is a transport/rendering improvement, **not a new AI
experiment, useful connection, repaired comparison or executed bridge**.

The projection lives in `missing_link/dashboard_state.py`; `app.py` only forwards
the query to the existing verified polling boundary. No database schema, parser,
provider instructions, spending limit, timeout or job-resume behavior changes.

## Explicit read contract

- `GET /api/missing-link` keeps the complete legacy representation, including
  provider traces. Existing queries without `view` still select that contract.
- `GET /api/missing-link?view=dashboard` returns the repository index, all job
  results/warnings/actions, budgets and safety metadata, but no selected evidence.
- Add `&repo=OWNER%2FREPO` to receive the selected repository's complete public
  capabilities and comparisons. Selection is case-insensitive; comparisons are
  bound to the current repository ID, not inferred from old names. Retained stale
  and superseded comparisons are not truncated or reclassified.
- Unselected repository summaries explicitly say `evidence_loaded: false`, with
  their capability counts. Projection metadata identifies the requested source,
  selected ID, account-wide counts and complete-state download URL.
- Only unused `ai_trace` contexts are omitted from dashboard job records. All job
  result details, non-demand evidence, candidate errors and usage/reservation
  counters remain. The page links to a full local-state download; the existing
  source-context, JSON handoff and ZIP endpoints are unchanged.

The existing identity verification, same-origin protections and typed outage
diagnostics still apply. A restricted identity response is never expanded into
full or projected evidence. Invalid/duplicate projection selectors fail before
state access; this uses the existing GET error mapping, not a global status-code
refactor.

The page debounces source changes and coalesces changes during a read to the latest
selection. Unloaded evidence is visibly unknown, not an empty investigation.
Mismatched responses fail without a read loop. An account epoch discards responses
started before an account change. Selection and refresh never opt into capability
review, AI, Discover, Resume, imports or feedback writes.

## Measured local responses

Each scoped response was compared for exact equality with the corresponding
projection of the complete HTTP state, not only its counts.

| Representation | Bytes | Comparisons | Jobs | Observed seconds |
| --- | ---: | ---: | ---: | ---: |
| Legacy full | 31,318,927 | 306 | 87 | 5.128 |
| Dashboard index | 351,110 | No source selected | 87 | 5.269 |
| `jaraco/path` | 836,574 | 3 | 87 | 4.240 |
| `pallets/itsdangerous` | 938,759 | 5 | 87 | 5.571 |
| `d3/d3-array` | 833,960 | 4 | 87 | 6.684 |

These are individual observations, not latency benchmarks. The server still
builds the existing full state before projection; this change reduces transfer,
JSON parsing and irrelevant evidence rendering, **not database read complexity**.
The measurements do not establish a latency improvement or explain the earlier
browser-tool socket timeout. Query-level storage optimization would need a
separate compatibility change, not removal of saved evidence.

## Verification and limitations

The complete local suite passes **978 tests**, including **35 Chromium browser
fixtures**. Eleven new projection/HTTP regressions cover losslessness, renames,
name reuse, legacy full state, all three export kinds, database immutability,
same-origin rejection, account switches/ambiguity and minimal identity outages.
Eight additional browser fixtures cover source loading, index auto-selection,
in-flight coalescing, failure/mismatched replies, deactivation and both active and
inactive account changes. All use fictional evidence and temporary stores; none
can acquire GitHub repositories or reserve provider funds.

A separate browser session selected the retained D3, ItsDangerous and Path results
and displayed 4, 5 and 3 cards. D3 requirement/bridge/file disclosures opened with
keyboard activation. A manual D3 refresh completed a scoped GET with HTTP 200;
selection and expansion survived. Navigation to Overview and back preserved Path
and its three cards. No browser-observed POST, AI opt-in or review opt-in occurred;
the owned session closed and page-error inspection was empty.

The live session was **not uniformly successful**: two additional observer export
reads returned HTTP 409 during intermittent identity checks; an intervening read
returned 200. One awaited browser evaluation exceeded its own CDP timeout. A
read-only `gh auth status` and the offline browser diagnostic also stalled and
were stopped without changing credentials or repairing the browser. Pointer
acknowledgements alone did not establish disclosure activation; keyboard checks
did. These failures are not counted as passes or attributed to the projection.
Live rendered-quote equality from that failed observer is not established;
losslessness is instead demonstrated by exact API equality, export equality and
the passing browser evidence fixture. No global polling, identity or networking
fix is bundled into this change.

The first full run exposed a wrong exact-text expectation in the newly added
active-account fixture (`Local account: ...` includes a prefix). After correcting
that test assertion, the complete suite was rerun successfully. Earlier frozen
failures and model mistakes are not rewritten.

## Integrity and spending

The complete HTTP state's content digest is identical before and after restart.
All 12 fresh JSON handoffs equal their original CLI exports, and all 12 ZIPs equal
both the frozen originals and deterministic pinned packages. All **12 Missing
Link table hashes** and **354 protected prior artifacts**, including the preceding
precision/refresh experiment, remain unchanged after verification.

The allowance remains **461 reservations / USD 7.2123066** under its USD 10 ceiling,
leaving USD 2.7876934 unreserved. There were **zero new paid AI calls**, investigations,
automatic resumes, analytics collections or executions of acquired code. Reserved
amounts are not an invoice; unknown earlier attempts remain charged.

Private observations and screenshots stay in the ignored local data directory,
not the README/public assets. The current-code local server remains available for
manual tests without a collector or scheduler.
