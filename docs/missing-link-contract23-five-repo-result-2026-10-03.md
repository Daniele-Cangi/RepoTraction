# Missing Link: partial five-new-repository contract-23 result

## Outcome

**One input completed; the second paused on GitHub identity-check timeout; three
were not started.** The strict frozen stop rule was followed, without retry,
resume or replacement. This is not a completed five-repository benchmark.

Asttokens produced six assessments: three non-fits, two similarity-only cases and
one source-grounded partial mechanism. No assessment is eligible for follow-up or
isolated execution. Freezegun has no completed comparison. No acquired/generated
code was executed, analysis imported, demand supplied by hand or external author
contacted. Babel remains paused.

The [protocol](missing-link-contract23-five-repo-protocol-2026-10-03.md) was pushed
before paid calls (`0f6b54f`, with unpaid startup clarifications through `ee069d2`).
Executable code stayed at merged `edcef83db733703fd0138b359d7403d33cdbd3b8`,
contract **23**, following PR #45's clean review and four green CI jobs. OpenAI
`gpt-6-luna` Responses/streaming/strict schema and all configured limits stayed
unchanged. Only repository names were inputs. The production investigation CLI,
local HTTP job API, public GitHub acquisition, provider, stored jobs and JSON
exports were used; no model completion was substituted with a fixture.

## Observed runs and spending

| Input | Status | Reserved calls / terminal receipts | Conservative USD reservation |
| --- | --- | ---: | ---: |
| `alexmojaki/asttokens` | Completed | 7 / 7 | 0.1216332 |
| `spulec/freezegun` | Paused: identity check timed out | 3 / 2 | 0.0516718 |
| `tox-dev/filelock` | Unstarted | 0 / 0 | 0 |
| `giampaolo/psutil` | Unstarted | 0 / 0 | 0 |
| `websockets/ws` | Unstarted | 0 / 0 | 0 |

Asttokens job `7b97a93913e54759b8225ae90c72527c` pinned source revision
`381af04c144c03e31eadbcbdf341bd91751ce0b1`; freezegun job
`570cd5a14a194b4295df841e16208df9` pinned
`92d61b3f5c31942a1039713574487bdcfcdbbfff`. They used 57 and 42 GitHub requests.
Both enrichment calls offered 30 candidates and returned eight interpretations.
The largest completed recorded wire request was 174,832 bytes, within 180,000.

The segment adds **10 reservations / USD 0.173305**, below its USD 1 cap.
Original allowance `missing-link-verification-2026-09-30` remains USD 10, now
**419 reservations / USD 6.4914746**, with **USD 3.5085254** headroom. The nine
completed responses report a combined token-based estimate of USD 0.0455916 at
configured rates. Neither estimate nor reservation is the vendor invoice.

Freezegun's third reserved attempt has no terminal receipt or stored model output.
Its **USD 0.0224674 remains fully charged in the conservative ledger**. Absence of
a receipt does not establish whether an outbound completion was sent or billed;
it must not be reported as zero-cost or a rejected model answer.

## Asttokens: useful primitive, not a full solution

