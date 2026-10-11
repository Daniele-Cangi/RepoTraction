# Capability-led retrieval: bounded comparison fixed before search

Prepared 2026-10-11 at baseline `62398c8334f10589ef1cb364bcc6ef4fced335c5`.
This tests the existing automatic path before proposing product changes.
No historical corpus, proposal or execution evidence is replaced.

## Arms and sources

Use the three unchanged pinned repositories in
`tests/fixtures/independent_behavior_contracts/corpus.json` (byte SHA-256
`38e39c089ede4b23b823cec55beb338986f06acf40d0ca45ea8dec0261a84fde`).
These source families are known from previous studies; new demand acquisition is
out of the old pool, but this is not a new-family generalization claim.

A: run existing `problem_queries` on the frozen structural capabilities.
B: one real existing `Provider.interpret_capabilities` call per repository, then
existing `problem_queries` on the returned capabilities. Preserve unreviewed
structural candidates exactly as Provider does. No manually authored search terms,
prompt edits, capability replacements or ranking changes.

Freeze all actual queries before any issue search. An invalid interpretation or
missing usable query is recorded; no retry or hand-written query rescues that arm.
This tests the complete existing enrichment-to-query behavior, including which
capabilities it prioritizes, not an isolated query-wording effect.

## Sampling and selection

For each arm/source, use at most three generated queries. Append only mandatory
`is:issue is:public` scope; preserve the helper's open/title-body/source-exclusion
qualifiers. Request the first three results per query sorted by update descending.
Keep returned order. This differs from the earlier oldest-first experiment and
will be compared only within this new paired study, not as a historical speed or
quality improvement. Maximum 18 queries and 54 result slots; duplicates retained
in query provenance and deduplicated by the existing selector.

Apply unchanged `select_candidates` with limit three separately to each arm/source.
If connector search omits issue state, hydrate returned issue metadata before
selection; record those read calls and do not infer metadata. No refill for empty,
duplicate, unavailable, bot, resolved-in-comments or irrelevant results. Preserve
overlap with previous demand pools as a separate historical-control flag.
Acquire selected discussion bodies/comments once per URL (at most 18 selected
slots across arms). Preserve coverage/redaction/truncation flags and unavailable
context; links/attachments/timelines remain unacquired. No target repository code
acquisition is implied by a body mentioning it.

## Review and success criterion

Review selected demands without arm/query labels or candidate source, using a
separate-context reviewer: real remaining demand, operation, constraints, later
resolution and unknowns. Then compare source behavior with those independently
identified operations. Reuse the current extraction and WASI boundary for any
defensible finite cases, fixed before matching. No host execution of acquired code,
new adapters, extractor extensions or expectations tuned to source outputs.

Report per-arm/source selected overlap, useful relations added/lost, misleading
contextual resemblance, incomplete interpretations and unsupported/runtime-blocked
cases. Distinguish static source support, finite execution, reuse advantage and
actual target integration. An issue hit, interpreted capability or lexical match
is not a useful relation. Unknowns stay unknown. If no supported useful relation
emerges, stop this bounded study without a search for better prompt/query weights.

## Paid-call boundary

Three prepared `gpt-6-luna` Responses requests use the existing prompt/schema,
medium reasoning, streaming, 12,000 output tokens and 180,000 request-byte cap.
Exact serialized sizes are 131,874, 57,802 and 129,123 bytes. At the currently
configured USD 0.10/0.50 per million input/output tokens, the existing conservative
reservation formula totals **USD 0.0504943**. This is not a billed-cost prediction.
Proposed new allowance: **USD 0.10**, maximum three attempts, no retries, no other
paid phases. Historical allowances cannot be reused. Execution awaits explicit
authorization for this new stage and retains existing atomic budget, identity,
lease, cancellation, attempt and output persistence controls. No new runner.

The exact preflight payloads and manifest are saved locally under
`data/capability-led-retrieval-2026-10-11/`; they contain public source context,
not credentials. Preflight intercepted before transport and made zero paid calls.
Windows/Linux CI and regression checks remain mandatory for any product change.
