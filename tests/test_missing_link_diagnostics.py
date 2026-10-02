"""Invalid quotes remain rejected, auditable and charged; no real provider calls."""
import copy
import hashlib
import json
import unittest
from unittest import mock

from missing_link.analysis import validate_matches
from missing_link.provider import CandidateValidationError, Provider
import test_missing_link as fixtures


class QuoteDiagnosticTests(unittest.TestCase):
    def test_an_added_backtick_is_rejected_with_safe_machine_diagnostics(self):
        raw = fixtures.request_raw()
        raw["requirements"][0]["quote"] = "`" + raw["requirements"][0]["quote"]
        provider = Provider({"REPOTRACTION_AI_URL": "http://localhost/v1", "REPOTRACTION_AI_MODEL": "fixture"})
        with mock.patch.object(provider, "complete", side_effect=fixtures.request_completion(raw)) as complete:
            with self.assertRaises(CandidateValidationError) as raised:
                provider.interpret_request(fixtures.issue(), mock.Mock())
        diagnostic = raised.exception.diagnostics
        self.assertEqual(diagnostic["kind"], "unavailable_demand_span")
        self.assertEqual(diagnostic["requirement_id"], "r0")
        self.assertEqual(diagnostic["citation_sha256"], hashlib.sha256(("unavailable:" + raw["requirements"][0]["quote"]).encode()).hexdigest())
        self.assertNotIn(raw["requirements"][0]["quote"], json.dumps(diagnostic))
        self.assertEqual(complete.call_count, 1)
        self.assertTrue(raw["requirements"][0]["quote"].startswith("`"))

    def test_unavailable_reference_is_not_echoed_in_diagnostics(self):
        raw = fixtures.request_raw()
        raw["requirements"][0]["source_id"] = "untrusted-private-label"
        provider = Provider({"REPOTRACTION_AI_URL": "http://localhost/v1", "REPOTRACTION_AI_MODEL": "fixture"})
        with mock.patch.object(provider, "complete", side_effect=fixtures.request_completion(raw)):
            with self.assertRaises(CandidateValidationError) as raised:
                provider.interpret_request(fixtures.issue(), mock.Mock())
        self.assertEqual(raised.exception.diagnostics["kind"], "unavailable_demand_span")
        self.assertNotIn("untrusted-private-label", str(raised.exception.diagnostics))


class DiagnosticPersistenceTests(unittest.TestCase):
    setUp = fixtures.ServiceTests.setUp
    fake_sources = fixtures.ServiceTests.fake_sources

    def test_failure_links_saved_attempt_without_accepting_analysis_refund_or_retry(self):
        provider = Provider({"REPOTRACTION_AI_URL": "http://localhost/v1", "REPOTRACTION_AI_MODEL": "fixture"})
        self.service.provider = provider
        raw = fixtures.request_raw()
        # A credential-shaped source string is redacted by persistence; neither
        # that string nor the raw quote is copied into public job diagnostics.
        quote = "`private ghp_" + "A" * 36
        raw["requirements"][0]["quote"] = quote
        def saved_attempt(instruction, data, budget, schema, phase):
            budget.reserve_ai(.10, 8, 2)
            budget.record_call({"phase": phase, "context_coverage": {}})
            output = fixtures.wire_request(data, raw)
            budget.record_output(phase, copy.deepcopy(output))
            return copy.deepcopy(output)
        source = self.fake_sources()
        with mock.patch("missing_link.service.PublicGitHub", return_value=source), \
             mock.patch("missing_link.service.extract_structure", return_value=fixtures.repository()["capabilities"]), \
             mock.patch.object(provider, "interpret_capabilities", return_value=fixtures.repository()["capabilities"]), \
             mock.patch.object(provider, "complete", side_effect=saved_attempt) as complete, \
             mock.patch.object(provider, "evaluate") as evaluate:
            started = self.service.start({"repo": "example/words", "issue_url": fixtures.issue()["url"], "use_ai": True}, background=False)
        job = self.service.store.get("jobs", started["job_id"])
        self.assertEqual(job["status"], "completed")
        self.assertTrue(job["result"]["partial"])
        self.assertEqual(job["result"]["match_ids"], [])
        failure = job["result"]["candidate_errors"][0]
        attempt = job["checkpoint"]["ai_outputs"][0]
        self.assertEqual(failure["attempt_id"], attempt["attempt_id"])
        self.assertEqual(job["ai_trace"][0]["attempt_id"], attempt["attempt_id"])
        self.assertEqual(failure["call_number"], 1)
        self.assertEqual(failure["validation_diagnostics"]["citation_characters"], len("unavailable:" + quote))
        self.assertAlmostEqual(job["cost_reserved_usd"], .10)
        self.assertEqual(job["ai_calls_used"], 1)
        self.assertIn("[REDACTED]", attempt["output"]["requirements"][0]["citation_id"])
        self.assertNotIn("ghp_", json.dumps(job))
        public = next(item for item in self.service.state()["jobs"] if item["id"] == job["id"])
        self.assertNotIn("checkpoint", public)
        self.assertNotIn(quote, json.dumps(public))
        self.assertEqual(complete.call_count, 1)
        evaluate.assert_not_called()
