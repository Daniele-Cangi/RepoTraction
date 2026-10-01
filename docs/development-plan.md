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
  - [x] Characterize event evidence boundaries, stale-data precedence and query
    short-circuiting before extracting window eligibility decisions.
  - [x] Characterize connection lifecycle, current/legacy migrations, provenance,
    account-selected paths and schema compatibility before extracting storage.
  - [x] Characterize registry IDs, renames, name reuse, history collisions,
    transaction boundaries and resolver failures before extracting registry SQL.
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
  - [x] Move event row eligibility, contiguous windows, comparison dates and
    waiting/stale decisions to `analytics/event_evidence.py`.
  - [ ] Extract remaining profile/timestamp adapters and database-backed event
    orchestration along with their stateful dependencies.
- [ ] Extract database connections, migrations, repository registry operations
  and snapshot persistence into `storage/`. Preserve existing database paths,
  schemas, transactions and account isolation; do not reset stored history.
  - [x] Move explicit-path connection lifecycle to `storage/database.py` and the
    existing migration statements to `storage/migrations.py`.
  - [x] Move registry SQL and history rename/archive operations to
    `storage/registry.py`, using supplied connections and explicit history hooks.
  - [ ] Extract snapshot persistence. Move remaining alias-resolution network
    orchestration with GitHub acquisition into `services/`.
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

`app.py` retains the existing SQLite queries and supplies eligible rows through
the event evidence helpers described below. Its metric adapter delegates valid
results to the calculation module; the Impact Lab builder delegates event headlines.
SQL, response fields, thresholds and missing-versus-zero semantics are unchanged.
Characterization tests cover the adapter and headline behavior, while direct
module tests check immutable inputs, SQLite-row compatibility and import isolation.
The installer and CI validate the installed module. Database access and the
remaining database-backed event orchestration are still planned work.

## Event evidence boundary

[`analytics/event_evidence.py`](../analytics/event_evidence.py) filters supplied
observed rows by creation/current-day boundaries, selects up to seven contiguous
post-event days, calculates equal comparison windows and returns waiting/stale
payloads when evidence is not usable. All dates and available-day counts are
explicit inputs; the module does not read the clock, database or active account,
infer missing buckets, import the entry point or load an AI provider.

The metric adapter still validates the metric before touching SQLite, parses the
creation timestamp, reads today's UTC date and executes the unchanged queries.
It checks post-event availability before loading a baseline, then checks baseline
completeness and partial-window staleness before loading portfolio aggregates.
The strict two-day freshness threshold, historical complete-window exception,
messages, fields and query short-circuiting are unchanged. Timestamp parsing and
the existing SQL creation-date cutoff also retain their current behavior.

Characterization tests distinguish unavailable zeros from observed zeros and
cover gaps, creation/current/future days, stale-status precedence, missing
baselines and read-only transactions. Direct tests check supplied boundaries,
duplicate handling, input preservation, SQLite-row compatibility and isolated
imports. Installation checks include the new module. Storage/query orchestration
will be extracted with `storage/`; this step changes neither schema nor history.

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

## Database storage boundary

[`storage/database.py`](../storage/database.py) opens the supplied SQLite path
when its context is entered, commits on success, rolls back ordinary exceptions
and always closes the connection. Default SQLite options and existing exception
behavior are unchanged. [`storage/migrations.py`](../storage/migrations.py)
applies the existing schema and migration statements to a supplied connection;
it does not select an account, open a second database or explicitly commit,
roll back or close the caller's connection.

`app.py` retains account selection, database paths, directory creation and the
patchable connection/migration adapters. Its connection wrapper resolves the
current path lazily, preserving account-specific state at context entry. The
migration SQL and its order are unchanged, including traffic provenance repairs,
registry constraints and state initialization. Existing `executescript` and DDL
transaction behavior is retained; this is not a new atomic-migration guarantee.

Tests cover successful and failed transactions, connection closure, late path
selection, current/legacy schema compatibility, idempotence, observed versus
unproven zero traffic, registry constraints, account isolation and supplied
connection ownership. Fresh storage imports do not open databases, create
directories, start services or load an AI provider. The Windows installer ships
the package; uninstall removes its code while preserving history by default and
refuses storage junctions. Isolated installed-module checks exercise migrations
only on a test database. Snapshot persistence remains planned work, along with
acquisition, scheduling and HTTP extraction.

## Repository registry boundary

[`storage/registry.py`](../storage/registry.py) contains history merge/archive
operations, current-ID reconciliation, alias persistence and active-name queries.
Every operation uses a supplied connection; the caller retains commit, rollback
and closure. The module does not select accounts or database paths, contact
GitHub, start services or import the entry point.

`app.py` retains input normalization, alias candidate filtering, GitHub resolution
and account-change/rate-limit propagation. Its compatibility adapters pass the
existing patchable history hooks explicitly. The current registry is committed
before network resolution; each resolved alias still has its own transaction.
SQL statements, ordering and collision precedence are unchanged, including
case-only renames, canonical snapshot precedence and the distinction between an
uninitialized registry and an initialized empty registry. The historical lookup
still excludes names found only in metadata snapshots or repository events.

Characterization and direct-module tests cover all five history tables, immutable
IDs, reused names, creation/first-seen dates, independent traffic metrics, caller
rollback, partial progress after resolver failure and account-selected databases.
Isolated imports and installed-module checks exercise only owned test databases,
with fake resolver replies and no paid provider calls.

One pre-existing collision issue is deliberately not changed in this structural
extraction: copying daily traffic counts and availability does not also copy the
corresponding provenance status. For example, a canonical row marked `missing`
can retain that status after receiving an observed value from a renamed row.
Correcting the per-metric status transfer needs a separate regression and fix,
not an undocumented behavior change in this refactor.

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
