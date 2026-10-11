# Independent-contract pilot: calls completed, utility comparison pending

On 2026-10-11 the authorized pilot completed all 12 frozen proposal calls through
the existing Provider, Budget, Store, account verifier and worker lease. Four
discussions yielded one contract each; eight returned `undetermined`. No retry,
validation failure or transport failure occurred. This establishes that the new
proposal path can produce cited, executable example data from real discussions.
It **does not yet establish a useful software connection or improved discovery**.

The [fixed protocol](missing-link-independent-contracts-protocol.md) requires an
independent, source-blind technical judgment and separately frozen challenge
cases before source matching. That judgment is still pending. The assistant
running this pilot already knew the source families; its observations below are
not an independent reference. No acquired source was executed in this pilot.
The earlier synthetic WASI controls remain separate evidence.

## Scope, identity and accounting

- Code: `5fdad305def8d371d81935d3475eff1180206bb9` (merged PR #115).
- Protocol: `19f5deb`; behavioral baseline: `c1d2d67`.
- Inputs: the unchanged 12 discussions in the
  [frozen corpus](../tests/fixtures/independent_behavior_contracts/corpus.json).
  No new GitHub acquisition, replacement or relevance-based filtering.
- Corpus byte SHA-256:
  `38e39c089ede4b23b823cec55beb338986f06acf40d0ca45ea8dec0261a84fde`.
- Model: `gpt-6-luna`, Responses API, strict JSON schema, medium reasoning,
  streaming, `store:false`, output cap 12,000 tokens per call.
- New authorized allowance: `independent-contracts-pilot-2026-10-11-authorized`,
  USD **0.20**, 12 attempts. No historical allowance reused or configuration file
  changed. The user's authorization allowed more if needed; no increase was needed.
- Execution used the existing components in a one-off local invocation, not a
  new runner or a full Service investigation. Normal capabilities, demand
  disposition and compatibility AI phases were not called. In particular, this
  isolated proposal sample does not measure the ordinary Service disposition gate.

| Measured quantity | Result |
| --- | ---: |
| Completed native responses / attempts | 12 / 12 |
| Proposed / undetermined / invalid discussions | 4 / 8 / 0 |
| Proposed contracts | 4 |
| Model-authored example/check cases (2 labelled explicit, 9 inferred) | 11 |
| Serialized request bytes, total | 652,160 |
| Request bytes, minimum / maximum | 14,405 / 142,747 |
| Reported input / output tokens | 173,693 / 13,583 |
| Persisted conservative reservation | USD 0.1396736 |
| Cost calculated from reported usage at configured prices | USD 0.0241608 |
| Total timed loop | 139.429 s |
| Sum of rounded per-proposal durations | 139.057 s |
| Qualified / integrated connections | 0 / 0 |

The cost is calculated from reported tokens at USD 0.10 / million input tokens
and USD 0.50 / million output tokens; it is not an independently reconciled invoice.
Reservation remains conservative and is not the billed amount. Per-call durations
include local context preparation, existing controls, transport and validation;
they are not model inference times. The approximately 0.372 s difference between
the loop and the sum is not a measurement of control overhead: controls also run
inside the calls, and durations were rounded. No stage-level timing or repeat-run
benchmark was collected. The historical 11-call forensic experiment used different
work and controls; this result does not establish a like-for-like speedup over it.

## Outcomes on the fixed pool

Indices are zero-based and preserve the original sample order. Reasons are
summaries of model output, not adjudicated explanations for absence of demand.

| Index / discussion | Output | Seconds | Operation or model's abstention reason |
| --- | --- | ---: | --- |
| 0 CPython #47369 | undetermined | 9.520 | Deep pickle nesting: scope and JSON representation unresolved |
| 1 ghettoq #2 | undetermined | 4.741 | Queue cleanup/performance semantics unspecified; fix mentioned |
| 2 PyBrain #71 | proposed | 16.992 | Number of batches from length and batch size |
| 3 CSL schema #70 | undetermined | 5.580 | Optional versus removed document ID; processor ID distinction |
| 4 CPython #42664 | proposed | 31.817 | Parse duplicate cookie names, retaining the first value |
| 5 SymPy #4238 | undetermined | 6.012 | Symbolic function/printer interface and output unresolved |
| 6 translate #582 | proposed | 19.684 | Suggest threshold-option settings when all terms are removed |
| 7 Twisted #3584 | undetermined | 4.897 | SIP states, messages, timing and outputs insufficiently specified |
| 8 CPython #42255 | undetermined | 5.830 | Event-loop redesign lacks settled executable semantics |
| 9 CPython #43521 | undetermined | 7.143 | Gzip opt-in/default, layering and safety choices unresolved |
| 10 CPython #44626 | proposed | 20.414 | Fully qualified Windows path classification, reported fixed |
| 11 SymPy #3461 | undetermined | 6.427 | Symbolic representation and conflicting proposed semantics |

The fixed baseline's first three remain indices **8, 1, 5** for every source
family. All three returned `undetermined`; all four proposals lie outside that
selection. This is an observed availability difference, **not four missed useful
opportunities**. Ranking and the ordinary three-candidate limit were unchanged:
top-three changes = **0**. There is no new baseline run or tuned selector.

## Preliminary semantic observations, not independent judgments

**PyBrain #71:** `[5, 2] -> 3`, `[4, 2] -> 2`, `[0, 2] -> 0` follow the
batch-count formula explicitly supplied in the issue. They do not address the
random permutation, order/content distinction or batching integration. The model
states these omissions. Recovering a small formula already present in the request
does not demonstrate an advantage from importing another project's implementation.

**CPython #42664:** the discussion explicitly shows
`SimpleCookie('foo=33;foo=34')` producing `Set-Cookie: foo=33` with a proposed patch
([saved comment reference](https://github.com/python/cpython/issues/42664#issuecomment-1094014535)).
The model preserves parsing/serialization, rather than silently replacing it with
generic list deduplication. Its second case changes the name and values only;
cookie syntax, quoting, attributes and compatibility are not covered. Later
comments discuss an existing external library and uncertainty over changing the
standard library. Neither unmet need nor reuse advantage is established.

**translate #582:** suggesting thresholds is supported by a
[discussion comment](https://github.com/translate/translate/issues/582#issuecomment-50275603).
The model invents an explicit interface (a boolean plus two mappings), ordered
option-string outputs and suggested values equal to observed maxima. It correctly
labels these cases inferred and leaves runtime unknown. The final acquired comment
reports that `--locs-needed=1` still produces no terms while `=0` produces output
([reference](https://github.com/translate/translate/issues/582#issuecomment-50275606)).
That does not directly refute the model's invented numeric example, but it prevents
treating the earlier `=1` advice as verified resolution of the actual case.
The proposal's prose also alternates between "terms were removed" and "all terms
were removed"; only the latter is its intended trigger. Independent review must
settle the operation and assumptions before any positive matching claim.

**CPython #44626:** the model explicitly cites the
[reported Python 3.13 fix](https://github.com/python/cpython/issues/44626#issuecomment-1890363203)
and later acceptance discussion. It proposes the already implemented fully
qualified-path interpretation, excluding the remaining rooted-path/relative-path
API and security questions. Even a successful implementation match would not
establish a new unmet opportunity for this suboperation. This is a warning against
equating `proposed` with `actionable`; it is not evidence that the ordinary
Service's earlier disposition gate fails, since that gate was not run here.

For the eight abstentions, the model often identifies a real engineering problem
but cannot specify it as a small JSON input/output operation from available text.
Abstention is not proof of irrelevance. Missing context, representation limits and
genuinely unsettled requirements must remain distinct until independently reviewed.

## Frozen evidence and remaining decision

The new [evidence directory](experiments/independent-contracts-pilot-2026-10-11/README.md)
contains the original preflight manifest, final persisted job with all raw decoded
model outputs and resolved citations, an unjudged review form, discussion-only
review input and offline verification results. Historical fixtures and preparation
results were not rewritten. All 12 outputs re-decode identically, request hashes
and sizes match their respective serialization conventions, the persisted job
equals its export, and public redaction leaves accepted proposals unchanged.

No independent judgments or independently authored challenge cases exist yet.
Consequently useful relations added/lost, interpretation accuracy, false-positive
rate, behavioral matches/failures and reuse advantage are **unmeasured**, not zero.
There are zero qualified leads because none has passed the required steps.

The next bounded activity is to review the frozen discussion-only packet and
proposals without candidate source knowledge, recording real unmet demand,
operation fidelity, representation assumptions and separate challenge examples.
Freeze that judgment before running the existing WASI comparison. Do not add
adapters, expand extraction, rewrite expectations or tune prompts to rescue these
four proposals. A code-review approval of this PR is not that semantic adjudication.

The pilot does not justify a new infrastructure phase, larger candidate limits or
a stronger model by itself. Its concrete functional concern is the gap between
an executable suboperation and a still-useful request: one proposal is explicitly
resolved, another extracts a formula already supplied, and another needs invented
interface semantics. Completing the independent judgment determines whether to
test any useful relations or instead address this interpretation/reuse boundary.
Retrieval coverage remains a separate observed limitation, not yet a demonstrated
cause of lost useful connections.
