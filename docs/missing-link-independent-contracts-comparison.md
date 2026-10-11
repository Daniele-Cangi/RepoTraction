# Demand-contract comparison: no useful relation demonstrated

The fixed-pool experiment is now complete within its declared extraction and
representation limits. A separate-context AI reviewer assessed all 12 discussions
before seeing the model proposals, then reviewed those proposals and authored
11 additional cases without candidate source knowledge. Six executions through
the existing WASI runner produced **zero complete behavioral matches** across
87 original-model bindings and 78 independent-challenge bindings. There are no
qualified or integrated connections, and no evidence to promote the opt-in
proposal stage as an improvement in autonomous discovery.

This is a negative result for the fixed experiment, not proof that the sampled
repositories contain no useful code. The review is independent of the proposing
model's context and source matches, but remains an AI judgment rather than human
ground truth. The original [pilot](missing-link-independent-contracts-pilot.md),
its raw responses and all historical fixtures remain unchanged.

## Order and controls

The user explicitly authorized the separate-context reviewer. It received only
the frozen discussion packet and proposals, with instructions to read and save
demand judgments before opening proposals. It used no network, acquired source,
execution results or paid API calls. The demand judgment was frozen first, then
proposal judgments and challenges. These artifacts were committed in `6976dbf`
before any source comparison. One quotation lost Markdown backticks; a separate
errata file corrects that transcription while retaining the original frozen file.

The comparison reused the three pinned source files, 40-function cap, existing
adapters, evaluator and WASI limits. Selection and execution code are unchanged
from `c1d2d67`. Replaying the fixed queries reproduced the original selections
exactly for all three sources: indices **8, 1, 5**. The ordinary candidate limit
was not raised; all-12 interpretation belongs only to the isolated study.

Both cohorts were specified before matching: all four original contracts remain
unchanged, including the rejected threshold policy as a diagnostic; the second
cohort contains only the separately justified reviewer cases for three operations.
These cases are saved under distinct IDs/origin metadata. They do not replace or
repair the model's original examples, and their expected values were not tuned
after inspecting matches. A useful behavioral result would need to survive both
cohorts and the demand/reuse checks. Neither cohort produced a complete match.

## Semantic review

| Proposed suboperation | Finite hypothesis | Remaining demand / utility |
| --- | --- | --- |
| PyBrain batch count | Supported arithmetic, narrow scope | Formula already exists in the discussion's `batches()` implementation; faulty randomization remains uncovered |
| First duplicate cookie value | Supported for simple valid single-name cookies under the printed-string convention | Adoption is contested; broader parsing, compatibility and existing alternatives remain unresolved |
| Threshold-option suggestions | Exact expected arrays not independently supported | Diagnostic need exists, but assignments to maxima, ordering and trigger/interface assumptions need decisions |
| Fully qualified Windows paths | Supported ordinary-path regression examples | The selected operation is reported fixed in Python 3.13+; remaining relative-path questions are different operations |

Thus **3/4 proposals are usable as bounded hypotheses**, not 3/4 useful
opportunities. One requires clarification before it can serve as an independently
grounded demand specification. The reviewer did not fabricate challenge expected
values for that uncertain case. Of the original 11 example/check cases, the model
labels two explicit and nine inferred; this labeling is separate from correctness.
The reviewer supplied 11 new cases for the other three proposals, conditional on
their declared representations and scope.

All eight abstentions were reviewed, including limitations in their explanations.
For example, deep pickling and SIP transactions are real reported engineering
needs despite not fitting this simple JSON interface. The CSL discussion supports
the narrower requirement to allow omission of an embedded item ID even though a
full validator contract is unavailable. In SymPy #4238, tuple unpacking is supplied
and confirmed working: the model overstates how unresolved that construction is.
Several runtime claims are also more uncertain than the visible Python context
warrants. These are semantic limitations, not malformed responses or transport
errors. No binary precision/recall score is inferred from these mixed judgments.

## Actual execution

