# Discover documented strategies

Discover can now investigate a technical idea from acquired documentation without
requiring an implementation in a supported language. This is an explicit opt-in
alongside implemented reuse, using the same Service, Provider, Store, GitHub reader,
allowances, cancellation and identity checks. It adds no acquisition backend,
runner, database table, native execution or automatic search retry.

## Use

The existing jobs API accepts `strategies: true` with AI-enabled `discover` or
`discover_from_request` and one `issue_url`. Source-first discovery also needs a
repository. `analyze`, structural-only jobs and behavioral execution cannot use
this flag. Existing jobs retain their original behavior and result contracts.

The ordinary CLI exposes the flag (substitute an actual public target issue):

```powershell
python scripts/investigate_missing_link.py --repo rvalavi/blockCV --issue https://github.com/OWNER/TARGET/issues/NUMBER --use-ai --strategies --report data/new-strategy-report.json
python scripts/investigate_missing_link.py --from-request --issue https://github.com/OWNER/TARGET/issues/NUMBER --use-ai --strategies --report data/new-request-strategy-report.json
```

These commands use the configured provider and **can spend its allowance**. They
were not run against a real provider for this change. Historical cohort ceilings
are not authorization for a new experiment. Strategy mode is available through
the CLI/API; it does not add a dashboard control or a code-proof export button.
The complete strategy is retained in the ordinary job result and CLI report.

Request-led mode still interprets the demand independently, compares with the
direct alternative, and may stop. Only a `search` decision uses the existing cap
of three queries, one metadata page of 20 per query and one inspected source.
Its planner and selector can now seek a documented mechanism rather than require
an importable implementation. Metadata still cannot prove pertinence or benefit.

For the selected source, strategy mode skips capability enrichment and code
compatibility evaluation. One strategy call sees only the already acquired
documentation plus the independent demand and bounded target context. It uses
the same prompt size, schema, public-text, reservation and attempt-retention
boundaries. With no documentation or a resolved/non-demand request, it makes no
strategy call. There are at most three proposals, not extra selected sources.

## Meaning of a result

`job.result.strategies[candidate_index]` contains the issue URL, whether any
documentation was acquired, and `items`. Each item records:

* The documented mechanism, supplied requirement IDs, relevance reason and
  `relevance`: `pertinent`, `undetermined` or `not_pertinent`.
* The proposed target adaptation, assumptions and limits, strongest direct
  alternative, expected advantage and a discriminating probe with baseline,
  change, success and failure criteria. These are hypotheses, not replacement
  acceptance criteria. The complete original request/requirements remain intact.
* Pinned source repository identity/revision and documentation evidence with
  original file, blob identity, lines and quotes, plus bounded-context coverage.
* `relevance_status: unverified_assessment`, `benefit_status: not_tested`,
  `implementation_verified: false`, `verification.status: not_executed`, and
  `qualified: false`. These fields are set locally; the model cannot promote them.

The model's relevance label is an interpretation, not a semantic proof. A citation
establishes where an idea was described; it does not establish applicability,
novelty, previously unknown information or improvement. A well-defined but
irrelevant analogy can be rejected. Unknown applicability and an empty result
are valid. A pertinent hypothesis needs adaptation, a direct comparison and a
probe; these requirements do not make that probe executed or sufficient.

Strategies are stored with the job, **not** in the qualified-reuse match table.
They do not create runnable bridge files or enter code-proof execution/export.
The ordinary code path still requires implementation context and its existing
qualification controls. A job cannot switch interpretation modes on CLI resume.

No benefit-demonstration workflow is added. To establish benefit later, a receiving
agent must actually apply the idea and show a concrete advance against the direct
alternative under the original criteria, without regressions. That evidence must
be reported independently; neither a generated claim nor a toy example promotes
this result to demonstrated benefit. No target modification is authorized merely
by a strategy proposal.

## Starting with the conserved blockCV source

The regressions reuse the exact README in the #133 acquisition, pinned to
[`51e6903`](https://github.com/rvalavi/blockCV/blob/51e6903fe652411248aa20937c80b122e5e12e09/README.md).
No new GitHub search or acquisition was used. The frozen #133 protocol and its
negative executable-retrieval outcome remain unchanged.

The authored positive fixture relates separated validation groups and checks of
prediction-domain separation to construction of excluded-prediction examples.
Its adaptation explicitly requires mapping dependency to shared references and
continuity, rather than copying spatial distances into RF. The direct alternative
is already available explicit masked refits. A grouping suggestion does not
recover an unrestricted unobserved clock, prove a cheaper refit algorithm or
demonstrate that changed grouping will improve G20. Conditional prediction must
not silently become whole-network causal forecasting.

Offline tests drive the real Provider transport interface with mocked responses
and the ordinary Service/Store for both explicit-source and request-led discovery.
They cover document-only and mixed code/document samples, source/requirement
binding, unknown/rejected/empty responses, unsupported benefit claims, failed
attempt retention, no implicit retry, existing code-only guards, atomic allowance,
cancellation/account checks, mode validation and CLI reporting/resume.

**These authored fixtures demonstrate software behavior, not autonomous model
quality, a useful native transfer, or an independently improved receiving agent.**
No paid API calls or Satellite writes, experiments, messages, PR updates or merges
were made for this change. Windows/Linux CI remains required before integration.
