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

Protocol frozen in commit **34abaa0** before the first job. All five initial runs
finished on the unchanged baseline. Two completed without candidate errors; three
completed partially. No failed candidate was retried or replaced. Previous cohort
results remain in [the autonomous discovery report](missing-link-autonomous-discovery.md).

### Processing results, not a success-rate benchmark

| Source | Files acquired / eligible | GitHub reads | AI calls | Conservative reservation | Stored comparisons |
| --- | --- | --- | --- | --- | --- |
| JSON Schema | 24 / 65 | 45 | 6 | $0.0868597 | 4 rejected; partial, one invalid quote |
| SQLparse | 24 / 64 | 45 | 7 | $0.1047475 | 2 investigate, 2 rejected |
| Markdownify | 16 / 16 | 37 | 7 | $0.1120381 | 4 rejected |
| DiskCache | 24 / 49 | 45 | 6 | $0.0861640 | 1 adapter, 3 rejected; partial, one invalid quote |
| Nano ID | 24 / 32 | 42 | 6 | $0.0869275 | 3 rejected; partial, one request-extraction failure |

Totals: **214 investigation GitHub reads, 32 AI calls, 15 selected issues,
12 issues compared, 19 stored comparisons**. Multiple capabilities can be compared
with the same issue; comparison counts are not independent opportunities. The
within-job deduplicated search pools were respectively 101, 115, 109, 113 and 11.
These are retrieved candidates, not relevant requests or matches. Every job used
the frozen three-candidate cap; search and repository/prompt coverage remain bounded.
Even acquiring all 16 eligible Markdownify files does not establish complete
prompt coverage, whole-repository coverage or execution.

Derived qualifications: **14 `not_a_fit`, 2 `similarity_only`, 2
`reference_review`, 1 `external_lead`**. All novelty fields remain `unverified`.
The sole external lead is tentative after independent inspection; this experiment
does **not** establish a new, integrated or adopted solution. No bridge was run.

### Automatically selected issues and independent assessment

These URLs came from the pipeline, not operator-supplied issues. Issue text and
generated files were treated as untrusted evidence, never execution instructions.
Independent follow-up inspection used public GitHub APIs after each initial report
was saved, without feeding corrections back into the jobs.

**JSON Schema** — queries: `python json schema file validation`, `python json
schema format validation`, `python json schema regex property validation`.

