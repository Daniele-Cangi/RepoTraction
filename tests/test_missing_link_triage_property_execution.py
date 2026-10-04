"""No-network terminal-stream controls for the explicit experimental executor."""
import copy
import json
import unittest
from unittest.mock import patch

from missing_link.provider import Provider, ResponseError, CandidateValidationError
from scripts import missing_link_triage_property_execution as task
import test_missing_link_triage_properties as fixtures


class Stream:
    def __init__(self, value): self.value = value
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def readline(self, limit):
        if self.value is None: return b""
        value, self.value = self.value, None
        return ("data: " + json.dumps(value) + "\n").encode()


def event(raw, status="completed"):
    return {"type": "response." + status, "response": {"id": "fixture", "status": status,
        "usage": {"input_tokens": 100, "output_tokens": 50},
        "output": [{"type": "message", "content": [{"type": "output_text", "text": json.dumps(raw)}]}]}}


def cases():
    raw, data, sources, body, spans = fixtures.fixture("Return command text.",
        "function operation() { return false; }", "output", "Command text", "Boolean false")
    return [{"case": n, "issue": "https://github.com/fixture/request/issues/1", "data": copy.deepcopy(data),
        "demand_sources": copy.deepcopy(sources), "operation_body": body, "operation_spans": copy.deepcopy(spans)}
        for n in range(1, 10)]


class PropertyExecutionTests(unittest.TestCase):
    def simulate(self, outputs, *, fail_identity=False, fail_reservation=None):
        provider = Provider({"REPOTRACTION_AI_URL": "http://127.0.0.1:1", "REPOTRACTION_AI_MODEL": "fixture",
            "REPOTRACTION_AI_API_KIND": "responses", "REPOTRACTION_AI_STREAMING": "1",
            "REPOTRACTION_AI_RESPONSE_FORMAT": "json_schema", "REPOTRACTION_AI_MAX_CALLS": "1",
            "REPOTRACTION_AI_MAX_OUTPUT_TOKENS": "6000", "REPOTRACTION_AI_INPUT_USD_PER_MILLION": ".1",
            "REPOTRACTION_AI_OUTPUT_USD_PER_MILLION": ".5"})
        rows = cases()
        before = copy.deepcopy(rows)
        self.jobs, self.reserves, self.results, self.identities, self.calls = {}, [], [], [], 0
        def persist(n, job): self.jobs[n] = copy.deepcopy(job)
        def identity(*, force=False):
            self.identities.append(force)
            if fail_identity: raise RuntimeError("Account changed")
        def reserve(job_id, cost):
            if len(self.reserves) + 1 == fail_reservation: raise ValueError("Original allowance cap")
            self.reserves.append((job_id, cost))
        with patch("missing_link.provider.urllib.request.build_opener") as opener:
            opener.return_value.open.side_effect = [Stream(output) for output in outputs]
            try:
                task.execute_cases(provider, rows, segment="fixture-property", identity=identity,
                    reserve=reserve, persist=persist, record=self.results.append)
            finally:
                self.calls = opener.return_value.open.call_count
                self.assertEqual(rows, before)
                for call in opener.return_value.open.call_args_list:
                    request = call.args[0]
                    payload = json.loads(request.data)
                    self.assertTrue(payload["input"][1]["content"].startswith(task.PROMPT + "\nUNTRUSTED_DATA_JSON:\n"))

    def test_nine_single_calls_preserve_raw_receipts_and_terminal_usage(self):
        raw = fixtures.unknown()
        self.simulate([event(raw) for _ in range(9)])
        self.assertEqual(self.calls, 9)
        self.assertEqual(sum(self.identities), 9)
        self.assertEqual(len(self.reserves), 9)
        self.assertEqual(len({key for key, cost in self.reserves}), 9)
        for result in self.results:
            job = self.jobs[result["case"]]
            self.assertEqual(result["raw"], raw)
            self.assertEqual(result["checked"]["summary"]["status"], "context_required")
            self.assertEqual(job["ai_calls_used"], 1)
            self.assertEqual(job["checkpoint"]["ai_outputs"][0]["output"], raw)
            self.assertEqual(job["reported_usage"][0]["input_tokens"], 100)

    def test_local_invalid_output_is_preserved_then_next_case_once(self):
        raw = fixtures.unknown()
        raw["facets"]["outcome"]["requested_part"] = "Invalid non-slice description"
        self.simulate([event(raw)] + [event(fixtures.unknown()) for _ in range(8)])
        self.assertEqual(self.calls, 9)
        self.assertEqual(self.results[0]["raw"], raw)
        self.assertIn("validation_error", self.results[0]["checked"])

    def test_provider_schema_rejection_stops_with_raw_receipt_not_repaired(self):
        raw = fixtures.unknown()
        raw["facets"]["output"].update(comparison_scope="requested_operation", operation_layer="selected_entrypoint",
            demand_property="Command text", operation_property="Boolean false", relation="different",
            demand_span_id="invented", operation_id="e0")
        with self.assertRaises(CandidateValidationError): self.simulate([event(raw)])
        self.assertEqual(self.calls, 1)
        self.assertEqual(self.results, [])
        self.assertEqual(self.jobs[1]["checkpoint"]["ai_outputs"][0]["output"], raw)

    def test_missing_terminal_stops_without_retry_and_keeps_usage_unknown(self):
        with self.assertRaises(ResponseError): self.simulate([event(fixtures.unknown()), None])
        self.assertEqual(self.calls, 2)
        self.assertEqual(len(self.reserves), 2)
        self.assertEqual(len(self.results), 1)
        self.assertNotIn("reported_usage", self.jobs[2])

    def test_incomplete_terminal_stops_with_original_usage_retained(self):
        with self.assertRaises(CandidateValidationError): self.simulate([event(fixtures.unknown(), "incomplete")])
        self.assertEqual(self.calls, 1)
        self.assertEqual(len(self.results), 0)
        self.assertEqual(self.jobs[1]["ai_trace"][0]["response_status"], "incomplete")
        self.assertEqual(self.jobs[1]["reported_usage"][0]["input_tokens"], 100)

    def test_account_failure_precedes_reservation_and_network(self):
        with self.assertRaisesRegex(RuntimeError, "Account changed"):
            self.simulate([], fail_identity=True)
        self.assertEqual(self.calls, 0)
        self.assertEqual(self.reserves, [])
        self.assertEqual(self.jobs, {})

    def test_atomic_allowance_rejection_stops_before_next_request(self):
        with self.assertRaisesRegex(ValueError, "Original allowance cap"):
            self.simulate([event(fixtures.unknown())], fail_reservation=2)
        self.assertEqual(self.calls, 1)
        self.assertEqual(len(self.reserves), 1)
        self.assertEqual(len(self.results), 1)
