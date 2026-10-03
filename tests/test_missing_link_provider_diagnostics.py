"""Safe provider stops: mocked transport, owned stores, no real paid calls."""
import io
import http.client
import json
import socket
import unittest
import urllib.error
from unittest import mock

from missing_link.job_errors import job_failure
from missing_link.provider import Provider, CandidateValidationError
from missing_link.service import Service
import test_missing_link as fixtures


class ProviderDiagnosticTests(unittest.TestCase):
    def provider(self, streaming=False):
        return Provider({"REPOTRACTION_AI_URL": "http://localhost/v1", "REPOTRACTION_AI_MODEL": "fixture",
            "REPOTRACTION_AI_API_KIND": "responses", "REPOTRACTION_AI_STREAMING": "1" if streaming else "0"})

    def failed_call(self, *, error=None, raw=None, lines=None, clock=None):
        opener, response, budget = mock.Mock(), mock.MagicMock(), mock.Mock()
        opener.open.return_value = response
        if error is not None:
            opener.open.side_effect = error
        response.__enter__.return_value.read.return_value = raw
        if lines is not None:
            response.__enter__.return_value.readline.side_effect = lines
        with mock.patch("urllib.request.build_opener", return_value=opener), \
             mock.patch("missing_link.provider.time.monotonic", side_effect=clock or [0, 1, 2, 3]):
            with self.assertRaises(Exception) as caught:
                self.provider(lines is not None).complete("private prompt", {}, budget, phase="request")
        outcome = job_failure(caught.exception)
        self.assertEqual(outcome["status"], "failed")
        self.assertIsNotNone(outcome["error_diagnostic"])
        self.assertEqual(outcome["error_diagnostic"]["category"], "ai_transport")
        self.assertEqual(outcome["error_diagnostic"]["phase"], "request")
        self.assertTrue(outcome["error_diagnostic"]["reservation_retained"])
        self.assertNotIn("private", json.dumps(outcome))
        self.assertNotIsInstance(caught.exception, CandidateValidationError)
        self.assertIsNone(caught.exception.__cause__)
        budget.reserve_ai.assert_called_once()
        budget.record_call.assert_not_called()
        budget.record_usage.assert_not_called()
        budget.record_output.assert_not_called()
        opener.open.assert_called_once()
        return outcome["error_diagnostic"]

    def test_socket_and_wrapped_timeouts_are_distinct_from_network_and_io(self):
        for error, code in ((socket.timeout("private timeout"), "ai_transport_timeout"),
                (urllib.error.URLError(socket.timeout("private timeout")), "ai_transport_timeout"),
                (urllib.error.URLError("private DNS message"), "ai_transport_network_error"),
                (OSError("private connection"), "ai_transport_io_error"),
                (http.client.IncompleteRead(b"private partial"), "ai_transport_io_error"),
                (ValueError("private header"), "ai_transport_protocol_error")):
            with self.subTest(code=code, kind=type(error).__name__):
                self.assertEqual(self.failed_call(error=error)["code"], code)

    def test_redirect_failure_has_no_external_request_or_response_receipt(self):
        from missing_link.provider import NoRedirect
        try:
            NoRedirect().redirect_request(None, None, 302, "private", {}, "https://private.example")
        except Exception as error:
            diagnostic = self.failed_call(error=error)
        self.assertEqual(diagnostic["code"], "ai_transport_redirect")

    def test_http_body_and_headers_are_not_read_or_copied(self):
        body = io.BytesIO(b"private response credential")
        error = urllib.error.HTTPError("https://private.endpoint", 503, "private reason", {"private": "key"}, body)
        diagnostic = self.failed_call(error=error)
        self.assertEqual(diagnostic["code"], "ai_transport_http_error")
        self.assertEqual(diagnostic["http_status"], 503)
        self.assertEqual(body.tell(), 0)

    def test_invalid_transport_json_and_envelope_have_separate_codes(self):
        for raw, code in ((b"private non-JSON", "ai_transport_invalid_json"),
                (b"\xff", "ai_transport_invalid_json"), (b"[]", "ai_transport_invalid_response")):
            with self.subTest(code=code, raw=raw):
                self.assertEqual(self.failed_call(raw=raw)["code"], code)

    def test_partial_and_malformed_streams_never_become_receipts(self):
        for lines, code in (([b'data: {private\n'], "ai_stream_invalid_event"),
                ([b'data: []\n'], "ai_stream_invalid_event"),
                ([b'data: {"type":"response.completed"}\n'], "ai_stream_invalid_event"),
                ([b'data: {"type":"response.completed","response":[]}\n'], "ai_stream_invalid_event"),
                ([b'data: {"type":"response.output_text.delta","delta":"private"}\n', b""], "ai_stream_missing_terminal")):
            with self.subTest(code=code, lines=lines):
                self.assertEqual(self.failed_call(lines=lines)["code"], code)

    def test_mismatched_terminal_event_and_status_never_become_receipts(self):
        for event in ("completed", "failed", "incomplete"):
            for status in ("completed", "failed", "incomplete", None):
                if event == status:
                    continue
                with self.subTest(event=event, status=status):
                    result = {"status": status, "usage": {"input_tokens": 1, "output_tokens": 2},
                        "output": [{"type": "message", "content": [{"type": "output_text", "text": '{"fixture":true}'}]}]}
                    line = ("data: " + json.dumps({"type": "response." + event, "response": result}) + "\n").encode()
                    self.assertEqual(self.failed_call(lines=[line, b""])["code"], "ai_stream_invalid_event")

    def test_consistent_terminal_events_preserve_receipt_and_output_boundaries(self):
        for status in ("completed", "failed", "incomplete"):
            with self.subTest(status=status):
                opener, response, budget = mock.Mock(), mock.MagicMock(), mock.Mock()
                result = {"status": status, "usage": {"input_tokens": 1, "output_tokens": 2},
                    "output": [{"type": "message", "content": [{"type": "output_text", "text": '{"fixture":true}'}]}]}
                response.__enter__.return_value.readline.side_effect = [
                    ("data: " + json.dumps({"type": "response." + status, "response": result}) + "\n").encode(), b""]
                opener.open.return_value = response
                with mock.patch("urllib.request.build_opener", return_value=opener):
                    if status == "completed":
                        self.assertEqual(self.provider(True).complete("Fixture", {}, budget), {"fixture": True})
                        budget.record_output.assert_called_once()
                    else:
                        with self.assertRaises(CandidateValidationError):
                            self.provider(True).complete("Fixture", {}, budget)
                        budget.record_output.assert_not_called()
                budget.record_usage.assert_called_once()
                budget.record_call.assert_called_once()

    def test_stream_size_and_deadline_bounds_are_unchanged(self):
        self.assertEqual(self.failed_call(lines=[b"x" * 512001])["code"], "ai_transport_size_exceeded")
        self.assertEqual(self.failed_call(lines=[b"event: private\n"], clock=[0, 241])["code"], "ai_stream_deadline_exceeded")


