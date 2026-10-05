"""No-network terminal-stream controls for the explicit experimental executor."""
import copy
import json
import unittest
from unittest.mock import patch

from missing_link.provider import Provider, ResponseError, CandidateValidationError
from scripts import missing_link_triage_property_execution as task
from scripts.missing_link_triage_receipts import ReceiptPersistenceError
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
    def simulate(self, outputs, *, fail_identity=False, fail_reservation=None, fail_receipt=False,
                 fail_close=False, fail_identity_after_receipt=False, mutate_receipt=False):
        provider = Provider({"REPOTRACTION_AI_URL": "http://127.0.0.1:1", "REPOTRACTION_AI_MODEL": "fixture",
            "REPOTRACTION_AI_API_KIND": "responses", "REPOTRACTION_AI_STREAMING": "1",
            "REPOTRACTION_AI_RESPONSE_FORMAT": "json_schema", "REPOTRACTION_AI_MAX_CALLS": "1",
            "REPOTRACTION_AI_MAX_OUTPUT_TOKENS": "6000", "REPOTRACTION_AI_INPUT_USD_PER_MILLION": ".1",
            "REPOTRACTION_AI_OUTPUT_USD_PER_MILLION": ".5"})
        rows = cases()
        before = copy.deepcopy(rows)
        self.jobs, self.reserves, self.results, self.identities, self.calls = {}, [], [], [], 0
        self.terminals, self.order = {}, []
        def persist(n, job): self.jobs[n] = copy.deepcopy(job)
        def retain(n, receipt):
            if fail_receipt: raise OSError("Storage failure with private content")
            self.terminals[n] = copy.deepcopy(receipt)
            self.order.append((n, "terminal"))
            if mutate_receipt: receipt["response"]["output"] = []
        def record(result):
            self.order.append((result["case"], "result"))
            self.results.append(result)
        def identity(*, force=False):
            self.identities.append(force)
            if fail_identity: raise RuntimeError("Account changed")
            if fail_identity_after_receipt and self.terminals: raise RuntimeError("Account changed in flight")
        def reserve(job_id, cost):
            if len(self.reserves) + 1 == fail_reservation: raise ValueError("Original allowance cap")
            self.reserves.append((job_id, cost))
        class CloseFailure(Stream):
            def __exit__(self, *args): raise OSError("Close failure")
        with patch("scripts.missing_link_triage_receipts.urllib.request.build_opener") as opener:
            opener.return_value.open.side_effect = [(CloseFailure if fail_close else Stream)(output) for output in outputs]
            try:
                task.execute_cases(provider, rows, segment="fixture-property", identity=identity,
                    reserve=reserve, persist=persist, retain_terminal=retain, record=record)
            finally:
                self.calls = opener.return_value.open.call_count
                self.assertEqual(rows, before)
                for row, call in zip(before, opener.return_value.open.call_args_list):
                    request = call.args[0]
                    payload = json.loads(request.data)
                    self.assertTrue(payload["input"][1]["content"].startswith(task.PROMPT + "\nUNTRUSTED_DATA_JSON:\n"))
                    endpoint, _, encoded = provider._encode_prompt(task.PROMPT, row["data"],
                        task.schema_for_context(row["data"]), "analysis")
                    self.assertEqual(request.data, encoded)
                    self.assertEqual(request.full_url, provider.url + endpoint)
                    expected_cost = ((len(encoded) + 2048) * provider.input_price + provider.max_tokens * provider.output_price) / 1e6
                    self.assertAlmostEqual(self.reserves[row["case"] - 1][1], expected_cost)

    def test_nine_single_calls_preserve_raw_receipts_and_terminal_usage(self):
        raw = fixtures.unknown()
        self.simulate([event(raw) for _ in range(9)])
        self.assertEqual(self.calls, 9)
        self.assertEqual(sum(self.identities), 9)
        self.assertEqual(len(self.reserves), 9)
        self.assertEqual(len({key for key, cost in self.reserves}), 9)
        for result in self.results:
            job = self.jobs[result["case"]]
            self.assertEqual(result["parsed"], raw)
            self.assertEqual(self.terminals[result["case"]], event(raw))
            self.assertLess(self.order.index((result["case"], "terminal")), self.order.index((result["case"], "result")))
            self.assertEqual(result["checked"]["summary"]["status"], "context_required")
            self.assertEqual(job["ai_calls_used"], 1)
            self.assertEqual(job["checkpoint"]["ai_outputs"][0]["output"], raw)
            self.assertEqual(job["reported_usage"][0]["input_tokens"], 100)

    def test_local_invalid_output_is_preserved_then_next_case_once(self):
        raw = fixtures.unknown()
        raw["facets"]["outcome"]["requested_part"] = "Invalid non-slice description"
        self.simulate([event(raw)] + [event(fixtures.unknown()) for _ in range(8)])
        self.assertEqual(self.calls, 9)
        self.assertEqual(self.results[0]["parsed"], raw)
        self.assertEqual(self.terminals[1], event(raw))
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
        self.assertEqual(self.terminals[1], event(raw))

    def test_missing_terminal_stops_without_retry_and_keeps_usage_unknown(self):
        with self.assertRaises(ResponseError): self.simulate([event(fixtures.unknown()), None])
        self.assertEqual(self.calls, 2)
        self.assertEqual(len(self.reserves), 2)
        self.assertEqual(len(self.results), 1)
        self.assertNotIn("reported_usage", self.jobs[2])
        self.assertNotIn(2, self.terminals)

    def test_incomplete_terminal_stops_with_original_usage_retained(self):
        with self.assertRaises(CandidateValidationError): self.simulate([event(fixtures.unknown(), "incomplete")])
        self.assertEqual(self.calls, 1)
        self.assertEqual(len(self.results), 0)
        self.assertEqual(self.jobs[1]["ai_trace"][0]["response_status"], "incomplete")
        self.assertEqual(self.jobs[1]["reported_usage"][0]["input_tokens"], 100)
        self.assertEqual(self.terminals[1], event(fixtures.unknown(), "incomplete"))

    def test_completed_envelope_preserves_extra_fields_and_full_output(self):
        terminal = event(fixtures.unknown())
        terminal.update(sequence_number=19, extra_event={"fixture": "retained"})
        terminal["response"].update(metadata={"extra": [1, 2]}, created_at=123, extra_response="retained")
        terminal["response"]["output"].insert(0, {"type": "reasoning", "summary": [{"text": "fixture summary"}]})
        self.simulate([terminal] + [event(fixtures.unknown()) for _ in range(8)])
        self.assertEqual(self.terminals[1], terminal)
        self.assertNotIn("terminal_receipt", self.jobs[1])
        self.assertNotIn("extra_response", self.results[0]["parsed"])

    def test_incomplete_partial_text_and_details_survive_without_acceptance(self):
        terminal = event(fixtures.unknown(), "incomplete")
        terminal["response"]["incomplete_details"] = {"reason": "max_output_tokens"}
        terminal["response"]["output"][0]["content"][0]["text"] = '{"unfinished":'
        terminal["response"]["usage"] = None
        with self.assertRaises(CandidateValidationError): self.simulate([terminal])
        self.assertEqual(self.terminals[1], terminal)
        self.assertNotIn("reported_usage", self.jobs[1])
        self.assertNotIn("ai_outputs", self.jobs[1]["checkpoint"])
        self.assertEqual((self.calls, len(self.results)), (1, 0))

    def test_refused_content_survives_without_acceptance(self):
        terminal = event(fixtures.unknown())
        terminal["response"]["output"][0]["content"] = [{"type": "refusal", "refusal": "Fixture refusal"}]
        with self.assertRaises(CandidateValidationError): self.simulate([terminal])
        self.assertEqual(self.terminals[1], terminal)
        self.assertNotIn("ai_outputs", self.jobs[1]["checkpoint"])
        self.assertEqual((self.calls, len(self.results)), (1, 0))

    def test_failed_response_preserves_error_without_logging_it(self):
        terminal = event(fixtures.unknown(), "failed")
        terminal["response"]["error"] = {"code": "fixture_failure", "message": "Untrusted details"}
        with self.assertRaises(CandidateValidationError) as caught: self.simulate([terminal])
        self.assertEqual(self.terminals[1], terminal)
        self.assertNotIn("Untrusted details", str(caught.exception))
        self.assertEqual(self.calls, 1)

    def test_receipt_storage_failure_stops_before_acceptance_or_next_request(self):
        with self.assertRaises(ReceiptPersistenceError) as caught:
            self.simulate([event(fixtures.unknown())], fail_receipt=True)
        self.assertNotIn("private content", str(caught.exception))
        self.assertEqual((self.calls, len(self.reserves), len(self.results)), (1, 1, 0))
        self.assertEqual(self.terminals, {})
        self.assertNotIn("ai_outputs", self.jobs[1]["checkpoint"])

    def test_close_failure_does_not_discard_received_terminal(self):
        terminal = event(fixtures.unknown())
        with self.assertRaises(ResponseError): self.simulate([terminal], fail_close=True)
        self.assertEqual(self.terminals[1], terminal)
        self.assertEqual((self.calls, len(self.results)), (1, 0))

    def test_account_change_after_terminal_preserves_receipt_but_stops(self):
        terminal = event(fixtures.unknown())
        with self.assertRaisesRegex(RuntimeError, "Account changed in flight"):
            self.simulate([terminal], fail_identity_after_receipt=True)
        self.assertEqual(self.terminals[1], terminal)
        self.assertEqual((self.calls, len(self.results)), (1, 0))

    def test_receipt_callback_cannot_mutate_interpreted_response(self):
        self.simulate([event(fixtures.unknown()) for _ in range(9)], mutate_receipt=True)
        self.assertEqual(len(self.results), 9)

    def test_inconsistent_terminal_is_not_certified_as_receipt(self):
        terminal = event(fixtures.unknown())
        terminal["response"]["status"] = "incomplete"
        with self.assertRaises(ResponseError): self.simulate([terminal])
        self.assertEqual(self.terminals, {})
        self.assertEqual((self.calls, len(self.results)), (1, 0))

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
