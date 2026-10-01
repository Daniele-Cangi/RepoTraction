# RepoTraction development plan

The next architectural task is to split the roughly 4,000-line `app.py` into
focused modules without changing application behavior. This is planned work,
not a completed migration. Effective immediately, new separable implementation
belongs in dedicated modules rather than the monolith; the repository instruction
in [AGENTS.md](../AGENTS.md) applies to future work.

## Modularization sequence

- [ ] Establish characterization tests for existing public behavior and map
  dependencies, including test patches of globals and account-specific state.
  - [x] Characterize the first five pure traffic/snapshot helpers and retain
    their compatibility names in the entry point.
  - [x] Characterize event metric results, evidence availability and event
    headlines before extracting their pure calculations.
  - [x] Characterize repository readiness, license interpretation and adoption
    signals before extracting their calculations.
  - [x] Characterize opportunity categories, thresholds, stable ranking and
    partial-evidence behavior before extracting their calculations.
  - [ ] Characterize remaining stateful boundaries before their extraction.
- [ ] Extract pure calculations into `analytics/`: date windows, traffic
  comparisons, event metrics, repository health and signal calculations. Pass
  timestamps and configuration explicitly where practical.
  - [x] Move percentage changes, traffic-period labels/summaries, UTC timestamp
    parsing and snapshot comparison windows to `analytics/traffic.py`.
  - [x] Move event date parsing, observed-window totals, portfolio median,
    confidence and event headline calculations to `analytics/events.py`.
  - [x] Move license metadata interpretation, repository readiness scoring and
    adoption signals to `analytics/repositories.py`, with explicit activity age
    and profile applicability for readiness calculations.
  - [x] Move per-repository opportunity calculations and stable ranking to
    `analytics/opportunities.py`, using supplied readiness and activity age.
  - [ ] Extract remaining event window/evidence orchestration.
- [ ] Extract database connections, migrations, repository registry operations
  and snapshot persistence into `storage/`. Preserve existing database paths,
  schemas, transactions and account isolation; do not reset stored history.
- [ ] Extract GitHub acquisition, cache and collection orchestration into
  `services/`. Give the scheduler an explicit lifecycle and shutdown behavior;
  importing a module must not start collection or network requests.
- [ ] Extract HTTP handlers and routing into `server/`. Keep export serialization
  separate from transport. Reduce `app.py` to CLI parsing and startup wiring.

These are intended boundaries, not a requirement to move entire sections blindly.
Each extraction should have explicit dependencies, avoid circular imports and be
small enough to review in a separate commit. Use thin compatibility delegates only
when needed during migration; modules must not import the entry point to obtain
mutable global state.

## First extraction boundary

[`analytics/traffic.py`](../analytics/traffic.py) depends only on standard-library
date/time and typing utilities. Its functions consume supplied rows, timestamps
and window parameters, not the active account, database, cache, GitHub client or
wall clock. The five function bodies are unchanged from the merged implementation.
[`app.py`](../app.py) re-exports the same function objects during migration, so
existing event, repository and community calculations retain their entry-point
names without duplicating their implementation.

Characterization tests cover zero baselines, absent and partial periods, timezone
normalization, cutoff selection, early/long-window labels, immutable inputs and
SQLite rows. Additional checks verify import isolation and compatibility names.
The Windows installer ships the new package, and CI checks its installed location.
This step does not move HTTP handling, persistence, scheduling or Missing Link,
and does not change analytics contracts or trigger paid reanalysis.

## Event calculation boundary

[`analytics/events.py`](../analytics/events.py) calculates totals, percentage
changes, the portfolio median, confidence and the headline for an event. Callers
supply valid before/after rows, the observed window, per-repository aggregates
and the profile-repository exclusion predicate. The module uses standard-library
utilities and `analytics/traffic.py`; it does not read the database or wall clock,
import the entry point or load an AI provider.

`app.py` retains the existing SQLite queries and evidence eligibility checks,
including creation-date and current-day exclusions, contiguous post-event days,
incomplete baselines and stale upstream data. Its metric adapter delegates valid
results to the new module; the Impact Lab builder delegates event headlines.
SQL, response fields, thresholds and missing-versus-zero semantics are unchanged.
Characterization tests cover the adapter and headline behavior, while direct
module tests check immutable inputs, SQLite-row compatibility and import isolation.
The installer and CI validate the new installed module. Database access and the
remaining event window orchestration are still planned work.

## Repository calculation boundary

[`analytics/repositories.py`](../analytics/repositories.py) interprets license
metadata and calculates repository readiness and same-window cloning signals.
Readiness receives profile applicability and the age of the last push explicitly;
the module does not read the wall clock, database or active account, import the
entry point or load an AI provider. Scoring weights, thresholds, gap order,
license-present versus license-missing rules and cloning labels are unchanged.

`app.py` preserves the metadata and adoption compatibility names and keeps the
original one-argument readiness interface through a small adapter. The existing
timestamp parser and profile rules still supply that adapter's dependencies.
Tests cover those patchable dependencies, immutable inputs, unknown versus zero,
direct calculations and isolated imports. Installation checks include the new
module. Profile filtering and timestamp adapter extraction remain separate work;
this step does not change HTTP, storage or acquisition.

## Opportunity calculation boundary

[`analytics/opportunities.py`](../analytics/opportunities.py) builds suggestions
for an eligible repository using supplied signals and readiness, then ranks the
portfolio's opportunity and readiness rows. The five categories, thresholds,
score caps, confidence labels, response fields and stable tie order are unchanged.
The module does not parse activity timestamps, read the wall clock or database,
import the entry point, collect data or load an AI provider.

`app.py` retains case-insensitive signal matching, last-duplicate selection,
repository exclusions and the existing patchable profile and readiness adapters.
It prepares and delegates one repository at a time so invalid inputs still fail
before evaluating later repositories. Cache, acquisition and the opportunity
center's payload limits and summary remain in the entry point.

Characterization tests cover complete results, partial traffic and star evidence,
native clone totals, exclusions, ranking and validation order. Direct tests check
supplied readiness, input preservation, row reference semantics and isolated
imports. Opportunity center tests retain cache behavior, response aliases and
the 40-item limit. The installer and CI check the new installed module. This is
a structural extraction, not a scoring change or a Missing Link feature.

## Acceptance checks

- Preserve CLI flags, defaults, response shapes, status codes and local-only
  HTTP safety checks.
- Preserve traffic provenance, missing-versus-zero distinctions, historical
  evidence and account-change protections.
- Preserve scheduler concurrency guarantees and SQLite transaction behavior.
- Keep analytics usable without loading an AI provider. Structural tests must
  not consume the paid discovery budget or execute acquired repository code.
- Run focused regressions and the full test suite for every extraction, with
  Windows and Linux CI on the supported Python versions.
- Keep structural changes separate from feature changes and review corrections.
  Complete the current review fixes before starting broad extractions.

## Deferred language coverage

- [ ] Consider structural analysis for Go and Rust after modularization and the
  current Missing Link validation work. This is optional future work, not part of
  the immediate implementation scope.

Current coverage is Python AST analysis and a partial JS/TS declaration scan,
not equivalent AST support across all three languages. Any future parser needs
language-specific fixtures, visible coverage limits and the same prohibition on
executing acquired code. Merely reading `go.mod` or `Cargo.toml` does not constitute
Go or Rust implementation analysis.
