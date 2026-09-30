# Missing Link held-out discovery — 30 September 2026

## Frozen protocol

Baseline: merged `main` **602a9f7**, including PR #13. This protocol is committed
before the first investigation. No product, prompt, provider or sampling changes
are made during the cohort. The purpose is to test repository-only discovery on
five projects absent from all previous account investigation jobs, not optimize
the earlier five-project recovery set.

The cohort and order are fixed before inspecting issues or search results:

| Repository | Domain | Caveat |
| --- | --- | --- |
| `python-jsonschema/jsonschema` | JSON Schema validation | Schema/version/reference-resolution requirements may constrain reuse. |
| `andialbrecht/sqlparse` | SQL parsing and formatting | Tokenization is not a full validating SQL parser. |
| `matthewwithanm/python-markdownify` | HTML-to-Markdown conversion | Input/output dialects and dependencies require review. |
| `grantjenks/python-diskcache` | Persistent caching | Storage, process and runtime constraints may block adoption. |
| `ai/nanoid` | JavaScript ID generation | Partial JS/TS acquisition; randomness and runtime guarantees need evidence. |

Metadata-only preflight confirmed all five repositories public and non-archived;
no issue or candidate search was inspected. This is a small purposive,
language-biased exploratory sample (four Python, one JavaScript), not a random
sample or a precision/recall benchmark. Its issues are not known in advance.

Each initial job receives only `repo`, `action=discover`, `use_ai=true`,
`max_candidates=3`, `max_requests=80`, with empty issue and query fields. Existing
automatic query generation, ranking and provenance validation choose the sample.
Jobs run sequentially. No manual analysis import, capability correction, tailored
query, candidate replacement, bridge execution or third-party publication is
allowed. Failed, partial, paused and empty runs are reported, not silently rerun.
Candidate-local validation failures remain charged and do not replace candidates.
A transport/authentication failure is investigated before spending further.

Provider remains OpenAI **gpt-6-luna**, strict Responses schemas, at most eight
calls per job. The existing allowance `missing-link-verification-2026-09-30`
remains capped at **$2**, with **$0.906622** already conservatively reserved and
**$1.093378** remaining. No allowance reset, increased ceiling or new budget ID.
Persistent budget guards can pause the cohort; unknown usage is not zero and
failed validation does not refund reservations. Token estimates are not invoices.

Investigations use the live local HTTP API and existing investigation script.
Raw reports remain ignored under `data/heldout-discovery-2026-09-30/`; account
checkpoints retain source revisions, discussions, traces, selection decisions
and cost. Only a public, redacted summary is committed.

## Assessment

Inspect only candidates returned by the pipeline after initial runs are saved.
Separate processing success, grounded technical contribution and new discovery:
record acquisition/prompt coverage, queries, selected URLs, all validation errors,
job IDs, source revisions, classifications and derived discovery qualification.
Independently inspect code and discussion for any potential external connection,
including mandatory constraints, prior references, resolution and bridge work.
Report rejected false positives and unsupported/incomplete comparisons too.

Here, held-out means the input repositories and candidate issues were not used
in previous experiments or supplied in advance. No reference found does not prove
worldwide novelty or author unawareness. Even a useful external lead is not
verified execution, target integration or adoption. No bridge runs in this cohort.

## Results

Pending the frozen initial runs. Previous cohort results are documented separately
in [the autonomous discovery report](missing-link-autonomous-discovery.md).
