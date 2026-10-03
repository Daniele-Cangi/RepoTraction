"""Persistent identity outages through the real HTTP route; no upstream calls."""
from contextlib import ExitStack
import hashlib
import http.client
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest import mock

import app
from github_cli import ActiveAccountChangedError, GitHubAccountVerificationError, GitHubCLIError
from missing_link.job_errors import job_failure
from missing_link.service import Service


class IdentityPollingTests(unittest.TestCase):
    def setUp(self):
        # TestCase.enterContext is unavailable on supported Python 3.10.
        stack = ExitStack()
        self.addCleanup(stack.close)
        directory = stack.enter_context(tempfile.TemporaryDirectory())
        self.path = Path(directory) / "history.sqlite3"
        self.verify = mock.Mock(return_value="alice")
        self.read = mock.Mock(side_effect=AssertionError("No GitHub acquisition"))
        self.provider = mock.Mock()
        self.provider.describe.return_value = {"configured": False}
        self.service = Service(self.path, "alice", self.read, self.verify, self.provider)
        self.key = ("alice", str(self.path.resolve()))
        self.bindings = {self.key: self.service}
        stack.enter_context(mock.patch.object(app, "ACCOUNT_LOGIN", "alice"))
        stack.enter_context(mock.patch.object(app, "DB_PATH", self.path))
        stack.enter_context(mock.patch.object(app, "verify_active_account", self.verify))
        stack.enter_context(mock.patch.object(app, "_MISSING_LINK_SERVICES", self.bindings))
        self.job_id = "a" * 32
        self.saved = {"id": self.job_id, "account": "alice", "input": {"repo": "private_source_marker"},
            "checkpoint": {"private_source_marker": "retained original evidence"},
            "result": {"candidate_errors": ["private_source_marker"]},
            **job_failure(GitHubAccountVerificationError("github_identity_cli_timeout"))}
        self.saved["error"] = "raw_cli_marker should never escape"
        self.saved["error_diagnostic"]["stderr"] = "raw_cli_marker"
        self.service.store.put("jobs", self.job_id, self.saved)
        self.service.store.reserve_ai_allowance("fixture", self.job_id, .10, 2)
        self.server = app.ThreadingHTTPServer(("127.0.0.1", 0), app.DashboardHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop_server)
        self.origin = f"http://127.0.0.1:{self.server.server_port}"

    def stop_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)

    def request(self, path="/api/missing-link", method="GET", headers=None):
        client = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        try:
            client.request(method, path, body="{}" if method == "POST" else None,
                headers=headers if headers is not None else {"Origin": self.origin, "Content-Type": "application/json"})
            response = client.getresponse()
            raw = response.read()
            return response.status, json.loads(raw) if response.getheader("Content-Type", "").startswith("application/json") else raw
        finally:
            client.close()

    def outage(self, code="github_identity_cli_timeout"):
        self.verify.side_effect = GitHubAccountVerificationError(code)

    def test_persistent_failed_identity_poll_exposes_only_saved_stop_without_writes(self):
        self.outage()
        # Even an abandoned active job must not be reconciled by diagnostic polls.
        active_id = "b" * 32
        self.service.store.put("jobs", active_id, {"id": active_id, "status": "running"})
        before = hashlib.sha256(self.path.read_bytes()).hexdigest()
        with mock.patch.object(self.service, "state", side_effect=AssertionError("No full state")), \
             mock.patch.object(self.service, "_reconcile_abandoned_jobs", side_effect=AssertionError("No reconciliation")), \
             mock.patch.object(self.service.store, "connection", side_effect=AssertionError("No writable Store")), \
             mock.patch("missing_link.service.Service", side_effect=AssertionError("No new service")):
            for _ in range(3):
                status, payload = self.request()
                self.assertEqual(status, 200)
                self.assertEqual(set(payload), {"account", "diagnostic_only", "identity_verified", "actions_available",
                    "identity_error", "identity_diagnostic", "jobs"})
                self.assertTrue(payload["diagnostic_only"])
                self.assertFalse(payload["identity_verified"])
                self.assertFalse(payload["actions_available"])
                self.assertEqual(payload["jobs"], [{"id": self.job_id,
                    **job_failure(GitHubAccountVerificationError("github_identity_cli_timeout"))}])
                serialized = json.dumps(payload)
                self.assertNotIn("private_source_marker", serialized)
                self.assertNotIn("raw_cli_marker", serialized)
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(), before)
        self.assertEqual(self.service.store.get("jobs", self.job_id), self.saved)
        self.assertEqual(self.service.store.get("jobs", active_id)["status"], "running")
        self.assertAlmostEqual(self.service.store.ai_reserved("fixture"), .10)
        self.assertFalse(self.service.threads)
        self.read.assert_not_called()
        self.provider.assert_not_called()
        self.provider.describe.assert_not_called()

    def test_current_poll_error_is_distinct_from_persisted_stop(self):
        for code in ("github_identity_cli_missing", "github_identity_cli_failed", "github_identity_cli_error",
                "github_identity_invalid_response", "github_identity_unavailable"):
            with self.subTest(code=code):
                self.outage(code)
                status, payload = self.request()
                self.assertEqual(status, 200)
                self.assertEqual(payload["identity_diagnostic"]["code"], code)
                self.assertEqual(payload["jobs"][0]["error_diagnostic"]["code"], "github_identity_cli_timeout")

    def test_unbound_or_missing_database_cannot_be_initialized_by_failed_poll(self):
        self.outage()
        self.bindings.clear()
        with mock.patch("missing_link.service.Service") as create:
            self.assertEqual(self.request()[0], 409)
            create.assert_not_called()
        missing = self.path.parent / "missing" / "history.sqlite3"
        self.service.store.path = missing
        with mock.patch.object(app, "DB_PATH", missing):
            self.bindings[("alice", str(missing.resolve()))] = self.service
            self.assertEqual(self.request()[0], 409)
        self.assertFalse(missing.parent.exists())

    def test_database_and_cached_binding_must_belong_to_expected_account(self):
        self.outage()
        for field, value in (("account", "bob"),):
            with mock.patch.object(self.service, field, value):
                self.assertEqual(self.request()[0], 409)
        with mock.patch.object(self.service.store, "account", "bob"):
            self.assertEqual(self.request()[0], 409)
        with mock.patch.object(self.service.store, "path", self.path.parent / "other.sqlite3"):
            self.assertEqual(self.request()[0], 409)
        with self.service.store.connection() as db:
            db.execute("UPDATE ml_identity SET account='bob'")
        self.assertEqual(self.request()[0], 409)

    def test_confirmed_switch_ambiguity_and_unclassified_errors_still_deny_state(self):
        for error in (ActiveAccountChangedError("Confirmed account switch"),
                GitHubAccountVerificationError("github_identity_ambiguous"), GitHubCLIError("Unknown failure")):
            with self.subTest(error=type(error).__name__, code=getattr(error, "code", None)):
                self.verify.side_effect = error
                status, payload = self.request()
                self.assertEqual(status, 409)
                self.assertEqual(set(payload), {"error"})

    def test_exports_context_packages_and_every_mutation_remain_blocked(self):
        self.outage()
        with mock.patch.object(app, "missing_link_service", side_effect=AssertionError("No service access")):
            for endpoint in ("export?match_id=x", "package?match_id=x", "context?job_id=x"):
                self.assertEqual(self.request("/api/missing-link/" + endpoint)[0], 409)
            for endpoint in ("jobs", "cancel", "resume", "capability", "feedback", "analysis", "example"):
                self.assertEqual(self.request("/api/missing-link/" + endpoint, "POST")[0], 409)
            self.assertEqual(self.request("/api/dashboard")[0], 409)

    def test_same_origin_protection_precedes_even_diagnostic_database_reads(self):
        self.outage()
        with mock.patch("missing_link.polling._read_saved_stops", side_effect=AssertionError("No cross-site read")):
            for headers in ({"Host": f"evil.example:{self.server.server_port}"}, {"Origin": "http://evil.example"},
                    {"Sec-Fetch-Site": "cross-site"}):
                self.assertEqual(self.request(headers=headers)[0], 403)
        self.verify.assert_not_called()

    def test_failures_during_accessor_or_state_also_have_read_only_fallback(self):
        failure = GitHubAccountVerificationError("github_identity_cli_timeout")
        with mock.patch.object(app, "missing_link_service", side_effect=failure):
            self.assertTrue(self.request()[1]["diagnostic_only"])
        with mock.patch.object(self.service, "state", side_effect=failure):
            self.assertTrue(self.request()[1]["diagnostic_only"])

    def test_recovery_returns_verified_full_state_without_resuming_saved_job(self):
        self.outage()
        self.assertTrue(self.request()[1]["diagnostic_only"])
        self.verify.side_effect = None
        status, payload = self.request()
        self.assertEqual(status, 200)
        self.assertNotIn("diagnostic_only", payload)
        self.assertIn("provider", payload)
        self.assertEqual(payload["jobs"][0]["status"], "paused")
        self.assertEqual(self.service.store.get("jobs", self.job_id), self.saved)
        self.assertFalse(self.service.threads)
        self.read.assert_not_called()

    def test_malformed_or_untyped_history_is_not_reclassified_or_leaked(self):
        self.outage()
        for index, updates in enumerate(({"error_diagnostic": None}, {"status": "completed"},
                {"error_diagnostic": {"category": "github_identity", "code": "raw_cli_marker"}},
                {"error_diagnostic": {"category": "other", "code": "github_identity_cli_timeout"}}), 1):
            key = f"{index:032x}"
            self.service.store.put("jobs", key, {**self.saved, "id": key, **updates})
        with self.service.store.connection() as db:
            db.execute("INSERT INTO ml_jobs VALUES (?, ?)", ("c" * 32, "invalid json raw_cli_marker"))
        status, payload = self.request()
        self.assertEqual(status, 200)
        self.assertEqual(len(payload["jobs"]), 1)
        self.assertNotIn("raw_cli_marker", json.dumps(payload))


if __name__ == "__main__":
    unittest.main()
