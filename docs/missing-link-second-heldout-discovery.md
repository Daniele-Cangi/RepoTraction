# Missing Link second held-out cohort — 30 September 2026

## Frozen protocol

Product baseline: merged `main` **b46cad8**, including PR #16; analysis contract
**7**. This protocol is committed before the first paid investigation. No product,
prompt, provider or sampling changes are allowed during the cohort. Earlier
experiments and failures remain unchanged in their original reports.

The inputs below were selected before viewing any of their issues or search
results. Read-only account history confirms that none was a source repository in
a previous investigation. Metadata-only GitHub preflight confirmed all five
public and non-archived, with their canonical names unchanged.

| Fixed order | Source repository | Domain |
| --- | --- | --- |
| 1 | `yaml/pyyaml` | YAML parsing and serialization |
| 2 | `kurtmckee/feedparser` | RSS/Atom feed parsing |
| 3 | `jd/tenacity` | Retry policies |
| 4 | `agronholm/anyio` | Structured asynchronous concurrency |
| 5 | `sindresorhus/pretty-bytes` | Human-readable byte-size formatting |

This is a small purposive, language-biased exploratory sample: four Python
projects and one JavaScript project. It is not random, representative, or a
precision/recall benchmark. New source inputs do not guarantee that the pipeline
will discover issue URLs absent from earlier experiments; any overlap will be
reported, not replaced.

Run these repository-only inputs sequentially through the live local HTTP API:
`action=discover`, `use_ai=true`, `max_candidates=3`, `max_requests=80`, and empty
issue/query fields. Source acquisition retains the product's 24-file bound.
Automatic queries and candidate ranking remain unchanged. No manual analysis
imports, capability corrections, supplied issues, tailored queries, candidate
replacement, automatic paid retries, bridge execution or third-party publication
are permitted. Record empty, failed, partial and paused outcomes, including
charged validation failures. A transport/authentication failure stops paid cohort
work until its cause is understood; it does not trigger a login or paid retry.

Provider remains OpenAI **gpt-6-luna**, Responses with strict JSON schemas,
medium reasoning, and at most eight calls per job. Configured token estimates
remain $0.10 input / $0.50 output per million tokens, consistent with the
[official model page](https://developers.openai.com/api/docs/models/gpt-6-luna)
checked before this cohort. Per-job reservation ceiling remains **$2**.

The user explicitly raised the existing shared allowance
`missing-link-verification-2026-09-30` from **$2 to $4 total**, not $4 additional.
Before this cohort, conservative reservations were **$1.3833588**, leaving
**$2.6166412**. Keep the same allowance ID, account database and reservation
history; do not reset/refund reservations, enlarge limits further, or create a
new allowance. Unknown usage is not zero. These are application-side estimates,
not a provider invoice or a modification to OpenAI organization/project limits.
The ignored local `.env` and credential must never be committed or included in
reports.

## Assessment and evidence

Save raw reports separately under ignored
`data/second-heldout-discovery-2026-09-30/`. Keep source revisions, acquisition
coverage, queries, selected URLs, job IDs, provider traces, validation errors,
comparison classifications and derived discovery qualification in checkpoints
and reports. Do not overwrite previous cohorts.

After each initial result is saved, independently inspect only its selected
candidates and their pinned code/discussions. Distinguish processing success,
grounded contribution, complete mandatory compatibility, current actionable
demand, prior reference/use, novelty, execution, integration and adoption. A model
label or absent reference is not independent proof of a new useful connection.
Describe rejected false positives and incomplete comparisons alongside any
supported connection. No winner is required or manufactured, and no interface
features or isolated bridges are added during this discovery cohort.

The known root-level `__init__.py` relative-import limitation was intentionally
deferred by the user. Flat/`src` layout selection and public-class sampling fixes
are included in the frozen product baseline. Those static hints still are not a
complete Python import resolver, dependency closure, or execution proof.

## Results

Pending initial cohort execution. This section will be appended only after the
frozen protocol commit; original scope and negative outcomes will be preserved.
