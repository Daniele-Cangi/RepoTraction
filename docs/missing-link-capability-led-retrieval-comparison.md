# Capability-led retrieval: different hits, no demonstrated useful gain

The existing capability interpreter completed three real calls and produced 20
enriched capability descriptions. Its queries changed eight of nine selected
issues, but the bounded comparison established **zero useful source/problem
relations in either arm**. This does not justify promoting enrichment as an
improvement in autonomous discovery, changing ranking weights, or expanding the
execution infrastructure. No production code is changed.

This is a negative result for the selected sample, not proof that enrichment is
useless or that the repositories contain no reusable software. Review was bounded
and performed by a separate-context AI reviewer, not a human oracle. The study
did not run paid request interpretation, compatibility evaluation or integration.

## What was held fixed

The [protocol](missing-link-capability-led-retrieval-protocol.md) was committed in
`3dbe656` before interpretation/search. Both arms use the same three pinned source
snapshots, unchanged `problem_queries` and `select_candidates`, three queries per
source and three selected candidates per source. A uses structural capabilities;
B uses actual `Provider.interpret_capabilities` output, including preserved
structural candidates. All 18 queries were frozen in `e974715` before acquisition.
This compares the entire enrichment-to-query behavior, including capability
prioritization; it does not isolate the effect of wording alone.

Queries request the first three updated-descending GitHub issue hits. There were
53 returned slots, 46 unique pool URLs and 17 unique selected URLs. All six local
selection replays match the saved outputs exactly. There is no overlap with the
old demand corpus, but the source families are already known. Ordinary Service
can acquire a larger pool; this deliberately small study is not a recall estimate
for that configuration or a comparison with the older oldest-first study.

Acquisition and the blind packet were frozen in `0b0d504`; independent judgments
and seven finite specification cases in `971243c`, before source/demand matching.
The reviewer received only discussion text and metadata, not queries, arm labels,
candidate code or model capability descriptions. All 47 cited quotation spans
were verified against the frozen packet. Source implementations were inspected
statically by the comparing agent; no acquired code was host-executed.

## Paired result

| Source | A selected | B selected | Shared | Demonstrated useful A / B | Issues with grounded finite cases A / B |
| --- | ---: | ---: | ---: | ---: | ---: |
| more-itertools | 3 | 3 | 1 | 0 / 0 | 0 / 0 |
| boltons | 3 | 3 | 0 | 0 / 0 | 1 / 0 |
| NetworkX | 3 | 3 | 0 | 0 / 0 | 1 / 0 |
| Total | 9 | 9 | 1 | 0 / 0 | 2 / 0 |

Eight B issues were added and eight A issues lost; **demonstrated useful additions
and losses are both zero**. This is not evidence of equal true utility. The
unknown population and incomplete review prevent such an equivalence claim.
Two more precisely specified demands in A do not make A a successful discovery
strategy: their paired source implementations do not substantiate those needs.

Sixteen of the 18 selected slots have zero title-term overlap. Each group retains
coverage of all three queries, consistent with the existing project/query
diversity priority. The two paths differ principally in the pools retrieved;
there was no new local score. Most selected entries occupy upstream rank one.
This experiment neither demonstrates a benefit from removing diversity nor
establishes that diversity caused the lack of useful relations.

The nine enriched capabilities directly used in B's queries have recognizable
implementation support: iterable take/group/partition; numeric clamp/ceil/floor;
DAG validation/topological/lexicographical order. That is a static reading of
those nine definitions, not a validation of all 20 model descriptions or their
runtime behavior. Short query phrases omit much of their operational context.
For example, deterministic ordering still depends on keys, comparable values,
graph stability and tie behavior; a phrase alone cannot establish target fit.

## Why retrieved context was not an opportunity

The full per-pair reasoning is in
[source-comparison.json](experiments/capability-led-retrieval-2026-10-11/source-comparison.json),
linked to the independent demand judgments. Representative distinctions:

| Retrieved demand | Source suggested by retrieval | Missing operational link |
| --- | --- | --- |
| `misofm/engine#291`: exact decimal integer lattice, off-grid validation and specified f32/default rank | boltons numeric helpers, arm A | `clamp` compares bounds; `ceil`/`floor` round or choose sorted options. They do not parse/scale exact decimal representations or implement the lattice contract. |
| `ry-cen/prizecheck#79`: atomic multi-source inventory move, version failure and Undo | NetworkX DAG functions, arm A | Reachability/cycle operations do not provide transactions, idempotence or reversible holding updates. |
| `tilorc-bot/satassume#149`: sound clause/rule minimization with measured runtime constraints | iterable grouping/partition, arm B | Partitioning values is not solver-rule minimization. Remaining rule inputs and benchmarks are missing. |
| `APPARANYX/grasstex#456`: remaining native device acceptance and owner/admin gates | numeric clamp, arm B | The clamp mention belongs to reported animation checks; it does not establish an outstanding numeric-helper need. |
| `nickderobertis/crozier#493`: remove unsubstantiated witness records | DAG validation/order, arm B | Record provenance and cleanup policy are different operations from graph ordering. |
| `rickylabs/netscript#2103`: milestone leaf work and runtime/release qualification | DAG ordering, arm B | A plan describing topological dispatch waves is not itself a missing graph implementation request. |

