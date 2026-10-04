# Luna property comparison execution protocol

This protocol freezes a nine-case development comparison of the reviewed
[property prompt](missing-link-triage-property-prompt-2026-10-05.md). The user
authorized a new segment of USD0.10 inside the original USD10 cumulative allowance.
The prepared requests need only USD0.068867 in conservative reservations, so no
additional spending segment is needed. **Preparation is offline; no new model
response or quality improvement is claimed.** Execution waits for scoped Codex
review and green CI.

## What changes and what stays fixed

PR64 is merged, with four green CI jobs and a no-findings review. The new run uses
its prompt string SHA256
`7697f92e260a315042b64ad92234a805e3629118b6aa660676fc8dcfc825c882`.
Only that paragraph changes relative to the preceding run. Model `gpt-6-luna`,
Responses streaming, medium reasoning, strict schema, 6,000 output tokens,
original nine inputs, exact spans, selected-operation ownership and normalization
stay unchanged. Prior predictions and reviewer labels are never sent to the model.

The original retained inputs are checked against fresh read-only reconstruction
from the saved acquired context. The nine schemas match the predecessor. Request
payloads differ only in prompt text, including unchanged system framing, context,
model options and schema. Payload files, canonical request hashes, serialized byte
hashes and code fingerprints are frozen privately before any paid call.

The same selected historical cases are development diagnostics, not held-out
accuracy or a new autonomous discovery run. No repository code is executed, no
new discussion is acquired, no historical response is repaired or regraded and no
production provider, ranking, qualification, isolation or UI change is made.

## Requests and cumulative spending boundary

Each case is attempted at most once, in its original order. Reservation estimates
use the exact serialized body plus the existing 2,048-byte buffer and maximum
output, not a token guess based only on visible source text.

| Case | Serialized bytes | Conservative reservation USD |
| --- | ---: | ---: |
| 1 | 17,845 | 0.0049893 |
| 2 | 20,687 | 0.0052735 |
| 3 | 150,198 | 0.0182246 |
| 4 | 14,546 | 0.0046594 |
| 5 | 44,271 | 0.0076319 |
| 6 | 16,232 | 0.0048280 |
| 7 | 17,306 | 0.0049354 |
| 8 | 94,127 | 0.0126175 |
| 9 | 25,026 | 0.0057074 |
| Total | 400,238 | 0.0688670 |

The standard configured prices remain USD0.10 input / USD0.50 output per million
tokens, consistent with the current [Luna model page](https://developers.openai.com/api/docs/models/gpt-6-luna).
These are conservative reservations and configured-price usage estimates, not an
invoice. No tool, regional or fast-mode routing is added.

The baseline has **489 original reservations / USD7.4039320**. The same original
allowance ID is retained; the atomic Store reservation ceiling becomes
**USD7.5039320**, the baseline plus this explicitly authorized USD0.10 segment,
and remains below USD10. Full execution would add nine reservations, reaching
USD7.4727990; that is a planned maximum, not spending already incurred. Earlier
triage reservations USD0.1916254 remain charged; this run would add USD0.0688670.
There is no refund, reset, replacement allowance or additional unbounded segment.

## One shot execution and failure handling

The owned private driver performs frozen-request, code, input, history and budget
checks before acquiring the existing worker lease. An exclusive `started.json`
marker precedes requests and prevents a second execution. The original CLI account
must freshly verify as `Daniele-Cangi` before each request; the unchanged bounded
identity cache is used only during that request. Account or budget failure stops
before further network access. No retry or automatic continuation is allowed.

The new public executor is `scripts/missing_link_triage_property_execution.py`.
It uses the existing Provider terminal-stream path and Budget callbacks, preserving
raw receipt JSON, response IDs/status, usage when supplied and normalization flags.
Only local validation after a completed provider response is candidate-local:
record its raw card and validation error, then attempt the next case once.
Transport, missing terminal, incomplete/refused output, provider-schema, account
and allowance failures stop the whole run. Unknown native usage stays unknown.

Only owned in-flight receipts are mutable. Completed results and diagnostics use
exclusive creation. After lease release, the final integrity check permits at most
nine exact new reservation rows and the corresponding increment of the original
allowance. All 489 earlier rows, other allowances, ten non-accounting tables and
510 earlier artifact hashes must remain unchanged. No production job is imported.

The owned driver is `data/luna-triage-property-run-2026-10-05/run.py`, with
canonical-LF source SHA256
`18ce562b37684692ef82444ee9879181122611360809c27bccd1f185e2f06005`.
The prepared manifest includes the public executor, prompt, provider, Store,
Budget, lease, account/configuration helpers and relevant tests in its source
fingerprints. The predecessor fingerprints remain protected separately.

## Checks before any paid request

Seven new no-network tests exercise the actual Provider terminal-stream path:
nine single calls, raw local-invalid preservation, provider-schema stop with raw
receipt, missing/incomplete terminal handling, account failure and atomic allowance
rejection before the next request. All 143 focused triage tests pass.
The full 1,123-test suite passes on the final source revision. The post-test
check reproduces the nine frozen requests and verifies all twelve table hashes,
489 prior reservation rows and 510 protected artifacts unchanged.

Offline preparation reproduces all nine request hashes. A second simulation sends
the exact frozen bodies through a mocked opener and in-memory receipt/reservation
callbacks. It is not a model run, makes no real reservation and cannot establish
Luna quality. It passes with all nine exact serialized bodies, nine fresh forced
identity checks and the expected USD0.068867 in memory-only reservations.

## Independent comparison after execution

Report terminal completion and mechanical validity separately from usefulness.
Retain all original raw outputs. Review every newly known property against its
original demand chunk and selected body, including runtime versus behavior,
declared interface versus enforcement, factory/method layers and citation relevance.
Inspect genuine delegate/interface gaps, the timestamp analogy and whole-product
overclaims even if the model abstains. Keep the requested mean slice bounded.

Compare the three prior known facets and 33 abstentions with the new run without
forcing old labels or crediting unknown as a correct rejection. More known facets
are useful only when independently supported. Fewer unknowns alone do not prove
accuracy; a no-issues abstention audit is not a usefulness score. This follows the
general emphasis on task-specific evaluation and human judgment in
[OpenAI evaluation guidance](https://developers.openai.com/api/docs/guides/evaluation-best-practices),
not a source of gold labels for these cases. Preserve failed usage as unknown and
publish the result separately before any further prompt or production decision.
