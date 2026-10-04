"""No credentials, subprocesses, network or real allowance writes."""
import copy
import json
import unittest
from unittest.mock import patch

from missing_link.contracts import obj, string, validate_shape
from missing_link.provider import Provider
from missing_link.service import Budget
from scripts.missing_link_triage_contract import FACETS
from scripts.missing_link_triage_transport import IdentityCheck, wire_schema, decode_references


def schema():
    facet = obj(relation=string("aligned", "different", "unknown", "slice"), reason=string(),
                **{name: {"type": ["string", "null"]}
                   for name in ("demand_source", "demand_quote", "operation_id")})
    return obj(demand_complete={"type": "boolean"},
               facets=obj(**{name: copy.deepcopy(facet) for name in FACETS}))


def unknown():
    return {"demand_complete": False, "facets": {name: {"relation": "unknown", "reason": "Fixture",
        "demand_source": "", "demand_quote": "", "operation_id": ""} for name in FACETS}}


class TransportTests(unittest.TestCase):
    def test_success_cache_expiry_and_fresh_request(self):
        clock, calls = [0], []
        check = IdentityCheck(lambda: calls.append(True), lambda: clock[0])
        check(force=True)
        for _ in range(100):
            check()
        self.assertEqual(len(calls), 1)
        clock[0] = 3
        check()
        check(force=True)
        self.assertEqual(len(calls), 3)

    def test_failure_invalidates_prior_success(self):
        calls = []
        def verify():
            calls.append(True)
            if len(calls) > 1:
                raise RuntimeError("unverified identity")
        check = IdentityCheck(verify, lambda: 0)
        check()
        for force in (True, False):
            with self.assertRaises(RuntimeError):
                check(force=force)
        self.assertEqual(len(calls), 3)

    def test_timestamp_after_latency_and_backward_clock(self):
        clock, calls = [0], []
        def verify():
            calls.append(True)
            clock[0] += 10
        check = IdentityCheck(verify, lambda: clock[0])
        check()
        check()
        self.assertEqual(len(calls), 1)
        clock[0] = 0
        check()
        self.assertEqual(len(calls), 2)

    def test_wire_shape_and_original_schema_preserved(self):
        original = schema()
        before = copy.deepcopy(original)
        validate_shape(unknown(), wire_schema(original))
        self.assertEqual(original, before)

    def test_unknown_nonempty_reference_rejected(self):
        for key in ("demand_source", "demand_quote", "operation_id"):
            raw = unknown()
            raw["facets"]["runtime"][key] = "not empty"
            with self.assertRaises(ValueError):
                decode_references(raw)

    def test_no_relation_quote_or_raw_repair(self):
        raw = unknown()
        raw["facets"]["outcome"].update(relation="different", demand_source="q0",
            demand_quote=" Original\nquote ", operation_id="e0")
        before = copy.deepcopy(raw)
        decoded = decode_references(raw)
        self.assertEqual(raw, before)
        self.assertEqual(decoded["facets"]["outcome"], raw["facets"]["outcome"])
        self.assertIsNone(decoded["facets"]["runtime"]["demand_source"])

    def test_real_provider_path_simulated_stream_and_receipt(self):
        provider = Provider({"REPOTRACTION_AI_URL": "http://127.0.0.1:1",
            "REPOTRACTION_AI_MODEL": "fixture", "REPOTRACTION_AI_API_KIND": "responses",
            "REPOTRACTION_AI_STREAMING": "1", "REPOTRACTION_AI_RESPONSE_FORMAT": "json_schema"})
        raw = unknown()
        terminal = {"type": "response.completed", "response": {"id": "fixture", "status": "completed",
            "usage": {"input_tokens": 10, "output_tokens": 20},
            "output": [{"type": "message", "content": [{"type": "output_text", "text": json.dumps(raw)}]}]}}
        clock, calls = [0], []
        events = [b'data: {"type":"response.output_text.delta"}\n'] * 150
        events.append(("data: " + json.dumps(terminal) + "\n").encode())
        class Stream:
            def __init__(self): self.lines = iter(events)
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def readline(self, limit):
                clock[0] += .05
                return next(self.lines, b"")
        def verify():
            calls.append(True)
            clock[0] += 2
        check = IdentityCheck(verify, lambda: clock[0])
        check(force=True)
        job = {"id": "fixture", "ai_calls_used": 0, "cost_reserved_usd": 0, "checkpoint": {}}
        budget = Budget(job, lambda: None, lambda: False, check)
        with patch("missing_link.provider.urllib.request.build_opener") as opener, \
                patch("missing_link.provider.time.monotonic", side_effect=lambda: clock[0]):
            opener.return_value.open.return_value = Stream()
            result = provider.complete("Fixture", {}, budget, schema=wire_schema(schema()))
        self.assertEqual(result, raw)
        self.assertEqual(job["ai_calls_used"], 1)
        self.assertEqual(len(job["ai_trace"]), 1)
        self.assertEqual(len(job["checkpoint"]["ai_outputs"]), 1)
        self.assertEqual(job["reported_usage"][0]["input_tokens"], 10)
        self.assertEqual(len(calls), 3)
        self.assertIsNone(decode_references(result)["facets"]["outcome"]["operation_id"])


if __name__ == "__main__":
    unittest.main()
