# Experimental demand-to-operation policy preparation

## Implementation and limits

The eleven [frozen development controls](missing-link-demand-operation-controls-2026-10-09.md)
now have a separate experimental policy and a
[bounded evaluation protocol](missing-link-demand-operation-policy-protocol-2026-10-09.md).
No prediction has been generated from those controls. No acquisition, provider
call, reservation, retry, source execution, production promotion or UI change occurs.
This prepares reviewed machinery for a later separately authorized experiment;
it does not establish useful triage, compatibility or improved Discover quality.

Two opt-in modules, unimported by production, implement the boundary:

- `scripts/missing_link_demand_operation_policy.py` defines instructions, exact
  original-section packing, closed scoped schema, envelope bounds and a local
  reader for caller-supplied predictions. It has no provider, credentials,
  persistence, budget or execution entrypoint.
- `scripts/missing_link_demand_operation_review.py` records explicit independent
  operator verdicts for kind, five fields, every predicted constraint, query
  relation and each context-gap claim, with aligned verdict lists and indexed
  diagnostic paths for constraints and gaps. It also records independently
  described omitted constraints. It does not match reference paraphrases or infer
  semantic truth.

The policy requests implementation/help kind, requested change, input/output,
reported runtime, acceptance, constraints and a query relationship hint. Unknown
fields remain independently unknown; a supported local fact can survive incomplete
discussion. A design question does not choose its solution. Neither an operation
hit nor a context-only relationship becomes qualification or automatic rejection.

Original supplied text/Unicode offsets and omissions are preserved in 500-character
chunks. There are at most 96 chunks, 180,000 UTF-8 text bytes and 180,000 bytes for
the full serialized experimental envelope. Overflow fails without truncation.
Known fields/kind/query hints require supplied IDs; unknown fields have exactly
empty descriptions/IDs and bounded reasons. All five fields, at most twelve
constraints and one to twelve context gaps are explicit. Local cross-field and
whitespace guards remain mandatory beyond the generation schema.

The reader recomputes context from the original packet, resolves exact citations
and preserves the output unchanged. Valid citation provenance cannot establish
that a description is supported. Independent review distinguishes unsupported
claims, appropriate unknowns and missed stated facts without repairing output.
Omitted constraints are operator assertions with reasons, not inferred facts.
Claim counts are diagnostic, never accuracy, scores, eligibility or useful leads.

## Reference separation and offline preparation

The public protocol was written and copied privately before authored contract
tests and before any model prediction. Its independent SHA-256, UTF-8/LF, is
`14155abfccb0cc1f2bc09747de10c4fd3afea7cc683e4cb4b95712d52c27c3df`.
The input/reference digests from PR91 remain unchanged:

- Exact input bytes:
  `c1311e56aebd31cd750c82d9a3f7192b5eb77ca9eadaef903b7d544aa44856dd`.
- Reference manifest, canonical LF:
  `6cc171bc9e83130479156e71af09869c9bc6100240f28f69865da5fc95b6e9df`.

The current private preparation is
`data/missing-link-demand-operation-policy-preparation-v4-2026-10-09/`.
It retains eleven inert `offline-request-*.json` envelopes, the exact protocol and
a manifest pinning instructions, code fingerprints, input IDs/fingerprints,
envelope hashes, sizes and coverage. It records zero predictions/calls/reservations
and `offline_only_no_executor`.

The independent preparation manifest SHA-256 is
`7a893d49e4ee6f76df35702feebf8f5f487de2df4e01843a6d466ce05378cd50`.
All eleven envelopes fit the bound: maximum **24,104 bytes** and **24 root spans**.
Ten have complete-root assertions; one preserves its omitted article middle.
All eleven retain incomplete-discussion assertions and unverified acquisition.
Those assertions are caller metadata, not independent proof of upstream coverage.

