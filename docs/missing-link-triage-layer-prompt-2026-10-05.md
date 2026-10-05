# Experimental source-layer explanations

This revision adds one instruction block to the experimental triage prompt. It
asks for accurate source-layer explanations even when the relation is `unknown`.
It is not connected to production, and no new model response is collected.

PR71 merged as `1d9c879` after a no-findings Codex review of `8aee74f` and four
successful CI jobs. Its [authored controls](missing-link-triage-layer-controls-2026-10-05.md)
remain unchanged, as do the [real Luna results](missing-link-triage-branch-result-2026-10-05.md).

## Bounded instruction change

`scripts/missing_link_triage_layer_prompt.py` wraps the branch prompt rather than
replacing it. Removing the single insertion reproduces the entire predecessor.
Missing or duplicated anchors fail explicitly. Schema and normalizer are the
exact same function objects; no semantic audit, provider or gate changes.

The new paragraph separates the selected factory's callback argument and callable
result from the later arguments/result of its returned callable. That distinction
also applies to free-text unknown reasons. The required `axis` stays populated;
only `comparison_scope`, `operation_layer`, `demand_property`, `operation_property`,
both citation IDs and all slice fields stay empty. An unseen delegate stays a specific evidence gap:
its name cannot establish a return contract, clock policy or external service.

A visible composition can be described without certifying its delegates. Any
known comparison still needs the explicitly requested property at the same layer.
The prompt forbids imposing a direct-call mechanism unless the demand requires
it and does not force a known relation just because a composition is visible.
In particular, the stricter authored fixture does not replace the historical
external-anchoring demand or mandate restoration of its timestamp relation.

| Prompt | Characters | SHA-256 |
| --- | ---: | --- |
| Frozen branch predecessor | 6,684 | `dde418f150a00fd90b30e8a8c5725ceb91f262a60e82942f8d7737252ceaa1d7` |
| Initial layer wording before review correction | 7,633 | `64c4635cf9533e5cafb966fe449e8767092d9185273b14cfb1ba70c0d211f0fa` |
| Corrected layer wording preserving axis | 7,740 | `cdc7ecc5c86a84512027ba803b95d5fe44efa887d7fb7b80176e8b901d96e6a0` |

This is our task-specific instruction hypothesis. OpenAI's
[prompt engineering guidance](https://developers.openai.com/api/docs/guides/prompt-engineering)
supports explicit task instructions and evaluating their effect. The
[model-family guide](https://developers.openai.com/api/docs/guides/latest-model#prompting-best-practices)
also says its examples need evaluation on the chosen model and workload.
Neither source validates our case labels or proves an improvement on Luna.
The intended model remains `gpt-6-luna`; no model migration is made.

## Offline checks and preservation

The test file reuses 16 authored layer/mechanism controls and adds eight checks
for frozen predecessor text, the sole insertion, anchor drift, instruction bounds,
unchanged delegates/guards, distinct factory/method layers, import without IO and
dummy encoding for both API formats. Instruction-presence checks are not model
compliance tests. Replayed controls still document that a false unknown reason
passes the existing relation audit: this PR does not add a truth classifier.

Before review correction, all 246 focused triage tests and 1,226 complete-suite tests pass. CLI help remains
available. No acquired or generated implementation is executed by the new tests;
only authored inert fixtures run.

The private read-only preservation check protects 634 earlier artifacts, all
twelve real table hashes, every allowance/reservation row and frozen executable
fingerprints. It replays nine saved cards unchanged: seven known facets,
29 abstentions and the mean slice survive, with context required and no selection
or qualification change. This is preservation, not retrospective regrading.

Nine original contexts are encoded locally with an explicit credential-free
loopback provider configuration: Responses, streaming, strict schema, medium
reasoning, 6,000 output-token limit and 180,000 request-byte limit. Only the task
prompt changes in those payloads. No HTTP request, environment credential lookup,
job or reservation is made. Private outputs stay separately under
`data/missing-link-triage-layer-prompt-2026-10-05/` and are not committed.
Initial encoded sizes are 20,397; 23,239; 152,750; 17,098; 46,823; 18,784; 19,858;
96,679; and 27,578 bytes. The largest is below the unchanged 180,000-byte limit.

Accounting remains **507 reservations / USD7.5430970 conservatively reserved**.
That is not an invoice. New model calls and reservations are both zero.

## Review correction

Codex found one relevant P2 on `bd8aec3`: the insertion's blanket instruction to
empty structured declarations contradicted the schema's nonempty facet `axis`
and the retained instructions. The corrected insertion explicitly preserves
`axis` and enumerates only the fields to empty. It does not change the schema or
normalizer. A new authored regression checks all four fixed axis enums, valid
unknown normalization and rejection of an empty axis, alongside the wording.
These checks establish contract consistency, not AI compliance or semantic truth.

After the fix, 247 focused and 1,227 complete-suite tests pass. A separately owned
check preserves 637 prior artifacts, all twelve tables and unchanged accounting;
the nine saved cards and mean slice replay unchanged. The earlier private
preservation outputs and their initial prompt/encoding records are retained,
not overwritten. The corrected dummy encoding records are stored separately in
`data/missing-link-triage-layer-axis-fix-2026-10-05/`. No model call is made.
Corrected request sizes are 20,506; 23,348; 152,859; 17,207; 46,932; 18,893;
19,967; 96,788; and 27,687 bytes, all below the unchanged 180,000-byte limit.

## Next step

Reconfirm only the corrected unknown declaration rule, then complete CI before
merging. Review only the insertion's layer attribution, unknown declaration rules and
delegate/comparison boundaries, together with unchanged guards and offline
encoding. Do not expand the parser, impose known labels or promote this prompt
to production. After review and CI, freeze a separate bounded model-evaluation
protocol before any paid comparison. No automatic rerun of the nine cases is
authorized or implemented here, and prompt wording alone establishes no useful
lead or corrected AI explanation.
