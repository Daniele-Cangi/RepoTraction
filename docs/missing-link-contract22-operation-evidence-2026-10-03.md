# Missing Link: selected implementation evidence (contract 22)

This is an offline correction of two attribution problems found in the frozen
[contract-21 Luna evaluation (PR #40)](https://github.com/Daniele-Cangi/RepoTraction/pull/40).
It is not a new model-quality experiment, retrospective repair or parser expansion.
No paid calls, acquired-code execution or production-server restart are part of it.

## Runtime candidates and declaration context

An acquired `.d.ts` declaration remains structural coverage and available source
context, but its ID is not offered as a runtime capability during enrichment or
comparison. The selection report records excluded declaration IDs and omissions.
Actual acquired implementation candidates retain their own IDs and evidence.

The retained `escape-string-regexp` case had both `index.js` and `index.d.ts`, but
the model attached a runtime description to the type-declaration ID. The offline
replay now offers the `index.js:escapeStringRegexp` candidate, not the `.d.ts` ID.
No name-based pairing merges IDs, transfers ownership or promotes a declaration
when its implementation is missing. A type-only snapshot still reports missing
implementation context.

## Evidence must belong to the selected operation

The new `missing_link/operation_evidence.py` module derives operation boundaries
from pinned structural definitions/declarations and acquired text. Python uses
AST ranges; JS/TS uses a deliberately partial named-function scan with the existing
lexical exclusions and balanced delimiters. Unsupported, ambiguous or incomplete
shapes remain unestablished. This is neither a full JS/TS grammar/export resolver
nor proof of semantics, execution or relevance to the target request.

Behavior credit requires an actual cited body inside the selected operation:

- A signature, type annotation, docstring, `pass`, ellipsis stub or empty body is
  not implementation evidence.
- A sibling function or a broad shared excerpt extending outside that operation
  cannot establish the selected helper's behavior.
- Truncated quotes cannot borrow matching words from a preceding docstring or
  default argument. Quoted body positions must actually be included.
- Exact LF/CRLF citations and their final line terminator remain valid.
- A Python forwarding wrapper can retain partial credit for its own delegation,
  without certifying the callee's behavior or complete integration.
- Claiming full `existing_behavior` does not bypass the body check. Passive API
  preservation, hard conflicts, requirement unknowns and follow-up gates retain
  their existing rules.

All partial-review anchors must lie within the selected operation; at least one
must actually include its body. Downgrades preserve the model's bounded review
and reason for inspection, while the contribution becomes `not_demonstrated`.
Even a valid body citation is only a provenance prerequisite, not semantic proof.

The provider receives compact `implementation_bounds` hints and precise selected
definition chunks before broad file prefixes. Existing candidate/file/chunk limits,
explicit omissions and the 180,000-byte final transport bound are unchanged.

## Offline verification

- The full Windows suite passes **894 tests**. Seventeen dedicated new regressions
  cover declaration selection and operation evidence, alongside the existing
  provider, persistence, account, history and transport tests.
- Two retained Zod comparisons are revalidated ephemerally: the `failure` helper
  borrowing a shared `safeParse` excerpt, and `getEnumValues` citing only its
  declaration, both lose the erroneous partial credit and stay undetermined.
  Their original saved analyses and raw responses are not modified or imported.
- All **61** retained provider contexts (9 enrichment, 27 extraction, 25 comparison)
  pass actual transport preflight, with a maximum of **178,000 bytes**. Each stops
  at a fake reservation before HTTP; there are zero real reservations or calls.
- Source/isolated-installed CLI startup and installed-module imports pass. The
  Windows installer includes the new module and preserves owned data/config
  fixtures. No server is started or acquired repository code executed.
- Read-only checks preserve all 12 real Missing Link table hashes, 70 frozen
  report hashes and the previous evaluation's 64 prior-report hash checks. The
  original cumulative USD 10 allowance remains **389 reservations / USD 6.0337989**;
  Babel remains paused and unknown paid outcomes remain charged.

New evaluations use contract **22**. Earlier contracts stay historical/stale under
the existing freshness rules; no migration silently reclassifies saved outcomes.

## Next gate

Request one targeted review of these two existing-contract regressions, then merge
only after relevant findings and CI are addressed. Parser-completeness extensions
belong in future issues, not an indefinite review loop. A fresh, small Luna retest
must be separately scoped after merge, with frozen code/settings and the unchanged
cumulative allowance; this replay does not demonstrate improved discovery quality.
UI/key-entry work and forced isolation remain deferred until the core evidence is
validated and there is a genuinely eligible grounded match.