Descriptive control IDs would expose hints such as an expected unknown/reference
state. The current payload therefore uses an opaque deterministic ID derived from
the packet fingerprint. Original IDs stay in the separate operator-side mapping;
root text, query and frozen input bytes are not rewritten. Instructions contain
general semantic-layer rules, not case-specific examples or expected labels.
No control reference card, issue title or source implementation is appended.

The initial preparation directory without `-v2` is preserved unchanged, with zero
predictions/calls and independent manifest SHA-256
`870e019e5cac116694d15b5afa2a39b52a586c30a4b19f6d90af05ceaefcbd95`.
It is superseded because its payload IDs were descriptive; do not execute it or
rewrite it. The opaque-ID v2 preparation is also preserved, SHA-256
`0e236bbc1761c00919c2cc7d690eef76d64c99b23e838bb4e117253c3f385ad5`.
The v3 preparation is preserved unchanged, SHA-256
`9abbb7ae14071055e4ba9c9a431cef306f4fa6989cb2e533d7351381ad4e0983`.
It clarified that no candidate implementation is supplied while code inside an
issue root remains unverified request data. The v4 successor pins the review
correction that requires a separate verdict for every context gap; its eleven
request envelopes are byte-identical to v3. Only v4 matches the current
instructions/code fingerprints. All four are offline-only with no outputs or
paid entrypoint. Successors precede any control prediction and retain the same
frozen input/reference evidence; never rewrite or execute a superseded preparation.

## Verification and next boundary

Twenty-six authored synthetic tests cover exact Unicode/gap packing, input
immutability, reference/ID leakage, scoped schema enums, UTF-8/envelope bounds,
tampered context, cross-field consistency and reader rejection without repair.
They preserve concrete educational demand, unresolved owner choice, local known
facts alongside unknown facets and mechanically valid all-unknown cards. A valid
but misleading tensor-cache citation remains in the prediction and is explicitly
marked unsupported by an authored independent review. Another control reports a
missed requested fact/constraint without filling the unknown prediction.
The PR92 P2 review finding exposed a single aggregate context-gap verdict.
Two additional regressions require mixed supported/unsupported gap verdicts with
individual paths, preserve raw output/review copies and reject aggregate,
misaligned or invalid gap verdicts. This implements the existing frozen protocol
without changing its text, predictions, instructions or generation schema.

These are authored declarations testing acceptance/preservation mechanics;
they are not semantic predictions produced by the policy, evidence that Luna
follows instructions, or a model-quality benchmark. Mechanical acceptance and
operator assertions do not independently establish their meanings.

The final full application suite passes **1,445 tests**, including the 26 new
authored controls. It was run after the per-gap review correction; earlier
1,442/1,443-test runs are preliminary evidence. Scoped review/CI are recorded
in the PR. The frozen-control provenance
checker confirms all original roots, input sections, 74 reference anchors and
independent digests still reproduce. The original owned-run verification passes
after committing the complete preparation on a clean tree, reproducing the sealed
inventory, original reservation prefix and 941 protected historical files.

The original ledger remains **555 reservations / USD8.0266132** of USD10,
with USD1.9733868 locally unreserved. These are software reservations, not a
verified invoice. Historical records, account isolation, missing/zero semantics,
production instructions/schema/normalizers and selection/scoring remain unchanged.

PR92 is now merged as `99064726996e6a2a150029c75d28efb8d792ef58`, with a clean
scoped review and four successful CI jobs on reviewed head `3a90a16` after the
Windows/Python 3.13 failed-job rerun. The separate
[native execution preparation](missing-link-demand-operation-execution-preparation-2026-10-09.md)
fixes exact wire bodies, historical baseline, native retention, identity/lease
and failure boundaries and an original-ledger segment cap. Next implement/review
its owned executor and freeze its exact-code successor before separately
authorized provider calls. These preparations grant no call authorization.
Development results remain separate from a
fresh repository-only useful-lead comparison and final qualification/adoption.
Zero qualified leads still defers execution/isolation, UI/key-entry and promotion.
