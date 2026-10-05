# Experimental prompt for branch returns and local property comparison

This revision adds two bounded instruction blocks to the experimental triage
prompt, following the [reviewed offline controls](missing-link-triage-branch-controls-2026-10-05.md).
It asks the model to distinguish conditional return behavior from declared types,
and comparable properties from an existing implementation relationship. It does
not yet establish that Luna follows those instructions or resolves the two
problems in the [retained model result](missing-link-triage-property-result-2026-10-05.md).

PR67 is merged after a no-findings Codex review of `ca3f713` and four green CI jobs.
The predecessor prompt, historical annotations and production behavior remain
unchanged. A new module, `scripts/missing_link_triage_branch_prompt.py`, contains
the revision; it is not wired into production or the frozen execution driver.

## Two instruction changes

The branch block asks the model to inspect supplied return paths and their
conditions before making an observed-return or behavior claim. A declared bytes
type is not an unconditional bytes result when a non-string branch returns its
input unchanged. Any branch or input restriction must appear explicitly in the
property and reason. A visible branch or declared contract may support its own
bounded comparison, but neither can silently substitute for an unsupported
general runtime claim. Missing return paths/delegates remain unknown, and
pass-through does not establish collection detection or transformation policy.

The comparison block asks the model to establish both properties in their cited
passages at the selected layer. Command text versus a visibly boolean result may
support a local output contrast without proving that the candidate already
implements the requested command generator. It does not establish a runtime ban,
whole-task rejection or adoption. Guessed nested interfaces, unrelated project
deliverables and unseen delegate contracts do not justify a forced contrast.

These are instructions informed by the same development cases, not held-out
examples or new gold labels. No repository, issue ID, prior model answer or
reviewer label is added to the prompt. The wording is an experimental choice;
the [official OpenAI prompt guidance](https://developers.openai.com/api/docs/guides/prompt-engineering)
supports explicit instructions and evaluations, not a claim that this particular
revision improves Luna.

## Frozen boundaries

The new module inserts the two blocks at unique fixed anchors, failing if either
anchor is missing or duplicated. Removing only those additions reconstructs the
predecessor prompt exactly. All existing evidence, unknown, scope, interface-layer,
slice, completeness and length instructions remain present.

Schema and normalizer remain identical delegated function objects. No new field,
semantic classifier, parser/resolver extension, relevance policy, qualification
gate or automatic repair is introduced. A false property summary may still pass
mechanical checks and need independent review. Abstentions remain unscored;
semantic-verification flags remain false.

The module performs no application IO or environment lookup on reload. Offline
dummy-provider encoding changes only the instruction string for Responses and
Chat; context, system message, schema and provider settings remain identical.
No real credentials are loaded and no request is sent.

## Offline verification

The new test file runs **22 checks**: the 14 existing authored branch/property
controls through the revision's delegates, plus eight checks of prompt changes,
drift rejection, schema/provenance/completeness guards, factory/method separation,
import behavior and actual JSON encoding. They verify contract mechanics and
explicit fixture-review consistency, not model behavior or discovery accuracy.

All **188 focused triage tests** and **1,168 full-suite tests** pass. These are
offline regression checks, not a fresh model-quality measurement. The read-only
preservation check verifies **577 earlier artifact hashes**, all **12 real table
hashes**, frozen code and every reservation/allowance row before and after testing.
The ledger remains unchanged at **498 reservations / USD7.4727990
conservatively reserved**, not invoiced spending. No cap reset or paid execution
is part of this work.

The revised prompt has 6,684 characters; its UTF-8 SHA256 is
`dde418f150a00fd90b30e8a8c5725ceb91f262a60e82942f8d7737252ceaa1d7`.

Post-test replay reproduces the same nine saved cards, eight known facets,
28 abstentions and bounded mean slice without regrading them. Separately, all nine
original contexts encode with an explicit dummy `gpt-6-luna` configuration, with
only the instruction string changing and each full JSON body under 180,000 bytes
(maximum **151,788 bytes**). CLI startup help also passes. This is context
feasibility, not a paid-execution protocol or
proof of live remote acceptance. Private artifacts stay in
`data/missing-link-triage-branch-prompt-2026-10-05/`.

## Next step

Obtain a narrow Codex review and green CI before freezing a separately authorized
model comparison with exact request hashes and conservative reservations. Keep
historical cards and unknown charges unchanged. No automatic retry, production
promotion, ranking change, isolation, interface or key-entry feature follows from
these offline checks. A later live result must independently assess conditional
return claims, useful local contrasts, genuine unknowns and the narrow mean slice.
