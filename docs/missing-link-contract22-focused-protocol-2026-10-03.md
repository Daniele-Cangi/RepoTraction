# Missing Link: frozen contract-22 focused retest

This protocol is committed before any new paid call. It follows the merge of
[PR #41](https://github.com/Daniele-Cangi/RepoTraction/pull/41), whose final targeted
review found no major issues. The executable baseline is
`93eafcfef84dd465680c0ae33f8cd272153296ec`, analysis contract **22**.
Documentation commits may follow; executable code and provider settings must not
change during the experiment.

## Question and prescribed inputs

Does a fresh repository-only discovery use the actual selected implementation
and distinguish its bounded contribution from unsupported integration?

Run these three inputs once, in this order:

1. `sindresorhus/escape-string-regexp`
2. `colinhacks/zod`
3. `theskumar/python-dotenv`

These repositories are selected because the earlier evaluation exposed relevant
attribution risks. This is a **focused retest**, not a blind benchmark or an
independent discovery cohort. Previously selected issues and analyses are not
supplied. Different discovered requests also prevent a controlled before/after
accuracy comparison.

Each job uses only `repository -> Discover`: empty issue URL and query, AI enabled,
three maximum candidates and 80 maximum GitHub requests. The production
`scripts/investigate_missing_link.py` calls the same local HTTP API as the UI.
No manual analysis import, source-code execution, bridge execution or external
publication is permitted. Babel remains paused.

## Provider and spending freeze

Keep the existing OpenAI provider unchanged: `https://api.openai.com/v1`,
`gpt-6-luna`, Responses API, streaming, strict JSON schema and medium reasoning.
Limits remain eight calls per job, USD 2 per job, 180,000 encoded request bytes
and 12,000 maximum output tokens. Never print or commit the API key.

The original cumulative allowance `missing-link-verification-2026-09-30` remains
**USD 10**, with the starting ledger at **389 reservations / USD 6.0337989**.
There is no replacement allowance or reset. This experiment adds at most
**USD 0.60 in conservative reservations**. At the configured standard rates,
USD 0.10 per million input tokens and USD 0.50 per million output tokens, the
maximum reservation is:

```text
one call: ((180000 + 2048) * 0.10 + 12000 * 0.50) / 1000000 = USD 0.0242048
three jobs, eight calls each: 24 * 0.0242048 = USD 0.5809152
```

Rates and model support were checked in the
[official Luna documentation](https://developers.openai.com/api/docs/models/gpt-6-luna).
Reservations are a conservative product guard, not the vendor invoice. Reported
token usage estimates remain a separate measure; unknown paid outcomes stay
charged in the ledger.

Before spending, check account identity, free model availability and public,
non-archived repository metadata. Freeze safe provider fingerprints, the actual
ledger, historical job/match/snapshot payload hashes, reservation rows and older
evaluation report hashes. Restart the owned local evaluation server on merged
code, without starting the analytics collector, and check the browser/API flow.

## Stop rules and evidence

Run sequentially. Recheck frozen code, provider, account and absence of active
jobs before each input. A fresh job's maximum possible reservation must fit the
segment ceiling. Stop on the first driver failure or non-completed job. Do not
replace a repository, automatically retry, resume, change settings or repair
code mid-experiment. Retain any acknowledged job ID and receipt uncertainty.

Reconcile real reservations, receipts, JSON outputs, persisted jobs and HTTP
exports. Verify old immutable payloads, reservation prefixes and reports are
unchanged. Inspect raw model answers as well as normalized assessments, including
operation-local body citations, unsupported sibling/declaration evidence, partial
mechanisms, extraction failures and unknown integration requirements.

A useful grounded primitive is not automatically a qualified complete match.
Report useful contributions and rejected false positives only when the actual
fresh output supports them. Zero eligible matches is a valid observed outcome,
not permission to select a positive case manually. Forced isolation and UI/key
entry changes remain deferred until there is an eligible grounded match.

The result report must name the observed inputs and issues, code/settings freeze,
spending, missing receipts/errors, preserved history, useful/rejected cases and
remaining limitations. This small retest cannot establish universal discovery
quality or semantic correctness from citation provenance alone.
