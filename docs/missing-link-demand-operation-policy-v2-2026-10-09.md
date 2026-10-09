# Isolated demand-operation instruction correction

The [revision 2 contract](missing-link-demand-operation-policy-v2-contract-2026-10-09.md)
was committed as `7e966d0afb6d82ba47f0e234e6bc7d401b522f12` before implementation.
It follows merged PR95 (`6dbafb0`) and the independently read
[eleven native results](missing-link-demand-operation-native-results-2026-10-09.md).
The consumed experiment remains immutable; this correction adds no model output.

`scripts/missing_link_demand_operation_policy_v2.py` supplies a separate pure
instruction successor. It imports the original packet/context/schema/reader
directly and implements its own complete-envelope bound. The model-facing
context, original input fingerprint, opaque IDs, exact root spans, coverage,
output schema and mechanical validation/review semantics are unchanged. Only
instructions change. The original policy and paid executor remain bound to
revision 1; neither production nor the historical runner selects this successor.

## Targeted instructions

- Compare demanded effects on values/domain and essential protocol/control flow
  with the query operation. Shared words, a partial primitive or a field name do
  not establish operation relevance. Explain the comparison in the relation reason.
- A changed implementation mechanism, including reuse of an existing parser,
  does not erase the demanded operation; external-source fit/adoption stays unknown.
- Retain a local behavioral output/preservation requirement despite an incomplete
  return schema. Retain explicit intended platforms or reported version context
  without requiring execution, and distinguish them from verified deployment.
- Keep a design question as demand. Conditional alternatives do not establish a
  selected output/overall acceptance contract; explicit consistency conditions
  survive as local constraints while the owner decision remains open.
- Keep root-stated constraints separate from query interpretations. Include relevant
  delivery/documentation/privacy/evidence conditions within the existing bound.
- Prefer behavioral paraphrase. Any literal example must preserve cited identifiers;
  contradictory examples become an explicit gap rather than a repaired/composed URI.
- Explicitly preserve coverage/discussion/references/actionability/fit/novelty/adoption
  unknowns without denying stated facts or excluding concrete learning requests.

No retained case IDs, reference answers or private excerpts enter these
instructions. There is no keyword classifier, URI validator, source allowlist,
schema expansion or semantic rejection rule. The reader deliberately still
retains a mechanically valid wrong relation, identifier or gap for independent
review. This implements an instruction correction; it does not prove the model
will obey it or remove the earlier errors.

## Offline checks and preserved evidence

Eight new authored controls check instruction-only envelope/native serialization,
schema naming, independent complete-envelope limits, exact Unicode/gap context,
reference-contamination rejection, known partial facts and reported target
context, pending owner choice/local consistency, and unchanged unsupported
cards with individual operator gap/claim diagnostics. Synthetic cards are supplied
by the test author, not generated predictions or evidence of improved semantics.
All **62 focused controls** pass, including the original policy and executor
controls. The complete application suite passes **1,481 tests** in 187.858 seconds.

Read-only preflight reproduces all eleven original native bodies and independently
checks the sealed native/assessment anchors, unchanged predictions/review scope,
old code fingerprints, input/reference bytes and exact original eleven-row ledger
extension. On the retained inputs, revision 2 yields identical contexts/schema and
different instruction/native hashes; all revised bodies fit. Maximum envelope is
**26,109 UTF-8 bytes**, maximum native Responses body **28,388 bytes**. Bodies are
encoded with public settings and no provider credential or request. This is a
packing check, not a new frozen execution preparation or model comparison.

| Fingerprint | SHA-256 of UTF-8 with LF |
| --- | --- |
| Revision 2 contract | `9a146f7969a4c767d6b151c603587a60da24ec82bbb7a603e9f469614ab1fdec` |
| Revision 2 module | `4a1692456492b509533a5c5db30f8fb19d8b1f60eb4e4f4abbbfb084859e48bc` |

The original independently anchored 105 native files plus manifest and twelve
operator-assessment files plus manifest remain unchanged, as do all 1,369
protected historical artifacts. Accounting stays **566 reservations / USD8.0779182**
within the original USD10 allowance. No credentials, new reservation/call,
acquisition, source execution, retry, refund, reference correction or output repair.
Software reservations remain separate from native usage and unverified billing.

## Subsequent boundary

Scoped review/CI and merge must precede a separately named execution protocol and
owned successor pinning this revised code and its changed native bodies. Existing
revision 1 preparations/runs cannot be repurposed or replayed. Future execution
also needs separate human call authorization within the original allowance.

Retained controls remain known development examples, not held-out accuracy,
causal improvement or fresh Discover utility. No comparison or quality gain is
reported for revision 2. A qualified grounded external lead still precedes
candidate execution/isolation, UI/key entry and production promotion.
