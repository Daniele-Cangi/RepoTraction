# Offline controls for slice declarations and explanation limits

Fifteen authored tests isolate the failures observed in the
[Luna layer comparison](missing-link-triage-layer-result-2026-10-05.md).
They confirm that the existing local validator rejects missing slice properties
without repairing the response. They also document that mechanical acceptance
does not detect false branch/delegate explanations, especially for unknown
relations. **No prompt, schema, normalizer or production behavior is changed.**
These are contract controls, not evidence that Luna has improved.

The report in PR74 has a no-findings Codex review of `267f719` and four successful
CI jobs. These controls form a separate follow-up to that report. Old reports,
responses, usage records and the experimental paid driver remain immutable.

## Known slice declarations

`tests/test_missing_link_triage_layer_result_controls.py` uses a small arithmetic
average function written for these tests. Its demand, selected body, span IDs
and descriptions are synthetic; no retained response is made into a gold label.
Only authored Python fixtures and inert callbacks execute.

The fully populated average slice remains a partial hint with context required,
not a qualified connection. A known relation must provide both `demand_property`
and `operation_property`, in addition to scope, layer and citations. Only `slice`
requires the three slice descriptions; `aligned` and `different` require them
to be empty. An empty property string currently satisfies the provider shape but
fails local normalization. A helpful reason or slice description cannot substitute
for a missing property.

The controls cover either/both empty properties, whitespace including Unicode,
omitted keys, and both 400/401-character boundaries. The same property requirement
also applies to aligned/different relations. An invalid slice rejects its entire
card without salvaging another known facet or mutating the original. An unknown
facet instead keeps its axis and must already have empty declarations; populated
declarations reject the response without mutation. It gets no slice credit.
Arbitrary 400-character text passing the mechanical limit is not source truth.

These outcomes preserve the real mean failure: its saved empty properties and
validation error are not filled, retried or upgraded into an accepted slice.

## Conditional and delegate explanations

The tests reuse the existing authored `encode_or_pass_through` fixture. A string
witness produces encoded bytes, while a mixed collection or `None` is returned
unchanged. A string-input-only property comparison is supported by that branch;
an unconditional bytes claim is not. A mechanically valid known claim is reported
as unsupported only when an independent fixture review supplies that assessment.
The audit does not infer semantic truth from source or a model's own reason.

Paired unknown reasons contain the same abstention structure: one incorrectly
claims universal bytes returns, and the other describes conditional encoding and
non-string pass-through. Both normalize unchanged and receive no relation-audit
issue. The witness explains why the first reason is wrong, but the unchanged audit
does not classify unknown-reason truth. Its no-issues result is not a quality score
or evidence that the explanation is correct.

An authored forwarder calls `serialize`, then `encode`, and returns the second
callback's result with a bytes return annotation. Inert alternate callbacks return
text or a list marker from the same body. Their names and annotation do not prove
actual bytes results, serialization semantics or reversibility. Comparing an
explicitly declared bytes contract can be supported without certifying observed
returns. A positively asserted unseen callback result needs independent review.
The analogous paired unknown explanations again remain unchanged, not graded.

## Preservation and verification

All fifteen new controls, 280 focused triage tests and 1,260 full-suite tests pass;
CLI help is unchanged. None of these new controls configures a provider, reads
credentials, sends a model request or executes acquired/model-proposed candidate
code. A separate run of the fifteen controls also passes with provider construction,
environment lookup, network, subprocess, SQLite and thread startup blocked.
The older test suite may use its existing mocked providers; that is not paid execution.

A separately owned read-only check under
`data/missing-link-triage-layer-result-controls-2026-10-05/` preserves **691
historical artifact hashes**, all twelve real table hashes and all allowance/
reservation rows. That includes the preceding 640 artifacts plus all 51 files
of the completed layer comparison. Frozen executable fingerprints stay unchanged.
No provider instance or credential lookup is required by the check.

The nine saved cards replay exactly: eight locally accepted cards, the rejected
mean card, nine raw non-unknown facets/27 abstentions and eight accepted
non-unknown facets/24 abstentions. No semantic-verification flag, qualification
or selection change is made. The original allowance stays at **516 reservations /
USD7.6143589 reserved**, with no new model call or reservation.

## Next bounded change

The local guards work; the provider shape still permits empty property strings
for a known relation, and explanation truth remains a separate source-reading
problem. Next consider a separate experimental schema change that distinguishes
unknown empty declarations from required known properties, without weakening
normalization or treating populated strings as semantic proof. Verify that change
offline before defining any new paid protocol. Do not patch historical cards,
force timestamp labels, promote the prompt or repeat the nine-case cohort.

Branch/delegate explanations still require independent review. These controls
do not add a semantic classifier, parser extension, autonomous usefulness claim,
ranking change, isolation step or UI/key-entry work.
