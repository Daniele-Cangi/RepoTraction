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

The frozen protocol was committed as `7494090` before the first call. All five
initial jobs ran on 2026-09-30, 11:34–11:46 UTC, with identical repository-only
inputs. No rerun, manual import, candidate replacement, bridge execution or
product change was used. The cohort is domain-diverse but deliberately small and
language-biased (four Python projects, one JavaScript project), not random.

**Finding: autonomous retrieval works; an independently verified, previously
unrecognized actionable reuse opportunity was not demonstrated by this cohort.**
Missing Link selected external issues without operator hints and produced some
technically meaningful comparisons. Four of five jobs nevertheless failed. The
one complete job primarily rediscovered discussions already mentioning p-limit.
This is evidence of retrieval and comparison, not evidence of novel adoption,
successful integration, or a measured precision/recall rate.

### Initial-run accounting

“Candidates found” means deduplicated results within bounded search pages, not
validated matches or the entire GitHub search result set. “Discussions fetched”
does not mean requirements or compatibility analysis completed for all of them.

| Repository | Files / eligible | Candidates found / selected | Discussions fetched | Final job status | Stored match classifications | AI calls |
| --- | --- | --- | --- | --- | --- | --- |
| Pillow | 24 / 460 | 0 / 0 | 0 | Failed: unsupported source-line citation | None | 1 |
| Click | 24 / 156 | 52 / 3 | 1 | Failed: requirement quote validation | None | 2 |
| dateutil | 24 / 78 | 94 / 3 | 1 | Failed: requirement quote validation | None | 2 |
| NetworkX | 24 / 899 | 81 / 3 | 2 | Failed on second candidate's requirement quotes | 2 investigate; 1 rejected, all for first candidate | 4 |
| p-limit | 11 / 11 | 78 / 3 | 3 | Completed | 1 direct; 2 investigate; 2 rejected | 7 |

All 16 paid responses supplied token usage, including responses subsequently
rejected by validation. The cohort reserved **$0.2303699** conservatively;
reported-token estimates at configured prices sum to **$0.0569524**. These are
not an invoice, and reservations are not refunded on validation failure. The
shared allowance finished at **$0.5247254 reserved out of $2**, including the
pre-experiment $0.2943555. No ceiling or allowance ID was changed. The initial
jobs consumed 169 GitHub requests in total, separately from independent checks.

### Autonomously generated searches and selected issues

The four searches below were bounded/incomplete. Neither their counts nor a
missing result establishes absence of demand. All selected issues were external
to the input repository. Pillow failed before it could search.

