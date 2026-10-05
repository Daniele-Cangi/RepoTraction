# Native probe execution safeguards

This prepares the owned driver required by the
[native schema protocol](missing-link-native-schema-protocol-2026-10-05.md).
It adds request, marker, lease and accounting safeguards without changing the
reviewed schema, prompt, fixture or provider transport. **No real request or
reservation is made during this preparation.** Native API acceptance and model
quality remain unverified.

PR77 has a no-findings Codex review of `c15bdd2` and four green CI jobs. Its merge
`e8bf3c2` first landed on the PR76 branch, with a file tree identical to the
reviewed PR77 head. After four green CI jobs and operator authorization, PR76
merged onto main as `3663652` on October 5. The driver safeguards remain separate.
The driver must not run until the reviewed safeguards revision, including its
schema/protocol ancestors, is reachable from freshly fetched main. An operator
must also confirm the relevant Codex review and CI before invoking the paid entrypoint.

## Public safeguards and owned adapter

`scripts/missing_link_triage_native_driver.py` has no IO or provider construction
on import. `verify_request` first requires the provider's own `configured=True`
readiness signal, so invalid remote authorization or other configuration errors
stop before encoding or consuming the marker. It raises a fixed diagnostic,
without retaining the provider's error text or inspecting credentials. It then
compares only whitelisted non-secret configuration,
the authored case, exact serialized payload, prompt/schema/body fingerprints,
request byte count and prepared reservation. The credential is never part of a
fingerprint or report. Original source fingerprints are checked by the owned
adapter, not inferred from a successful payload comparison.

`run_once` performs frozen preflight and a main-ancestry check before taking the
lease. After acquisition it repeats preflight, forces account verification,
exclusively creates the start marker and invokes the one-request probe. It never
removes or overwrites the marker. Lease release is followed by integrity checking,
even when execution or release raises an error. A missing main revision, busy
lease or preflight/account failure stops before a model attempt. A duplicate
marker prevents another execution; a failed model attempt consumes the marker.

The separately owned adapter under
`data/missing-link-triage-native-driver-2026-10-05/` supplies the real read-only
history, canonical-LF executable fingerprints, fresh-main Git check, existing
worker lease, GitHub CLI identity `Daniele-Cangi`, private exclusive receipts and
the existing Store atomic reservation callback. Its prepared manifest binds the
required main commit to the checked-out committed source revision. Preparation,
verification and simulation use an explicit dummy encoder, not real provider
configuration or credential lookup. Only an explicitly invoked future `run`
loads the existing key into memory; this turn does not invoke it.

There are two forced identity checks in the complete path: before consuming the
marker and again at the probe boundary. Neither is a model call. Full terminal
event capture and final experimental branch/provenance/bounds normalization
remain the existing reviewed contracts. Raw output is retained before local
rejection, without retry, repair, qualification or selection changes.

## Exact budget and post-attempt verification

The request stays **21,913 bytes**, with the original protocol's body and schema
hashes. Its configured-price reservation stays **USD0.0053961**, not an invoice.
The original allowance remains `missing-link-verification-2026-09-30`, and the
atomic cumulative segment ceiling stays **USD7.6343589** under the USD10 total.
No allowance is reset, refunded or replaced; no older unused segment is borrowed.

`verify_increment` uses the existing reader's full ordered reservation and
allowance rows. It permits no new row, or one row for the exact owned job and
amount, with the corresponding original-allowance increment. It rejects prior
row changes, foreign jobs/allowances, duplicate reservations, wrong amounts,
incorrect counts, aggregate drift, other allowance changes, active jobs,
artifact changes and non-accounting table changes. With no owned increment,
even accounting table hashes must remain identical. The real reservation callback
enforces the cap atomically before outbound traffic; this post-check does not
replace that transaction.

Unrelated allowance balances must compare exactly. The numeric tolerance applies
only to the declared owned allowance increment, not to foreign balances; changes
of even USD0.000000005 to another allowance are rejected.

The post-attempt reader uses the original low-level snapshot reader, not obsolete
pre-payment assertions requiring 516 rows. That permits the one declared increment
without weakening protection of old history. Only owned in-flight job persistence
can be updated. Start markers, terminal events, results, diagnostics and integrity
snapshots use exclusive creation. Diagnostics retain exception type/status only,
not credential values or raw error messages. Unknown usage remains unknown.

## Offline checks and next decision

Thirteen authored controls test exact configuration/request reproduction,
credential exclusion, drift rejection, zero/one allowed synthetic increment,
historical/accounting mutations, marker replay, main/lease/account barriers,
failure retention, release/integrity ordering and import safety. Real database
rows are never edited by these controls; filesystem writes use temporary markers.
All 320 focused triage tests and 1,300 full-suite tests pass; CLI help is unchanged.

The owned offline simulation sent one exact frozen body to a mocked stream,
retained the complete authored terminal envelope and parsed card, recorded
USD0.0053961 only in memory and exercised both forced identity checks. Its marker was temporary,
not the live start marker. The read-only post-test check verified **703 historical
artifact hashes** and all twelve real tables; the actual allowance stays **516
reservations / USD7.6143589 reserved** with no new model call or reservation.

Request review only for concrete regressions in these gates and the adapter's
documented responsibilities. After review, green CI, merge onto main and explicit
invocation, attempt the single request and publish its mechanical outcome. Do not
claim schema acceptance from mocks, force a known/slice label, rerun the nine-case
development cohort, promote the prompt or infer autonomous usefulness. A bare
HTTP status is not proof of the specific cause of request rejection.

## Review corrections and frozen manifests

Codex identified two concrete violations on `f69b746`: invalid provider readiness
could consume the sole marker, and the balance tolerance could admit tiny changes
to unrelated allowances. Three additional regressions reproduce both failures
and check that readiness rejection does not encode or echo raw provider errors.
The fixes do not change payload, schema, prompt, fixture, pricing or reservation.
All 323 focused and 1,303 full-suite tests pass, including the sixteen driver
controls. CLI help is unchanged; no paid call or new reservation was made.

The initial offline simulation above predates these fixes. Its owned artifacts and
prepared manifest remain immutable; the changed executable fingerprints make that
manifest reject the corrected driver. After review and green CI, prepare and
simulate a separately owned successor manifest bound to the reviewed corrected
source before the one paid attempt. Do not overwrite the old manifest, bypass its
checks or reuse its earlier mocked success as validation of the new revision.
