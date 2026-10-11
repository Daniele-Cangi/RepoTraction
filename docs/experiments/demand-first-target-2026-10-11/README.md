# Demand-first source selection: author ordering in audio-feeder

This is a small **negative source-selection experiment**, not a new production
discovery capability. No candidate has demonstrated useful reuse. Native HTTP
verification of the direct correction is pending CI at this commit.

## Independent need and frozen boundary

The maintainer's [audio-feeder issue #81](https://github.com/pganssle/audio-feeder/issues/81)
asks for case/diacritic-insensitive author ordering with the original text as
tie-breaker. It names no solution package. The target is pinned to
`2a5b58dab43a5195ccc964916bbddaf7f8727c1d`. The issue, acceptance interpretation,
eight fixtures, direct baseline and automatic selection rule were committed at
`871d650` **before repository search**. The chronological Git commit is the freeze;
the protocol's boolean alone is not evidence of it.

The engineer chose the need and wrote acceptance cases and the direct correction.
The program generated three queries and selected three repositories from the
returned ranks. This is a deliberately simple lexical baseline, not semantic
package selection, autonomous patch generation, or the production Discover
pipeline. The engineer was not blind to existing library names. Synthetic fixture
records exercise a real maintained application's database, HTTP route and templates;
they are not a user deployment or evidence of adoption.

## What the program selected

Replay without acquisition:

```
python docs/experiments/demand-first-target-2026-10-11/discover_sources.py docs/experiments/demand-first-target-2026-10-11/search-results.json
```

`search-results.json` retains three ordered batches of 20 repository metadata
records. `selection.json` is the program's output, still marked unassessed; the
following human source assessment does not rewrite that output. Search qualifiers
requested public non-fork, non-archived Python repositories. The connector does
not return language/fork metadata in this packet, so those fields were not
independently verified. Rankings are GitHub's, not a usefulness score.

| Selected repository, revision | Inspected evidence | Assessment |
| --- | --- | --- |
| `sebastianruder/NLP-progress`, `379f03ff7568b18bd9843490b84c94679f880a79` | [README and repository tree](https://github.com/sebastianruder/NLP-progress/tree/379f03ff7568b18bd9843490b84c94679f880a79) | Catalogue of NLP results. No author-ordering implementation identified. Reject for this demand; no claim that every linked project was inspected. |
| `dmort27/panphon`, `a49c242d3307864312a2701055faefa4e548501c` | [featuretable.py](https://github.com/dmort27/panphon/blob/a49c242d3307864312a2701055faefa4e548501c/panphon/featuretable.py#L73), README | Phonetic segment features. Its `normalize` returns `unicodedata.normalize('NFD', data)` directly. It does not remove marks or casefold; IPA filtering is not author collation. Wrapping the same standard-library primitive adds no identified capability over the direct baseline. No performance claim was measured. |
| `hearsaycorp/normalize`, `cff13b1d89f9760f12003c3134351acd48b8f85d` | [README](https://github.com/hearsaycorp/normalize/blob/cff13b1d89f9760f12003c3134351acd48b8f85d/README.md), [public API](https://github.com/hearsaycorp/normalize/blob/cff13b1d89f9760f12003c3134351acd48b8f85d/src/normalize/__init__.py) | Normalization refers to records/data modelling. No relevant ordering API identified; no exhaustive absence claim about all internal code. |

All three are rank 1 in their respective query. A known natural-sorting library
appears further down the retained first pool. Promoting it after seeing the
results would violate this experiment; it was not substituted. Even finding a
relevant package would still require beating the full direct correction.

## Native check and limits

`native_http.py` applies only the direct author-key correction to a disposable
copy of the pinned target. It starts the actual Flask application, persists fixture
records through the real database handler, sends loopback HTTP requests to
`/books`, and checks rendered IDs/names, both directions, cached repeats, pagination
and title/date priorities. Target page/navigation tests run for both variants.
No target sorter, renderer, database handler or HTTP response is mocked.

The narrow CI workflow executes external code in a disposable Linux container,
with no runtime network or host credentials. Dependencies install during image
build; their resolved versions and image ID are exported. Dependencies/base image
are not pinned by digest, so this is not a bit-for-bit reproducible environment.
No downloaded target code runs in the local host Python. This is a target-specific
integration test, not a replacement runner, transport, or production service.
The first CI image build failed before any HTTP test: the credential-free Git
archive lacked versioningit's VCS metadata. The image supplies a `PKG-INFO` version
of `0.0.0+study.2a5b58d` for packaging only; the pinned application code is unchanged.

**Protocol deviation:** the planned 9-repeat latency comparison at 1,000/10,000
authors is not performed, because no selected source reached integration. There
is no package adapter, speedup result or passed benefit gate. The HTTP check can
validate the direct solution only; it cannot repair the failed discovery result.
The protocol and acceptance fixtures remain unchanged. The full upstream media
processing suite and production adoption are outside this test and remain unknown.

## Decision

Do not promote this lexical selector into Discover or tune it against this pool.
The system did choose where to search, but the chosen repositories were not useful.
The previous source-first cohort had zero demonstrated advantageous reuse; this
reverse-direction lexical baseline also has zero. One demand does not establish
which direction is generally better. Unlike the earlier cohort, this test fixes
a target demand and a complete direct alternative before selecting any source.

The missing functional decision is to understand a requested operation well enough
to choose implementations, and to abstain when a direct local correction is
already sufficient. It is not another API grammar, audit, or search score. A
semantic selection experiment would need a separately declared intervention and,
if using the existing provider, new paid-call authorization. It has not run here.

No paid AI calls, historical changes, external maintainer contact or merges.
