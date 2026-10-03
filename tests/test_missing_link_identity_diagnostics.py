"""Typed pauses retain original-account history and charges; zero real AI calls."""
import json
import unittest
from unittest import mock

from github_cli import ActiveAccountChangedError, GitHubAccountVerificationError
from missing_link.job_errors import job_failure
from missing_link.provider import Provider
from missing_link.service import Service
import test_missing_link as fixtures


class IdentityDiagnosticTests(unittest.TestCase):
    setUp = fixtures.ServiceTests.setUp
    fake_sources = fixtures.ServiceTests.fake_sources

    def interrupted_fixture(self, *, changed=False, terminal=False):
        provider = Provider({"REPOTRACTION_AI_URL": "http://localhost/v1", "REPOTRACTION_AI_MODEL": "fixture",
            "REPOTRACTION_AI_TOTAL_BUDGET_USD": "2", "REPOTRACTION_AI_BUDGET_ID": "identity-fixture"})
        self.service.provider = provider
        source = self.fake_sources()

        def interrupt(issue, budget):
            budget.reserve_ai(.10, 8, 2)
            if terminal:
                budget.record_usage(1, 2, 0)
                budget.record_call({"phase": "request"})
                budget.record_output("request", {"fixture": "retained completed output"})
            if changed:
                self.account = "bob"
            else:
                self.service.verify = mock.Mock(side_effect=GitHubAccountVerificationError("github_identity_cli_timeout"))
            budget.checkpoint()
            self.fail("Identity failure must stop processing.")

        with mock.patch("missing_link.service.PublicGitHub", return_value=source), \
             mock.patch("missing_link.service.extract_structure", return_value=fixtures.repository()["capabilities"]), \
             mock.patch.object(provider, "interpret_capabilities", return_value=fixtures.repository()["capabilities"]), \
             mock.patch.object(provider, "interpret_request", side_effect=interrupt) as interpret, \
             mock.patch.object(provider, "evaluate") as evaluate, \
             mock.patch.object(provider, "complete", side_effect=AssertionError("No provider HTTP")) as complete:
            started = self.service.start({"repo": "example/words", "issue_url": fixtures.issue()["url"], "use_ai": True}, background=False)
        job = self.service.store.get("jobs", started["job_id"])
        self.assertEqual(job["status"], "paused")
        self.assertEqual(job["account"], "alice")
        self.assertEqual(job["ai_calls_used"], 1)
        self.assertAlmostEqual(job["cost_reserved_usd"], .10)
        self.assertAlmostEqual(self.service.store.ai_reserved("identity-fixture"), .10)
        self.assertEqual(job["result"]["match_ids"], [])
        self.assertFalse(job["checkpoint"].get("requests"))
        self.assertFalse(job["result"].get("candidate_errors"))
        interpret.assert_called_once()
        evaluate.assert_not_called()
        complete.assert_not_called()
        source.fetch_reference_context.assert_not_called()
        self.assertTrue(self.service.lease.acquire())
        self.service.lease.release()
        return job, source, provider

    def recover_verifier(self):
        self.account = "alice"
        self.service.verify = lambda: self.account

    def test_interrupted_call_remains_charged_unknown_and_diagnostic_survives_restart(self):
        job, _, provider = self.interrupted_fixture()
        self.assertEqual(job["error_diagnostic"], {"category": "github_identity",
            "code": "github_identity_cli_timeout", "timeout_seconds": 10})
        self.assertIn("No account change is confirmed", job["error"])
        self.assertFalse(job.get("ai_trace"))
        self.assertFalse(job["checkpoint"].get("ai_outputs"))
        self.recover_verifier()
        restarted = Service(self.path, "alice", self.read, lambda: "alice", provider)
        stored = restarted.store.get("jobs", job["id"])
        self.assertEqual(stored, job)
        public = next(x for x in restarted.state()["jobs"] if x["id"] == job["id"])
        self.assertEqual(public["error_diagnostic"], job["error_diagnostic"])
        self.assertAlmostEqual(restarted.store.ai_reserved("identity-fixture"), .10)
        self.assertFalse(restarted.threads)

    def test_completed_output_is_preserved_without_becoming_accepted_analysis(self):
        job, _, _ = self.interrupted_fixture(terminal=True)
        self.assertEqual(len(job["ai_trace"]), 1)
        self.assertEqual(len(job["reported_usage"]), 1)
        self.assertEqual(job["checkpoint"]["ai_outputs"][0]["output"], {"fixture": "retained completed output"})
        self.assertEqual(job["error_diagnostic"]["code"], "github_identity_cli_timeout")

    def test_actual_account_switch_stays_fail_closed_and_separate_from_timeout(self):
        job, _, _ = self.interrupted_fixture(changed=True)
        self.assertEqual(job["error_diagnostic"]["code"], "github_identity_changed")
        self.assertIn("Switch back", job["error"])
        with self.assertRaises(ActiveAccountChangedError):
            self.service.state()
        self.assertEqual(self.service.store.get("jobs", job["id"]), job)

    def test_explicit_fixture_resume_clears_stale_diagnostic_without_refunding(self):
        job, source, provider = self.interrupted_fixture()
        self.recover_verifier()
        with mock.patch("missing_link.service.PublicGitHub", return_value=source), \
             mock.patch.object(provider, "interpret_request", return_value=fixtures.validate_request(fixtures.request_raw(), fixtures.issue())), \
             mock.patch.object(provider, "evaluate", return_value=[]), \
             mock.patch.object(provider, "complete", side_effect=AssertionError("No provider HTTP")):
            self.service.resume({"job_id": job["id"]}, background=False)
        resumed = self.service.store.get("jobs", job["id"])
        self.assertEqual(resumed["status"], "completed")
        self.assertIsNone(resumed["error"])
        self.assertIsNone(resumed["error_diagnostic"])
        self.assertEqual(resumed["ai_calls_used"], 1)
        self.assertAlmostEqual(self.service.store.ai_reserved("identity-fixture"), .10)

    def test_explicit_fixture_cancellation_clears_old_identity_diagnostic(self):
        job, _, _ = self.interrupted_fixture()
        self.recover_verifier()
        self.service.cancel(job["id"])
        cancelled = self.service.store.get("jobs", job["id"])
        self.assertEqual(cancelled["status"], "cancelled")
        self.assertIsNone(cancelled["error_diagnostic"])

    def test_typed_and_legacy_stops_use_only_safe_diagnostics(self):
        for code in ("github_identity_cli_missing", "github_identity_cli_failed", "github_identity_invalid_response",
                "github_identity_unavailable", "github_identity_ambiguous", "github_identity_cli_error"):
            with self.subTest(code=code):
                result = job_failure(GitHubAccountVerificationError(code))
                self.assertEqual(result["status"], "paused")
                self.assertEqual(result["error_diagnostic"]["code"], code)
        result = job_failure(RuntimeError("account private-fixture"))
        self.assertEqual(result["error_diagnostic"]["code"], "github_identity_unclassified")
        self.assertNotIn("private-fixture", json.dumps(result))
        result = job_failure(ActiveAccountChangedError("private-fixture"))
        self.assertEqual(result["error_diagnostic"]["code"], "github_identity_changed")
        self.assertNotIn("private-fixture", json.dumps(result))
        self.assertEqual(job_failure(RuntimeError("GitHub rate limit"))["status"], "paused")
        self.assertEqual(job_failure(ValueError("Fixture failure"))["status"], "failed")


if __name__ == "__main__":
    unittest.main()
