# Current demand interpretation: six-call diagnostic, not yet executed

Baseline: `9f893958df2680902a0f8880580393c61ab0345a`, the merge of PR #118.
The previous three-call authorization is exhausted and does not authorize this
stage. No production implementation, historical evidence, transport or runner
changes are proposed here.

## Question and fixed sample

Does the existing `Provider.interpret_request` preserve actual requested
operations, distinguish completed work from current needs, and retain uncertainty
when evidence is missing? Its prompt already asks for these distinctions. Do not
add another interpreter or change the prompt before observing this baseline.

Use only the frozen PR #118 discussions, with the following diagnostic selection
fixed before any model output. These cases are deliberately selected challenges,
not a random sample or an estimate of general precision.

| Index | Reason for inclusion | Judgment to check |
| --- | --- | --- |
| 2 | Report with an explicit stop and residual decisions | Do not turn completed fixes into new unmet requirements; preserve outstanding decisions and unknowns. |
| 7 | First independently reviewed finite specification | Preserve decimal/integer lattice operation and constraints; do not invent a generic rounding need. |
| 9 | Concrete cleanup outside the sampled libraries' scope | Keep a real request even when it offers no obvious reusable-library connection. |
| 12 | Second independently reviewed finite specification | Preserve atomic inventory Move/Undo rather than infer graph traversal from project context. |
| 15 | Active research with later updates | Distinguish current measured solver goals from superseded examples or unverified remaining behavior. |
| 16 | Largest known gap in retained comment text | Preserve unresolved uncertainty; do not infer the current decision backlog from missing later comments. |

The other 11 indices are reserved against output-driven tuning. Their discussion
labels and context have already been examined; this is a **model-output holdout**,
not a new independent demand population. They are outside this authorization.

## Offline finding and its limits

The existing request-context path shortens long discussion entries and separately
limits selectable original citation spans. In the lattice and inventory cases,
some independently cited central specifications are omitted from the model's
source context. A visible multi-sentence reviewer quotation also need not fit a
single selectable citation. These are distinct measurements: absence of a whole
review quotation from one citation does not prove that no atomic clause is
citable. Do not score that shortcut as a semantic model failure.

Evaluate each output against both the supplied payload and the larger frozen
discussion. Separate (1) unavailable source text, (2) visible but unavailable
citation, (3) incorrect interpretation despite available evidence, (4) legitimate
uncertainty, and (5) schema/validation failure. Preserve raw native outputs and
validated results separately: `validate_request` can change an unsupported
`unresolved` status to `unclear` when context is incomplete.

The six normalized inputs retain all historical text, truncation, redaction and
coverage flags. Map existing user login to `author`, labels to their names and
add an empty timeline with coverage still false. GitHub issue IDs, bot/type and
association metadata unavailable in the connector packet stay unknown (`id=null`);
results are identified by frozen index, URL and fingerprint in the experiment
job, not inserted as null-key production request records. Recompute a derived
fingerprint and retain the original snapshot fingerprint. No metadata acquisition
or body rewrite is authorized. This tests the real interpretation method on a
saved packet, not the complete ordinary acquisition/Service flow.

## Frozen request boundary

The exact six request bodies were prepared by intercepting `complete` before
transport; no credentials, reservation or paid call was used. Their hashes,
sizes, input identities and pricing assumptions are recorded in
[preflight.json](experiments/current-demand-interpretation-2026-10-11/preflight.json).
Local ignored inputs and wire bodies are under
`data/current-demand-interpretation-2026-10-11/`.

Use unchanged `gpt-6-luna` Responses, JSON schema, medium reasoning, streaming,
12,000 output-token cap and 180,000 request-byte cap. Six attempts maximum, no
retry, output repair, source comparison or additional paid stage. Conservative
reservation totals **USD 0.0827249**. The proposed **new USD 0.10 ceiling requires
explicit authorization**; it is not a reuse of the prior allowance or a billing
prediction. Reuse the existing Store, Budget, account verification, worker lease,
attempt/output persistence and safe-stop behavior. Do not create a new runner.

## Decision rule

Compare grounded operation/constraint coverage, invented or wrongly reopened
requirements, lost real requests, and treatment of missing status evidence.
Document disagreements with the prior AI review; it is not a human oracle.
Counting valid JSON or more requirements is not success. No connection utility
or integration gain can be inferred from this diagnostic alone.

If a reproducible failure appears, correct its specific cause in the existing
functional path and add offline regressions before any further paid comparison.
If the method already makes the needed distinctions, leave it unchanged and
locate the next actual loss between its output and source matching. Do not start
a prompt/weight search or optimize the forensic harness. Any future product
change must pass the full Windows/Linux CI before merge.
