# Missing Link demand triage contract

## Purpose and outcome

This offline contract separates reviewed mechanism differences from missing
context before any new discovery strategy is tested. It **does not classify text
automatically**, change production discovery or prove an improvement in Luna.

Nine retrospective reference cases from the retained contract-25 discussions
preserve five outcome differences, three limited primitives and one unknown
outcome. All nine remain `context_required`. None becomes eligible, rejected by
a new filter, imported into a job, or executed.

## Reviewed facets

The experimental pure helper is
`scripts/missing_link_triage_contract.py`. No production module imports it.
Callers annotate four facets independently:

| Facet | Question | Important distinction |
| --- | --- | --- |
| Runtime | Where does the mechanism run and where is it required? | Different languages alone do not prove that interoperation is impossible. |
| Input | What values and structures does it consume? | One string is not a mixed-dtype array. |
| Output | What does it return or emit? | A position or collection is not a search index or generated interface. |
| Outcome | What requested behavior does it establish? | A primitive or shared word is not completion of a whole task. |

Relations are `aligned`, `different`, `unknown`, and, for outcome only, `slice`.
Known relations require exact character spans on **both** the supplied demand
body and operation body, plus an explicit review reason. Unknown relations carry
no claim of established evidence. Titles are not supplied as demand evidence.

The helper validates offsets and verbatim quotes, not their meaning, exhaustive
context, code ownership or execution. A caller must independently establish those
properties. An exact quote can still support a false interpretation. These
annotations are human reference labels, not provider predictions.

Each body is bounded to 180,000 UTF-8 bytes; oversized inputs are rejected rather
than truncated. A span and reason are each bounded to 1,600 characters. The
four-facet shape and boolean completeness are explicit. This is an offline
evaluation bound, not a provider budget or an added HTTP endpoint.

## Conservative summary states

The summary preserves difference and partial hints even when the primary state
is unknown. It never emits eligibility, a compatibility verdict, a score, or an
automatic rejection:

| Condition in reviewed annotations | State |
| --- | --- |
| Full demand incomplete or any facet unknown | `context_required` |
| Complete demand and all facets known, with a difference | `mismatch_hint` |
| Complete demand and all facets known, with only a limited outcome | `partial_candidate` |
| Complete demand and every facet aligned | `candidate_for_review` |

`candidate_for_review` is only permission to continue inspection, not a verified
fit. Full-demand completeness includes referenced requirements and unresolved
acceptance/adoption details, not just successful retrieval of the issue thread.
Differences cannot justify skipping a broad request that may contain a useful
subtask. A slice cannot hide a known input or runtime difference.

## Retrospective reference cases

The source jobs and revisions are pinned in the
[contract-25 result](missing-link-contract25-three-repo-result-2026-10-03.md).
The [retrieval audit](missing-link-discovery-relevance-2026-10-04.md) explains why
title overlap alone cannot settle relevance. No issue was newly acquired here.

| Acquired demand | Inspected operation | Human reference outcome |
| --- | --- | --- |
| Hermes failure-safe file publication | Path `only_newer` | Different: timestamp skipping is not atomic publication. |
| Caro advanced grep command generation | Path `Pattern.__call__` | Different: filename matching is not command generation. |
| zedBSD POSIX compliance workstream | Path `Traversal.__call__` | Slice: generator traversal primitive, not POSIX compliance. |
| NumPy mixed-input dtype detection | ItsDangerous `want_bytes` | Different: scalar encoding is not mixed-array detection. |
| Model token-compression research | ItsDangerous `dump_payload` | Slice: serialized-byte transport, not measured model-token savings. |
| External timestamp anchoring | ItsDangerous `TimestampSigner.sign` | Different: locally signed time is not independent anchoring. |
| SvelteKit i18n generated key tree | D3 `group` wrapper | Unknown: wrapper delegation does not establish the requested generation. |
| JLS hosted-help search | D3 `bisector` | Different: ordered-array insertion is not help search. |
| Timeline graph and profiling roadmap | D3 `mean` | Slice: one metric, not the complete roadmap. |

Runtime, input and output remain unknown in these reference cards where adoption
has not been independently established. This intentionally avoids filling every
facet merely to force a decision. Eight acquired threads are incomplete; Caro's
complete acquisition still leaves acceptance/adoption details unresolved. Thus
all nine summaries require context, while preserving the five differences and
three partial hints. The SvelteKit case stays unknown rather than laundering the
previous invalid broad citation into new support.

The owned private checker pins each issue fingerprint, source revision, original
operation line range, operation hash and exact quote offsets. It does not invoke
the provider, execute acquired code, or write into SQLite. These retrospective
cards were selected after inspecting known outcomes: they are **not held-out
examples, accuracy labels for an autonomous run or evidence of generalization**.

## Verification

Fourteen committed synthetic tests cover complete positive controls, paired
near-wording negatives, partial outcomes, incomplete demand, each unknown facet,
runtime differences, invalid spans, invalid completeness, UTF-8 bounds and
input preservation. The synthetic labels are supplied by the test author; the
tests check summary behavior, not semantic inference.

Run them without credentials or local investigation data:

```sh
python -m unittest discover -s tests -p test_missing_link_triage_contract.py -v
```

The separate private replay verifies all nine reference cards. Before/after
hashes are identical for 12 Missing Link tables and 374 prior artifacts.
Original allowance remains 461 reservations / USD 7.2123066; this work consumes
zero new GitHub acquisition or paid AI calls and does not refund unknown attempts.
The complete local suite passes 994 tests. The 14 new tests do not alter the
existing 37 Chromium browser fixtures; no live dashboard or AI quality test is
claimed by this offline run.

## Next validation before production

Freeze a separate evaluation protocol before asking Luna to extract these
facets. The model must receive acquired repository/demand context **without the
reference labels**, preserve missing context and cite both evidence sides.
Validate its operation ownership and quote support through existing evidence
guards, not substring presence alone. Compare its predictions against reviewed
annotations and report invented alignment, lost partials and unknown handling
separately.

Use independent held-out positive and negative cases for a quality claim; the
synthetic controls and nine known cases cannot establish useful autonomous
discovery. Any live acquisition or paid segment must declare source selection,
request/context/call bounds and a reservation cap within the remaining original
allowance before execution. No provider/schema change, paid run, new selector,
UI work or bridge is authorized by this offline contract itself.
