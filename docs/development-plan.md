# RepoTraction development plan

The next architectural task is to split the roughly 4,000-line `app.py` into
focused modules without changing application behavior. This is planned work,
not a completed migration. Effective immediately, new separable implementation
belongs in dedicated modules rather than the monolith; the repository instruction
in [AGENTS.md](../AGENTS.md) applies to future work.

## Modularization sequence

- [ ] Establish characterization tests for existing public behavior and map
  dependencies, including test patches of globals and account-specific state.
- [ ] Extract pure calculations into `analytics/`: date windows, traffic
  comparisons, event metrics, repository health and signal calculations. Pass
  timestamps and configuration explicitly where practical.
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
