# Prospective triage driver safeguards

The six-case [source protocol](missing-link-triage-prospective-protocol-2026-10-06.md)
now has experimental request, execution and accounting controls, exercised without
a model call. Source preparation PR80 merged as `bf6610d` after Codex reviewed
`72555ad` without findings and all four Windows/Linux CI jobs passed.

The new driver gates still need their own scoped review and merge. **Do not execute
the initial offline driver**: its manifest is bound to the source-preparation
merge, not the future reviewed driver merge. Preserve that folder unchanged and
prepare a separately owned successor against the reviewed main revision before
any real invocation. Offline simulation is neither API acceptance nor source
accuracy of an AI response.

## Exact request preflight

`scripts/missing_link_triage_prospective_driver.py` is opt-in experimental code;
production imports and CLI behavior remain unchanged. Import performs no IO,
credential lookup, provider construction or execution. The source helper,
original contract literals, selected bodies, separate operator references,
prompt and declaration schema remain unchanged.

Provider readiness is required before encoding, acquiring the lease or consuming
the exclusive start marker. Preflight compares all public configuration fields
without reading or serializing the credential, reproduces six ordered cases and
checks each exact payload, body byte count/hash, scoped schema hash, job ID and
reservation against the private manifest. A mismatch stops before payment.

The owned caller also reproduces full cases from acquired source records and
checks original source/reference/payload hashes and canonical executable
fingerprints. It must verify the reviewed successor revision on freshly fetched
main, acquire the existing worker lease, repeat preflight and force the GitHub
identity check before consuming a one-use marker. Repeat the fingerprint and
exact-prior-prefix checks before and after each case's forced identity check.
The merged-revision gate is authorization for the reviewed code, not a reason to
reuse the unreviewed initial manifest or repeat an old paid driver.

## Execution and private retention

Each ordered case gets one fresh budget object, one owned job ID and one attempt.
The existing receipt reader sends the unchanged Luna Responses request and saves
the entire decoded terminal before parsing or acceptance. Native usage, including
cache details, stays in the terminal; missing usage is not manufactured.
Journal versions of in-flight job receipts and final terminal/result files are
written exclusively in the caller's private directory. Persist copies of job
state, never mutate the original raw response or acquired code.

Transport, missing/inconsistent terminal, incomplete/refused response, generic
receipt-shape failure, account/budget failure and private persistence failure stop
the cohort without retry. Only the explicit final declaration-branch/provenance
normalizer is candidate-local: keep its completed parsed card and validation
error, then allow the next frozen case once. Result storage and post-case integrity
must succeed before continuing. No labels, positive counts or slice relations are
forced; every accepted comparison/slice remains independently unverified.

## Ordered reservation accounting

Use the existing atomic `Store.reserve_ai_allowance` under the original
`missing-link-verification-2026-09-30` allowance. Keep the user's USD10 total,
USD0.10 segment and cumulative USD7.7197550 ceiling. Six proposed reservations
still total USD0.0341576, with USD0.02 maximum per case. There is no new allowance,
refund, reservation replacement or alternate model.

The post-payment reader must read actual history without the obsolete assertion
of 517 rows. The new pure increment validator compares full historical rows,
permits only the ordered prefix of the six exact owned IDs/costs and checks the
matching count/aggregate/original-allowance increment. Between completed cases
require an exact count. If an attempt stops, allow only that attempt's possible
additional row, not arbitrary future cases. Foreign, duplicated, reordered,
missing or excess rows stop execution. Unrelated allowance balances remain exact,
including sub-tolerance changes. With zero added rows, accounting hashes must
also remain identical.

Retain the lease-release/final-audit behavior of the reviewed one-shot gate even
on failure. Preserve prior artifacts, all previous reservations, non-accounting
tables, unrelated allowances and source/code fingerprints. The initial owned
baseline adds the sixteen source-preparation files to the 720 earlier protected
artifacts, for 736 protected files. A successor must additionally preserve the
initial offline manifest, simulation and post-test audit rather than overwrite
or re-prepare that directory.

## Offline verification

Fifteen new authored tests cover exact prefixes from zero through six, row/order/
cost drift, ceilings, unrelated balances, provider readiness, frozen payloads,
import safety and six mocked transport calls. They also cover preserved final
branch rejection followed by one next attempt, and stop behavior for preflight,
identity, atomic reservation, transport, refusal and private storage failures.
The unchanged reviewed one-shot tests cover marker exclusivity, main/lease gates
and final audit after lease release, including failures.

All **356 focused and 1,336 full-suite tests pass**; CLI help and diff checks are
unchanged. The owned offline simulation reproduces all six actual frozen payload
hashes and retains six authored terminal envelopes. Case 2 deliberately contains
an invalid unknown declaration: its raw card is kept, the final branch validator
rejects it, and case 3 proceeds once. There are seven forced identity checks in
the simulation: one at the cohort gate and one per case. Memory-only reservation
increments reproduce all six exact amounts. These are authored mocks, not Luna
responses, operator semantic judgments or real accounting writes.

Post-test read-only checks reproduce all 736 protected artifacts, twelve tables,
517 reservation rows and unchanged USD7.6197550 reserved balance. No live start
marker, model call or new reservation was made. The initial private folder is
`data/missing-link-triage-prospective-owned-driver-2026-10-06/`, excluded from Git.

After scoped Codex review, green CI and merge, freeze/replay the separately owned
reviewed-main successor before the six real attempts. Then independently read
every returned facet against the already frozen source references, separating
local validity, explanation accuracy, useful partial contributions and the
wrong-candidate control. Production promotion, autonomous Discover evaluation,
candidate isolation and UI/key-entry work remain separate later gates.