For [Source-Code-Review-Tool-TIET #198](https://github.com/jatinsingh1603/Source-Code-Review-Tool-TIET/issues/198),
the model found `MarkTokens._visit_after_children` assembling token boundaries
from a node and its children. Its pinned implementation-body citation, lines
63–99 of `asttokens/mark_tokens.py`, passes the operation-local provenance gate.
This is a bounded contribution to the request's function-range work, **not** a
scope resolver, symbol table or complete multilingual parsing subsystem.

The accepted partial review explicitly leaves function selection/qualified names,
header/body/decorator boundary policy, conversion to the target byte/line location
contract, required languages and tests undone. The operation is an internal
helper. It is normalized to `investigate` / `partial_contribution`, not a verified
adapter or qualified opportunity. No integration or isolated test was attempted.

The same request's Python-AST initialization suggestion is rejected as a complete
answer to mandatory JS/TS scope/symbol work. For
[NeverC #16](https://github.com/NeverSight/NeverC/issues/16), Python parsing and
token initialization are correctly not presented as a C++/other-language
translation pipeline, lowering or target-language emission. The verdict is
`rejected` / `not_a_fit`, not revived by the unknown remaining checks.

For [stack #39](https://github.com/The-Interdependency/stack/issues/39), the model
distinguishes token/source-position infrastructure from the requested compiler
validation, root-binding, CI and review repairs. It explicitly notes that the
`parse=True` path invokes `ast.parse`, not the required compiler validation.
This is a non-fit for the full request, not proof that tokens can never help a
separately designed component.

These discovered requests were not supplied as inputs. A new automatically found
partial primitive is observed; novelty, complete fulfillment, adoption and general
discovery accuracy are **not** established.

## Class-level claims lose method attribution

Two raw comparisons select the `LineNumbers` class and describe plausible
line/character/UTF-8 coordinate conversion primitives. Both normalize to
`similarity_only`, with no accepted partial behavior. The class-region/body gate
does not let a class citation borrow executable proof from its nested methods.

This is not simply missing source coverage: enrichment was also offered
`LineNumbers.__init__`, `from_utf8_col`, `line_to_offset` and `offset_to_line`.
The model instead selected/enriched the broader class capability. A targeted
future improvement should guide method-level claims to the actual supplied
method ID/body and make normalization downgrades easier to explain. Do not weaken
the evidence gate, invent acceptance or require a universal parser expansion.

## Retrieval pools: now auditable, still lexical

The unchanged selector's sanitized input/decision is retained for both runs:
asttokens has 64 per-query rows / **63 distinct candidates**, freezegun has
117 / **117**. No raw search body is stored by this transparency wrapper. Its
decision exactly matches each persisted candidate checkpoint.

Asttokens searches cover token positions, recursive token marking and UTF-8
column conversion. The three selected discussions above include a useful span
primitive but also very broad product demands. Freezegun searches concern frozen
time, ignored modules and async context/decorators; selected titles concern an
async context-manager import, Python bytecode-cache exclusion and per-request
tool-timeout configuration. These title collisions are **retrieval hints**, not
completed compatibility verdicts: freezegun stopped before comparison output.
Unselected titles are not evidence of a better match without their full context.
No ranking/prompt change or post-hoc replacement occurred during the experiment.

## Stop diagnosis and artifact limits

The freezegun job records diagnostic `github_identity_cli_timeout`, category
`github_identity`, with timeout 10 seconds. This means the bounded
`gh auth status --json hosts` subprocess failed to finish in time. No account
change or expired token was confirmed. A subsequent unrestricted `gh auth status`
succeeded as **Daniele-Cangi**, using Windows keyring. This supports investigating
transient CLI/keyring/network/system latency, not logging in again or accepting
unknown identity. The particular latency source is not established here.

All six asttokens inspection ZIPs are **blocked** because `handoff.json` exceeds
the existing 128,000-byte per-file package bound. All six JSON handoffs were
received through the HTTP export API and retained by the CLI. JSON availability
must not be described as downloadable ZIPs, runnable artifacts or target
integration. No package limit was raised to force a demonstration.

## Verification, preparation corrections and history

- Merged production behavior had 920 passing offline tests and four green
  Ubuntu/Windows Python 3.10/3.13 CI jobs. No production code changed in this run.
- Six owned no-network harness tests validate transparent selector delegation,
  no raw-body retention/input mutation, capture failure, configured provider
  fields and public-source access independent of its own issue tracker.
- Unpaid setup first rejected an additive live budget field, then mistakenly
  required source issues to be enabled. The old setups/preflights were preserved;
  corrected final driver/server hashes were frozen before paid calls. Neither
  correction replaces an input or retries a live job.
- The initial post-run helper incorrectly compared logical `job:call` receipt IDs
  with SQLite INTEGER reservation primary keys. It stopped without modifying
  records. Independent read-only reconciliation uses per-job row counts, ordered
  calls, exact reserved-cost formulas and logical call IDs; it accounts for the
  nine receipts and one uncertain attempt without editing the frozen driver.
- All **79 prior job payloads, 273 prior matches, 251 prior match snapshots,
  409 old reservation rows and 123 protected JSON artifacts** retain their exact
  hashes/values. Mutable acquisition caches may refresh normally. No old evidence
  was deleted, rewritten, imported or relabeled.
- The startup/browser checks preserved all 12 table hashes before spending.
  Missing Link/Overview render without JS errors. Post-run browser refresh shows
  the new source-span result, paused identity-check reason and blocked package
  reason. Only read-only refresh/navigation is used, never Analyze/Resume/Run.
- No job is queued/running. The experimental capture wrapper is removed from the
  live localhost server afterward by restarting the normal merged-code handler,
  without starting analytics collection or resuming any paused job.

## Next decision

Investigate identity-check latency before defining another paid segment. Keep
fail-closed account isolation, unknown-attempt reservations and stopped histories.
Then address method-level attribution/diagnostic clarity and inspection handoff
size as separately bounded work, with fixtures rather than another universal
review loop. The three unstarted inputs need a new explicitly scoped segment;
this incomplete cohort must not silently resume. No eligible lead exists yet for
forced isolation, UI/key-entry work or a marketing claim of autonomous adoption.
