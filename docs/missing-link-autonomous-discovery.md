# Missing Link autonomous discovery experiment

## Frozen protocol — 2026-09-30

Question: can repository-only discovery surface a previously unselected,
technically useful public request, rather than reproduce a handpicked example?
This is a small exploratory cohort, not a benchmark of general discovery accuracy.

Baseline: merged `main` commit `624e62f`. No product/UI/provider changes during
the experiment. The cohort was fixed before inspecting any issue or result:

| Repository | Domain | Sampling caveat |
| --- | --- | --- |
| `python-pillow/Pillow` | Image processing | Native components; Python acquisition is partial. |
| `pallets/click` | Command-line interfaces | Runtime/integration constraints still require assessment. |
| `dateutil/dateutil` | Date/time parsing and recurrence | Time-zone/data-version assumptions may block reuse. |
| `networkx/networkx` | Graph algorithms | Large codebase; a 24-file sample is not full coverage. |
| `sindresorhus/p-limit` | JavaScript async concurrency | Partial JS/TS declaration analysis, not a full parser. |

Every initial job receives only `repo`, `action=discover`, `use_ai=true`,
`max_candidates=3`, `max_requests=80`; `issue_url` and `query` are empty. Queries
and candidate issues must be generated/selected by Missing Link. No manual
analysis import, maintainer corrections, tailored queries, candidate replacements,
code execution or third-party publication are permitted in these initial runs.
The UI's review step is bypassed through the existing explicit local API to test
the autonomous pipeline rather than operator curation.

Provider: existing OpenAI `gpt-6-luna`, strict Responses contract, maximum 8 calls
per job. The existing shared **$2** allowance is not reset or increased. Starting
conservative reservations: **$0.2943555**; remaining ceiling: **$1.7056445**.
Unknown usage is not zero; reservations and reported token estimates are separate.
Jobs run sequentially. Failure, empty search, pause and omitted context all count
as outcomes. No rerun is used to replace an unsuccessful primary result. An
explicit recovery, if necessary, must be labeled separately with its cost.

## Assessment rubric

Review only issues returned by the pipeline, after each initial run is saved.
Report each repository and candidate, including negative results:

- Acquisition and context coverage, generated queries, search sample and actual
  candidate count; exact repository revision and persistent job IDs.
- Same-project issue versus external-project discovery. A previously unselected
  same-project issue is not an unexpected cross-project reuse opportunity.
- Request actually unresolved/current enough to be actionable, versus resolved,
  obsolete, bot-generated or too incomplete to assess.
- Existing contribution cited to actual code, all mandatory constraints examined,
  and bridge work/assumptions distinguished from functionality already present.
- Useful lead, plausible-but-unverified lead, correctly rejected false positive,
  incorrect positive, or no evaluable result. Model classification alone is not
  independent validation or successful target integration.

Novelty here means **not supplied or inspected in advance in this experiment**,
not novel to the world or proof that a human could never discover it. Stronger
evidence would be a genuinely useful external request with a concrete reuse path;
this still needs independent technical review and, later, target integration.

Local raw reports are stored under ignored `data/autonomous-discovery-2026-09-30/`.
The account database retains checkpoints, queries, issue snapshots, AI traces and
cost reservations. Do not publish credentials, account databases or private data.

## Results

Pending initial cohort execution. This protocol is committed before execution;
results will be appended without changing cohort, inputs or evaluation rules.
