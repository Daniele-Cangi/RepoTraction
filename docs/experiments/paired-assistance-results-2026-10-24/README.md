# Execution of the frozen #141 comparison

The user authorized the proposed two development agents and USD 0.30 aggregate
on 2026-10-24 (Europe/Rome), conditional on readiness. Preparation #141 is merged
at `c52ca49`; its exact head `771205b` has a clean Codex review and all four
Windows/Linux Python 3.10/3.13 CI jobs passed (run `40027748982`).

This follow-up retains the same request, tests, prompts, limits, source policy
and acceptance. Historical files are unchanged. `execution_bindings.py` is the
small case binding anticipated in the protocol: the previous frozen-read pattern,
ordinary Service/Provider/Budget/Store and identical metered notes/GitHub access
for both solvers. It adds no product mode, transport or agent runner. The existing
worker lease serializes helper use. Operator-created clocks cannot be reset by
the helper CLI. B's discovery and later helper calls consume one shared ledger.

Official [GPT-6 Luna documentation](https://developers.openai.com/api/docs/models/gpt-6-luna)
was fetched on 2026-10-24: Standard short-context input USD 0.10 and output USD
0.50 per million tokens. Both arms explicitly request `service_tier=default`;
the existing serialized-byte reservation and persisted USD 0.15 ceilings remain.
There are no hosted model tools or extra tool charges in these provider calls.
Six worst-size calls reserve USD 0.1452288 per arm, not a predicted invoice.

Offline preflight (`python test_bindings.py`) uses temporary ledgers, mocked
identity and no provider requests. It checks expiry, no restart, shared call and
request counters, atomic allowance protection, provider settings and frozen
reads. Effective solver prompts will be the original common/arm text plus only
operational paths, remaining resources and any native strategy packet. The
existing native pipeline retains its own prompts, recorded in private job data.

The two solver dispatches will both use `fork_turns=none`, with model and effort
overrides omitted. Tool semantics guarantee inheritance of the same parent
settings. The runtime does not expose an exact backend model snapshot or hidden
reasoning token use; record that limitation rather than inventing identifiers or
claiming proven identical compute. Run A then B, as frozen. No outcome is assumed.

This initial execution commit precedes both clocks, agents, donor searches and
paid calls. Review this binding/effective-prompt contract before dispatch. Results,
ledgers, patches, native checks and timing observations will be appended here;
no old evidence is rewritten. All target copies stay in ignored RepoTraction data.