Other selections include secondhand contribution digests, translation freshness,
parked migration, scientific/physics campaigns and coordination maps. Some have
real remaining work. Their status does not establish a reusable contribution
from the selected source; broad projects must not be declared non-demands merely
because a particular library does not fit.

There are 17 selected source/issue pairs with no supported relation in the
reviewed context, and one whose current demand is unassessable because later
comment bodies are unavailable. **These are not 18 measured false-positive
product verdicts**: retrieval emits candidates, and production qualification was
not run. If promoted to opportunities from lexical hits alone, all 18 would be
unsupported. No calibrated false-positive rate or precision/recall is inferred.

## Finite cases and execution boundary

The blind reviewer froze four lattice cases and three inventory cases. They are
useful domain specifications with explicit assumptions; they do not establish an
application API or a match to the selected source. They remain unchanged.

No meaningful binding to the current extractor/adapters was established. The
boltons snapshot exposes only `clamp` through the existing extraction boundary;
`ceil`/`floor` are omitted because of their dependency. NetworkX exposes zero
callables through that boundary. More fundamentally, neither paired source
establishes the requested decimal or transactional operation. Feeding a domain
dictionary to a scalar function would produce a signature/type failure, not an
informative semantic test; writing the missing operation into an adapter would
manufacture the result.

Therefore **zero WASI runs and zero finite cases executed** in this study. This
is not a zero-match execution result. There are seven preserved specification
cases, no qualified connection and no target integration. No extractor extension,
adapter or runner was introduced to rescue the sample.

## Cost and coverage

Three `gpt-6-luna` calls completed with no retry in **80.355 seconds**, enriching
8 / 4 / 8 capabilities. The separately authorized ceiling was USD 0.10. Atomic
reservations total **USD 0.0504943**; cost computed from reported token usage and
configured prices is **USD 0.0126303**, not a billing statement. No additional
paid call is part of this study. Codex review work is not included in that API
usage total.

GitHub acquisition used **73 connector calls**: 18 searches, 46 metadata hydrations
because search omitted state, and 9 comment fetches. Connector pagination means
this is not a measured HTTP count. Acquisition/review elapsed time was not
instrumented. Local helper medians over 50 repetitions per group range from
7.9 to 51.9 ms; these do not include AI, network or review. No whole-run speedup
is claimed.

All 571 comment records are present by count, but five bodies and 89 comments are
truncated. Eighty-seven comments in `superheroes#695` have no retained text. The
reviewer also read bounded windows, recorded per issue, rather than all retained
text. Missing timelines, links, target code and unread text remain unknown.
`comments_complete` must not be read as semantic or full-text completeness.
The current advisory screener retains all 17 normalized packets; bot/type metadata
was unavailable, so this is not exact parity with ordinary acquisition.

## Decision and next functional obstacle

Keep the existing enrichment capability, but do not present this run as an
autonomous-discovery improvement. Stop this comparison with its fixed sample;
do not keep tuning phrases, weights, adapters or infrastructure in pursuit of a
positive result. Historical evidence and the product remain unchanged.

The observed obstacle is selecting a **current, specific requested operation**
from retrieved discussion before treating source similarity as a reusable
contribution. `Provider.interpret_request` already has source-independent atomic
requirements, original-span citations and resolution checks; `Service` already
uses it after selection. A new demand interpreter or orchestration layer is not
needed. Its existing behavior on these noisy, partly resolved discussions is
still untested by this three-call allowance.

The next functional work should target that existing demand-to-operation path,
using the frozen cases and contextual negatives to check that it preserves real
requests without inventing a missing library need. Any change must show useful
source-supported additions against the fixed baseline, keep unknowns explicit,
and be judged on a held-out demand set. Improving descriptions or rejecting more
roadmaps alone is not success. No further paid stage or implementation is started
as part of this report.

The [evidence README](experiments/capability-led-retrieval-2026-10-11/README.md)
documents lineage, replay and artifact semantics. CI on Windows/Linux remains
required before merge; this PR changes documentation/evidence only.
