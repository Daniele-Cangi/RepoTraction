"""Experimental triage transport adapters; not wired into production discovery.

No network or credential lookup on import. These adapters do not establish
semantic support, repair citations, select candidates or qualify connections.
"""
import copy


class IdentityCheck:
    """Reuse only a successful fixed-account check for at most three seconds.

    A caller must force a fresh check before each provider request. Failed checks
    invalidate prior success; time spent verifying does not consume the cache.
    Cancellation and allowance checks remain the responsibility of Budget.
    """
    def __init__(self, verify, clock):
        self.verify, self.clock = verify, clock
        self.checked = float("-inf")

    def __call__(self, *, force=False):
        if not force and 0 <= self.clock() - self.checked < 3:
            return
        self.checked = float("-inf")
        self.verify()
        self.checked = self.clock()


def wire_schema(original_schema):
    """Use empty-string unknown references with the existing local validator."""
    result = copy.deepcopy(original_schema)
    for facet in result["properties"]["facets"]["properties"].values():
        for name in ("demand_source", "demand_quote", "operation_id"):
            facet["properties"][name] = {"type": "string"}
    return result


def decode_references(raw):
    """Map only declared unknown sentinels, preserving the original response."""
    result = copy.deepcopy(raw)
    for facet in result["facets"].values():
        if facet["relation"] == "unknown":
            for name in ("demand_source", "demand_quote", "operation_id"):
                if facet[name] != "":
                    raise ValueError("Unknown wire references must be empty strings")
                facet[name] = None
    return result
