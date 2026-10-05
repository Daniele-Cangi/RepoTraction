# Prospective source-supported triage protocol

Six new comparisons across five pinned repositories are prepared offline on
October 6, 2026. No model response has been obtained for this cohort. The question
is whether Luna's explanations match the supplied code, including accurate
abstention, bounded contributions and rejection of a misleading candidate.

This is **not repository-only Discover**, an external-issue investigation or a
held-out accuracy benchmark. The operator explicitly selected Python API contracts
and entrypoints and read them before freezing references. The five repositories
are new to this triage comparison, but this selection is not blind or random.
It does not measure JS/TS, Go/Rust or full-pool ranking. The familiar nine-case
development cohort and all previous responses remain immutable.

## Frozen source cohort

Each link uses the full commit acquired through GitHub's file API. Both raw Git
blob identity and UTF-8 SHA256 were checked. The pure source helper checks file
identity, not remote commit membership; that association comes from acquisition.
Only the selected top-level function is supplied, including decorators, nested
body and original docstring, not sibling implementations. Acquired Python is
parsed with AST, never imported or executed. Documentation is untrusted data.

| Case | Documented contract | Selected operation | Source-review boundary |
| --- | --- | --- | --- |
| 1 | [boltons `first`](https://github.com/mahmoud/boltons/blob/4e5faa3d7e4008d89e0d8bf1ea87b6d9a061a16d/boltons/iterutils.py#L968) | `first`, lines 968–994 | Selected element/default; custom predicate is not universal truthiness. |
| 2 | [more-itertools `chunked`](https://github.com/more-itertools/more-itertools/blob/1ea82a711c69f590054987b5cb194157f8ce8ac4/more_itertools/more.py#L215) | `chunked`, lines 215–250 | Caller versus nested generator; conditional strict check; unseen `take`. |
| 3 | [MarkupSafe `escape_silent`](https://github.com/pallets/markupsafe/blob/4e111271b1494995708a9e878a10829b5e10c7ba/src/markupsafe/__init__.py#L48) | `escape_silent`, lines 48–61 | Visible None dispatch; unseen `Markup` constructor and `escape`. |
| 4 | [JMESPath README](https://github.com/jmespath/jmespath.py/blob/2812594e69d43098ef60f81f4efc404c071b0418/README.rst) | [`compile`, lines 7–8](https://github.com/jmespath/jmespath.py/blob/2812594e69d43098ef60f81f4efc404c071b0418/jmespath/__init__.py#L7) | Immediate expression argument/parser delegation versus later `.search(data)` results. |
| 5 | [humanize `intcomma`](https://github.com/python-humanize/humanize/blob/6ed367fbeee9bfc4250789b5e47b1011c99a46b6/src/humanize/number.py#L143) | `intcomma`, lines 143–203 | Conditional conversions, fallback and formatting; unseen locale/delegate contracts. |
| 6 | [boltons `flatten`](https://github.com/mahmoud/boltons/blob/4e5faa3d7e4008d89e0d8bf1ea87b6d9a061a16d/boltons/iterutils.py#L1012) | `first`, same pinned body as case 1 | Wrong-candidate control: iterable vocabulary alone does not implement nested flattening. |

Five demands are exact original docstring literals, including delimiters and
indentation; case 4 keeps the entire README. Linked specifications and unseen
delegates are not fetched. All contexts set `acquisition_complete=false`.
Complete text coverage is not complete requirements, adoption or execution proof.
The full selected operation is represented in contiguous 1,200-character citation
chunks, within the unchanged 1,600-character local quote limit. Case 5 uses two
chunks; no body is clipped. Original demand chunks remain 500 characters.

## Independent reading, not forced relations

The operator's four-facet references were saved separately before any response.
They are source-reading notes, **not independently established gold labels** or
model inputs. No expected relation, prior prediction or reviewer metadata enters
the prompt. Each returned facet, including every `unknown` reason, will receive
a separate source reading after execution.

Report local shape/provenance acceptance separately from source-supported claims.
Check immediate entrypoint versus factory/later-call attribution, conditional
branches, unseen delegates, and whether each citation actually supports its
property. A valid string or resolving ID does not establish a true explanation.
A useful partial contribution needs a concretely requested, visibly implemented
suboperation, not merely shared vocabulary or general usefulness. Case 6 should
not receive an unsupported flattening slice; an accurate difference or grounded
abstention is acceptable. No known relation or minimum positive count is forced.
An all-unknown response can be mechanically valid while inaccurate or unhelpful.
Preserve and report every rejection rather than repairing or discarding it.

Private preparation is owned under
`data/missing-link-triage-prospective-2026-10-06/`, excluded from Git. Its original
source records, contexts, references, exact payloads and executable fingerprints
remain immutable; public documentation contains no credentials or response data.
Frozen SHA256 values are:

- Acquired files: `4720f42aaa2fba019c3e1f55989e88d73b6a9d938b452d95963516f0e994cc9f`.
- Inputs: `9ef0385a2e46d3fe512947c367a5410cc432adbee539b182fb6c3e0169fe8cb2`.
- Separate references: `ff535be9a93a8cda6f19b3c8ee66307ad963496b1c6ae15a3f3ba0406000a0d8`.

## Exact requests and budget

Keep `gpt-6-luna`, Responses streaming, medium reasoning, strict JSON Schema,
6,000 maximum output tokens and `store=false`. The reviewed declaration schema
is instantiated with each case's own citation IDs; the explicit branch validator
and unchanged provenance/bounds/completeness normalizer remain mandatory after
the generic receipt reader. The unchanged 7,740-character layer prompt SHA256 is
`cdc7ecc5c86a84512027ba803b95d5fe44efa887d7fb7b80176e8b901d96e6a0`.

| Case | Exact request bytes | Planned reservation, USD |
| --- | ---: | ---: |
| 1 | 23,941 | 0.0055989 |
| 2 | 23,809 | 0.0055857 |
| 3 | 22,548 | 0.0054596 |
| 4 | 30,663 | 0.0062711 |
| 5 | 25,217 | 0.0057265 |
| 6 | 23,110 | 0.0055158 |
| Total | | 0.0341576 |

The private manifest records each exact body/schema hash and the ordered job IDs
`missing-link-triage-prospective-2026-10-06-01` through `-06`. These are prospective
reservations, not six executed calls. Configuration retains USD0.10 input and
USD0.50 output per million tokens; the existing reservation formula includes a
body-size input buffer and maximum output, not reported usage. Native cache-write
usage/pricing must be retained separately; configured-price calculations are not
invoices. See [Luna pricing](https://developers.openai.com/api/docs/models/gpt-6-luna).

Actual accounting remains **517 reservations / USD7.6197550**, with zero new
calls or reservations. Use the original `missing-link-verification-2026-09-30`
allowance under the user's USD10 total, not a reset or additional allowance.
The proposed segment cap is USD0.10, cumulative ceiling USD7.7197550, at most
one attempt per case and USD0.02 per case. Do not retry, substitute inputs,
schemas/models or refund reservations based on smaller usage estimates.

## Execution gate and offline checks

This change supplies a pure offline source helper and protocol, **not a paid
cohort executor**. Execute only after scoped Codex review, green CI and merge,
then separately freeze and verify an owned one-use driver. That driver must bind
these exact inputs, references, configuration and requests to the reviewed main
revision and fresh GitHub identity. Provider readiness precedes start-marker
consumption. Use the existing worker lease and atomic original-allowance/segment
reservation; do not reuse the old branch-schema executor unchanged.

Before each attempt, require the expected ordered case and unchanged fingerprints.
Retain exclusive start/receipt/raw terminal/result artifacts. Stop on identity,
integrity, transport or terminal/refusal failure, without retry. A completed,
non-refused candidate that fails local normalization is retained as rejected;
the next pre-frozen case may proceed once. After any spend, validate an exact
ordered prefix of at most six owned reservations and their allowance increments,
not the obsolete pre-attempt assertion of 517 rows. Preserve all 517 prior rows,
720 protected earlier artifacts, non-accounting tables and exact unrelated
allowances. Future driver implementation must test these gates before payment.

Eighteen authored controls cover source identity, ownership, UTF-8 AST columns,
CRLF, original documentation, complete long-body spans, bounds and metadata
exclusion without provider construction, credentials or acquired-code execution.
All **341 focused and 1,321 full-suite tests pass**. The six frozen contexts and
requests reproduce exactly; authored all-unknown cards replay identically and
all original demand/body spans cover the selected text. These are mechanical
controls, not AI responses or semantic results. CLI help is unchanged. Post-test
read-only checks preserve the earlier history and accounting in full.

No production prompt/schema, selection, qualification, UI or parser coverage is
changed. A later repository-only autonomous usefulness test still needs its own
new cohort and frozen protocol; this explicit-entrypoint comparison does not
answer that question or authorize isolation of a candidate.
