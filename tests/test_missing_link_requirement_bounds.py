"""Observed request bounds regressions; fixtures only, no paid calls."""
import copy
import json
import unittest
from unittest import mock

from missing_link.analysis import validate_request
from missing_link.contracts import MAX_REQUEST_REQUIREMENTS, schema_for, validate_shape
from missing_link.provider import CandidateValidationError, Provider
from missing_link.store import Store
import test_missing_link as fixtures


def request_with_count(count):
    raw = fixtures.request_raw()
    raw["requirements"] = [copy.deepcopy(raw["requirements"][0]) for _ in range(count)]
    return raw


class RequirementBoundTests(unittest.TestCase):
    def test_import_and_indexed_wire_schemas_share_existing_bound(self):
        for options in ({}, {"source_ids": ["q0"], "citation_ids": ["s1"]}):
            with self.subTest(options=options):
                requirements = schema_for("request", **options)["properties"]["requirements"]
                self.assertEqual(requirements["minItems"], 0)  # Only typed non-demands may use zero locally.
                self.assertEqual(requirements["maxItems"], MAX_REQUEST_REQUIREMENTS)

    def test_local_and_json_mode_accept_one_and_thirty_without_truncation(self):
        for count in (1, 30):
            with self.subTest(count=count):
                raw = request_with_count(count)
                original = copy.deepcopy(raw)
                validate_shape(raw, schema_for("request"))
                request = validate_request(raw, fixtures.issue())
                self.assertEqual(len(request["requirements"]), count)
                self.assertEqual(raw, original)

    def test_underflow_type_and_overflow_have_distinct_diagnostics(self):
        for value, message in (([], "at least one"), ({}, "must be a list"),
                               (request_with_count(31)["requirements"], "maximum 30 (received 31)"),
                               (request_with_count(33)["requirements"], "maximum 30 (received 33)"),
                               (request_with_count(35)["requirements"], "maximum 30 (received 35)")):
            with self.subTest(message=message):
                raw = fixtures.request_raw()
                raw["requirements"] = value
                with self.assertRaises(ValueError) as raised:
                    validate_request(raw, fixtures.issue())
                self.assertIn(message, str(raised.exception))
                if value != []:  # Wire permits zero; semantic status-dependent validation remains strict.
                    with self.assertRaises(ValueError):
                        validate_shape(raw, schema_for("request"))

    def test_provider_prompt_and_payload_state_the_same_bound(self):
        provider = Provider({"REPOTRACTION_AI_URL": "http://localhost/v1", "REPOTRACTION_AI_MODEL": "fixture"})
        with mock.patch.object(provider, "complete", side_effect=fixtures.request_completion()) as complete:
            provider.interpret_request(fixtures.issue(), mock.Mock())
        instruction, data, _, schema, phase = complete.call_args.args
        self.assertIn("between 1 and 30", instruction)
        self.assertIn("Do not silently drop constraints", instruction)
        self.assertEqual(schema, data["schema"])
        self.assertEqual(schema["properties"]["requirements"]["maxItems"], 30)
        self.assertEqual(phase, "request")

    def test_provider_overflow_is_not_retried_or_silently_truncated(self):
        provider = Provider({"REPOTRACTION_AI_URL": "http://localhost/v1", "REPOTRACTION_AI_MODEL": "fixture"})
        for count in (31, 33, 35):
            with self.subTest(count=count):
                raw = request_with_count(count)
                with mock.patch.object(provider, "complete", side_effect=fixtures.request_completion(raw)) as complete:
                    with self.assertRaises(CandidateValidationError) as raised:
                        provider.interpret_request(fixtures.issue(), mock.Mock())
                self.assertIn(f"maximum 30 (received {count})", str(raised.exception))
                self.assertEqual(complete.call_count, 1)
                self.assertEqual(len(raw["requirements"]), count)

    def test_completed_transport_output_is_audited_before_bounds_rejection(self):
        for count in (33, 35):
            with self.subTest(count=count):
                provider = Provider({"REPOTRACTION_AI_URL": "http://localhost/v1", "REPOTRACTION_AI_MODEL": "fixture",
                    "REPOTRACTION_AI_API_KIND": "responses"})
                raw = request_with_count(count)
                result = {"id": "resp_fixture", "status": "completed", "output": [{"type": "message", "content": [
                    {"type": "output_text", "text": json.dumps(raw)}]}], "usage": {"input_tokens": 10, "output_tokens": 20}}
                response = mock.MagicMock()
                response.__enter__.return_value.read.return_value = json.dumps(result).encode()
                opener, budget = mock.Mock(), mock.Mock()
                opener.open.return_value = response
                with mock.patch("urllib.request.build_opener", return_value=opener):
                    with self.assertRaises(CandidateValidationError):
                        provider.complete("Fixture", {}, budget, schema_for("request"), "request")
                budget.record_output.assert_called_once_with("request", raw)
                budget.record_usage.assert_called_once()
                budget.record_call.assert_called_once()
                self.assertEqual(opener.open.call_count, 1)

    def test_completed_non_object_json_is_audited_before_shape_rejection(self):
        for kind in ("responses", "chat"):
            for parsed in ([], ["fixture"], None, True, 0, "fixture"):
                with self.subTest(kind=kind, parsed=parsed):
                    provider = Provider({"REPOTRACTION_AI_URL": "http://localhost/v1", "REPOTRACTION_AI_MODEL": "fixture",
                        "REPOTRACTION_AI_API_KIND": kind})
                    result = {"id": "resp_fixture", "status": "completed", "output": [{"type": "message", "content": [
                        {"type": "output_text", "text": json.dumps(parsed)}]}], "usage": {"input_tokens": 10, "output_tokens": 20}}
                    if kind == "chat":
                        result = {"id": "chat_fixture", "choices": [{"finish_reason": "stop", "message": {"content": json.dumps(parsed)}}],
                            "usage": {"prompt_tokens": 10, "completion_tokens": 20}}
                    response, opener, budget = mock.MagicMock(), mock.Mock(), mock.Mock()
                    response.__enter__.return_value.read.return_value = json.dumps(result).encode()
                    opener.open.return_value = response
                    with mock.patch("urllib.request.build_opener", return_value=opener):
                        with self.assertRaisesRegex(CandidateValidationError, "JSON object"):
                            provider.complete("Fixture", {}, budget, None, "request")
                    budget.record_output.assert_called_once_with("request", parsed)
                    budget.reserve_ai.assert_called_once()
                    budget.record_usage.assert_called_once()
                    budget.record_call.assert_called_once()
                    self.assertEqual(opener.open.call_count, 1)

    def test_incomplete_refused_and_undecodable_json_are_not_completed_output(self):
        results = ({"status": "incomplete"}, {"status": "completed", "output": [{"type": "message",
            "content": [{"type": "refusal", "refusal": "Fixture refusal"}]}]},
            {"status": "completed", "output": [{"type": "message", "content": [{"type": "output_text", "text": "["}]}]})
        for result in results:
            with self.subTest(result=result):
                provider = Provider({"REPOTRACTION_AI_URL": "http://localhost/v1", "REPOTRACTION_AI_MODEL": "fixture",
                    "REPOTRACTION_AI_API_KIND": "responses"})
                response, opener, budget = mock.MagicMock(), mock.Mock(), mock.Mock()
                response.__enter__.return_value.read.return_value = json.dumps(result).encode()
                opener.open.return_value = response
                with mock.patch("urllib.request.build_opener", return_value=opener), self.assertRaises(CandidateValidationError):
                    provider.complete("Fixture", {}, budget, schema_for("request"), "request")
                budget.record_output.assert_not_called()


