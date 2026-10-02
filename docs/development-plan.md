# RepoTraction development plan

The next architectural task is to split the roughly 4,000-line `app.py` into
focused modules without changing application behavior. This is planned work,
not a completed migration. Effective immediately, new separable implementation
belongs in dedicated modules rather than the monolith; the repository instruction
in [AGENTS.md](../AGENTS.md) applies to future work.

## Modularization sequence

Product validation currently takes priority over the next extraction and interface
features. The [1 October live Luna evaluation](missing-link-live-discovery-2026-10-01.md)
ran eight repository-only inputs with 52 real calls, preserving the user's existing
allowance while raising its cumulative ceiling to $10. It found no qualified
external lead and exposed quotation-generation failures, undercounted optional
contributions, implementation-context gaps and source/retrieval bias.

The follow-up corrections use contract 16: deterministic demand-span selection,
independent optional-field review with source-bound, explicit non-requirement
decisions for unrelated context, bounded static JS/TS export sampling, actual
implementation context before later discussion, preflight before paid comparisons,
and fragmented-name/reference-only retrieval cleanup. Exact acquired npm `bin`
targets can override only the `scripts/`/`tools/` directory role heuristic, without
promoting neighboring scripts, tests, mocks or build helpers. Implementation and
offline regressions were separate from the frozen live experiments; the fixes
themselves made no paid calls or historical-analysis migrations.

After PR #31 merged, the [2 October contract-16 retest](missing-link-live-discovery-2026-10-02.md)
ran the same eight source inputs plus five new, prespecified inputs, through the
real API without supplied issues, custom queries, imports or paid retries. It
made 78 calls, selected 36 distinct issues and saved 57 comparisons. All 57 exports
remain identical after server restart, traces/usage/reservations reconcile, and
697 offline tests pass. The cohort reserves $1.2226658 (token estimate $0.3163063),
bringing the unchanged $10 cumulative allowance to $3.844534 reserved.

No quotation-validation or missing-implementation-context failures occurred in
this sample, but no qualified new external lead is demonstrated. Useful partial
mechanisms and sound rejections remain distinct from complete request fulfillment.
Most Group A issues changed, so this is not causal proof of higher model accuracy.
Isolation was not forced: useful candidates were rejected whole matches, unresolved
or not reproducible with the current Python/WASI runner. Product code and provider
settings stayed frozen throughout this evaluation.

Next validation work, in narrow modules rather than `app.py`:

- [x] Align the existing 1..30 request requirement bound across provider schema,
  prompt and local validation; distinguish underflow/overflow diagnostics. Two
  live outputs contained 35 and 33 requirements. Add offline boundary fixtures
  before explicitly scoped paid verification; no truncation, limit increase,
  provenance relaxation or automatic paid retries.
- [x] Represent an explicitly source-grounded non-demand/reference outcome without
  inventing requirements or compatibility comparisons. A model correctly returned
  zero requirements for an article, but local validation rejected it; another
  article became seven inferred mandatory outline criteria. Keep strict validation
  for actual requests and preserve charged traces on empty/non-demand outcomes.
- [ ] Separately investigate contribution granularity, gap-versus-prohibition
  hints and bounded source/retrieval ranking using retained fixtures. These are
  recall/qualification questions, not authorization for universal parser expansion.

Contract 18 implements the first two items with offline regressions. Actual
demands remain bounded to 1..30 requirements. The wire schema allows 0..30 so a
typed `not_a_request` disposition can use exactly zero; local validation enforces
that status-dependent rule in both schema and JSON modes. Such dispositions need
complete supplied discussion, known discussion source IDs and a nonempty reason.
They are model interpretations, not proof of absent demand or compatibility
rejections. They persist separately, stop before target/comparison acquisition,
and do not trigger replacement candidates, implicit retries or budget refunds.
Completed JSON outputs are audited before wire/semantic validation, including
charged invalid outputs; malformed, refused or incomplete responses are not
accepted as completed JSON evidence. Historical evaluations are unchanged and
older contracts remain historical. Fresh real-model verification of these fixes
is still pending; implementation and offline tests make no paid calls. The local
Windows run passes 736 tests, including 21 browser fixtures and 26 typed-outcome
tests covering provider/import persistence, resume, mixed samples, atomic rollback
and comparison short-circuiting. Review corrections preserve valid non-object
JSON attempts before shape rejection, attribute and atomically persist coding-agent
non-demand imports, and expose safe source links in the dashboard. These remain
offline checks, not a fresh model-quality experiment.

