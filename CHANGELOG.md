# Changelog

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
