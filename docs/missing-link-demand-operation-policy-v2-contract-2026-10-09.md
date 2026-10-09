# Demand-operation policy revision 2 contract

This contract is recorded before implementing revision 2 or observing any output
from it. Base main is `6dbafb095c885fbea8f8050baf5759338ce0650e` (PR95), whose
tree matches reviewed `9b4632e533bfe9cc4aefe3054fccb78d455159e1`; scoped review
is clean and all four CI jobs passed. The [completed retained-control run](missing-link-demand-operation-native-results-2026-10-09.md)
remains consumed and immutable. Its findings motivate a bounded instruction
revision, not reference correction, output repair or a claim of model improvement.

## Isolated instruction successor

Add a separate opt-in `scripts/missing_link_demand_operation_policy_v2.py`.
Keep the original policy, review helper, executor, run adapter, authored tests,
protocols, frozen bodies, references and sealed evidence unchanged. Production
imports, prompts, schema, normalization, ranking, acquisition and UI are unchanged.
The original executor continues to bind revision 1; it must not silently dispatch
revision 2. No provider execution, credential lookup or real reservation belongs
to this correction phase.

Reuse the original packet/context/schema and mechanical reader directly. Only
revision 2 instructions and their complete-envelope fingerprint/bound change.
Input keys, opaque IDs, exact spans/coverage, schema enums, five fields, citation
scope, array/text/UTF-8 limits, review format and false semantic/qualification
flags remain compatible. The new builder must enforce the same 180,000-byte
complete-envelope limit including its own instructions. Neither reader may
classify semantics, rewrite a field or hide an unsupported prediction.

## Semantic instructions to revise

| Boundary | Revision 2 instruction |
| --- | --- |
| Operation versus vocabulary | Compare the demanded effect on the relevant values/domain and essential control/protocol behavior, not shared words or an incidental primitive inside a broader task. Explain this comparison in the relation reason. |
| Operation versus mechanism | Changing how an operation is implemented does not make its demanded effect incidental. Reusing an existing implementation can still directly satisfy a requested operation; it does not establish external-source adoption or fit. |
| Partial known field | Retain a stated local behavioral requirement even if a complete schema/return format is absent. Unknown context must be described without negating that known part. Output includes preservation/behavior, not only a return-value schema. |
| Reported runtime | Explicit declared target languages/platforms or reported tool versions can be described without proof of execution. Keep intended/reported status clear; infer no deployment, compatibility or adoption. |
| Open owner choice | The question is stated demand; proposed conditional outcomes are not a selected output contract. Leave unsettled output/overall acceptance unknown while retaining explicit local consistency conditions. |
| Explicit constraint | Only root-stated requirements/conditions belong here. Query interpretations are relation diagnostics. Retain relevant behavior and delivery/documentation/privacy/evidence requirements, combining related requirements within the existing twelve-item bound. |
| Identifier fidelity | Prefer behavioral paraphrase. If an exact identifier/example is included, preserve its spelling from cited text. If examples conflict, describe the known relation and record the discrepancy instead of repairing or combining identifiers. |
| Context gaps | Preserve coverage and unknown discussion/references/actionability/source fit/novelty/adoption explicitly, combining related gaps within twelve. A gap must not erase local facts or recast a learning request as absence of demand. |

These are general directions. Do not insert retained control IDs, frozen reference
cards, expected labels, private excerpts or per-case answers into instructions.
No lexical label lookup, source-domain allowlist, URI parser or semantic rejection
heuristic is introduced. Existing mechanically valid misleading cards remain
possible; instruction adherence requires separately retained model outputs and
independent reading to evaluate.

## Offline verification and subsequent boundary

Use authored synthetic packets/cards only for new committed controls. Verify new
instruction selection with unchanged contexts/schema, exact Responses encoding,
schema naming, input immutability, reference contamination rejection and new
complete-envelope bounds. Check unchanged mechanical preservation of partial
known fields, pending choices, unsupported cards and per-gap operator annotations.
These tests establish mechanics, not that the model obeys semantic directions.

Before pushing, run focused and full application tests and independently verify
the consumed native and operator-assessment inventories, old code fingerprints,
original exact eleven-row reservation extension and earlier input/reference bytes.
Original allowance remains 566 reservations / USD8.0779182 within USD10; no new
call, acquisition, refund/reset or allowance is authorized.

Obtain scoped review/CI and merge this revision before any separate future
preparation. A paid experiment needs a newly named execution protocol and owned
successor binding the revised code, exact new envelopes/native bodies and original
allowance, plus explicit call authorization. Do not adapt or replay the consumed
revision 1 run, infer permission from an unchanged output schema or promote the
policy into production. Fresh utility/lead qualification remains a separate gate.