Keep structural extractions separate. UI/key-entry features and Go/Rust expansion
remain deferred until the core discovery outcomes are adequately validated.

The prior contract-14 offline replay of the retained eight-repository cohort packed
all 8 enrichment, 24 extraction and 20 comparison inputs within the existing
180,000-byte transport bound (maximum 164,598 bytes). The contract-16 no-spend
replay repeated all 8 enrichment, 24 extraction and 20 comparison inputs, with a
maximum of 164,617 bytes. Both stopped at a fixture reservation before HTTP,
without calling the model or rewriting saved results. These checked context
feasibility, not discovery accuracy or full repository coverage.

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
  - [x] Characterize repository counters, metadata changes, event deduplication,
    validation/clock order and batch rollback before extracting snapshot writes.
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
  - [x] Move repository counter/metadata snapshots and their event writes to
    `storage/repository_snapshots.py`, using supplied connections and callbacks.
  - [ ] Extract traffic and relationship snapshot persistence. Move remaining
    alias-resolution network orchestration with GitHub acquisition into `services/`.
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
only on a test database. Traffic and relationship snapshot persistence remain
planned work, along with acquisition, scheduling and HTTP extraction.

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
Registry ordering and collision precedence are retained, including
case-only renames, canonical snapshot precedence and the distinction between an
uninitialized registry and an initialized empty registry. The historical lookup
still excludes names found only in metadata snapshots or repository events.

Characterization and direct-module tests cover all five history tables, immutable
IDs, reused names, creation/first-seen dates, independent traffic metrics, caller
rollback, partial progress after resolver failure and account-selected databases.
Isolated imports and installed-module checks exercise only owned test databases,
with fake resolver replies and no paid provider calls.

The separate daily-traffic collision fix now copies each selected metric's
counts, unique counts, availability and provenance together. Views and clones
remain independent: retaining the canonical observation also retains its status.
Unavailable legacy or missing rows are not promoted to observed evidence.
Regressions cover observed values, explicit observed zeroes, unique-only values,
partial metrics, rollback, registry renames and CSV/JSON exports. No retrospective
migration is attempted: provenance already lost in earlier merges cannot reliably
be reconstructed from stored counts alone.

## Repository snapshot boundary

[`storage/repository_snapshots.py`](../storage/repository_snapshots.py) writes
repository counters, metadata snapshots and repository events using a supplied
connection. Name validation, detection-time fallback and metadata event recording
are explicit callbacks; the module does not choose an account or path, read a
global clock, contact GitHub or import the entry point or AI provider.

`app.py` retains thin compatibility delegates and connection ownership. Existing
patches of the validator, clock and event writer still apply. Metadata changes and
their events share a transaction, including rollback of earlier writes when a
later repository fails. SQL text, normalization, latest-snapshot comparison,
replacement/deduplication rules, changed-field ordering and callback order are
retained. The counter writer deliberately retains its existing conversions and
does not introduce new repository-name validation.

Characterization and direct-module tests cover default and malformed values,
duplicate timestamps, topic ordering, all changed metadata fields, duplicate
events, false/failed event callbacks, account-selected paths, input preservation
and caller-managed rollback. Fresh imports perform no database/directory/thread
work. The installer ships the module, and isolated installed-module checks write
only owned fixture snapshots and metadata events. Traffic evidence rules,
relationship membership persistence, collection orchestration and event reads
remain outside this extraction.

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
