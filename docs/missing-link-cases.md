# Missing Link: inspected public cases

These cases were acquired read-only from GitHub on **2026-09-30**. Repository
implementation and complete available issue comments were inspected. They are
live **source/context observations**, not live execution proofs or promises of
adoption. Old open issues are not automatically current unmet demand.

All proposed bridge code below is **NOT EXECUTED**. The local Docker CLI exists,
but its Docker Desktop Linux engine was unavailable during inspection. Missing
Link does not execute acquired or generated code on the user's host. Package
integrity tests exercise RepoTraction's own packaging code using fixtures; they
do not prove third-party behavior.

## Selected repository and provenance

[python-slugify](https://github.com/un33k/python-slugify) was inspected at commit
[`866401ea6b346d7575cf941bc73ad32a362e34aa`](https://github.com/un33k/python-slugify/tree/866401ea6b346d7575cf941bc73ad32a362e34aa).
Its [project metadata](https://github.com/un33k/python-slugify/blob/866401ea6b346d7575cf941bc73ad32a362e34aa/pyproject.toml)
declares Python >=3.10, MIT licensing, and a `text-unidecode>=1.3` dependency.
The dependency's own licensing is separate and must be reviewed when distributing
an environment. Unicode-preserving calls avoid transliteration, but installing
the full package still brings its declared dependencies.

The product is a slug generator. Its lower-level `smart_truncate` mechanism is
also publicly exported: calling it without `slugify` does not normalize prose
into a URL slug. This is an additional reusable capability, **not a private or
undocumented interface**. The [implementation](https://github.com/un33k/python-slugify/blob/866401ea6b346d7575cf941bc73ad32a362e34aa/slugify/_legacy.py#L68-L102)
and [test source](https://github.com/un33k/python-slugify/blob/866401ea6b346d7575cf941bc73ad32a362e34aa/tests/test_legacy.py)
are distinct evidence from actually running those tests, which was not done.

## Positive capability candidate: readable Cyrillic project filenames

[Manuskript issue #1006](https://github.com/olivierkes/manuskript/issues/1006)
reports unreadable filenames after non-ASCII character names are slugified.
The issue remained open, last updated 2022-01-29, and had no comments when
collected. It proposes a Unicode-compatible slug helper. The old date means
maintainer interest must be reconfirmed; it does not invalidate the reported
technical need.

The [current inspected Manuskript implementation](https://github.com/olivierkes/manuskript/blob/01e05747f3c13f637d802ca915c31f9a27a601f8/manuskript/load_save/version_1.py#L81-L95)
still accepts only ASCII letters and digits, substitutes underscores for
whitespace, and dashes for other characters. This makes the report more than a
keyword match. The candidate [Unicode-preserving branch](https://github.com/un33k/python-slugify/blob/866401ea6b346d7575cf941bc73ad32a362e34aa/slugify/_legacy.py#L137-L150)
has a relevant existing implementation.

Request-derived criterion: a Cyrillic character name should remain recognizable
in the generated filename stem. Filename uniqueness, existing saved-project
compatibility, supported target Python versions, and filesystem policy remain
adoption questions, not facts established by the issue.

Smallest inspection example:

```python
from slugify import slugify

stem = slugify("Персонаж Алиса", allow_unicode=True,
               lowercase=False, separator="_")
# Expected inspection target: "Персонаж_Алиса"
# This expected value has not been confirmed by executing the package here.
```

The existing capability supplies Unicode normalization, filtering, and separator
handling. New work is integration with Manuskript's naming/storage contract,
not a replacement transliteration algorithm. An adapter should preserve the
old ASCII naming path and explicitly decide whether existing paths are migrated;
silently replacing the old helper could change historical filenames.

Classification: **adapter candidate, pending target-context verification**.
This is not a claim that every mandatory adoption constraint is satisfied.

## Non-obvious lower-level reuse: prose metadata truncation

[LessWrong issue #519](https://github.com/bellroy/lesswrong/issues/519) reports a
meta description cut in the middle of a word. It remained open with no comments;
the last update was 2015-08-19. The original report came from a migrated tracker.
Current deployment/runtime and whether the old report remains applicable were
not established. Treat this as an **investigation candidate**, not a freshly
qualified opportunity.

The request suggests a whole-word description boundary. It does not give a
required length budget or behavior for a first word longer than that budget.
Those are missing requirements, not values the matcher may invent.

`smart_truncate` can be called independently of the slug pipeline to preserve
prose. A proposed call is:

```python
from slugify import smart_truncate

# 160 is an EXPLICIT ASSUMPTION for illustration, not an issue requirement.
description = smart_truncate(text, max_length=160,
                            word_boundary=True, save_order=True)
```

The existing mechanism handles character budgets and ordinary space-separated
word selection. New integration would prepare plain text, choose a documented
budget, and perform HTML attribute escaping after truncation. It must not process
raw HTML as if it were plain text. A legacy Python runtime may require extracting
and adapting the MIT-licensed helper rather than importing the current package;
that route is a proposal, not a verified standalone extraction.

Two source-visible obstacles prevent claiming strict whole-word compliance:

- `save_order=False` is the default and can skip earlier words to fit later ones.
- When no whole word fits, or there is no separator, the helper falls back to a
  hard character cut. A requirement forbidding all partial words needs an
  explicit policy and a narrow adapter; the source helper alone does not meet it.

The relevant contribution is the lower-level truncation mechanism. Calling
`slugify` instead would incorrectly lowercase/filter/reformat prose. No ablation
run was performed. A future isolated comparison should use the same input and
budget, comparing ordinary slicing against the proposed mechanism, and assess
word completeness and preservation of the original prefix—not cause an import
error by deleting the dependency.

## Deceptive similarity: native CSS clipping

[CSSWG issue #4406](https://github.com/w3c/csswg-drafts/issues/4406) also asks for
word-boundary clipping. Its available follow-up comment distinguishes the two
properties: `line-clamp` already specifies clipping at soft wrapping opportunities,
whereas `text-overflow` is a paint-time effect over overflowing content.
The issue and its one comment were read; open status alone would have lost this
important clarification.

The unresolved part concerns browser CSS rendering, widths, scrolling, and CSS
property semantics. A Python function using character counts cannot supply that
native behavior. Changing text on the server does not implement a CSS property
and would require a materially different solution with layout-measurement logic.

Classification: **reject as a direct or narrow-adapter match**. The shared
phrase "word boundaries" cannot outweigh the runtime/layout constraint.
The `line-clamp` branch must not be presented as an unsolved opportunity merely
because the encompassing issue is still open.

## Sustainable baseline comparison

This is a qualitative source inspection, not a scored benchmark:

| Baseline | Useful signal | Important limitation exposed by these cases |
| --- | --- | --- |
| Keyword retrieval | Finds Unicode slugging and word-boundary discussions | Retrieves CSS clipping too; words alone do not establish compatible execution/context |
| README-only matching | Identifies the slug product and advertised options | Does not independently establish the lower-level helper's ordering and oversized-word fallback behavior |
| Source-aware Missing Link analysis | Can reference the exact implementation and preserve requirement-level unknowns | Still needs complete discussion, adoption constraints, and isolated execution before claiming success |
| A careful coding agent reading the same sources | Can make the same distinctions manually | Missing Link must save and expose that investigation plus a reproducible handoff, not claim a unique reasoning ability |

The added value to test is whether pinned evidence, original criteria, obstacle
checks, and an inspectable bridge save the maintainer work without increasing
false positives. These three inspected cases do not establish general retrieval
precision, a working extractor for every language, user demand volume, or
third-party integration success.
