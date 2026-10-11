# Independent demand examples: fixed offline comparison

Protocol fixed on 2026-10-11, before acquiring the new files or issue results below.
Baseline: `c1d2d67` (merged behavioral prototype). No historical corpus changes.

## Sampling rule

Source families, one file each, pinned to the default-branch head returned at acquisition:

| Family | File | Reason fixed before inspection |
| --- | --- | --- |
| more-itertools/more-itertools | more_itertools/recipes.py | Sequence transformations |
| mahmoud/boltons | boltons/mathutils.py | Numeric transformations |
| networkx/networkx | networkx/algorithms/dag.py | Dependency/graph operations, likely extraction limits |

Acquire repository identity/license, exact source and license text. Do not replace a
file because it has few extractable functions. Parse it as data only on the host.
Do not import or execute downloaded code outside the existing WASI runner.

Problem queries, in this order:

1. `"batch" "items" language:Python is:issue is:public is:open`
2. `"duplicates" "order" language:Python is:issue is:public is:open`
3. `"dependencies" "cycle" language:Python is:issue is:public is:open`

Take the first four results per query sorted by creation ascending. Deduplicate by
issue URL, keeping the first occurrence. Do not refill duplicates, unavailable
discussions, resolved-in-comments issues or irrelevant results. Preserve returned
search order, issue bodies and up to the first 100 comments, with explicit coverage
flags. This is a small, query-biased sample, not a prevalence estimate. Queries
are operator-authored, so success cannot establish autonomous problem retrieval.

## Comparison fixed before interpretation

Same source snapshots, problem pool, candidate limits and existing extraction and
adapter repertoire in both paths. Record baseline `select_candidates` ordering
with the same explicit queries, source capabilities and cap of three per source;
do not tune retrieval after reading bodies. The new proposal stage does not change
this ordering. Evaluate all unique sampled discussions separately in the isolated
study to measure potential outside the first three; never claim those are extra
ordinary Discover selections.

The baseline prototype takes operator-written contracts. The new path proposes
contracts from the discussion without source code, names or baseline contracts.
Freeze proposed contracts before comparing with source behavior. Use identical
WASI artifacts/limits and candidate set for behavioral comparisons. Never tune
examples, expected values or adapter choices to obtain a match.

Before inspecting source matches, independently review the discussion and proposed
operation: real unmet demand, requested operation, explicit versus inferred cases,
preconditions/runtime, contradictions/later resolution, unknowns and uncovered
requirements. Reviewers must not see candidate code or matching results for this
step. An assistant's own hypotheses are not an independent reference judgment.
Cases labelled `checks` by the proposing model are **not an independent oracle**.
Freeze separately authored challenge cases before execution; keep unresolved
interpretations unknown. Do not tune on any of these three new source families.

## Metrics and decision

Record denominators: issues retrieved, duplicates, visible discussions, proposed /
undetermined / invalid interpretations, extracted and omitted functions, bindings
observed / failed / unobserved, and proposals surviving independent review.
Compare useful relations added/lost, contextual false positives, top-three changes,
hard-constraint failures and unknowns. A useful relation needs a valid operation,
source-supported behavior and a plausible reuse advantage over implementing the
operation directly. Example agreement alone is insufficient. Record actual target
integration separately; none is implied by slice execution.

Report call count, bytes, reserved/reported cost and wall time separately from
local preparation and WASI time. Same supplied contracts must reproduce the
baseline prototype observations. Synthetic positive/negative controls check the
implementation only; they must not be pooled with public-demand quality results.

Advance only if independent judgments identify a useful relation enabled by the
new interpretation stage, without hiding invalid cases, new false positives or
lost baseline relations. Otherwise report the failure and the next functional
bottleneck. No weight search or infrastructure expansion to rescue this sample.

## Authorization and current limits

Acquisition and local preparation are free. No external model calls are authorized
by this protocol. A future model pilot requires a new explicit budget, with a
fixed model/configuration and source-blind request list. Do not reuse historical
allowances. Existing Service/Provider/Store budget, identity and attempt controls
remain the execution boundary. This document defines a comparison, not an AI
quality result or a commitment to obtain a positive connection.
