# Capability-led retrieval evidence

This is a bounded comparison of existing helpers, not an end-to-end Discover
qualification run. The protocol is in
[../../missing-link-capability-led-retrieval-protocol.md](../../missing-link-capability-led-retrieval-protocol.md).
No historical evidence or production code is replaced.

## Order

1. Baseline `62398c8334f10589ef1cb364bcc6ef4fced335c5`; protocol fixed in
   `3dbe656` before paid capability interpretation or issue acquisition.
2. The user separately authorized USD 0.10 for three capability calls, no retries.
   `manifest.json` retains the *preflight* status; `run-result.json` records the
   completed execution. They describe different stages, not conflicting results.
3. All 18 queries and three completed interpretations frozen in `e974715` before
   search. A uses structural capabilities; B uses the real Provider enrichment.
4. Pools, selections and redacted discussion packet frozen in `0b0d504` before
   demand-review results. Queries were not repaired after observing results.
5. Separate-context demand review and seven domain cases frozen in `971243c`
   before source/demand matching. All 47 quoted UTF-16 spans match the packet.
   The review remains an AI assessment with explicit bounded reading coverage.

## Files and scope

- `search-pools.json`: query order, returned rank and hydrated state/title for
  all 53 result slots (46 unique URLs). Bodies are retained only for selected
  discussions. This is sufficient to replay the existing title-based selector.
- `selections.json`: the exact six helper outputs, three candidates each.
- `discussions.json`: the 17 unique selected issues, without arm/source/query
  labels. The separate-context reviewer receives this packet only.
- `retrieval-metrics.json`: exact selection replay, helper timing, coverage,
  historical overlap and advisory screening replay.
- `blind-demand-review.json` / `.md`: independent judgments, reading coverage,
  original quotations and seven domain cases frozen without candidate knowledge.
- `source-comparison.json`: subsequent per-pair static assessment and the reasons
  none of the domain cases was bound/executed through the current extractor.
- `run-result.json`: persisted job, source snapshots, enriched capabilities,
  native response traces and reported usage. It retains the existing budget,
  identity, attempt, cancellation and persistence controls for the three calls.

The job's `requests_used: 0` belongs to the isolated paid-capability job; it does
**not** mean this study made no GitHub reads. Acquisition used 18 search, 46 issue
metadata and 9 comment connector calls. A connector may paginate internally;
73 tool calls is not a measured HTTP-request count. GitHub acquisition elapsed
time and total review wall time were not instrumented. The packet's `fetched_at`
values are snapshot assembly timestamps, not individual HTTP timings.

The helpers are those used by Service, but this deliberately small study uses
three results per query. Ordinary Service can request two pages of 20 per query.
The subsequent paid `interpret_request`, target-context acquisition, evaluation
and qualification stages were not invoked. Independent offline review is not
evidence that those production stages succeed or fail on these discussions.

## Coverage and interpretation limits

All 571 comment records were acquired according to the metadata counts. Five
issue bodies and 89 comment bodies are truncated under the existing 64 KiB text
and 512 KiB discussion limits. Of those comments, 87 have no retained body.
`comments_complete` describes record-count coverage, **not complete text** or
complete resolution history. Links, attachments, timelines and target repository
code were not acquired. Reviewer inspection coverage is a separate limitation.

Only normalized text and necessary comment metadata are published; duplicate
HTML bodies are excluded. Existing redaction is applied to public artifacts.
Redaction is a bounded defense, not proof that arbitrary text contains no secret.
The local ignored raw acquisition and exact wire request files are not part of
this public evidence bundle. The preflight hashes refer to those exact wire
files; Provider trace request hashes use its own canonical request convention.

There is no selected-URL overlap with the old corpus. The three source families
are nevertheless known from earlier studies. Sorting by most recently updated
and taking three hits creates a small, nonrandom sample; do not compare its
quality or speed directly with the older oldest-first sample.

## Offline replay

Use `tests/fixtures/independent_behavior_contracts/corpus.json` repositories for
arm A, and `run-result.json` checkpoint repositories for arm B. For each of the
six arm/source groups, call unchanged `problem_queries(repository)`, append
` is:issue is:public`, and compare with `queries.json`. Pass the group's three
`search-pools.json` item lists and queries to
`select_candidates(batches, queries, repository, 3)`. Compare both returned
objects and pool count with `selections.json`. All six replays match exactly.
No network or paid call is needed for this replay.

Timing is 50 warm repetitions of query generation plus selection per group on
local Windows/Python 3.13, with medians retained. It excludes networking, model
latency and review. It is not a benchmark of whole-product performance.
The advisory `screen_candidate` replay retains all 17 packets. Author type/bot
fields were unavailable in this connector packet, so this is not a claim of
exact parity with all metadata acquired by ordinary `PublicGitHub`.
