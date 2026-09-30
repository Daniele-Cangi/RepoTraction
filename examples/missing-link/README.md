# Source-reviewed case analyses (not simulated successes)

These coding-agent analyses correspond to the public cases documented in
[the case study](../../docs/missing-link-cases.md). They are **not** automatically
loaded into the product or used as a discovery engine. In these source-reviewed
analyses no third-party code or proposed bridge was executed. The positive result is a source-supported adapter
candidate, not a demonstrated third-party integration.

To inspect them in Missing Link:

1. Analyze `un33k/python-slugify` and inspect the coverage/capabilities.
2. Evaluate one of the three issue URLs in the case study, with AI disabled.
3. Download that job's source context. Compare the actual fetched revision,
   discussion quotes and capability IDs with this example before importing.
4. Import the corresponding `*-analysis.json` in **Coding-agent handoff**.
5. Inspect requirements, constraints and the NOT EXECUTED bridge; download the
   handoff JSON or ZIP if useful. No external contribution is published.

The inspected repository revision was
`866401ea6b346d7575cf941bc73ad32a362e34aa`. A new commit, changed discussion or
changed requirements requires a fresh review. Do not blindly reuse these
conclusions on a different revision. The importer checks references and quotes,
not the truth of arbitrary coding-agent reasoning.

`check_meta_description.py` is different: a human-reviewed controlled test used
by the subsequent [real API/WASI verification](../../docs/missing-link-api-verification.md).
It is not an analysis import. Run it only through the approved isolated example
API, with the inspected generated adapter and pinned public source. Fixture
budgets and the strict oversized-word policy are explicit assumptions.
