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
also applies to free-text unknown reasons, whose structured declarations and IDs
must still remain empty. An unseen delegate stays a specific evidence gap:
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
| Experimental layer wording | 7,633 | `64c4635cf9533e5cafb966fe449e8767092d9185273b14cfb1ba70c0d211f0fa` |

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

All 246 focused triage tests and 1,226 complete-suite tests pass. CLI help remains
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
Encoded sizes are 20,397; 23,239; 152,750; 17,098; 46,823; 18,784; 19,858;
96,679; and 27,578 bytes. The largest is below the unchanged 180,000-byte limit.

Accounting remains **507 reservations / USD7.5430970 conservatively reserved**.
That is not an invoice. New model calls and reservations are both zero.

## Next step

Review only the insertion's layer attribution, unknown declaration rules and
delegate/comparison boundaries, together with unchanged guards and offline
encoding. Do not expand the parser, impose known labels or promote this prompt
to production. After review and CI, freeze a separate bounded model-evaluation
protocol before any paid comparison. No automatic rerun of the nine cases is
authorized or implemented here, and prompt wording alone establishes no useful
lead or corrected AI explanation.
