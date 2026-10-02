"""Completed-output cancellation regressions; mocked HTTP and owned fixture DBs."""
import json
import unittest
from unittest import mock

from missing_link.provider import Provider
from missing_link.store import Store, redact_payload
import test_missing_link as fixtures


class CancellationAuditTests(unittest.TestCase):
    setUp = fixtures.ServiceTests.setUp
    fake_sources = fixtures.ServiceTests.fake_sources

    def cancelled_response(self, *, kind="responses", streaming=False, value=...,
                           cancel_at="complete", account_change=False, terminal_status="completed",
                           refusal=False, undecodable=False, malformed_partial=False):
        provider = Provider({"REPOTRACTION_AI_URL": "http://localhost/v1", "REPOTRACTION_AI_MODEL": "fixture",
            "REPOTRACTION_AI_API_KIND": kind, "REPOTRACTION_AI_STREAMING": "1" if streaming else "0",
            "REPOTRACTION_AI_INPUT_USD_PER_MILLION": "1", "REPOTRACTION_AI_OUTPUT_USD_PER_MILLION": "1"})
        self.service.provider = provider
        opener, response, source = mock.Mock(), mock.MagicMock(), self.fake_sources()
        retained = {}

        def stop():
            if account_change:
                self.account = "bob"
            else:
                current = self.service.store.list("jobs")[0]
                self.service.cancel(current["id"])

        def opened(request, **kwargs):
            payload = json.loads(request.data)
            messages = payload["input"] if kind == "responses" else payload["messages"]
            context = json.loads(messages[1]["content"].split("\nUNTRUSTED_DATA_JSON:\n", 1)[1])
            parsed = fixtures.wire_request(context) if value is ... else value
            retained["output"] = parsed
            content = "{" if undecodable else json.dumps(parsed)
            result = {"id": "resp_cancel_fixture", "status": terminal_status, "output": [{"type": "message", "content": [
                {"type": "refusal", "refusal": "Fixture refusal"} if refusal else {"type": "output_text", "text": content}]}],
                "usage": {"input_tokens": 10, "output_tokens": 20}}
            if kind == "chat":
                result = {"id": "chat_cancel_fixture", "choices": [{"finish_reason": "stop", "message": {"content": content}}],
                    "usage": {"prompt_tokens": 10, "completion_tokens": 20}}
            if streaming:
                partial = b'data: {\n' if malformed_partial else b'data: {"type":"response.output_text.delta","delta":"partial"}\n'
                lines = iter([b'event: fixture\n', partial,
                    ("data: " + json.dumps({"type": "response." + terminal_status, "response": result}) + "\n").encode()])

                def read_line(*_args):
                    line = next(lines, b"")
                    if (cancel_at == "partial" and line == partial) or (cancel_at == "complete" and b'"response":' in line):
                        stop()
                    return line

                response.__enter__.return_value.readline.side_effect = read_line
            else:
                def read(*_args):
                    stop()
                    return json.dumps(result).encode()
                response.__enter__.return_value.read.side_effect = read
            return response

        opener.open.side_effect = opened
        with mock.patch("missing_link.service.PublicGitHub", return_value=source), \
             mock.patch("missing_link.service.extract_structure", return_value=fixtures.repository()["capabilities"]), \
             mock.patch.object(provider, "interpret_capabilities", return_value=fixtures.repository()["capabilities"]), \
             mock.patch("urllib.request.build_opener", return_value=opener), \
             mock.patch("missing_link.provider.validate_shape", side_effect=AssertionError("No post-cancel validation")) as validate, \
             mock.patch.object(provider, "evaluate") as evaluate:
            started = self.service.start({"repo": "example/words", "issue_url": fixtures.issue()["url"], "use_ai": True}, background=False)
        stored = Store(self.path, "alice").get("jobs", started["job_id"])
        self.assertEqual(stored["status"], "paused" if account_change else "cancelled")
        self.assertEqual(stored["ai_calls_used"], 1)
        self.assertGreater(stored["cost_reserved_usd"], 0)
        self.assertEqual(stored["result"]["match_ids"], [])
        self.assertFalse(stored["checkpoint"].get("requests"))
        self.assertFalse(stored["result"].get("non_demands"))
        self.assertFalse(stored["result"].get("candidate_errors"))
        self.assertEqual(opener.open.call_count, 1)
        evaluate.assert_not_called()
        validate.assert_not_called()
        source.fetch_reference_context.assert_not_called()
        return stored, retained["output"], response

    def assert_completed_audit(self, job, output):
        self.assertEqual(len(job["reported_usage"]), 1)
        self.assertEqual(len(job["ai_trace"]), 1)
        self.assertEqual(len(job["checkpoint"]["ai_outputs"]), 1)
        audit = job["checkpoint"]["ai_outputs"][0]
        self.assertEqual(audit["phase"], "request")
        self.assertEqual(audit["output"], redact_payload(output))
        self.assertEqual(audit["attempt_id"], job["ai_trace"][0]["attempt_id"])
        self.assertEqual(audit["call_number"], 1)

    def test_completed_valid_json_survives_cancel_without_becoming_analysis(self):
        for kind, streaming in (("responses", False), ("responses", True), ("chat", False)):
            with self.subTest(kind=kind, streaming=streaming):
                job, output, _ = self.cancelled_response(kind=kind, streaming=streaming)
                self.assert_completed_audit(job, output)

    def test_completed_non_object_json_survives_cancel_and_is_redacted(self):
        for streaming in (False, True):
            for value in ([], None, ["ghp_" + "A" * 36]):
                with self.subTest(streaming=streaming, value_type=type(value).__name__):
                    job, output, _ = self.cancelled_response(streaming=streaming, value=value)
                    self.assert_completed_audit(job, output)
                    self.assertNotIn("ghp_", json.dumps(job))

    def test_completed_shape_invalid_object_survives_cancel_without_candidate_failure(self):
        job, output, _ = self.cancelled_response(value={"requirements": [{}] * 35})
        self.assert_completed_audit(job, output)
        self.assertEqual(len(output["requirements"]), 35)

    def test_cancelled_invalid_output_redacts_colliding_credential_keys_without_loss(self):
        first, second = "ghp_" + "A" * 36, "github_pat_" + "B" * 36
        value = {first: {second: "fixture"}, second: 2, "[REDACTED]": "literal"}
        for streaming in (False, True):
            with self.subTest(streaming=streaming):
                job, output, _ = self.cancelled_response(streaming=streaming, value=value)
                self.assert_completed_audit(job, output)
                saved = job["checkpoint"]["ai_outputs"][0]["output"]
                self.assertEqual(len(saved), len(value))
                self.assertEqual(saved["[REDACTED]"], "literal")
                self.assertNotIn(first, json.dumps(job))
                self.assertNotIn(second, json.dumps(job))

    def test_cancellation_during_partial_stream_does_not_read_or_audit_the_terminal_response(self):
        job, _, response = self.cancelled_response(streaming=True, cancel_at="partial")
        self.assertEqual(response.__enter__.return_value.readline.call_count, 2)
        self.assertFalse(job.get("reported_usage"))
        self.assertFalse(job.get("ai_trace"))
        self.assertFalse(job["checkpoint"].get("ai_outputs"))

    def test_malformed_partial_frame_does_not_override_requested_cancellation(self):
        job, _, response = self.cancelled_response(streaming=True, cancel_at="partial", malformed_partial=True)
        self.assertEqual(response.__enter__.return_value.readline.call_count, 2)
        self.assertFalse(job["checkpoint"].get("ai_outputs"))

    def test_refused_incomplete_and_undecodable_responses_remain_excluded_after_cancel(self):
        for options in ({"refusal": True}, {"terminal_status": "incomplete"}, {"undecodable": True}):
            for streaming in (False, True):
                with self.subTest(options=options, streaming=streaming):
                    job, _, _ = self.cancelled_response(streaming=streaming, **options)
                    self.assertEqual(len(job["ai_trace"]), 1)
                    self.assertEqual(len(job["reported_usage"]), 1)
                    self.assertFalse(job["checkpoint"].get("ai_outputs"))

    def test_account_change_keeps_audit_in_the_original_account_and_stops_processing(self):
        job, output, _ = self.cancelled_response(account_change=True)
        self.assert_completed_audit(job, output)
        self.assertEqual(job["account"], "alice")
        with self.assertRaisesRegex(ValueError, "account changed"):
            self.service.state()
