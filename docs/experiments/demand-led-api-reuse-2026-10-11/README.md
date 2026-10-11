# Demand-led search over package APIs

**A new executable capability, not a demonstrated novel reuse opportunity.**
Given examples and a supplied package, Missing Link now enumerates a bounded
composition of a constructor/factory and a method/property, including inherited
methods. It imports the actual supplied package in the existing WASI sandbox.
It found `GitIgnoreSpec.from_lines(patterns).match_file(path)` without being given
that binding. All nine frozen cases passed, including a fresh-sandbox export.
The previous function extractor, over the same source snapshot, found no match.

There are still **zero demonstrated new advantageous autonomous connections** in
this study. The operator selected both libraries; the related public requests
already named them. The ignore-pattern specification is an authored control,
not a new issue independently discovered and solved by the product. This is a
bounded functional prototype, not an improved end-to-end discovery score.

## Why change the search direction

[PR #120](https://github.com/Daniele-Cangi/RepoTraction/pull/120) completed its
transport and interpretation pipeline, but selected 15 discussions and produced
no advantageous reuse. Twelve behavioral abstentions were reasonable; only two
requests supported executable suboperations. More keyword matches would not
establish relevance, novelty or advantage.

Its search also fixed a source first and later asked whether one of that
source's isolated top-level functions implemented the requested operation.
The PEP 440 request explicitly names `packaging`; it does not establish that
Black implements version-constraint membership. Nor does the retained target
manifest establish that `packaging` is already installed. The appropriate
source can be outside the repository from which issue retrieval started.

I chose to make the **requested behavior a query**, and library API compositions
the searchable objects. This avoids deriving compatibility from names, README
similarity or citations alone. It also avoids reimplementing the requested
algorithm in a generated adapter. This is a specific omission in the old code,
not proof that it caused all of PR #120's negative results.

Alternatives considered: richer lexical/embedding retrieval would still leave
execution and advantage unknown; unconstrained adapter generation could implement
the answer instead of reuse it; automatic target/test mining could be valuable
but would require a different corpus and target-specific integrations. The
bounded API grammar is small enough to implement and challenge now.

## What changed in the product

- `api_reuse.py` parses supplied source without host imports. It enumerates
  public direct functions and one constructor/classmethod-factory followed by a
  method/property. Inheritance follows literal same-package class bindings;
  multiple inheritance and rebound module/member names are conservatively omitted.
  Positional arity gates eligibility; ordering is deterministic, not a learned
  or lexical ranking. No method name is supplied as an answer.
- `prepare_behavior_search(..., package_root=...)` uses that optional catalog.
  The default extractor remains unchanged. Source files and wrappers share the
  existing 64-file, 256-KiB/file, 2-MB/total and 40-candidate bounds. Omitted
  candidates remain explicit; whole files are never shortened to execute them.
- `Service.behavioral_plan(..., reuse_repository=..., package_root=...)` can
  apply a saved Discover demand to another explicitly supplied public pinned
  package. It preserves account/discussion checks and writes no job or result.
- The existing assessor and bridge exporter retain provenance and keep results
  unqualified. Export carries the package and argument-routing wrapper. It does
  not implement pattern matching or version parsing itself.

There is no new runner, provider, storage layer, scheduler, acquisition service,
cache implementation or paid model call. Atomic budget, identity, attempts,
cancellation and ordinary Discover persistence were not changed. The rigorous
historical bench and every historical result remain untouched.

Package selection and contract construction are still external to this search.
This feature does not make `Service.start` an autonomous library finder.

## Inputs and pre-execution freeze

Initial code/inputs: commit `45fc6e1`. Corrected execution semantics/inputs:
commit `13995cc`. The initial [manifest](manifest.json), [contracts](contracts.json),
[catalog](plan-index.json) and [results](results.json) are retained, not replaced.
The follow-up [manifest](followup-manifest.json), [catalog](followup-plan-index.json)
and [results](followup-results.json) retain the same sources, cases, candidate
identities and order. No outcome-dependent candidate or case was added.

| Supplied source | Revision | Python files | Slice candidates / eligible per contract | API candidates |
| --- | --- | ---: | ---: | ---: |
| pypa/packaging | `332d716676eb934b67ede4054a3e3e0d4022b2d3` | 22 | 40 / 5 | 40 |
| cpburnz/python-pathspec | `cd79e3c74e2af8d8eadcc0d74d979db518c80f12` | 31 | 13 / 2 | 32 |

The complete supplied Python trees, metadata and license texts are retained in
[packaging-snapshot.json](packaging-snapshot.json) and
[python-pathspec-snapshot.json](python-pathspec-snapshot.json). They were acquired
as public text from pinned Git trees, never installed or imported on the host.
This opt-in package bundle uses the existing execution-artifact bounds; it does
not enlarge ordinary Discover's source sampler. Missing resources/native or
external dependencies remain failures rather than substitute implementations.

Three contracts were frozen before executions:

1. **PEP 440:** the PR #120 example and its three original checks plus four
   already-frozen separate-context reviewer checks. Those checks are not newly
   blind to this engineering investigation.
2. **Ignore patterns:** two examples and seven operator-authored checks covering
   negation, root anchoring, directory matches, `**`, comments and escaped `#`.
   The rule reference is the [Git manual](https://git-scm.com/docs/gitignore).
   Scope is one pattern list and an already-enumerated relative POSIX file path;
   no nested `.gitignore` traversal or excluded-parent pruning is established.
3. **Raw HTTP target:** the historical example and six original/reviewer checks.
   It is a negative cross-domain control here. Its historical runtime remains
   `unknown`; the actual issue concerns Go, and we do not reinterpret this
   identity-shaped contract as proof of a recording/resending lifecycle.

Exploration rejected two apparent opportunities as novel discoveries:
[files-to-prompt#40](https://github.com/simonw/files-to-prompt/issues/40) already
mentions pathspec and a working maintainer branch; [copier#1131](https://github.com/copier-org/copier/issues/1131)
is principally a configuration/design request with existing `_exclude` support.
The first inspired the labeled ignore-pattern control, not a claimed new lead.
The PEP 440 [request](https://github.com/Q00/ouroboros/issues/2546) likewise already
names packaging. These are purposively selected warm controls, not an independent
sample, and provide no estimate of open-world discovery precision.

## Results and failed executions

| Source / search | PEP 440 | Ignore patterns | Raw HTTP target |
| --- | --- | --- | --- |
| packaging / previous slices | 0 witnesses | 0 witnesses | 0 witnesses |
| packaging / API compositions | Not evaluated: fuel exhausted | Not evaluated: fuel exhausted | Not evaluated: fuel exhausted |
| pathspec / previous slices | 0 witnesses | 0 witnesses | 0 witnesses |
| pathspec / API compositions | 0 witnesses | **1 witness, 9/9 cases** | 0 witnesses |

All 32 pathspec bindings were reported in each API search: no omitted observation,
load error or unobserved binding. Only `GitIgnoreSpec.from_lines[1].match_file`
survived the ignore-pattern cases. Removing constructor/factory compositions
from this enumerated catalog leaves no surviving direct-function binding.
This is catalog-limited evidence: 28 further arity-eligible pathspec compositions
were omitted by the unchanged artifact count limit, and 5 packaging compositions
by the callable limit. It is not exhaustive API coverage.

The exported pathspec binding passed the same nine cases in a **fresh WASI
invocation** (3.182 seconds). This checks export fidelity and removes dependence
on other search bindings' warmed package state. It is not a new holdout, target
integration, performance proof or whole-issue solution.

The frozen stdlib shortcut `any(fnmatchcase(path, p) for p in patterns)` passes
both examples but only 3/7 checks: **5/9 total**, against 9/9 for the selected API.
This demonstrates why ordinary wildcard resemblance does not satisfy the chosen
ordered-pattern semantics. It does not establish an advantage over the best
alternative: Git itself implements ignore semantics, and the maintainer had
already found pathspec. Adoption benefit and dependency cost remain unestablished.

The first search version evicted package modules between bindings. All six API
runs exhausted WASI fuel during parsing/compilation and had no assessable output.
A single packaging diagnostic enabled CPython's ordinary temporary bytecode
while retaining eviction; it also exhausted fuel ([record](loader-diagnostic.json)).
That change was discarded. The follow-up uses **ordinary Python imports**, with
one shared imported package per search. No custom cache was introduced. It makes
the pathspec query work; the full packaging search still exceeds fuel. This
study ends there, without expanding the runner, trimming the source, tuning
candidate ordering or choosing a favorable packaging entry point manually.

The guarantee changes explicitly: package searches can depend on shared module
state and search order. Their matches carry `independent_replay_required=true`.
A regression intentionally constructs a warm-only match and shows that its
fresh export fails. Neither the search observation nor an export plan certifies
that replay happened. The old slice-only path keeps its fresh-namespace behavior.

Review follow-up excludes ambiguous inheritance/rebinding and reserves the four
artifacts needed by an export (at most 60 package files). Authored regressions
cover diamond inheritance, descendants, class/function/member rebinding and the
60/61/62-file boundary. Regenerating all twelve frozen plans after these fixes
produces identical candidate identities and executable artifact hashes. Their
recorded observations still apply; no experiment or historical record was rewritten.

The corrected 12-search study, one export and one stdlib comparison took
**43.956 seconds** wall time, including bookkeeping. Search runner durations sum
to 33.435 seconds; the positive search itself took 3.371 seconds. These include
runtime setup and are measured latencies, not isolated benchmarks: the unit
suite was running concurrently. They exclude acquisition, protocol preparation,
engineering and the initial failed study. Comparing them to PR #120's 22.920
minutes of acquisition/model work would be invalid. Paid API calls: **zero**.

The evaluator only runs checks when all examples pass. Rejected bindings are
not evidence that every held-out input ran. Explicit failures and non-evaluated
searches are retained separately; neither is counted as a useful discovery.

## Use and reproduction

Use the existing APIs, with a snapshot and contract already available:

```python
plan = prepare_behavior_search(snapshot, contracts, package_root=snapshot["package_root"])
execution = runner.run(plan["files"], plan["entrypoint"])
result = assess_behavior_search(plan, execution)
# A witness remains unqualified. Review the source and contract, then:
bridge = prepare_behavior_bridge(plan, result["matches"][0])
replay = runner.run(bridge["files"], bridge["entrypoint"])  # fresh sandbox
```

For a saved Discover proposal, use the read-only
`service.behavioral_plan(job_id, candidate_index, reuse_repository=snapshot,
package_root=snapshot["package_root"])`. No acquisition or paid call is triggered.
The contracts/snapshots plus code at the frozen commits regenerate each plan;
the catalog records artifact hashes and omissions. Full generated plans and the
working export are also retained locally under
`data/demand-led-api-reuse-2026-10-11/`. Downloaded code must execute only through
the existing isolated runner; unit tests execute authored fixtures only.

## Engineering conclusion

Keep this opt-in functional capability: it can identify and export an API
composition that the previous search grammar could not represent. Do not
interpret it as solving autonomous opportunity discovery, or open another
infrastructure project to make packaging pass. There is one proven assisted
suboperation, zero demonstrated new opportunities and zero target integrations.

The next decisive experiment should start with independently sourced unmet
target behavior and a fixed software corpus chosen without reading the answer
in that target's discussion. Its success criterion must include a target-level
change and benefit relative to the target's best available alternative. More
API witnesses alone would not satisfy that criterion. No such paid experiment
or target modification is authorized or initiated by this report.

## Attribution

The packaging snapshot retains its Apache-2.0/BSD license texts and source
notices. The pathspec snapshot retains its MIT license and file notices. Copies
are unmodified public source text for reproduction; the generated argument-routing
wrappers and authored regression fixtures belong to RepoTraction. Runtime bundles
and credentials are not included.
