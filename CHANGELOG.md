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

### Changed

- Windows installer includes the new modules; an explicit temporary destination
  supports install/update smoke checks while preserving data.
- CI covers Windows/Linux and Python 3.10/3.13; existing analytics remain independent
  from Missing Link and optional AI.
- Missing Link results are placed ahead of the collapsible capability inventory;
  no fictional successful matches are added to synthetic demo mode.

### Boundaries

- No private repository analysis, automatic publication or host execution.
- No isolated proof runner is configured. Third-party bridges are not executed.
- Real model quality/integration remains untested without a configured provider;
  protocol tests are fixtures, not AI evaluation or third-party execution proof.

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