- [aipr #127](https://github.com/yunaremaia/aipr/issues/127): CLI validation and
  format-checker comparisons rejected. The request needs a project-specific policy
  schema, multiple input formats and CLI integration. Those deliverables are not
  already supplied by the compared mechanisms. However, schema validation can be
  a useful partial contribution; rejection of the entire feature is not proof
  that the library cannot help.
- [UCP #817](https://github.com/Universal-Commerce-Protocol/ucp/issues/817): no
  comparison; requirement extraction failed exact supplied-context quote validation.
- [AFD #310](https://github.com/lushly-dev/afd/issues/310): CLI and
  `additionalProperties` callback rejected as end-to-end solutions. Command
  registration, error-shape mapping and conformance tests remain new work. The CLI
  comparison nevertheless records a supported strict-type contribution. This is
  another reason not to equate the final rejection with zero reusable value.

Important source-coverage failure: acquisition omitted **`jsonschema/validators.py`**,
the public validation engine, while retaining the CLI and keyword callbacks.
Independent pinned inspection confirms
[`validate` and `validator_for`](https://github.com/python-jsonschema/jsonschema/blob/51cd75e399c760e5aa3adce600dcce1385756ab0/jsonschema/validators.py#L1267),
alongside Draft 7 and Draft 2020-12 validators. The acquired/prompt sample therefore
does not adequately represent the library's principal reusable API. This creates
a false-negative risk; it does not justify manually upgrading these results.

**SQLparse** — queries: `python sql parsing`, `python sql tokenization`,
`sql delimiter matching`.

- [Lakebridge #2283](https://github.com/databrickslabs/lakebridge/issues/2283):
  `parse` is `investigate`; lower-level tokenization rejected. Independently checked
  [`parse` / `parsestream`](https://github.com/andialbrecht/sqlparse/blob/60cdc649726bf1bc4f1b336050560b336da715ec/sqlparse/__init__.py#L20)
  consume SQL text and produce grouped statements. They do not extract SQL from
  Python/PySpark source. The generated AST adapter is an unexecuted example for
  literal `spark.sql` calls, not proof of target integration or all input forms.
  This is a plausible partial mechanism, not a qualified solution. The model's
  phrase "supplied issue" refers to the pipeline-fed context: no human supplied it.
- [DuckDB Python #338](https://github.com/duckdb/duckdb-python/issues/338):
  `investigate`, but the issue explicitly proposes using DuckDB's `sql_tokenize`
  table function. An unrelated SQL lexer does not perform that migration. Do not
  interpret the non-rejected label as an actionable connection.
- [SQLFluff #8564](https://github.com/sqlfluff/sqlfluff/issues/8564): generic
  `split` rejected. Its
  [entry point](https://github.com/andialbrecht/sqlparse/blob/60cdc649726bf1bc4f1b336050560b336da715ec/sqlparse/__init__.py#L63)
  delegates generic statement splitting; this does not demonstrate the requested
  statement-position MySQL/MariaDB `SOURCE` lexer support, filename rules and alias.
  Rejecting it as an existing drop-in solution is appropriate. Bounded source and
  incomplete target discussion cannot prove absence of every possible adapter.

**Markdownify** — queries: `python html conversion cli`, `python html to
markdown api`, `python recursive html tree markdown`.

- [InVEST #2657](https://github.com/natcap/invest/issues/2657): HTML conversion
  CLI rejected for an RST-to-Markdown/docstring-tooling migration. Shared Markdown
  output does not make the input formats or documentation pipeline equivalent.
- [Yetimail #16](https://github.com/hiasinho/yetimail/issues/16): converter and
  anchor handler rejected for a behavior-preserving MIME/message-parser extraction.
  Independent inspection of
  [`convert_a`](https://github.com/matthewwithanm/python-markdownify/blob/bc98c9e134ec55b2853716ab859754f061cb7054/markdownify/__init__.py#L438)
  confirms it emits supplied anchor destinations without an HTTP(S)-scheme check.
  It cannot be substituted as-is for the required restricted link handling.
  This is a concrete false-positive rejection, not a claim that Markdownify is
  unsafe for its intended conversion use. Unresolved constraint hints also block
  positive qualification.
- [Plone REST API #1997](https://github.com/plone/plone.restapi/issues/1997):
  HTML-to-Markdown conversion rejected as bidirectional blocks/Markdown and HTTP
  negotiation support. New block mappings, reverse conversion and endpoint glue
  are absent from the compared API. Constraint review and discussion coverage are
  incomplete; no third-party contact or implementation followed.

**DiskCache** — queries: `portable cache key hash`, `django persistent cache
backend`, `python sqlite key serialization`.

- [Telemeta #11](https://github.com/Parisson/Telemeta/issues/11): `DjangoCache.set`
  classified `adapter` / `external_lead`; low-level `Disk.store` rejected. Independent
  [adapter inspection](https://github.com/grantjenks/python-diskcache/blob/ebfa37cd99d7ef716ec452ad8af4b4276a8e2233/diskcache/djangocache.py#L139)
  confirms Django key/expiry handling, backend set/get and a `FanoutCache` instance.
  This is a real integration mechanism, but the opportunity is weak: the issue was
  opened in **2014**, last updated in **2017**, and gives only a cache example without
  naming the data or acceptance tests. "Non-persistent" may mean transient
  application data or strictly non-durable storage; the disk-backed adapter cannot
  be assumed to satisfy the latter. Current target
  [`setup.py`](https://github.com/Parisson/Telemeta/blob/c47d9c1a1ec25153320ac0164e29818716e21bba/setup.py#L52)
  pins Django 1.8, while the acquired DiskCache package requires Python 3. Target
  runtime/version compatibility has not been demonstrated. The non-archived flag
  and an open issue do not establish current demand. Retain the original label as
  an experiment outcome, but do not count it as an independently validated useful
  or novel connection.
- [Ambora #43](https://github.com/xetorthio/ambora/issues/43): no comparison;
  requirement extraction failed exact supplied-context quote validation.
- [LangGraph #8942](https://github.com/langchain-ai/langgraph/issues/8942): JSON key
  encoding and generic value storage both rejected. They do not implement the
  requested SQLite checkpoint metadata helper, synchronous/asynchronous saver
  changes or filter/regression tests. Shared SQLite/serialization vocabulary is
  not a compatible saver contract.

**Nano ID** — queries: `node js web crypto chunked random`, `browser unbiased
random string generator`, `java script noncryptographic random id`.

- [Devops #47](https://github.com/DEVOPSIN77/Devops/issues/47): random bytes
  rejected against a broad Express/Node practice sheet. This is retrieval noise,
  not demonstrated unmet demand. It should not be promoted because it is an open
  issue containing relevant language keywords.
- [s3nd #20](https://github.com/AbderrahmaneMouzoune/s3nd/issues/20):
  `customRandom` and `customAlphabet` rejected / `reference_review`. The issue
  explicitly describes existing Nano ID use and asks to remove the dependency,
  with an `INVALID_CONFIG` error for alphabets over 256 characters. Independent
  [pinned implementation inspection](https://github.com/ai/nanoid/blob/bb68abcd59ebb86a849d634320726add6be54d47/index.js#L96)
  confirms the oversized-alphabet branch delegates to `customRandom` rather than
  raising that error. Reuse as-is is a false positive, and the connection is already
  known to the author. Extracted rejection-sampling logic plus new validation may
  still contribute, but it is neither novel discovery nor verified integration.
- [blog #51](https://github.com/JChehe/blog/issues/51): no comparison. The model
  supplied no grounded requirement, so extraction validation rejected the reading
  notes instead of inventing an actionable request. No paid retry.

Query strings above omit the common appended `is:open in:title,body -repo:SOURCE`
wrapper; the API also enforces `is:issue is:public`. All selected issues were
external to their source repositories. The first four sources each read two pages
per query (40 raw hits per query); Nano ID read one page per query (8, 3, 0 raw hits).
No search, including a zero-hit query, establishes exhaustive demand coverage.

### Reproduction identifiers

| Source | Pinned source revision | Job ID |
| --- | --- | --- |
| JSON Schema | `51cd75e399c760e5aa3adce600dcce1385756ab0` | `23faabdcc1604b4d902474bc75b6d803` |
| SQLparse | `60cdc649726bf1bc4f1b336050560b336da715ec` | `e1b9cd886c30462faa364d4b1536713f` |
| Markdownify | `bc98c9e134ec55b2853716ab859754f061cb7054` | `c1154c73ba8b4fe2a439b7917fdfb0ee` |
| DiskCache | `ebfa37cd99d7ef716ec452ad8af4b4276a8e2233` | `b79d262a4f5f4de7a6e6427dd1dd0689` |
| Nano ID | `bb68abcd59ebb86a849d634320726add6be54d47` | `c5fed4a09719453182e6fe23c77700d2` |

Account checkpoints retain discussions, source excerpts, exact query/selection
provenance and provider traces. Public issue pages can change after collection;
source code links above are revision-pinned. JSON Schema and Ambora quote failures
were candidate-local `invalid_candidate_analysis`; Nano ID's notes issue failed
the minimum-one-grounded-requirement rule. These are not transport/auth failures
and did not block later cohort inputs. All three remain charged and visible.

### Budget and verification

This cohort conservatively reserved **$0.4767368**. Reported token usage at the
configured prices estimates **$0.1122062**, not an invoice or refund. The persistent
shared allowance now reserves **$1.3833588 of $2**, leaving **$0.6166412** under the
same budget ID. The allowance was neither reset nor increased. Independent public
API inspection and local mock tests are outside the investigation-read counts;
they made no additional AI calls.

- `python -m unittest discover -s tests -q`: **248 tests passed**.
- Read-only browser verification before the cohort and again for the four new
  DiskCache cards: **no JavaScript errors, no mutation requests, no mobile overflow**;
  four inspection-package links available in the latter check. The configured
  browser CLI was unavailable, so the existing Playwright verification script was
  used. Export links/rendering do not prove a bridge runs.
- Live local API jobs and saved exports agree with read-only database checkpoints;
  no jobs remained running/queued after the cohort. Server stays available locally.
- No acquired/generated code execution, manual imports, publication to target
  projects, prompt changes or product changes occurred during these runs.

### What to fix before the next experiment

1. **Source acquisition:** preserve the actual exported validation engine and its
   bounded dependency context rather than overrepresenting CLI helpers. Add a
   regression for `validators.py` coverage without hardcoding one project.
2. **Contribution versus complete fulfillment:** represent a grounded partial
   mechanism separately from an incompatible requirement and missing target glue.
   Keep unsupported acceptance criteria and mandatory conflicts visible; do not
   relax guards to manufacture positives.
3. **Opportunity qualification:** an old, underspecified open issue is not current
   demand. Evaluate ambiguity and target manifest/runtime constraints before
   describing the Telemeta result as follow-up-ready. Preserve known-use/removal
   requests as prior references, not new connections.
4. **Provider reliability and retrieval noise:** keep exact-quote fail-closed
   behavior, diagnose the two quote failures, and distinguish study/practice notes
   from actionable requests. No automatic paid recovery was performed here.

The answer to the experiment question is therefore **not demonstrated yet**.
Missing Link autonomously retrieved external issues, exposed a real cache adapter
and refused several misleading matches. It has not yet demonstrated a new useful
connection that survives independent contextual review. These findings should
guide the next fixes before adding interface features or spending on another run.
