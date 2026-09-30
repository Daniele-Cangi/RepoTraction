# Changelog

## 3.1.0 — 2026-09-30 (development)

### Added

- Missing Link: public source acquisition at pinned revisions, Python AST and
  partial JS/TS declaration coverage, issue/comment/timeline context and bounded
  capability-derived discovery.
- Independent demand interpretation, requirement-level compatibility, hard
  blockers, existing-versus-new bridge contributions, and coding-agent handoffs.
- Optional OpenAI-compatible provider with explicit opt-in, request/call/cost
  bounds; conservative no-provider mode does not certify lexical candidates.
- Per-account persistent jobs with cancellation/resume, immutable-source reuse,
  corrections/feedback provenance and stale-result handling.
- Inspection-only JSON/ZIP proof packages with original criteria, source/license
  evidence, hashes, safe file paths and NOT EXECUTED status.
- Source-reviewed positive, lower-level reuse and deceptive-similarity cases;
  repeatable optional browser regressions and a read-only live browser check.
- Real GitHub/OpenAI API investigation without manual analysis import, including
  a useful narrow adapter, rejected false positives and recorded uncertainty.
- Optional explicitly approved Wasmtime/WASI Python examples without Docker;
  pinned runtime bootstrap, bounded execution and separate persistent receipts.

### Changed

- Windows installer includes the new modules; an explicit temporary destination
  supports install/update smoke checks while preserving data.
- CI covers Windows/Linux and Python 3.10/3.13; existing analytics remain independent
  from Missing Link and optional AI.
- Missing Link results are placed ahead of the collapsible capability inventory;
  no fictional successful matches are added to synthetic demo mode.
- Freshness follows immutable repository/issue identities and effective capability
  interpretations; corrections retain history and require reevaluation.
- Open dashboards recover abandoned investigations when the worker lease becomes
  free, without pausing healthy workers or automatically restarting paid work.
- Candidate definition spans precede broad file context, and tiny package
  initializers are sampled after implementation modules.
- WASI Python startup disables site hooks and unsafe startup paths; trusted
  stdlib precedes project dependencies, which are added only after startup.

### Boundaries

- No private repository analysis, automatic publication or host execution.
- Optional pure-Python examples have run in isolation; they do not establish
  original-request compliance or production/target-application integration.
- Real API cases are separate from fictional protocol and browser acceptance
  fixtures. They do not establish general discovery accuracy or fresh demand.

## 3.0.0 — 2026-09-28

RepoTraction 3.0.0 consolidates the Insights expansion and hardens the data model, collection pipeline, account isolation, and local HTTP surface.

### Added

- Impact Ledger and Impact Lab with portfolio-baseline comparisons.
- Headless snapshot collection for local schedulers.
- Repository identity tracking based on immutable GitHub repository IDs.
- Explicit support contact and automated CI across supported Python versions.

### Changed

- Views and clone availability are tracked separately so missing GitHub data is not presented as measured zero.
- Collection status now distinguishes completed, partial, and failed runs.
- Account changes in GitHub CLI are detected before data is written.
- GitHub API concurrency is capped locally and explicit rate-limit failures stop the active collection.
- The local HTTP server validates loopback hosts and cross-origin requests.
- JSON export is documented as an analytics export rather than a restorable database backup.
- Impact Lab confidence is aligned with the metric that produced the reported result.

### Fixed

- Headless collection exit status after failed runs.
- Partial traffic failures being reported as fully successful collections.
- Historical traffic preservation during repository renames and legacy migrations.
- Reused repository names and empty active-repository registry edge cases.
- Archived repositories affecting traffic readiness.
- Empty traffic windows and default HTTP-port handling.

## 2.0.0 — 2026-08-21

Initial public baseline, originally released under the GitHub Pulse name, with local repository traffic analytics, stars, relationship tracking, activity signals, SQLite history, and exports.