class ProviderStopPersistenceTests(unittest.TestCase):
    setUp = fixtures.ServiceTests.setUp
    fake_sources = fixtures.ServiceTests.fake_sources

    def stopped_call(self, *, terminal_event=None):
        provider = Provider({"REPOTRACTION_AI_URL": "http://localhost/v1", "REPOTRACTION_AI_MODEL": "fixture",
            "REPOTRACTION_AI_API_KIND": "responses", "REPOTRACTION_AI_INPUT_USD_PER_MILLION": "1",
            "REPOTRACTION_AI_STREAMING": "1" if terminal_event else "0",
            "REPOTRACTION_AI_TOTAL_BUDGET_USD": "2", "REPOTRACTION_AI_BUDGET_ID": "transport-fixture"})
        self.service.provider = provider
        source, opener = self.fake_sources(), mock.Mock()
        source.search_issues.return_value = {"items": [{"url": fixtures.issue()["url"]},
            {"url": "https://github.com/example/other/issues/9"}]}
        if terminal_event:
            def opened(request, **_kwargs):
                context = json.loads(json.loads(request.data)["input"][1]["content"].split("\nUNTRUSTED_DATA_JSON:\n", 1)[1])
                result = {"status": "completed", "usage": {"input_tokens": 1, "output_tokens": 2},
                    "output": [{"type": "message", "content": [{"type": "output_text", "text": json.dumps(fixtures.wire_request(context))}]}]}
                response = mock.MagicMock()
                response.__enter__.return_value.readline.side_effect = [
                    ("data: " + json.dumps({"type": "response." + terminal_event, "response": result}) + "\n").encode(), b""]
                return response
            opener.open.side_effect = opened
        else:
            opener.open.side_effect = urllib.error.URLError(socket.timeout("private key prompt"))
        with mock.patch("missing_link.service.PublicGitHub", return_value=source), \
             mock.patch("missing_link.service.extract_structure", return_value=fixtures.repository()["capabilities"]), \
             mock.patch.object(provider, "interpret_capabilities", return_value=fixtures.repository()["capabilities"]), \
             mock.patch.object(provider, "evaluate") as evaluate, \
             mock.patch("urllib.request.build_opener", return_value=opener):
            started = self.service.start({"repo": "example/words", "use_ai": True}, background=False)
        job = self.service.store.get("jobs", started["job_id"])
        self.assertEqual(job["status"], "failed")
        self.assertEqual(job["ai_calls_used"], 1)
        self.assertGreater(job["cost_reserved_usd"], 0)
        code = "ai_stream_invalid_event" if terminal_event else "ai_transport_timeout"
        self.assertEqual(job["error_diagnostic"], {"category": "ai_transport", "code": code,
            "phase": "request", "reservation_retained": True, "response_receipt": "unavailable",
            "call_number": 1, "attempt_id": job["id"] + ":1"})
        self.assertFalse(job.get("ai_trace"))
        self.assertFalse(job["checkpoint"].get("ai_outputs"))
        self.assertFalse(job["result"].get("candidate_errors"))
        self.assertFalse(job["result"]["match_ids"])
        source.fetch_issue.assert_called_once()
        evaluate.assert_not_called()
        opener.open.assert_called_once()
        restarted = Service(self.path, "alice", self.read, lambda: "alice", provider)
        self.assertEqual(restarted.store.get("jobs", job["id"]), job)
        self.assertEqual(restarted.store.ai_reserved("transport-fixture"), job["cost_reserved_usd"])
        self.assertFalse(restarted.threads)

    def test_failed_call_is_global_and_keeps_attempt_charge_after_restart(self):
        self.stopped_call()

    def test_mismatched_terminal_keeps_unknown_charge_and_stops_later_candidates(self):
        self.stopped_call(terminal_event="incomplete")


if __name__ == "__main__":
    unittest.main()
