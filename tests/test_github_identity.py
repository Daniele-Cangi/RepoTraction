"""No-network identity diagnostics and cache/compatibility regressions."""
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

import app
from github_cli import (ActiveAccountChangedError, GitHubAccountVerificationError,
    GitHubCLIError, GitHubRateLimitError, verify_cli_account)


def response(entries=None):
    if entries is None:
        entries = [{"login": "ALICE", "active": True, "state": "success"}]
    return subprocess.CompletedProcess([], 0, json.dumps({"hosts": {"github.com": entries}}), "")


class IdentityTests(unittest.TestCase):
    def assert_failure(self, runner, code):
        with self.assertRaises(GitHubAccountVerificationError) as raised:
            verify_cli_account("alice", run=runner)
        self.assertEqual(raised.exception.code, code)
        self.assertEqual(raised.exception.diagnostic()["code"], code)
        self.assertIsInstance(raised.exception, GitHubCLIError)
        self.assertNotIsInstance(raised.exception, ActiveAccountChangedError)
        self.assertNotIn("private-fixture", str(raised.exception))
        self.assertNotIn("private-fixture", json.dumps(raised.exception.diagnostic()))
        runner.assert_called_once()
        return raised.exception

    def test_single_matching_identity_is_case_insensitive_and_one_bounded_read(self):
        runner = mock.Mock(return_value=response())
        self.assertEqual(verify_cli_account("alice", run=runner, creationflags=123), "alice")
        runner.assert_called_once_with(["gh", "auth", "status", "--json", "hosts"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10,
            check=False, creationflags=123)

    def test_missing_timeout_and_os_failures_are_distinct_and_never_echo_output(self):
        failures = [(FileNotFoundError("private-fixture"), "github_identity_cli_missing"),
            (subprocess.TimeoutExpired("gh", 10, output="private-fixture", stderr="private-fixture"), "github_identity_cli_timeout"),
            (PermissionError("private-fixture"), "github_identity_cli_error")]
        for error, code in failures:
            with self.subTest(code=code):
                exc = self.assert_failure(mock.Mock(side_effect=error), code)
                if code.endswith("timeout"):
                    self.assertEqual(exc.diagnostic()["timeout_seconds"], 10)

    def test_cli_nonzero_exit_does_not_claim_a_token_expired_or_an_account_switch(self):
        result = subprocess.CompletedProcess([], 1, "private-fixture", "private-fixture")
        error = self.assert_failure(mock.Mock(return_value=result), "github_identity_cli_failed")
        self.assertIn("No account change is confirmed", str(error))

    def test_malformed_json_and_identity_shapes_fail_closed(self):
        values = ["private-fixture", "null", "[]", "{}", '{"hosts":[]}',
            '{"hosts":{"github.com":{}}}', '{"hosts":{"github.com":[null]}}',
            json.dumps({"hosts": {"github.com": [{"active": "yes", "state": "success", "login": "alice"}]}}),
            json.dumps({"hosts": {"github.com": [{"active": True, "state": "success", "login": None}]}}),
            json.dumps({"hosts": {"github.com": [{"active": True, "state": "success", "login": "../private-fixture"}]}})]
        for stdout in values:
            with self.subTest(stdout=stdout):
                result = subprocess.CompletedProcess([], 0, stdout, "private-fixture")
                self.assert_failure(mock.Mock(return_value=result), "github_identity_invalid_response")

    def test_no_verified_active_identity_is_unavailable_not_changed(self):
        for entries in ([], [{"active": False, "state": "success", "login": "bob"}],
                [{"active": True, "state": "error", "login": "alice"}]):
            with self.subTest(entries=entries):
                self.assert_failure(mock.Mock(return_value=response(entries)), "github_identity_unavailable")

    def test_multiple_verified_active_identities_are_ambiguous_not_changed(self):
        entries = [{"active": True, "state": "success", "login": login} for login in ("alice", "bob")]
        self.assert_failure(mock.Mock(return_value=response(entries)), "github_identity_ambiguous")

    def test_only_one_verified_different_identity_is_a_confirmed_switch(self):
        runner = mock.Mock(return_value=response([{"active": True, "state": "success", "login": "bob"}]))
        with self.assertRaises(ActiveAccountChangedError) as raised:
            verify_cli_account("alice", run=runner)
        self.assertIsInstance(raised.exception, GitHubCLIError)
        self.assertNotIsInstance(raised.exception, ValueError)
        runner.assert_called_once()

    def test_app_keeps_existing_exception_aliases(self):
        self.assertIs(app.GitHubCLIError, GitHubCLIError)
        self.assertIs(app.ActiveAccountChangedError, ActiveAccountChangedError)
        self.assertIs(app.GitHubRateLimitError, GitHubRateLimitError)

    def test_failed_check_never_advances_success_cache_or_bypasses_force(self):
        with mock.patch.object(app, "ACCOUNT_LOGIN", "alice"), \
             mock.patch.object(app, "_ACCOUNT_CHECKED_AT", 100), \
             mock.patch.object(app.time, "monotonic", return_value=102), \
             mock.patch.object(app.subprocess, "run", side_effect=subprocess.TimeoutExpired("gh", 10)) as runner:
            self.assertEqual(app.verify_active_account(), "alice")
            runner.assert_not_called()
            with self.assertRaises(GitHubAccountVerificationError):
                app.verify_active_account(force=True)
            self.assertEqual(app._ACCOUNT_CHECKED_AT, 100)
            with mock.patch.object(app.time, "monotonic", return_value=110):
                with self.assertRaises(GitHubAccountVerificationError):
                    app.verify_active_account()
            self.assertEqual(app._ACCOUNT_CHECKED_AT, 100)
            self.assertEqual(runner.call_count, 2)

    def test_app_only_caches_a_successful_check(self):
        with mock.patch.object(app, "ACCOUNT_LOGIN", "alice"), \
             mock.patch.object(app, "_ACCOUNT_CHECKED_AT", 0), \
             mock.patch.object(app.time, "monotonic", return_value=110), \
             mock.patch.object(app.subprocess, "run", return_value=response()) as runner:
            self.assertEqual(app.verify_active_account(), "alice")
            self.assertEqual(app._ACCOUNT_CHECKED_AT, 110)
            self.assertEqual(app.verify_active_account(), "alice")
            runner.assert_called_once()

    def test_fresh_module_import_has_no_network_disk_account_or_provider_work(self):
        code = '''
import subprocess, sqlite3, threading, urllib.request
from pathlib import Path
from unittest import mock
import sys
with mock.patch.object(subprocess, 'run', side_effect=AssertionError('CLI')), \\
     mock.patch.object(sqlite3, 'connect', side_effect=AssertionError('DB')), \\
     mock.patch.object(Path, 'mkdir', side_effect=AssertionError('directory')), \\
     mock.patch.object(threading.Thread, 'start', side_effect=AssertionError('thread')), \\
     mock.patch.object(urllib.request, 'build_opener', side_effect=AssertionError('network')):
    import github_cli
    assert 'app' not in sys.modules and 'missing_link.provider' not in sys.modules
'''
        result = subprocess.run([sys.executable, "-c", code],
            cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
