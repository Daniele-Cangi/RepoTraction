# Missing Link: bounded contract-24 offline corrections

## Outcome and scope

Three separate fixes follow the stopped
[contract-23 five-input experiment](missing-link-contract23-five-repo-result-2026-10-03.md):
successful GitHub identity cache timing, method-level interpretation guidance and
explanations, and lossless inspection handoff packaging. No real AI call, job
resume, new investigation, historical repair, source-code execution or account
change is part of this work. The original USD 10 allowance remains **419
reservations / USD 6.4914746**, including the uncertain freezegun attempt.

## GitHub identity: a reproduced cache defect, not a proven timeout cause

Three unrestricted, bounded `gh auth status --json hosts` probes report one
verified active account, `Daniele-Cangi`, in **0.728, 0.740 and 0.760 seconds**.
The prior ten-second timeout is not reproduced; these checks do not identify
whether its cause was CLI, Windows keyring, network or system latency.

The successful cache timestamp previously preceded the subprocess. A six-second
successful check therefore already exceeded the five-second cache interval at
return, inviting another immediate check. The localized correction timestamps
success at completion, under the existing lock. Offline fixtures reproduce that
timing and verify expiry at five seconds after completion, forced checks and
unchanged last-success time after a failed forced check.

The ten-second subprocess bound, five-second success cache, fail-closed identity
validation, ambiguous-account rejection and explicit resume requirement remain.
There is no retry, login prompt, longer timeout or acceptance of unverified
identity. Reduced redundant checks are not proof that the historical timeout is
fixed.

## Method attribution and explanations

Both capability enrichment and comparison now ask for an **available method
capability ID and that method's body** when claiming method-level behavior. An
enclosing class cannot borrow nested-method implementation credit. Missing IDs
and source bodies remain unestablished; no ID is invented, candidate substituted
afterward or parser/resolver expanded. The existing evidence gate is unchanged.

When an assertion is normalized, affected checks add `support_normalization` with
the original status, contribution and reason, fixed diagnostic codes and messages.
The explanation is also appended to the displayed reason. The original charged
model output stays unchanged. Reusable primitives remain distinct from complete
fulfillment; target context, analogy, signatures, sibling bodies and passive
constraints cannot become implementation proof through the diagnostic.

Interpretation contract **24** separates fresh results from contracts 21–23.
Old records are retained exactly and marked historical by existing freshness
rules, not rewritten, promoted or automatically re-evaluated. Fixtures cover
class-versus-method selection, signature-only evidence, target/analogy/missing
review, full claims without a body, unchanged valid partials and both prompts.

## Large inspection ZIPs: preserve data, preserve bounds

Small packages retain the complete schema-version-1 `handoff.json`. When that
serialized handoff exceeds **128,000 bytes**, only that metadata is split into
UTF-8-readable `handoff-parts/NNNN.json.part` fragments. Its `handoff.json` is a
**schema-version-2 multipart index**, explicitly not the complete handoff or an
execution receipt. It lists ordered parts, byte counts, per-part SHA-256, total
bytes and payload SHA-256. `HANDOFF.md` explains byte concatenation and integrity
verification before UTF-8 decoding/JSON parsing; fragments are not standalone
JSON. The manifest hashes the index and every fragment. The separate JSON HTTP
export still returns the complete handoff.

The **128,000-byte per-file** and **2,000,000-byte total uncompressed** bounds
remain unchanged, including index, manifest, Markdown, evidence, license and
bridge files. Generated bridge files cannot evade their bound through splitting.
Credential-shaped content is redacted before segmentation. Existing bounded
evidence snippets and their explicit omission warnings remain separate from the
complete handoff metadata; no requirements, comparisons or acquired discussion
are silently removed to make it fit. All packages remain **NOT EXECUTED**.

Fixtures cover exact/over boundary, UTF-8 reconstruction, every file/hash/total,
reproducibility, small-package compatibility, redaction, oversized bridges and
total limits. A service fixture verifies the imported analysis and both service
export delegates without a real provider call. Original stored package-block
annotations remain historical; export regenerates a package from its pinned
snapshot using the current formatter, without updating those old annotations.

## Retained-output replay and integrity

A private read-only replay feeds the three retained asttokens comparison outputs
through the current provider validation with completion mocked before HTTP. It
does not call the model to obtain improved answers or replace historical outputs.
All six original classifications, contribution kinds and discovery verdicts
remain the same: **three non-fits, two similarity-only cases and one grounded
partial**, with zero eligible leads. The class claims now explain their missing
selected-operation body evidence. The accepted token-span primitive remains
partial and does not become a full solution or isolated-execution candidate.

The three encoded comparison contexts stay below the unchanged 180,000-byte
transport limit; maximum **175,141 bytes**. All six originally blocked handoffs
are losslessly reconstructed from two or three fragments, with payload sizes
**129,926–276,673 bytes**, and every package member at most 128,000 bytes. This
verifies formatting and validation, not fresh Luna quality or target adoption.

All **12 real Missing Link table hashes and 132 protected JSON artifact hashes**
are identical before/after the replay. Freezegun and Babel remain paused, no job
is queued/running, and unknown reservations are not refunded. The existing live
server is not restarted onto unreviewed code.

The final full Windows offline suite passes **935 tests** (15 new regressions).
Source CLI and investigation-driver `--help` startup checks also pass. Focused
identity, attribution, packaging, historical-freshness and service checks pass.
No universal parser coverage, UI/key entry or forced integration is included. After targeted
review and merge, freeze a new explicitly scoped live segment for the three
unstarted source inputs; the stopped original experiment is still incomplete.