class RequirementBoundPersistenceTests(unittest.TestCase):
    setUp = fixtures.ServiceTests.setUp
    fake_sources = fixtures.ServiceTests.fake_sources

    def test_completed_non_object_attempt_survives_storage_with_charge_and_redaction(self):
        for parsed in ([], ["ghp_" + "A" * 36]):
            with self.subTest(parsed_type=type(parsed).__name__):
                provider = Provider({"REPOTRACTION_AI_URL": "http://localhost/v1", "REPOTRACTION_AI_MODEL": "fixture",
                    "REPOTRACTION_AI_API_KIND": "responses", "REPOTRACTION_AI_INPUT_USD_PER_MILLION": "1",
                    "REPOTRACTION_AI_OUTPUT_USD_PER_MILLION": "1"})
                self.service.provider = provider
                result = {"id": "resp_fixture", "status": "completed", "output": [{"type": "message", "content": [
                    {"type": "output_text", "text": json.dumps(parsed)}]}], "usage": {"input_tokens": 10, "output_tokens": 20}}
                response, opener = mock.MagicMock(), mock.Mock()
                response.__enter__.return_value.read.return_value = json.dumps(result).encode()
                opener.open.return_value = response
                source = self.fake_sources()
                with mock.patch("missing_link.service.PublicGitHub", return_value=source), \
                     mock.patch("missing_link.service.extract_structure", return_value=fixtures.repository()["capabilities"]), \
                     mock.patch.object(provider, "interpret_capabilities", return_value=fixtures.repository()["capabilities"]), \
                     mock.patch("urllib.request.build_opener", return_value=opener), \
                     mock.patch.object(provider, "evaluate") as evaluate:
                    started = self.service.start({"repo": "example/words", "issue_url": fixtures.issue()["url"], "use_ai": True}, background=False)
                job = Store(self.path, "alice").get("jobs", started["job_id"])
                self.assertEqual(job["status"], "completed")
                self.assertTrue(job["result"]["partial"])
                self.assertEqual(job["result"]["match_ids"], [])
                self.assertEqual(job["checkpoint"]["ai_outputs"][0]["output"], ["[REDACTED]"] if parsed else [])
                self.assertNotIn("ghp_", json.dumps(job))
                self.assertEqual(job["ai_calls_used"], 1)
                self.assertGreater(job["cost_reserved_usd"], 0)
                self.assertEqual(len(job["reported_usage"]), 1)
                self.assertEqual(len(job["ai_trace"]), 1)
                self.assertEqual(opener.open.call_count, 1)
                source.fetch_reference_context.assert_not_called()
                evaluate.assert_not_called()

    def test_charged_overflow_retains_output_and_skips_target_and_comparison(self):
        provider = Provider({"REPOTRACTION_AI_URL": "http://localhost/v1", "REPOTRACTION_AI_MODEL": "fixture"})
        self.service.provider = provider
        raw = request_with_count(35)

        def complete(instruction, data, budget, schema, phase):
            budget.reserve_ai(.10, 8, 2)
            budget.record_call({"phase": phase, "context_coverage": {}})
            output = fixtures.wire_request(data, raw)
            budget.record_output(phase, output)
            return output

        source = self.fake_sources()
        with mock.patch("missing_link.service.PublicGitHub", return_value=source), \
             mock.patch("missing_link.service.extract_structure", return_value=fixtures.repository()["capabilities"]), \
             mock.patch.object(provider, "interpret_capabilities", return_value=fixtures.repository()["capabilities"]), \
             mock.patch.object(provider, "complete", side_effect=complete) as completed, \
             mock.patch.object(provider, "evaluate") as evaluate:
            started = self.service.start({"repo": "example/words", "issue_url": fixtures.issue()["url"], "use_ai": True}, background=False)
        job = self.service.store.get("jobs", started["job_id"])
        self.assertEqual(job["status"], "completed")
        self.assertTrue(job["result"]["partial"])
        self.assertEqual(job["result"]["match_ids"], [])
        self.assertEqual(len(job["checkpoint"]["ai_outputs"][0]["output"]["requirements"]), 35)
        self.assertEqual(job["ai_calls_used"], 1)
        self.assertAlmostEqual(job["cost_reserved_usd"], .10)
        self.assertIn("received 35", job["result"]["candidate_errors"][0]["error"])
        self.assertEqual(completed.call_count, 1)
        source.fetch_reference_context.assert_not_called()
        evaluate.assert_not_called()
