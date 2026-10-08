# Fresh-source test of evidence strength

The [experimental instruction revision](missing-link-triage-evidence-strength-prompt-2026-10-08.md)
was merged in PR85 (`06e1a2b`). This protocol freezes six new source comparisons
before any model response. It tests whether Luna distinguishes declared behavior
from body-demonstrated behavior, and possible differences from established ones.
It does not change production, repeat the October 6 paid cohort, or establish
autonomous Discover quality.

## Sources and comparisons

Acquisition reads three public GitHub files through authenticated `gh api` at
full commit IDs. Decoded UTF-8 length, Git blob identity and SHA-256 are checked.
The existing source helper retains each complete top-level function, including
decorators and original docstring, without importing or executing upstream code.
Only the selected function body is supplied as implementation evidence: acquiring
the containing file does not make its other definitions visible to the model.

| Case | Pinned documented demand | Selected implementation | Evidence distinction to inspect |
| --- | --- | --- | --- |
| 1 | [Packaging `canonicalize_name`](https://github.com/pypa/packaging/blob/ea25b7d2befd0068fb3d46b375f6f926f4473472/src/packaging/utils.py#L82) | Same function | Visible lowercase/replacement composition versus an unseen validation pattern; declared `NormalizedName` is not runtime enforcement |
| 2 | [Packaging `canonicalize_version`](https://github.com/pypa/packaging/blob/ea25b7d2befd0068fb3d46b375f6f926f4473472/src/packaging/utils.py#L154) | Same function | Exception fallback and flag-dependent forwarding versus unseen `Version` / `_TrimmedRelease` behavior |
| 3 | [Werkzeug `secure_filename`](https://github.com/pallets/werkzeug/blob/594452f6a4fe4de38a544962fbf04bfc9d37fbc2/src/werkzeug/utils.py#L163) | Same function | Bounded string composition and conditional Windows prefix versus unseen regex/device-name policy; no filesystem inspection |
| 4 | [Werkzeug `redirect`](https://github.com/pallets/werkzeug/blob/594452f6a4fe4de38a544962fbf04bfc9d37fbc2/src/werkzeug/utils.py#L210) | Same function | Visible constructor arguments and header assignment versus unseen response/escape implementation and client behavior |
| 5 | [python-dateutil `parse`](https://github.com/dateutil/dateutil/blob/2642afacc33fb839c404b75b230fff58b79793f2/src/dateutil/parser/_parser.py#L1270) | Same function | Visible parser dispatch versus unseen datetime/fuzzy-token return shapes and keyword interpretation |
| 6 | Werkzeug `redirect`, at the same pinned revision as case 4 | `secure_filename`, at the same pinned revision as case 3 | Wrong candidate: shared string inputs do not supply response creation, a Location header or a requested redirect mechanism |

These are explicitly selected API-contract comparisons, not unresolved user issues
or repository-only discovery. Three repositories and six related cases are not an
independent accuracy sample. Operator references cover all four facets of each
case, are frozen before responses, and remain separate from model inputs. They
are source-reading notes, not automatic gold labels.

Each context has `acquisition_complete = false`. Full original demand/body span
coverage does not establish unseen delegates, deployment, adoption or execution.
References, expected judgments, previous cards and proposed answers are excluded
from the serialized requests. Source text remains untrusted data.

## Frozen requests and spending limits

Use `gpt-6-luna`, Responses, streamed strict JSON Schema, medium reasoning,
`store = false`, 6,000 maximum output tokens and a 180,000-byte request bound.
No tools, provider fallback, parallel paid attempts or model change is introduced.
The experimental schema and normalizer remain exact predecessor delegates.

The configured standard text rates remain USD0.10 per million input tokens and
USD0.50 per million output tokens. The [official Luna model documentation](https://developers.openai.com/api/docs/models/gpt-6-luna)
also distinguishes cached reads and cache writes. The local reservation formula
is a conservative request-byte estimate plus maximum output allowance, **not an
invoice or guaranteed billed-spend calculation**. Native usage fields, including
cache-write usage when provided, must be retained rather than flattened away.

| Case | Request bytes | Local reservation, USD |
| --- | ---: | ---: |
| 1 | 27,358 | 0.0059406 |
| 2 | 26,736 | 0.0058784 |
| 3 | 27,143 | 0.0059191 |
| 4 | 29,018 | 0.0061066 |
| 5 | 34,150 | 0.0066198 |
| 6 | 28,262 | 0.0060310 |

Total planned reservations are **USD0.0364955**, within a USD0.10 segment.
Use only the original allowance `missing-link-verification-2026-09-30`, authorized
at USD10. The preparation baseline is 523 reservations / USD7.6539126 reserved;
the segment's cumulative reservation ceiling is USD7.7539126. No reset, refund,
new allowance or borrowing beyond this segment is permitted. Six exact completed
reservations would reach USD7.6904081; failures remain reserved too.

The ignored local manifest freezes public settings without a key, exact payloads,
schema/body hashes, source records, operator notes, code fingerprints and current
history. This preparation is **offline-only**, based on main `06e1a2b`, with no paid
entrypoint or live marker. After review and merge, a separately owned one-shot
successor must preserve these exact inputs/references/requests and bind the
reviewed executable revision. Never rewrite this preparation or execute it against
an unreviewed preparation-base revision.

## Execution contract and offline checks

The [fresh driver](../scripts/missing_link_triage_evidence_strength_driver.py)
binds the new prompt in exact-request checking and one-attempt execution.
Those function bodies are otherwise identical to the frozen prospective driver;
reservation-prefix verification delegates directly to it. Historical executors
and their prompt bindings remain unchanged.

The caller must check source, reference, code, request and configuration fingerprints,
current-account identity, reviewed-main ancestry, worker lease, exclusive start
marker and an atomic original-allowance cap. Recheck exact history and the owned
ordered reservation prefix before each case, before and after forced identity.
Keep all prior rows, artifacts, non-accounting tables and unrelated allowances
unchanged. A stale 517-row pre-spend reader is not a valid current baseline.

Make at most one attempt per ordered case. Retain the full native terminal before
acceptance; keep parsed cards and local normalization separately. An explicit
post-response branch/provenance rejection is retained without repair, and only
that candidate-local rejection permits the next case once. Transport, refusal,
incomplete/missing terminal, generic malformed output, identity, cap, fingerprint
or persistence failures stop the sequence. No retry, replacement or edited answer.

The [18 driver controls](../tests/test_missing_link_triage_evidence_strength_driver.py)
reuse 15 authored safety/receipt controls with the new binding, and add exact
function/delegate equivalence plus bidirectional rejection of old/new frozen
request drift. They use fictional contexts, memory accounting and mocked transport.
The focused triage suite has 421 passing tests; the complete suite passes all
1,401 tests. CLI help and changed documentation's local links also pass checks.

Separately, the six exact fresh-source requests are simulated offline with authored
terminals: all original source spans are covered, raw terminals are retained, and
one deliberate invalid unknown declaration is rejected without repair before the
next case runs once. The temporary marker is fictional. No credential lookup,
model request, real reservation or production job is created.

## Reading the eventual responses

Review all 24 facets, including reasons for unknowns, against only the context
actually supplied. For known comparisons check both property declarations, scope,
implementation layer, citations and branch/input restrictions. An explicit
declared-contract comparison may be useful when the requested property itself
concerns a declaration; it cannot silently replace an actual-result demand.

Do not certify unseen constructor/delegate outputs by repeating docstrings,
examples, names or annotations. Do not call a conditional policy an established
difference merely because it might change a result. Preserve bounded visible
composition, dispatch, fallback and requested suboperations where supported;
do not force a slice or invent missing acceptance criteria. Case 6 should not
become a connection based on shared string vocabulary.

A useful result needs supported bounded information as well as honest uncertainty.
All-unknown output or fewer known labels alone does not demonstrate improved
usefulness. An accurate bounded contrast in the wrong-candidate case is stronger
than abstention; a well-founded abstention is not falsely advertised as a proven
rejection. Report unsupported labels, unsupported unknown reasons, grounded local
comparisons and genuine rejections separately. Do not publish a percentage-accuracy
score or claim a causal prompt improvement from a different, selected cohort.

Local mechanical acceptance is not semantic verification or eligibility. Production
selection/qualification, parser coverage, UI/key entry, autonomous Discover and
candidate execution remain outside this test. A grounded eligible lead still
precedes isolation or interface work.

## Preparation fingerprints

Private source records and full historical tables are not published. Their frozen
SHA-256 identifiers allow a later local audit to reproduce this preparation:

```text
prompt       8df0c58ec671bfbfeb8114fc08414a8dd94a8669e6dcf75a78bb92d4e0c6e1d0
manifest     53bb5f67066f27b33805afd19b52005b28eed0a68089404d1dfb3754771d3c20
inputs       2eaef0ee2edf14d22efcc50cfca056109d8fa6c42880d556f4c1cadc9dded73a
references   9d3f6c58b3a5e049aa4db446100477d199a17b3833d2a35f496b1a266b997839
sources      d359d2e9d3dd9f0d7d2ae88025d5dd1141e43fa81cd1de09859b2c094cf820f8
baseline     c9613e9e04cccaa9a1ba981818bf38a52795d5bacf94152102e0daa0fe2a3e48
request-01   b43ed3efc18b27d20132225a388381c0f583c6aa1006fe8aef3c683314eafe93
request-02   8215af939aa49ab1aa813b4715c09564541153f7ecfb99ad51580f320517c579
request-03   9e0566d393726aba6aedff25220b30dfb1c53938cfaa358692c686614b28cd05
request-04   b4471eaabd97c63618ea23668ba8109402e9dc90dc20ddbc18905c5c454bec9e
request-05   c2f9656f53577bc6f4558d03899ddd843f692d3fc1710286b2f692c60b78da0d
request-06   6205925f890ed6e91028a9347ee8cb26a6d39c582b4964e64d5968751613732d
```

The baseline extends protection to 865 prior artifacts, all 523 reservation rows,
12 table hashes and unrelated allowances. No new paid response has been observed
in this preparation. These are protocol/safety checks, not model-quality results.
