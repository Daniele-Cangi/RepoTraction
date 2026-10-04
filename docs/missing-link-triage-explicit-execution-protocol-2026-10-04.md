# One shot execution of the explicit scope comparison

PR61 merged at `e0567f99fa43184b82b1e1662b1fe8109a6e2684`: Copilot reported
no findings on the reviewed head and all four Linux/Windows CI jobs passed.
The user authorized merge and continuation. This addendum freezes execution
**before paid requests**. It does not report model results or change the
[reviewed explicit-scope protocol](missing-link-triage-explicit-scope-protocol-2026-10-04.md).

## Frozen driver and guards

The fresh private driver is `data/luna-triage-explicit-run-2026-10-04/run.py`,
canonical LF SHA256 `e7b1926b48a1f181305e7aad384d65b4a3a193719733522136444584a85240c7`.
Its fixture script hash is
`fabbaa9fdba5af3a5f2f0a26718a0e6c0ff54c0ce49a80ee63cdc3d18c9a65fd`.
Both are retained locally; acquired bodies, receipts and credentials stay private.
Earlier drivers and preparation artifacts remain immutable.

The driver adapts the previous one-shot span harness to the reviewed helper,
new frozen preparation directory and current accounting baseline. Transport,
identity pacing, atomic reservation, receipt preservation and stop behavior are
unchanged. It verifies original inputs, selected-body ownership, canonical code
hashes and all nine schema/payload fingerprints before acquiring the worker lease,
then rechecks history under the lease. Exclusive `started.json` creation prevents
silent repeat or resume. No acquired repository code is executed.

Each request uses `Provider.complete` and `Budget`. Fresh verification of
`Daniele-Cangi` precedes each request; streaming reuses only recently successful
checks through the existing adapter. Reservations use the original allowance
and atomic ceiling **USD7.4123066**, not a reset cap. The configured model stays
[gpt-6-luna](https://developers.openai.com/api/docs/models/gpt-6-luna), with
Responses, streaming, strict schema, medium reasoning, 6,000 output tokens and
180,000 serialized bytes maximum. No provider configuration or production code
changes are made. No experimental verdict is imported into application jobs.

Identity, budget, transport, incomplete/refused response or wire-schema failure
stops the segment with typed diagnostics and no retry. Completed cards failing
local scope, property, citation or slice-description validation retain the raw
response as a failure, then continue once to the next case. Native usage is unknown
unless a terminal usage receipt exists. No credential-bearing exception or HTTP
body is published or copied into stop diagnostics.

## Verification and preservation baseline

Five private no-network simulations pass through the actual provider streaming
path: nine single requests with untouched raw receipts; invalid description
retained before the next case; invalid project scope retained without rewriting;
missing-terminal stop without retry; incomplete-response stop with terminal
usage retained. These are authored controls, not model-quality evidence.
The merged public suite previously passed 1,086 tests and 106 focused triage
checks; repeat the suite and final integrity verification in this execution phase.

The new read-only baseline retains **480 reservations / USD7.3363205**, all
12 table hashes and **474 historical artifacts**: the earlier 468 plus six files
from explicit-scope preparation. All old reservation rows, allowance identities,
ten non-accounting tables and protected artifacts must remain unchanged after
release. Only up to nine uniquely owned reservations, their corresponding original
allowance increment and new private receipts may be added. No active job is created.

The frozen maximum reservation is **USD0.0676115**. Reserving all nine requests
would bring the original allowance to **489 / USD7.4039320**, with combined triage
reservations **USD0.1916254**, inside the unchanged USD0.20 test cap and USD10 total
allowance. These are conservative reservation bounds, not native usage or invoices.
Earlier failed native usage remains unknown; no refund, retry or extra request is
authorized by unused headroom.

## Independent response assessment

Publish actual receipts and findings separately after execution. Recheck every
known facet against the original selected demand chunk and visible operation;
assess scope, claimed properties and selected-entrypoint/returned-interface layer
independently. A syntactically valid declaration cannot certify itself. Report
mechanical validation, semantic support, qualification requests, unknown context
and cost accounting separately.

Use the predeclared controls, including missing integration versus runtime,
unseen delegates, product versus operation scope, wrong-chunk relevance, external
anchoring/help-search analogies and defensible narrow mean value. Abstention is
not a correct negative by default; prior traversal/compression hints are not
compulsory ground truth. Do not rewrite historical cards, claim held-out accuracy,
promote the prompt into production or infer an eligible contribution from this
retrospective comparison alone.