| Input | Generated queries, in order | Selected candidates, in order |
| --- | --- | --- |
| Click | `iterable batching fixed-size tuples`; `augment usage errors BadParameter context`; `parameter processing order callback evaluation order` | [pytorch/text#664](https://github.com/pytorch/text/issues/664); [dask/distributed#5671](https://github.com/dask/distributed/issues/5671); [torchaudio-contrib#29](https://github.com/keunwoochoi/torchaudio-contrib/issues/29) |
| dateutil | `update timezone data tzdata mirror download`; `calculate Easter date Western Easter algorithm`; `relativedelta constructor calendar interval` | [positive-choi/rag#1](https://github.com/positive-choi/rag/issues/1); [OpenTranscribe#563](https://github.com/attevon-llc/OpenTranscribe/issues/563); [rpi-image-gen#168](https://github.com/raspberrypi/rpi-image-gen/issues/168) |
| NetworkX | `core decomposition node core number`; `k-core main core`; `k-shell core shell decomposition` | [FalkorDB/flex#102](https://github.com/FalkorDB/flex/issues/102); [apogee#174](https://github.com/LogOS-Development/apogee/issues/174); [jsjs#70](https://github.com/yoonbuck/jsjs/issues/70) |
| p-limit | `p-limit promise concurrency limiter`; `resumeNext concurrency slot scheduler`; `enqueue limited promise task async execution context` | [filemaker-odata#36](https://github.com/beezwax/filemaker-odata/issues/36); [magicdawn#186](https://github.com/magicdawn/magicdawn/issues/186); [pokemon2#3](https://github.com/ManoFardo-PR/pokemon2/issues/3) |

The p-limit search explicitly named the source package. That makes its results
particularly vulnerable to rediscovering existing references rather than finding
unrecognized needs. Selected candidates after a failure were not silently
replaced or credited as evaluated opportunities.

### Independent assessment after selection

1. **Pillow — no evaluable discovery.** The 24-file acquisition included root
   scripts, checks, build infrastructure and tests, but no `src/PIL` implementation
   file. The model cited `.github/compare-dist-sizes.py#L71-L91`, outside the
   supplied source spans. The provenance guard correctly refused the analysis;
   source selection also failed to represent the product. This is not evidence
   that Pillow has no reusable capabilities or external demand.
2. **Click — failed extraction, weak first lead.** The first candidate was a
   broad torchtext revamp discussion from 2019, last updated in 2021; its target
   repository is now archived. Its discussion was incomplete. Reconstructing the
   exact request context showed that the rejected quotation matches after only
   whitespace normalization: this particular rejection is a brittle exact-text
   check, not evidence of invented requirements. The other two selected issues
   never reached compatibility analysis.
3. **dateutil — failed extraction, poor first-candidate relevance.** The first
   issue was a Korean CPU installation guide, selected from a time-zone
   maintenance query. Three rejected quotations were not exact substrings of
   their supplied source, even after whitespace normalization. The calendar-sync
   issue is a possible lead by title only, not a completed match. No candidate
   reached compatibility analysis, so none is credited as useful.
4. **NetworkX — plausible algorithmic reference, not verified new adoption.**
   `core_number` and `k_core` genuinely address the algorithmic portion of
   FalkorDB/flex#102, while `to_networkx_graph` only constructs a graph and was
   correctly rejected. The target is JavaScript, however; the source mechanisms
   are Python and do not implement its `flex.exp.*` API. Independent inspection
   also found [flex PR #109](https://github.com/FalkorDB/flex/pull/109), open and
   unmerged at assessment, already proposing that implementation in JavaScript.
   The pipeline recorded the cross-reference but did not read its implementation.
   Keeping these matches as `investigate` was appropriate. The second candidate
   then failed on a non-verbatim requirement quote; the third was not analyzed.
5. **p-limit — relevant demand found, novelty and qualification not established.**
   Three issues completed comparison:

   - **filemaker-odata#36:** a current TypeScript client request for configurable
     HTTP concurrency, FIFO queueing and release after rejection. The source's
     `pLimit` code supports the limiter behavior, and independent target-code
     inspection found no concurrency setting in `src/client.ts`; `src/request.ts`
     directly calls Axios. This is a useful integration lead, but the issue
     itself already proposes p-limit. Complete client dispatch coverage,
     configuration and ESM/CJS compatibility still need implementation/validation.
     The model correctly retained `investigate`, not an integration claim.
   - **magicdawn#186:** personal learning/reference notes, with no issue body and
     comments already describing p-limit, a custom limiter, and a Mutex example.
     `pLimit` was labeled `direct` for generic concurrency, but the independently
     assessed discussion does not establish new unresolved adoption demand.
     This is an overqualified positive for discovery purposes, not a newly found
     customer need. The internal `resumeNext` helper was correctly rejected as a
     standalone concurrency/lock facility.
   - **pokemon2#3:** a substantial TCGdex ETL request needing much more than a
     scheduler. The benchmark subsystem was correctly rejected; the limiter was
     kept as `investigate`. A later automation-generated plan explicitly says
     “No `p-limit` or Axios” and proposes an internal limiter. The request prompt
     included that sentence, but the extracted requirements omitted it. Because
     this is a generated plan, maintainer acceptance/authority still needs review;
     it cannot be treated as either absent or automatically authoritative.
     Either way, adopting p-limit is not a qualified lead. Context was truncated,
     and the JSON handoff remained available while the inspection ZIP exceeded
     its size bound. Neither execution nor target integration was attempted.

The three rejected capability comparisons above are independently reasonable.
They do **not** offset the failed runs or establish a general false-positive
rate. The stored `direct` classification is reported unchanged; independent
assessment is separate and was not imported into Missing Link.

### What to fix before expanding the interface

No fixes were made during this experiment. The evidence points to reliability
work before adding features or presenting results as new opportunities:

- Sample real exported/product implementations before shallow infrastructure;
  expose why source coverage cannot represent a repository.
- Preserve quotation provenance while allowing harmless whitespace differences;
  do not weaken the guard to accept paraphrases or fabricated evidence.
- Isolate a candidate-specific validation failure so other selected candidates
  can finish, while visibly retaining the failed candidate and charged usage.
- Distinguish current demand from archived work, reference notes, prior adoption,
  and an existing implementation proposal. Package-name searches are not proof
  of an unrecognized reuse opportunity.
- Preserve later constraints and their authorship/authority through context
  selection and requirement extraction; incomplete or ambiguous constraints must
  block qualification, not disappear behind a similarity score.

This cohort supports continuing the project, but not a claim that autonomous
discovery is already reliable or uniquely insightful. UI improvements and key
entry remain deferred; credentials stay in the ignored local environment file.

### Revisions and persistent evidence

| Input | Source revision | Job ID | Reserved USD | Reported-token estimate USD |
| --- | --- | --- | --- | --- |
| Pillow | `b25d85356f296103f22c0127358f91536c53b399` | `738f348ea8304aa299472d07d631b6bf` | 0.0193209 | 0.0050846 |
| Click | `06b2a678741131fd577ce170e23e5ca0aeba0309` | `44d39f554ca54755809b14217621ab2b` | 0.0352906 | 0.0086937 |
| dateutil | `2642afacc33fb839c404b75b230fff58b79793f2` | `055f3520331b40b78ebc4da0c182b80e` | 0.0278130 | 0.0063047 |
| NetworkX | `92f497e2eb8192d1ce9205595f512294e4a9b696` | `97b0a1354b854aea8e6e838e3faccf25` | 0.0533808 | 0.0126765 |
| p-limit | `a8a6fbec4e0e866d6d779b10889bb4f5567e70eb` | `cf42c7de7a1a4dbba0db3e9e0403b3ac` | 0.0945646 | 0.0241929 |

The ignored local reports are `pillow.json`, `click.json`, `dateutil.json`,
`networkx.json` and `p-limit.json` in the directory named above. They contain
terminal job summaries and exported matches, including partial matches from the
failed NetworkX job. Checkpoints in the local account database retain discussion
snapshots and parsed model outputs, enabling the independent quotation/context
checks without additional paid calls. Private account state is not published.

Each primary run used the existing script, replacing only the fixed repository
and report filename, with no `--issue` or `--query`:

```sh
python scripts/investigate_missing_link.py --repo sindresorhus/p-limit --max-candidates 3 --use-ai --report data/autonomous-discovery-2026-09-30/p-limit.json
```

Do not rerun this command merely to reproduce the documentation: it starts a new
paid job and current GitHub discussions/search ordering can differ. No third-party
code was executed in this experiment. Automated code tests were not rerun for
this documentation-only branch; report accounting and frozen-input invariants
were checked against the five saved initial runs.

## Recovery cohort — protocol frozen before execution

After merging the reliability fixes in PR #10 (`691f1a2`), repeat the same five
repository-only inputs sequentially with the same three-candidate, 80-request,
eight-AI-call limits. These are **recovery runs**, not replacement primary results.
The original failures and assessments above remain unchanged. Current GitHub
revisions and search ordering may differ; this is not a controlled accuracy benchmark.

Use the existing OpenAI `gpt-6-luna` provider and unchanged shared allowance
`missing-link-verification-2026-09-30`: **$2 total**, with **$0.5247254** already
reserved before this cohort. No issue URLs, tailored queries, manual analysis
imports, candidate replacement or bridge execution are supplied. Save new raw
reports separately under ignored `data/autonomous-discovery-recovery-2026-09-30/`.
Assess selected candidates independently only after their run finishes, using
the original rubric; retain partial outcomes and charged validation failures.
No automatic retry is permitted, and no UI/key-entry features are added here.

### Recovery results

Protocol commit: `cceac41`, before paid execution. Runs used the merged product
code `691f1a2`, from 13:49 to 14:05 UTC on 2026-09-30. All five inputs retained
empty issue/query fields. Original reports were not overwritten. No code changes,
manual imports, maintainer corrections or third-party execution occurred during
the cohort.

**Reliability improved in candidate isolation, but autonomous useful novelty is
still not demonstrated.** Four jobs finished processing with explicitly partial
results, rather than aborting at a candidate validation error. None finished
without a failure: Pillow failed before search, and seven of twelve selected
candidates failed analysis validation. The five evaluated candidates produced
nine comparisons: six `investigate`, three `rejected`, no qualified positive.
These counts describe this small recovery cohort, not precision or recall.

| Input | Candidates found / selected | Discussions fetched | Outcome | Comparisons | AI calls |
| --- | --- | --- | --- | --- | --- |
| Pillow | 0 / 0 | 0 | Failed during capability interpretation | None | 1 |
| Click | 108 / 3 | 3 | Partial; 2 candidate errors | 1 investigate, 1 rejected | 6 |
| dateutil | 28 / 3 | 3 | Partial; 2 candidate errors | 1 investigate | 6 |
| NetworkX | 85 / 3 | 3 | Partial; 2 candidate errors | 2 rejected | 5 |
| p-limit | 78 / 3 | 3 | Partial; 1 candidate error | 4 investigate | 6 |

All searches remained bounded/incomplete. A finished job is not necessarily a
successful investigation; the script returned nonzero for every partial/failed
run, and continued to the next fixed repository without retrying a failed one.

#### Independent assessment of selected candidates

- **Pillow:** acquisition now includes `src/PIL` implementation, but the prompt
  still heavily represents Windows build infrastructure. Path heuristics label
  `winbuild/build_prepare.py` as implementation. The model cited
  `file:winbuild/build_prepare.py#L520-L538`; supplied spans were L520-L530 and
  L533-L538, leaving an actual gap. The provenance guard correctly rejected this
  wider citation. Fixing source acquisition alone did not fix prompt selection or
  model citation discipline; no demand search occurred.
- **Click:** generated searches named Click and returned
  [Click #730](https://github.com/pallets/click/issues/730),
  [Ollama #17778](https://github.com/ollama/ollama/issues/17778) and
  [TensorFlow #62523](https://github.com/tensorflow/tensorflow/issues/62523).
  Only the first completed comparison. It is a same-project ordering feature,
  not unexpected external reuse. Pinned `src/click/core.py` lines 168–192 sort
  by eagerness then invocation position, confirming that declaration-order
  precedence requires new policy and command-loop integration. The model kept
  that mechanism provisional and rejected `Context.invoke`, which invokes a
  callback rather than defining parameter-processing precedence. Incomplete
  cross-referenced discussion prevents a qualified current-demand claim.
  Ollama failed requirement-quote provenance; TensorFlow failed compatibility
  source-line provenance. They were not credited as evaluated matches.
- **dateutil:** searches centered on timezone archive updating, Easter and
  calendar intervals, but selected
  [syno-mihomo-gateway #75](https://github.com/czhaoca/syno-mihomo-gateway/issues/75),
  [MSB database #122](https://github.com/Gregovate/MSB-Production-Database-Project/issues/122)
  and [Android #59](https://github.com/Benjamin-Loison/android/issues/59).
  Only the settings-panel issue completed comparison. A timezone archive updater
  does not implement settings persistence, HTTP endpoints, migration or mutation
  auditing. Every mandatory check was `undetermined`; the result stayed
  `investigate`, with constraint blockers. Discussion also reports an already
  completed local implementation, without proving publication or adoption.
  This is a weak/overinclusive investigation lead, not useful new demand.
  The database candidate failed request quotations, and Android failed source
  citations during compatibility analysis.
- **NetworkX:** searches for core decomposition, k-core and k-truss selected
  [PySDKit #53](https://github.com/wwhenxuan/PySDKit/issues/53),
  [RH_Lean #163](https://github.com/OVVO-Financial/RH_Lean/issues/163) and
  [gam #2951](https://github.com/SauersML/gam/issues/2951).
  The first reports VMD memory usage for long signals, not graph decomposition.
  Pinned `networkx/algorithms/core.py` and `networkx/convert_matrix.py` confirm
  that `k_core` returns a graph subgraph and `to_scipy_sparse_array` constructs
  graph adjacency. Neither remedies signal-domain VMD history allocation.
  Both rejections are independently reasonable. The other two candidates failed
  request-quote validation and provide no evaluated reuse evidence.
- **p-limit:** selected the same three discussions as the primary run:
  [FileMaker #36](https://github.com/beezwax/filemaker-odata/issues/36),
  [magicdawn #186](https://github.com/magicdawn/magicdawn/issues/186) and
  [pokemon2 #3](https://github.com/ManoFardo-PR/pokemon2/issues/3).
  Pinned `index.js` still supports queueing and capacity release after fulfillment
  or rejection, but not client configuration or routing all FileMaker methods.
  FileMaker's issue itself suggests p-limit; this remains a useful known
  integration lead, not new discovery. Product documentation yielded a separate
  `investigate` comparison rather than implementation proof. Personal notes
  remain empty-body reference material: both `pLimit` and `limitFunction` are
  now blocked from qualification, fixing the primary run's misleading `direct`.
  pokemon2 failed request-quote provenance in this run, so the later prohibition
  was not freshly evaluated. Offline regression coverage of that guard is not a
  replacement for a completed real investigation.

No bridge was executed or target integrated. Correctly rejecting three capability
comparisons does not compensate for seven invalid candidate analyses, weak search
selection, or the absence of a newly verified actionable opportunity.

#### Cost and persistent evidence

The cohort used 144 GitHub requests and 24 paid responses. All responses reported
token usage. Conservative reservations added **$0.3818966**; reported-token
estimates at configured prices total **$0.0931035**, not an invoice. Failed
validation remained charged. The unchanged shared $2 allowance now has
**$0.906622 reserved**, leaving **$1.093378** of conservative headroom.

| Input | Source revision | Job ID | Reserved USD | Token estimate USD |
| --- | --- | --- | --- | --- |
| Pillow | `9d30729003b5dae074c60fa73d7cc135cccae734` | `87748e1eb662475ba6b2fa2d248269fa` | 0.0194454 | 0.0050853 |
| Click | `06b2a678741131fd577ce170e23e5ca0aeba0309` | `4b01cff5ac184eb1a9300bc01469e948` | 0.0966342 | 0.0230493 |
| dateutil | `2642afacc33fb839c404b75b230fff58b79793f2` | `36bbba94d8ca4095b9b8995b5718021d` | 0.1090991 | 0.0254475 |
| NetworkX | `92f497e2eb8192d1ce9205595f512294e4a9b696` | `1f352209b08e4e1ca2b76e41ad340a65` | 0.0802752 | 0.0206454 |
| p-limit | `a8a6fbec4e0e866d6d779b10889bb4f5567e70eb` | `aac1f972c7734b489cd3281b40937df4` | 0.0764427 | 0.0188760 |

Raw reports remain in the ignored recovery directory; account checkpoints retain
source/discussion snapshots and model traces. Only this public summary is committed.
The merged code's local suite passed 196 tests before this cohort; this recovery
branch changes documentation only. Protocol/accounting assertions were checked
against saved reports without additional model calls.

#### Next reliability work, before UI expansion

1. Keep source acquisition and actual prompt selection aligned, including build
   directories not recognized by today's path heuristic. Merely acquiring product
   code does not mean it reaches the model.
2. Tighten output guidance to supplied quote spans/source IDs without weakening
   provenance or silently retrying paid failures. Whitespace normalization did
   not solve all real citation failures.
3. Improve capability-to-demand query relevance and separate same-project work,
   existing package mentions and reference notes from unexpected external needs.
   Test improvements on new held-out repositories as well as this recovery set;
   repeatedly optimizing these five would not establish general discovery quality.

The safe conclusion is that conservative filtering and persistence improved,
while reliable autonomous discovery remains unproven. UI/key-entry work and
another paid cohort are deferred pending a decision on these remaining weaknesses.

### Offline discovery-qualification regression — 30 September 2026

After the source-context/citation fixes merged in PR #12, retrieval and discovery
qualification were tested locally against fixtures and the **already acquired**
recovery snapshots. This is regression verification, not another autonomous run:
no new GitHub candidate search, model response, manual analysis import, stored
match rewrite, publication or bridge execution occurred.

Automatic queries now remove source-package names, target open external issues,
skip unreviewed declaration filler and balance source modules within each
source/review tier. Sampling a different file cannot promote weak documentation
over reviewed implementation. Selection ranks the bounded pool and balances
projects/query provenance instead of retaining the first hits. These remain
lexical heuristics; a query such as graph core decomposition can still retrieve
an unrelated domain, and compatibility review must reject it.

Read-only application of the new qualification rules to saved comparisons gives:

| Saved discussion | Technical assessment retained | Separate discovery qualification |
| --- | --- | --- |
| Click #730 | 1 investigate, 1 rejected | Same-project work, not external discovery |
| syno-mihomo-gateway #75 | 1 investigate | Similarity only; no supported contribution |
| PySDKit #53 | 2 rejected | Not a usable connection |
| FileMaker #36 | 2 investigate | Existing package-name reference requires intent/identity review |
| magicdawn #186 | 2 investigate | Empty-body reference notes; demand not established |

Historical stored records are left untouched. New evaluations use analysis
contract **5**, derive qualification from acquired sources rather than accepting
model/import novelty claims, and preserve it in JSON/ZIP handoffs. A potential
external lead still has `novelty: unverified`; technical fit, execution,
integration and author awareness are separate questions.

The shared allowance remains **$0.906622 reserved out of $2**. No new AI spending
was incurred. A new held-out repository cohort is still needed to measure whether
these changes improve real autonomous discovery; this offline regression does
not demonstrate a new useful connection, precision, recall or generalization.
