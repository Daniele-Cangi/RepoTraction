# Luna native schema acceptance protocol

This prepares a single request to establish whether OpenAI accepts the experimental
[declaration schema](missing-link-triage-declaration-schema-2026-10-05.md) and
returns a completed object that also passes our unchanged local guards. **Preparation
and mocked execution are offline; no model call or reservation is made.**
It is a mechanical provider-contract test, not a new quality evaluation or Discover
run. Its configured-price reservation is USD0.0053961 within a USD0.02 segment.

PR76 has a no-findings Codex review of `352f9ed` and four successful CI jobs.
It is ready for merge; this follow-up is stacked on that reviewed branch. Actual
execution waits for schema/protocol merge, narrow Codex review, green CI and a
separately prepared owned one-shot driver. The preparation script has no paid
entrypoint; caller safety checks below are requirements, not claimed implemented
controls in that script.

## Frozen request

The only case is authored in `scripts/missing_link_triage_native_probe.py`:
an explicit numeric-summary demand asks for sum and count, and the supplied Python
body returns `sum(values)`. Full original demand text and the whole owned body are
provided with scoped citations. Acquisition is marked incomplete because acceptance
and adoption context are absent. The body is data; it is not executed. No external
issue, acquired code, model card, reviewer label or expected relation is imported.

This is not a repeat of the nine familiar development contexts and is not a
held-out usefulness benchmark. Do not force a known or slice label: all-unknown
output is permitted if mechanically valid. A single response cannot establish
coverage of every schema branch, accuracy or usefulness.

Keep the exact 7,740-character layer prompt, SHA256
`cdc7ecc5c86a84512027ba803b95d5fe44efa887d7fb7b80176e8b901d96e6a0`, and the
reviewed declaration schema. Use `gpt-6-luna` at `https://api.openai.com/v1/responses`,
Responses streaming, medium reasoning, strict JSON Schema, 6,000 maximum output
tokens, 180,000 maximum request bytes and `store=false`. No tools, alternate model,
prompt revision, cache-saving assumption, regional routing or fast mode is added.

The [Luna model page](https://developers.openai.com/api/docs/models/gpt-6-luna)
documents streaming and Structured Outputs support, with standard text prices
USD0.10 input / USD0.50 output per million tokens. The
[Structured Outputs guide](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses)
documents nested unions, references and patterns, but also refusal and incomplete
response handling. These documented features do not establish acceptance of our
exact combined schema; that remains the purpose of the future request.

The frozen body is 21,913 UTF-8 bytes with SHA256
`5f66014941c185738c925682b7f5e8b621ca865b2260cec2bba5f88f4a41f0ab`.
The schema's sorted-JSON SHA256 is
`5f6ddcfed82a2b805680c3af4ff5b96e346e61a9395fb94ef39bf0b9b6ecabd6`.
Private owned preparation under
`data/missing-link-triage-native-schema-protocol-2026-10-05/` retains the baseline,
case, payload, non-secret configuration and canonical-LF source fingerprints.
Re-encoding reproduces the exact request. No provider instance or credential
lookup is required for preparation; no key is retained in these artifacts.

## Budget and one attempt

The original allowance `missing-link-verification-2026-09-30` remains **516
reservations / USD7.6143589 reserved**, under the user-authorized USD10 total.
Use the existing estimate: `(request_bytes + 2048) * 0.10 / 1,000,000` plus
`6000 * 0.50 / 1,000,000`, giving USD0.0053961. Enforce an atomic cumulative
segment ceiling of **USD7.6343589**, baseline plus USD0.02. One exact owned
reservation would bring the original allowance to **USD7.6197550**.

This is reservation accounting, not an invoice or guaranteed billed-cost ceiling.
No failed or unknown-usage reservation is refunded or reset. Do not borrow unused
headroom from older segments or create another allowance. Attempt this case once:
no network retry, alternate schema, fallback format, repaired response or adaptive
label selection. If a failure occurs, preserve it and report the limit before
proposing another protocol.

## Required caller safety and preservation

The public probe builds the fixed case, forces identity verification and makes at
most one request through the existing receipt reader and Budget. It has no CLI or
production caller and does not configure a real provider or acquire a lease on
import. Before invoking it, the future owned driver must verify source/configuration/
case/schema/request fingerprints and the unchanged baseline; obtain the existing
worker lease; verify fresh GitHub CLI identity `Daniele-Cangi`; and exclusively
create a one-shot start marker. That marker must prevent replay even after failure.
The atomic reservation callback must enforce both the original allowance and the
segment ceiling. These responsibilities are not replaced by the probe function.

Save the full decoded terminal event privately before parsing, stream closure or
acceptance, including refusal/incomplete content and extra fields. This is not
wire whitespace or earlier stream deltas. Never synthesize missing usage or a
terminal event, and never import receipts into production or public UI data.
Only owned in-flight persistence may change; other receipts, results and start
markers use exclusive creation. The raw parsed card must remain unchanged.

The generic typed reader does not enforce the nested union/ref/pattern constraints.
The probe therefore invokes the experimental final normalizer, then all frozen
provenance, whitespace, length and completeness guards. A final local error is
recorded with its original raw card, without salvage; there is no second case.
Transport, account, budget, receipt-storage, stream-close, missing/inconsistent
terminal, refusal/incomplete and generic-shape errors stop execution without retry.

After lease release, permit only one uniquely owned reservation at USD0.0053961
and the corresponding original-allowance increment. Preserve all 516 old rows,
other allowances, the ten non-accounting tables and **697 prior artifact hashes**.
All older predictions, validation errors, reports and executable fingerprints
remain immutable. Use a post-payment check aware of the one permitted increment,
not the obsolete 516-row pre-payment assertion.

## Assessment fixed before execution

Report request/terminal outcome and final mechanical validation separately. A
completed, non-refused object passing both schema branches and frozen guards
establishes acceptance of this exact request/response contract for one observation.
It does not prove every branch was generated or that any reason/property is true.
Passing only the generic reader is not success. Incomplete or refused output is
not a valid card. A bare HTTP 400 does not identify an unsupported schema keyword;
if the frozen transport exposes only a status, report the cause as unestablished.

Known labels, number of properties, slice hints and valid IDs are not a quality
score, independently verified implementation or qualified lead. Selection and
qualification remain unchanged. Keep native usage, configured-price estimates,
unknown usage and reservation totals distinct. No branch/delegate explanation
improvement or autonomous usefulness is inferred from this authored probe.

## Offline checks and next step

Ten authored controls cover one exact mocked request, permissible abstention,
an unverified slice, preserved invalid declarations, identity/budget preflight,
receipt storage, HTTP rejection, incomplete/refused/missing terminal and wrong
shape, fresh full-source fixture data and import safety. They use explicit dummy
loopback configuration and memory-only callbacks, not real credentials or ledger
writes. Historical replay and exact encoding remain unchanged.
All 307 focused triage tests and 1,287 full-suite tests pass; CLI help is unchanged.
A post-test read-only check preserves all twelve real table hashes, 697 earlier
artifacts and the original allowance at 516 rows / USD7.6143589, with no new call
or reservation. Native schema acceptance is still unverified.

Request Codex review only for the one-request/no-retry contract, mandatory final
guards, receipt/accounting boundaries and these stated limits. After merge and
green CI, prepare/review the separately owned one-shot driver before execution.
Do not rerun the familiar nine-case cohort, expand parser completeness, promote
the prompt or move to isolation/UI/key entry from a mechanical acceptance result.
