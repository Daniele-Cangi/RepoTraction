# Request-led discovery: executed outcome

The two jobs completed, but **neither searched for a package**. This run demonstrates
that the product can interpret an independent request and decide to stop without
an operator supplying a donor or a query. It does **not** demonstrate autonomous
useful reuse, correct source selection, or an advantage over a tested direct
implementation. Both stops are plausible, conditional judgments, not verified
optimal decisions.

Execution used `0760d6b40f5ccb6806aa9fca4f5df9af0702a871` on 2026-10-11,
21:20:11--21:21:19 UTC. The preparation records remain unchanged:
[manifest](manifest.json), [acceptance notes](acceptance-before-selection.md),
[original primary discussion](demand-before-selection.json), and
[protocol](../../missing-link-request-led-discovery.md). Their statements that
the experiment is not yet authorized/run describe preparation, not current state.
[Authorization](authorization.json), [readiness](readiness.json),
[measured results](run-result.json), and [public evidence](evidence.json)
record the subsequent execution separately.

## Measured outcome

| Case | Decision | AI calls | GitHub requests | Wall seconds | Reserved USD |
| --- | --- | ---: | ---: | ---: | ---: |
| audio-feeder #81, historical control | `use_direct` | 2 | 9 | 34.904 | 0.0153359 |
| tunesynctool #21, fresh primary | `defer` | 2 | 9 | 32.539 | 0.0163293 |
| Cohort | Two completed jobs | 4 | 18 | 67.445 | 0.0316652 |

Each job used the ordinary Service: request interpretation followed by the new
discovery decision. There were four completed native responses and four unique
attempt/reservation records, with no retry, resume, replacement, repository
search, donor acquisition, compatibility evaluation or new target integration.
The cohort wall time includes a small amount of work outside the two job timers;
it is not the sum of model inference times. No callback-time breakdown was
measured, and this is not a speed comparison with the older forensic experiment.

Reported usage totals 16,025 input and 4,608 output tokens. At the existing
configured USD 0.10/0.50 per million input/output tokens, the usage estimate is
**USD 0.0039065**, distinct from the conservative reservation of **USD 0.0316652**
and the authorized ceiling of **USD 0.25**. This is not a billing receipt or a
newly verified tariff. The unused allowance does not authorize another cohort.

## Assessment against the independent criteria

**audio-feeder.** The model retained the four requested behaviors: natural
sorting, diacritic removal, case normalization and an original-string tie-break.
It proposed a local normalization/sort correction and found no established
incremental package benefit. This avoids the irrelevant donor inspection in
the separate #122 lexical experiment. That historical direct correction passed
128/128 assertions versus 112/128 for the original, but those fixtures establish
case/diacritic/tie behavior, **not numeric natural-sort semantics**. They do not
certify the whole newly normalized request or its strongest possible direct
solution. The new model explicitly leaves the sort algorithm and Unicode cases
unspecified. No new direct implementation was tested in this cohort. A false
negative from preferring direct implementation remains possible.

**tunesynctool.** The model correctly distinguishes mapping an ISRC already
returned by a server from finding a track by ISRC. It retains the owner's
specification-conformance constraint and proposes exact validation of returned
ISRC values using the existing client. It defers because the discussion does not
establish a portable, accepted lookup mechanism or a benefit from another package.
That is consistent with uncertainty recorded before selection. It is not evidence
that no supported mechanism or useful package exists: neither current protocol
support nor a real server was tested. The normalized requirements also omit
exact matching and avoiding MusicBrainz traffic as separately checkable acceptance
items, although that intended benefit survives in the environment text and the
planner mentions exact matching. Consequently extraction completeness and direct
adequacy cannot be claimed. No native acceptance criterion was newly demonstrated.

**Shared limitation.** The existing `fetch_reference_context` acquisition is
designed for manifests and explicitly cited source paths, not for choosing the
implementation relevant to an operation. It supplied only `pyproject.toml` and
`setup.py` for audio-feeder, and `pyproject.toml` and `requirements.txt` for
tunesynctool. Neither sample included product implementation. Coverage reports
and both model decisions disclose this. The independently prepared assessor
notes inspected tunesynctool's driver/mapper code; those notes were not sent to
the product and must not be credited to its reasoning.

The recorded coverage's generic "File budget sampled 4" message describes the
configured bound; the actual file lists and `files_scanned` show **two** per
target. Four acquired files across the cohort do not mean four per target.
Both pinned target revisions agree with the preparation context; the primary
discussion identity/update markers also agree. No evidence was rewritten to
hide drift or a different result.

## What this changes relative to earlier experiments

The #120 source-first cohort examined 15 discussions with 46 AI calls and found
no advantageous autonomous reuse. #121 added executable API search with sources
supplied by the operator. The separate #122 demand-first lexical experiment
selected irrelevant donors and tested a limited direct correction in the native
target. This cohort adds a real model-driven decision *before* source search,
including an economical stop, through the existing product path.

It supplies no live evidence for query generation, semantic repository selection,
source capability assessment or target integration: those branches did not run.
Offline regressions establish their mechanics, not decision quality. Comparing
zero irrelevant inspections here with three lexical choices in the historical
control is descriptive; it does not establish better retrieval precision or
recall. One known control and one predetermined fresh issue cannot estimate
general stop accuracy, false negatives, or the chance of useful reuse.

## Validation and engineering conclusion

Before any paid dispatch, Codex review completed on `0760d6b` with no unresolved
threads after three public-provenance fixes. The full
[CI run 38174755193](https://github.com/Daniele-Cangi/RepoTraction/actions/runs/38174755193)
passed on Linux and Windows, Python 3.10 and 3.13. The current code has 20 focused
request-discovery regressions; 24 investigation/CLI tests also pass. Full CI
collects 1,933 tests, with platform-dependent skips. These checks protect behavior
and data handling; they do not establish useful discovery.

The public evidence retains original normalized requests, decisions, coverage,
native response text, usage and trace identities, plus pinned source identities.
Full job records remain in the ignored local experiment directory; their hashes
are included in the public evidence. A read-only check reconciled the four
attempts and reservation sum with the fresh SQLite allowance. Historical
experiment files were not changed. No additional runner, audit system or store
was introduced for this result.

Keep the opt-in functional path, with its unverified-decision status. Do not
interpret this cohort as completing the requested autonomy, and do not force
`search`, replace the primary, or tune prompts until it produces a positive.
The next functional obstacle is an informed decision under uncertainty: the
product currently reasons about a direct alternative without acquiring its
relevant implementation, and can treat unresolved protocol support as a stop
without investigating it. Missing context is not evidence that searching has
negative value. This suggests a targeted functional question for the next change,
not another retrieval framework or infrastructure phase. Any later evaluation
must still establish native acceptance and a concrete benefit over the strongest
direct alternative; no such result is available here.
