# Budget-matched assistance preparation: minimum-length cycles

Selected real request: [NetworkX #8128](https://github.com/networkx/networkx/issues/8128),
still open at acquisition. It asks whether minimum-length cycle enumeration can
avoid the work of enumerating all cycles and filtering. The maintainer explicitly
left the algorithm open. This is a feature/research request, **not evidence of an
agent currently blocked or a demonstrated production bottleneck**.

This PR freezes a comparison; it does not implement the feature, run solvers,
search donors, generate an assistance packet or spend API budget. No product,
transport, runner, workflow or historical evidence changes are included.

## Verified starting point

Pinned NetworkX: `9d866a5f447d9fe1c989b31f90c520dc2813ee26`.
Windows / Python 3.13.5, isolated dependencies in [environment.json](environment.json).

| Check | Observation |
| --- | --- |
| Unmodified native cycle module | **63 passed**, no skips; source-tree backend registration warning retained |
| Independent requested API checks on unmodified target | **14 groups fail**, all on missing `min_length` keyword |
| Same 14 groups using visible enumerate/filter reference | **14 passed** |
| Frozen efficiency workloads | 8 output counts/digests and baseline batch observations retained |
| Solver attempts / source searches / new paid calls | **0 / 0 / 0** |

The 14 groups contain seed-fixed graphs, exhaustive small graphs, the public
example, directed/undirected multigraphs, unsortable labels and compatibility
controls. The reference adapter is test-only and leaves target code untouched.
Its successful output filtering does not demonstrate algorithmic improvement.

[baseline.json](baseline.json), [baseline-workloads.json](baseline-workloads.json)
and [native logs](baseline-native-logs.json.gz) retain the observations. Batch
times are preliminary calibration, **not a speedup result**. The first global-
environment attempt is retained separately under `initial-global-environment/`:
its native collection failed on unrelated installed backend metadata. The clean
environment replay above supersedes that collection failure, without removing
tests or suppressing warnings. No native Linux result is claimed here.

## Pair to execute after review and authorization

| Resource/access | A: ordinary development | B: Missing Link assisted |
| --- | --- | --- |
| Initial state, demand, criteria, model/settings | Same | Same |
| Total wall clock | 20 minutes | 20 minutes including discovery/packet |
| Optional metered provider calls | At most 6 | At most 6 including discovery |
| Proposed persisted paid ceiling | USD 0.15 | USD 0.15 including discovery |
| Ordinary public research/proposal inspection | Allowed | Allowed |
| External packet | None | First pertinent native strategy item, if any; at most 16 KB |

Missing Link gets at most five of B's twenty minutes, three model-chosen queries
and one source. It may select direct/defer/none. B then gets the remaining time
and calls, even if no packet exists. A can use the same bounded provider helper
for ordinary technical notes; this access must be working before dispatch.
No preliminary successful direct attempt cancels the pair. Both arms are run
sequentially, without coaching, sibling context, retries or replacements.

These are equal ceilings/access, not a claim of equal actual spending or known
subscription inference cost. Both ledgers and elapsed times must be reported.
Shared task/test preparation precedes both arms; its total operator/inference
cost was not measured. It is not additional source preparation available to B.
The full [protocol](protocol.md), [bounds](execution-bounds.json) and
[prompts](prompts.json) define the comparison and launch gates. USD 0.30 aggregate
is **proposed, not authorized**; configured rates are not verified live tariffs.

Use existing request-led Service/Provider/Store and the documented-strategy
path. This pair tests transfer from documentation, including documented code
examples; it does not simultaneously test the code-compatibility path. The
native resolved strategy evidence supplies source identity, quotes and line
URLs. No generated target patch is handed to B. No new product mode is required.

## What would count

[Acceptance](acceptance.md) was committed at `f2e94d3` before native replay,
solvers or source search. The lower bound is experimentally inclusive; the
original prose and sample filter disagree, and no upstream API agreement is
claimed. Timing workloads and thresholds are assessor choices, not requirements
invented by a donor. They remain fixed after this freeze.

First require native correctness/no regressions. Then measure efficiency against
both the reference and direct solution on the same host. A stable 1.25x aggregate
advantage on positive workloads, no control regression above 20%, and a traced
source-to-target operation can support a bounded efficiency contribution. A
requested invariant passed only by B can support a narrower functional advance.
An API wrapper alone, a relevant citation, equal outcomes or donor-only execution
does not establish a better cycle-search algorithm or incremental assistance.
Synthetic-graph benefit does not establish production benefit or general novelty.

The complete five-comment [demand](frozen-inputs.json) already contains a yield-
gate suggestion and names/links to earlier proposals. [Upstream status](upstream-status.json)
includes open proposal #8791 and three unmerged closed proposals. Metadata only
was inspected; their contents are available equally within the arm budgets.
Missing Link cannot receive novelty credit for rediscovering them. Cross-reference
contents remain explicitly unknown in the native context record.

Selection was not blind: [selection-rule.md](selection-rule.md) records the empty
wrong-label query, its metadata-only correction and the deliberate departure from
first-eligible selection. The [pool](demand-pool.json) is retained. This case was
chosen for an unprescribed algorithmic comparison, not as a sampled success-rate
estimate or proof that a contemporary solver will find it difficult.

## Reproduce the preparation checks

Clone the exact target into an ignored directory under RepoTraction; do not
change it. Create an isolated Python 3.13.5 environment with the pinned packages
in `environment.json`. From RepoTraction in PowerShell, with the paths adjusted:

```powershell
$env:ML_CYCLE_TARGET = (Resolve-Path data/paired-assistance-2026-10-23/target).Path
$env:PYTHONPATH = $env:ML_CYCLE_TARGET
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
$env:ML_CYCLE_MODE = 'reference'
& data/paired-assistance-2026-10-23/venv/Scripts/python.exe -m pytest docs/experiments/paired-assistance-2026-10-23/native_acceptance.py -q
& data/paired-assistance-2026-10-23/venv/Scripts/python.exe -m pytest data/paired-assistance-2026-10-23/target/networkx/algorithms/tests/test_cycles.py -q
& data/paired-assistance-2026-10-23/venv/Scripts/python.exe docs/experiments/paired-assistance-2026-10-23/native_acceptance.py
$env:ML_CYCLE_MODE = 'candidate'
& data/paired-assistance-2026-10-23/venv/Scripts/python.exe -m pytest docs/experiments/paired-assistance-2026-10-23/native_acceptance.py -q
```

The last command is expected red on the original target; do not rewrite the
frozen baseline files with new observations. `provenance.json` hashes canonical
Git blob bytes (LF text), so reproduction also works after a Windows checkout.
The ordinary full Windows/Linux RepoTraction CI matrix remains a separate
regression gate and does not run these expected-red external fixtures.
