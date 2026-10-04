# Experimental prompt for comparing requested and candidate properties

This revision clarifies property comparison without requiring proof that a candidate
already implements or integrates the demand. It is an experimental prompt only,
not a production change or a new Luna result. The earlier explicit-scope prompt,
all prior predictions and their independent review stay frozen.

The prior [nine-card comparison](missing-link-triage-explicit-result-2026-10-04.md)
retained only three known facets and 33 abstentions. The independent review noted
lost narrow contrasts as well as genuine gaps. Ambiguous implementation-oriented
wording is a hypothesis for some abstentions, not an established cause. The
[authored controls](missing-link-triage-property-controls-2026-10-04.md) show that the
unchanged validator already permits supported local comparisons; they do not show
how Luna will respond to this wording.

## The comparison rule and its limits

The new paragraph asks for the explicit property of the requested operation and
the candidate property visible at the chosen layer. They must describe the same
property dimension. `comparison_scope=requested_operation` identifies the scope of
the demand property, not a proven implementation relationship with the candidate.
A directly supported difference can be stated without full adoption or acceptance
context; those gaps still keep `demand_complete=false`.

The paragraph also separates a declared interface contract from runtime enforcement.
An annotation may describe the former, but cannot alone prove runtime rejection.
Alignment of a property is not proof of the requested behavior or a supported slice.
Missing wiring, unseen delegates, generic parameters and whole-product deliverables
must not be converted into narrow incompatibility evidence. An unknown corresponding
interface or property still requires abstention; the prompt does not force a label.

All other instructions remain byte-for-byte unchanged in the prompt string:
untrusted-source boundaries, original character coverage, runtime attribution,
operation layers, citation relevance, exact IDs, the narrow slice requirements,
reason bounds and incomplete acquisition. There are no new few-shot answers,
repository-specific examples, historical predictions or reviewer labels in the prompt.

## The frozen contract and the new module

`scripts/missing_link_triage_property_prompt.py` replaces one exact paragraph from
the frozen predecessor. It fails if that paragraph is missing or duplicated rather
than silently dropping safeguards. It aliases the predecessor's schema and
normalizer; it does not implement another context builder or change field semantics,
validation, provenance, normalization or verification flags. Nothing imports it
from production, and importing the revision performs no application IO.

The predecessor remains `scripts/missing_link_triage_explicit_scope.py`, with
canonical-LF source SHA256
`649f7b8f48c64334dcb04af115900e5b7a6ec3f67cf672c9851d93aac3daa0f2`.
The new prompt string has SHA256
`7697f92e260a315042b64ad92234a805e3629118b6aa660676fc8dcfc825c882`
and 5,116 characters. This fingerprints the wording, not a completed live request
or an approved execution protocol.

Keeping a versioned module and representative controls follows the general
[OpenAI prompt engineering guidance](https://developers.openai.com/api/docs/guides/prompt-engineering).
Separating task-specific checks from human review follows the
[evaluation guidance](https://developers.openai.com/api/docs/guides/evaluation-best-practices).
Those sources do not establish Luna-specific quality or validate this comparison
contract; those judgments remain local and require testing.

## Offline verification and historical preservation

Fourteen new tests check the paragraph boundary and predecessor fingerprint,
unchanged schema/normalizer delegation, retained contrasts and abstentions, factory
versus method layers, provenance/completeness guards, the mean slice and absence of
application IO when reloading the revision with its frozen dependency already loaded.
Offline request encoding checks both existing API kinds: only prompt text changes;
the original context, schema and remaining payload fields stay identical. These
use explicit dummy configuration, never a key lookup or network call.

All **136 focused triage tests** and the full **1,116-test suite** pass on the
final test revision. The post-test check verifies all 12 table hashes, every
accounting row and 507 protected artifact hashes unchanged, along with the frozen
predecessor code fingerprints. All nine retained cards normalize identically,
preserving their 33 unknown facets and the mean slice without scoring abstention.

The private baseline protects all 12 table hashes, every accounting row and 507
earlier artifact hashes: the preceding 502 plus the five offline-control artifacts.
A read-only replay checks the original nine cards against the unchanged schema and
normalizer; it is not a response to the new prompt, semantic regrading or a new
quality score. The original allowance remains 489 reservations / USD7.4039320;
combined triage reservations remain USD0.1916254. No new calls, reservations,
provider/key lookup, job import, acquired-code execution or history repair occurs.
Earlier unknown native failure usage stays unknown, without refund or budget reset.

## Review before another model comparison

Review only the new comparison wording and its boundaries: independent property
comparison versus implementation proof, real evidence gaps, annotation versus runtime
enforcement, operation layers, citation relevance and the retained mean slice.
Do not expand parser completeness or treat authored fixtures as observed Luna quality.

After review, freeze a separate comparison protocol, actual encoded requests and
an explicitly authorized spending segment within the original cumulative allowance.
The existing combined triage cap has only USD0.0083746 remaining; this revision does
not renew it. Preserve raw outputs and distinguish assertion coverage from independently
supported assertions. Reusing the nine development cases is a diagnostic comparison,
not held-out accuracy. Production, ranking, isolation, UI and key-entry work remain deferred.
