# One-shot execution of the reviewed span comparison

PR58 merged at `49c78eb4b4bcfb5bbe148f6afeb55588db333535`. Copilot reported
no findings on its reviewed head. The user authorized proceeding after merge.
This addendum records the execution harness **before paid execution**, not results.
The [original span protocol](missing-link-triage-span-protocol-2026-10-04.md)
remains unchanged, including its nine cases, semantic controls, prompt, schemas,
request hashes, provider settings and combined spending ceiling.

## Frozen execution

The private driver is `data/luna-triage-span-run-2026-10-04/run.py`, with canonical
LF SHA256 `e729cfe0b5408f15210be75c4fc0ad38de0c8f040eb8105aa7ba17e3d5369eac`.
Its offline fixture script SHA256 is
`4e623c20495d7963fa72cda1c5294b259d564ae139a8d0655244612ec8a0af58`.
Both are retained locally, outside the tracked repository; credentials and
acquired context are not published. The original preparer is read-only.

Preflight reproduces every frozen source input, selected-body span, canonical
code hash, per-case schema hash and actual serialized request hash. The driver
checks these again before acquiring the worker lease and rechecks database and
artifact history after acquiring it. It records an exclusive one-shot start;
a later invocation cannot silently resume or repeat this segment.

Each case uses the existing `Provider.complete` and `Budget`, with a forced
fresh `Daniele-Cangi` account check before the request and bounded successful
check reuse during streaming. Atomic reservations use the original allowance
and ceiling **USD7.4123066**, not baseline plus a new cap. No production job is
created or imported. No source code is executed, and no production wiring changes.

Reference/description-invalid completed cards retain raw output and fail locally,
then the next case runs once. Identity, budget, transport, incomplete/refused or
wire-schema failure stops the segment with typed diagnostics, retained reservations
and no retry. Native usage is known only if a terminal usage receipt exists.
Failure messages and credential-bearing HTTP bodies are not copied into diagnostics.

## Offline verification and preservation

Four private fixture tests exercise the actual streaming `Provider.complete`
path with mocked transport: nine single calls with raw receipts, a non-slice
description failure followed by the remaining cases once, missing-terminal stop
without retry, and incomplete-response stop with terminal usage retained.
All four pass. All **61 focused public triage tests** also pass. These checks make
no network requests, paid calls or database writes.

The fresh baseline retains **471 reservations / USD7.2717195**, all 12 table hashes
and **435 prior artifacts**, including the five files from the reviewed preparation.
Final integrity must preserve every prior reservation, all ten non-accounting
tables and every protected artifact. Only up to nine uniquely owned reservations,
their original allowance increment and new private receipts may be added.

The frozen future reservation is **USD0.0646010**. If all nine calls reserve once,
the original allowance becomes **480 / USD7.3363205**, and combined triage
reservations become **USD0.1240139**, within the existing USD0.20 test cap and
USD10 total allowance. These are conservative reservations, not invoices.
Earlier failed native usage remains unknown and is never refunded or assumed zero.

## Result assessment

Publish a separate report after execution. Check exact receipt fingerprints and
independently read every known facet's selected demand chunk against the selected
operation. Keep mechanical provenance, semantic relevance and cost accounting
separate. In particular, evaluate timestamp/external anchoring, insertion/help
search, narrow mean/compression/traversal value, wrapper abstention, CI/runtime
claims and incomplete demand against the predeclared controls. Do not repair raw
relations, infer held-out accuracy or promote a candidate or prompt to production.
