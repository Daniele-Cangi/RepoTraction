# Offline factory layer and visible mechanism controls

Sixteen authored controls capture the remaining limits in the
[Luna branch comparison](missing-link-triage-branch-result-2026-10-05.md): an
abstention explanation confuses a factory with its returned wrapper, and a
previously useful timestamp mechanism contrast is omitted. **This is an offline
regression suite, not a model retest, prompt correction or production fix.**

Only tests and documentation change. The prompt, schema, normalizer, semantic
audit, provider, selection and qualification stay unchanged. Historical responses
and reviews are preserved, including the explanation defect. No AI call is made.

## Factory and returned callable

The tests cite and execute three small Python functions written in the test file.
`make_copy_guard(copy_func)` returns `wrapper(src, dst, newer=False)` without
calling the copy delegate. Its keyword-only flag models a branch decision, not
real filesystem timestamps or copy safety. No acquired repository function or
generated code is executed and no real file operation is performed.

| Layer | Positive authored evidence | Unsupported inference |
| --- | --- | --- |
| Selected factory | Its signature takes `copy_func`; its own return is a callable. | `src`/`dst` or the copy result are the factory's arguments/result. |
| Returned callable | Its signature takes source/destination plus a branch flag; the explicitly selected skip branch returns `dst` unchanged without invoking the delegate. | This establishes the selected factory's path interface or every branch's output contract. |
| Non-skip delegate | The wrapper returns the delegate's result. | The result is a particular proof, dictionary or path without the delegate contract. |

Independent signature and inert-callback witnesses support explicit reviewer
labels. False layer declarations can still pass exact-citation normalization;
the existing audit reports the independently supplied `unresolved_interface_layer`
basis for known claims. Neither label shape nor source quotation certifies truth.

The unknown-explanation control deliberately preserves a false claim that the
selected factory takes `src` and `dst`. Its signature contradicts that explanation,
but the relation audit still reports no issue because the relation is unknown.
This records a limitation, not a passing quality assessment: there is no automatic
unknown-reason classifier, correction, rejection credit or accuracy score.

## Visible mechanism and hidden delegates

`assemble_envelope` visibly obtains a timestamp callback result, builds a delimited
payload and appends a signature callback result. Inert authored callbacks witness
that composition and its dependence on their results. Different marker strings
do not simulate real clocks, external services, cryptographic proofs or network
policies. `forward_proof` supplies the paired pure-delegation case.

The authored demand for the positive contrast **explicitly requires direct steps
in the requested entrypoint**: invoke a proof command and publish its result.
That supports comparison of the visible local composition at the stated layer,
while preserving unknown helper internals and full external-anchoring behavior.
An ordinary requirement to produce an external proof does not automatically impose
that direct call shape. These stricter authored words are not substituted for the
historical issue and do not compel its old timestamp relation to return.

The negative controls reject independently reviewed claims that a timestamp name
proves a local clock or absence of external calls, that envelope assembly alone
establishes an external-proof slice, or that a forwarding helper's name establishes
its output contract. A bounded mechanism comparison stays an outcome comparison,
not a runtime ban, whole-workflow rejection or full proof of incompatibility.

An unchanged unknown response remains unscored even where the authored request
supports a local contrast. No reviewer label forces a known relation. The full
existing suite continues to cover genuine delegate gaps, factory/method layers,
branch returns, grep local contrasts and the bounded mean slice.

## Verification and preservation

The new file is `tests/test_missing_link_triage_layer_mechanisms.py`.
All 16 new controls, 222 focused triage tests and 1,202 complete-suite tests pass.
CLI help remains available. Test counts establish reproducible software behavior,
not that Luna has corrected its explanations or regained a useful comparison.

A separate read-only check preserves all twelve real table hashes, 631 earlier
artifact hashes, every reservation and allowance row, and frozen executable-code
fingerprints. The original allowance remains **507 reservations / USD7.5430970
conservatively reserved**, not invoiced spending. No provider is instantiated,
credential loaded, job started or model called by that check.

Post-test replay reproduces the same nine saved cards, seven known facets,
29 abstentions and mean slice. It does not regrade or repair their semantics.
Private preservation outputs are kept separately under
`data/missing-link-triage-layer-controls-2026-10-05/`; no account data is committed.

## Next bounded decision

PR70 merged as `e5ac980` with four green CI jobs. The paid-result report remains
unchanged. These controls define the source-layer and delegate boundaries for any
later guidance change; they do not themselves justify production promotion,
parser expansion, another paid comparison or forced timestamp/positive labels.

Next, review only the source-reading controls, then consider minimal experimental
guidance for layer-accurate explanations, including unknown reasons. Retain the
current prompt and all history. Any later model-quality measurement needs a
separately frozen protocol and must not be inferred from these authored labels
or an automatically repeated run of the same nine cases.
