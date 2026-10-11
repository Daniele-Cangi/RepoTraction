# Acceptance and direct alternatives before model calls or donor search

These are assessor judgments from the fixed demand/target context, not model
inputs, independent human ground truth, or measured acceptance results. No donor
search was performed. A scan of earlier retained documentation found no occurrence
of either fresh issue URL. Both discussions already name possible source projects;
selecting those projects later cannot count as an unexpected package discovery.

## Historical controls

Retain the #123 pre-selection notes and outcomes without edits. audio-feeder #81
at `2a5b58dab43a5195ccc964916bbddaf7f8727c1d`: normalize case/diacritics, preserve
original display and tie behavior. Natural sorting is also requested; its exact
algorithm is unspecified, and the #122 native direct baseline did not establish
numeric natural-sort semantics. Do not infer complete satisfaction from it.

tunesynctool #21 at `b705691ba7d02d34ff3b6423ca03fcfca1514994`: exact ISRC lookup,
no MusicBrainz traffic for suitably tagged matches, maintainability/specification
constraints, preserved mapping/async behavior. The existing-client direct option
remains conditional on actual server/protocol support. A target-only read cannot
by itself establish current external specification or server behavior.

## Fresh 1: Agentic-AI-Pipeline #23

The request offers a specific RunLedger integration: optional deterministic CI
record/replay, no live tool calls during replay, mismatch failure, a small suite/
case/schema/cassette and baseline, with optional workflow. The owner accepts the
offer and identifies `src/agentic_ai/graph.py:run_chat`; the requester subsequently
links PR #24. Assessor lookup establishes PR #24 is merged. The ordinary product
receives the acquired discussion/timeline, not this assessor's PR lookup as an
injected conclusion; therefore any unresolved product status must be interpreted
against its actual context.

Target revision `443716a7d227b0d36cd73b82f134ccf00aa34185`. Static inspection of
`src/agentic_ai/graph.py` confirms an async streaming chat entrypoint delegating to
the graph and tool registry. The acquired tree includes
`evals/runledger/agent/agent.py` and `evals/runledger/INTEGRATION.md`. This is not
proof that replay is deterministic or that all requested behavior passes.

Strongest direct alternative: inspect/use the existing merged integration before
proposing another package. No new unresolved need has been established. A claim
of useful progress would have to identify a genuine residual failure and satisfy
the original replay/no-network/mismatch contract in the native target; merely
rediscovering RunLedger or repeating the accepted adapter is not autonomous reuse.
Never run the real chat graph with external tools/credentials in this experiment.

## Fresh 2: PINA #761

The request asks for named tensor contraction/rearrangement while preserving
LabelTensor semantics. Later discussion corrects the root example: a list of
labels describes coordinates on the last axis; named axes require structured
metadata. The original list `['batch', 'width', 'height']` therefore cannot be
silently treated as three axis names. Later proposals mention einops, NamedTensor
and functorch dimension objects; these are prior context, not novel discoveries.
A collaborator declines dependence on the proposed feature until stable and asks
whether existing label extraction remains intact. Compilation/autograd problems
are linked as motivation, not proof that a named-contraction API fixes them.
The historical comment's account of upstream release availability is not a current
verified fact. The stakeholder's stated stability preference still matters.

Target revision `0cd8afb51beae9883d38705ddb1997d37ae75b44`. The public
`pina/label_tensor.py` re-exports `pina._src.core.label_tensor.LabelTensor`.
Static inspection of that implementation establishes a torch.Tensor subclass,
last-axis list labels, per-axis `name`/`dof` metadata, dimension-size/uniqueness
validation, and extraction operations. The manifest already depends on torch.
These are static observations, not executed semantics.

Independent acceptance:

1. Named contractions/rearrangements compute the same values/shapes as the direct
   torch operation for the accepted expression, using actual axis metadata.
2. Preserve surviving axis names/coordinate labels in output order; remove metadata
   for contracted axes. Preserve the existing last-axis list-label convention.
3. Keep existing extraction/indexing and gradients working in native PINA tests.
   Independence/aliasing expectations and multi-input label conflicts remain
   unsettled until grounded in target semantics; do not invent acceptance policy.
4. Respect the stated stable-dependency preference. Do not silently substitute a
   rejected experimental representation. Do not claim to fix compilation/autograd
   without reproducing and checking that separate target failure.

Strongest direct alternative: a bounded parser mapping named axes to ordinary
torch.einsum plus target-owned metadata validation and reconstruction, as suggested
in the original request. Compare against an existing dependency/implementation if
the target inspection establishes one. This direct option is unimplemented here
and is not presumed optimal. A candidate must demonstrate a concrete reduction
in missing algorithmic behavior or maintenance burden, or improved correctness,
without outsourcing the target's metadata semantics to an unrelated API.

The cohort can fail because neither fresh case establishes an advantageous new
opportunity. Keep that outcome; no substitution, broader pool or changed success
criterion. More informative abstention is diagnostic progress only.
