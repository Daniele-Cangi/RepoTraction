# Current-demand diagnostic: complete citations before further semantic work

The six authorized baseline calls completed without retry in **144.534 seconds**.
They returned **79 requirements**, all validated, with **USD 0.0210848** estimated
from reported usage at the configured prices. The conservative reservation was
USD 0.0827249 within the separately authorized USD 0.10 ceiling. This is not a
billing statement. No additional calls, source comparisons or acquisitions were
performed. The remaining allowance does not authorize another stage.

The baseline was `9f893958df2680902a0f8880580393c61ab0345a`, with the exact six
wire bodies frozen by PR #119 before execution. The native parsed outputs and
normalized results were committed as `1210996` before the functional correction.
All six native statuses were already `unclear`; normalization did not change
them. The preparation document's "not yet executed" status records that earlier
stage and is intentionally unchanged.

| Frozen index | Requirements | Call elapsed seconds | Validated status |
| --- | ---: | ---: | --- |
| 2 | 1 | 10.773 | unclear |
| 7 | 13 | 26.609 | unclear |
| 9 | 21 | 26.097 | unclear |
| 12 | 30 | 32.756 | unclear |
| 15 | 11 | 25.116 | unclear |
| 16 | 3 | 22.862 | unclear |

These are selected difficult discussions, not an estimate of general accuracy.
The test exercises `Provider.interpret_request` on saved inputs, not the complete
ordinary acquisition and Service path. Missing GitHub identities remain unknown;
the experiment results are keyed by frozen index/URL, not null production IDs.

### Execution boundary used for this diagnostic

The preparation text did not specify the entrypoint clearly enough. Calling
`Service._execute` would also acquire source/target context and invoke capability
and match analysis, so it was **not used**. There is no claim that Service has an
existing request-only mode. After authorization, a one-off local invocation
called the existing `Provider.interpret_request` for exactly the six saved
indices, composing the existing Store, Budget, WorkerLease and account verifier.
No reusable runner, alternate transport or product entrypoint was introduced.

Before the first call it checked the baseline implementation and all six frozen
input/wire hashes, refused an existing diagnostic database, verified the active
account and acquired the existing lease. The new persisted allowance and Budget
had a six-attempt limit and USD 0.10 ceiling. Each call checked the exact outgoing
wire bytes and used the existing atomic reservation, cancellation/account checks,
attempt persistence and native-output persistence. There was no retry branch.
The saved job records six `request` phases, zero GitHub requests, no capability
or match phase, and completion. This is the concrete execution record for this
authorized diagnostic, not a new recommended general-purpose execution system.

## Independent findings

The authorized separate-context reviewer read all 79 requirements against both
the actual supplied payload and the larger frozen record, without the candidate
implementation or source-library comparison. This is an independent AI review,
not a human ground truth. Its frozen [review](experiments/current-demand-interpretation-2026-10-11/independent-output-review.md)
and [detailed evidence](experiments/current-demand-interpretation-2026-10-11/independent-output-review.json)
distinguish four concrete defects from legitimate uncertainty:

- Index 7/r12 cites numeric float differences for a writer rule. The writer rule
  exists elsewhere in visible text; the selected quotation is unrelated.
- Several index 7 requirements cite incomplete physical lines: the operation and
  its constraint are separated even though the complete sentence is visible.
- Index 16/r2 cites only part of its claim despite another relevant selectable
  span. Better input boundaries alone cannot ensure correct model selection.
- Index 15 incompletely reconciles later measured SIGN work with earlier
  proposals. Later measurements do not prove every proposed behavior completed,
  but describing the implementation only as a proposal is too broad.

Index 2 explicitly treats the metrics report as possibly retrospective and
recognizes completed fixes and the stop decision. Index 9 retains the cleanup
request without manufacturing library relevance. Index 12 preserves atomic
Move/Removal/Undo, reaches the 30-requirement cap, and reports gaps: detailed
transaction text is omitted from the middle, while related API-test bullets
remain visible but uncitable. Index 16 correctly leaves the current pending set
unknown given its large discussion gaps. Formal citation identity passed for
every returned row; it did not establish semantic support.

## Narrow functional correction

`missing_link/demand.py` previously split citations at every physical newline.
It now keeps consecutive prose lines together before the existing conservative
sentence split. It preserves literal source text and original offsets. Titles,
blank lines, recognized Markdown items/headings/tables/quotes and code fences
retain separate boundaries; synthetic omission seams never join. This is a
bounded citation helper, not a complete Markdown or semantic parser. Very long
sentences still split at the existing 1,600-character bound.

