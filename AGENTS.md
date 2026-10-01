# Repository development instructions

## Keep new implementation out of the monolith

Do not add separable business logic, storage operations, migrations, HTTP routing,
GitHub acquisition or scheduling logic to `app.py`. Put new implementation in
dedicated modules with explicit dependencies and tests. Existing `missing_link/`
functionality should remain in that package.

Changes to `app.py` should be limited to startup wiring, thin delegation and
necessary localized corrections to existing behavior. A bug fix does not require
a broad extraction, but must not introduce a new subsystem into the monolith.

Follow [the modularization plan](docs/development-plan.md). Extract incrementally;
preserve CLI commands, HTTP contracts, account isolation, database compatibility,
traffic evidence semantics and optional-provider behavior. Avoid circular imports,
module imports that start threads or perform network calls, and modules that import
`app.py` to access mutable global state.

Keep refactoring separate from feature changes and review fixes. Run focused
regressions and the complete suite before pushing each extraction. Do not merge
pull requests or perform paid AI calls merely to verify a structural change.