| Cohort / source | Extracted | Omitted functions | Observed bindings | Complete matches | Runner seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| Original / more-itertools | 40 | 27 | 83 | 0 | 3.405 |
| Original / boltons | 1 | 2 | 4 | 0 | 1.663 |
| Original / NetworkX | 0 | 20 | 0 | 0 | 1.607 |
| Independent cases / more-itertools | 40 | 27 | 75 | 0 | 1.773 |
| Independent cases / boltons | 1 | 2 | 3 | 0 | 1.737 |
| Independent cases / NetworkX | 0 | 20 | 0 | 0 | 1.713 |

All six processes exited successfully. There were zero candidate load errors,
unobserved bindings, output omissions or discarded print characters. A binding is
one arity-compatible function/contract/adapter combination, not an independent
software opportunity. All contracts use positional arguments, so only the existing
identity adapter applies. Functions rejected by arity are not executed bindings.
The evaluator skips checks when initial examples fail; these totals do not mean
every case was evaluated against every function.

For the original cohort, first failures comprise 39 `TypeError`, 28 `ValueError`
and 20 observed-value mismatches. For the independent cohort they comprise 31
`TypeError`, 27 `ValueError`, one `AssertionError` and 19 value mismatches. Exception
type alone does not identify whether a function, argument representation or output
normalization caused failure. In particular, the normalizer excludes arbitrary
iterator objects; such failures cannot establish algorithmic non-applicability.
NetworkX's zero extracted functions establish no negative behavioral evidence at all.

A concrete partial coincidence was rejected: `_is_scalar` agreed with the
independent UNC-path example but returned true for the root-only path check, whose
expected value is false. It is not a path classifier. Likewise, applying
`unique_everseen` directly to the original cookie string yielded a sequence of
distinct characters, not cookie parsing with first-name retention. These observations
show why local output resemblance or a related operation name is insufficient;
they do not rule out a separately justified adaptation.

Runner durations sum to **11.898 s**; the six-run loop including preparation and
local plan persistence took **13.983 s**. These are one-shot host measurements,
not performance benchmarks. No new paid calls or acquisitions were made. The
preceding pilot's usage-based estimate remains USD 0.0241608; reviewer/subscription
compute is not assigned a fabricated dollar cost or described as resource-free.

## Comparison and decision

- Top-three selection changes: **0**. Four proposals outside that selection are
  not four lost useful relations: none produced a full behavioral witness here.
- Complete witnesses and demonstrated useful relations added: **0** in this
  bounded experiment. Qualified and integrated connections: **0**.
- False positive complete witnesses observed: **0**; a precision rate is undefined
  when no positive witness is emitted. Treating all four proposals as opportunities
  would be unsupported, but that is not what the product claimed.
- Useful relations lost versus a historical operator baseline: **unmeasured**.
  There was no independently adjudicated historical operator-contract set for these
  real issues. Same-code replay and unchanged candidate selection do not invent one.
- Recall outside the extracted functions, through other representations, or across
  the eight unencoded demands: **unknown**. Extraction omissions and incomplete
  discussions remain visible, rather than becoming semantic negatives.

Close this experiment without prompt/weight searches, extra adapters or extraction
changes to rescue the sample. The infrastructure phase remains closed. The
source-independent interpretation handoff works, but has not yet demonstrated the
user's desired discovery capability.

The next functional experiment should test **finding demands from a demonstrated
source operation**, rather than spending more effort matching this exhausted pool.
The existing `Provider.interpret_capabilities`, `problem_queries` and Service search
path already provide the integration points; no new orchestrator is necessary.
This study used three operator-authored queries and therefore did not test that
automatic path. A new, separately frozen sample should compare those capability-led
queries with a fixed baseline, preserving candidate limits and independent demand
review, and require a code-supported relation with plausible reuse advantage.
That is a hypothesis to test, not a proven retrieval fix. Do not change ranking or
declare retrieval the dominant cause from these results alone. Existing supported
operations, proposed adaptations, unresolved semantics and extraction limits must
remain distinguishable; another executable formula alone is not the success criterion.

Evidence and reproduction details are in the
[comparison directory](experiments/independent-contracts-comparison-2026-10-11/README.md).
All six plans reconstruct to their exact execution hashes and all assessments
recompute from the saved receipts. The 30 existing behavioral tests pass; full
Windows/Linux CI remains a merge requirement. No product code was changed.