For example, the baseline citation ending in "every continuous parameter gets
one" becomes a contiguous citation containing the objective decimal resolution,
integer count and interval. The clause ending in "with zero" now includes
"floating-point operations". The escape-validation citation now includes both
flanking grid points. Exact before/after examples are in the
[offline comparison](experiments/current-demand-interpretation-2026-10-11/offline-citation-comparison.json).

No prompt, model, schema, transport, ranking, candidate count, source acquisition,
budget or storage change accompanies this fix. Quote limits, the 18,000-byte
citation budget, 180,000-byte wire limit, 400 citation IDs, root opening and
round-robin source ordering remain unchanged. Public redaction, truncation flags
and source identity flow through the existing context builder. Saved results
are not regenerated or reinterpreted. The analysis contract version stays the
same because the output schema and saved-result meaning remain compatible;
newly generated spans continue to bind their exact original offsets and text.

## Offline benefit and tradeoffs

The six baseline wire bodies were reproduced **byte for byte**. Both versions
were then compared on all 17 retained discussions, stopping at `complete` before
any transport. The other eleven cases remain a model-output holdout; their
discussion texts were previously reviewed and are not an independent population.
There are no candidate model outputs or candidate discovery outcomes.

| Diagnostic index | Baseline spans | Candidate spans | Baseline wire bytes | Candidate wire bytes |
| --- | ---: | ---: | ---: | ---: |
| 2 | 69 | 69 | 58,494 | 58,494 |
| 7 | 152 | 100 | 75,054 | 72,362 |
| 9 | 129 | 97 | 58,109 | 56,420 |
| 12 | 130 | 130 | 53,709 | 53,709 |
| 15 | 88 | 88 | 63,770 | 63,770 |
| 16 | 64 | 61 | 145,825 | 145,668 |

Every candidate quote remains an exact original substring; all bounds pass.
The supplied source text and the set of represented sources remain identical
for each of the 17 discussions. This does **not** mean identical clause coverage:
six previously selected spans no longer fit as complete candidate spans:

- Index 7: the short fragment "At 16384 Hz".
- Index 11: a sentence describing generated-page removal and route reconciliation.
- Index 14: the label "Scope delivered".
- Index 16: a rulings-record sentence, a superseded/declined-items decision, and
  a reference to read-back pages.

The index 11 sentence is substantive evidence of completed behavior; its loss
is a real tradeoff, even though it remains in supplied source text and the source
retains other citations. The fixed byte budget and unchanged ordering can
displace later clauses when earlier citations become longer. No equivalence of
coverage or semantic accuracy is claimed. No weights were adjusted to rescue
these examples. The W-A writer passage and inventory test bullets are still not
made selectable by this patch; index 12 is unchanged.

Citation construction was measured seven times per arm per discussion. The sum
of per-discussion medians was 2,132.721 ms for baseline and 2,088.606 ms for the
candidate. Individual cases vary in either direction and the full test suite
ran concurrently. These are descriptive local CPU/wall-clock observations, not
a speedup claim or predicted model latency. The demonstrated improvement is
complete original citation availability for wrapped clauses, not more useful
connections. No newly qualified connection is claimed.

## Validation and next decision

Four generic regressions cover wrapped operation/constraint preservation,
sentence and Markdown boundaries, omission seams, and long-text byte/quote
bounds. All **111 focused tests** passed. The full suite and all Windows/Linux
Python 3.10/3.13 CI jobs remain merge requirements; consult the current
[PR #119 checks](https://github.com/Daniele-Cangi/RepoTraction/pull/119/checks)
for the exact reviewed commit rather than treating older CI as validation.

The next functional obstacle is selecting evidence that supports each atomic
claim and reconciling later state, while explicitly retaining uncitable/missing
constraints. The baseline already shows these defects independently of this
fix. Any follow-up should start from those frozen failures and negative controls;
it must not infer a source-library opportunity from lexical overlap. A fresh
paid before/after comparison would need its own bounded decision and authorization.
This result does not reopen the completed infrastructure phase.

Artifacts: [frozen preparation](missing-link-current-demand-interpretation.md),
[preflight](experiments/current-demand-interpretation-2026-10-11/preflight.json),
[native and normalized results](experiments/current-demand-interpretation-2026-10-11/run-result.json).
All earlier retrieval and behavioral experiment evidence remains unchanged.
