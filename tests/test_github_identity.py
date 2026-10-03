"""No-network identity diagnostics and cache/compatibility regressions."""
import json
import subprocess
import sys
import threading
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

    def test_failed_forced_check_invalidates_success_cache_for_the_next_normal_check(self):
        with mock.patch.object(app, "ACCOUNT_LOGIN", "alice"), \
             mock.patch.object(app, "_ACCOUNT_CHECKED_AT", 100), \
             mock.patch.object(app.time, "monotonic", return_value=102), \
             mock.patch.object(app.subprocess, "run", side_effect=subprocess.TimeoutExpired("gh", 10)) as runner:
            self.assertEqual(app.verify_active_account(), "alice")
            runner.assert_not_called()
            with self.assertRaises(GitHubAccountVerificationError):
                app.verify_active_account(force=True)
            self.assertEqual(app._ACCOUNT_CHECKED_AT, float("-inf"))
            with self.assertRaises(GitHubAccountVerificationError):
                app.verify_active_account()
            self.assertEqual(app._ACCOUNT_CHECKED_AT, float("-inf"))
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

    def test_slow_success_has_a_full_cache_interval_from_completion(self):
        with mock.patch.object(app, "ACCOUNT_LOGIN", "alice"), \
             mock.patch.object(app, "_ACCOUNT_CHECKED_AT", 0), \
             mock.patch.object(app.time, "monotonic", return_value=100) as clock:
            def slow_success(*args, **kwargs):
                clock.return_value += 6
                return response()
            with mock.patch.object(app.subprocess, "run", side_effect=slow_success) as runner:
                self.assertEqual(app.verify_active_account(), "alice")
                self.assertEqual(app._ACCOUNT_CHECKED_AT, 106)
                self.assertEqual(app.verify_active_account(), "alice")
                clock.return_value = 110.99
                self.assertEqual(app.verify_active_account(), "alice")
                runner.assert_called_once()
                clock.return_value = 111
                self.assertEqual(app.verify_active_account(), "alice")
                self.assertEqual(runner.call_count, 2)
                self.assertEqual(app._ACCOUNT_CHECKED_AT, 117)

    def test_forced_timeout_after_slow_success_invalidates_fresh_timestamp(self):
        with mock.patch.object(app, "ACCOUNT_LOGIN", "alice"), \
             mock.patch.object(app, "_ACCOUNT_CHECKED_AT", 0), \
             mock.patch.object(app.time, "monotonic", side_effect=[100, 106, 106, 106]), \
             mock.patch.object(app.subprocess, "run", side_effect=[response(), subprocess.TimeoutExpired("gh", 10),
                 subprocess.TimeoutExpired("gh", 10)]) as runner:
            self.assertEqual(app.verify_active_account(), "alice")
            with self.assertRaises(GitHubAccountVerificationError):
                app.verify_active_account(force=True)
            self.assertEqual(app._ACCOUNT_CHECKED_AT, float("-inf"))
            with self.assertRaises(GitHubAccountVerificationError):
                app.verify_active_account()
            self.assertEqual(runner.call_count, 3)

    def test_every_failed_forced_verification_requires_a_new_success_before_caching(self):
        changed = response([{"active": True, "state": "success", "login": "bob"}])
        ambiguous = response([{"active": True, "state": "success", "login": name} for name in ("alice", "bob")])
        failures = [subprocess.TimeoutExpired("gh", 10), changed, ambiguous, response([]),
            subprocess.CompletedProcess([], 0, "not JSON", ""),
            subprocess.CompletedProcess([], 1, "", "private-fixture"),
            PermissionError("private-fixture"), FileNotFoundError("private-fixture")]
        for failure in failures:
            with self.subTest(failure=type(failure).__name__), \
                 mock.patch.object(app, "ACCOUNT_LOGIN", "alice"), \
                 mock.patch.object(app, "_ACCOUNT_CHECKED_AT", 100), \
                 mock.patch.object(app.time, "monotonic", return_value=102), \
                 mock.patch.object(app.subprocess, "run", side_effect=[failure, failure, response()]) as runner:
                for forced in (True, False):
                    with self.assertRaises(GitHubCLIError):
                        app.verify_active_account(force=forced)
                    self.assertEqual(app._ACCOUNT_CHECKED_AT, float("-inf"))
                    self.assertEqual(app.ACCOUNT_LOGIN, "alice")
                self.assertEqual(app.verify_active_account(), "alice")
                self.assertEqual(app._ACCOUNT_CHECKED_AT, 102)
                self.assertEqual(app.verify_active_account(), "alice")
                self.assertEqual(runner.call_count, 3)

    def test_invalidated_cache_cannot_look_fresh_near_monotonic_clock_origin(self):
        with mock.patch.object(app, "ACCOUNT_LOGIN", "alice"), \
             mock.patch.object(app, "_ACCOUNT_CHECKED_AT", 0.1), \
             mock.patch.object(app.time, "monotonic", return_value=0.2), \
             mock.patch.object(app.subprocess, "run", side_effect=subprocess.TimeoutExpired("gh", 10)) as runner:
            with self.assertRaises(GitHubAccountVerificationError):
                app.verify_active_account(force=True)
            with self.assertRaises(GitHubAccountVerificationError):
                app.verify_active_account()
            self.assertEqual(runner.call_count, 2)

    def test_waiting_normal_check_cannot_reuse_success_after_forced_failure(self):
        started, release, following = threading.Event(), threading.Event(), threading.Event()
        errors = []
        def verify(forced):
            if not forced:
                following.set()
            try:
                app.verify_active_account(force=forced)
            except GitHubAccountVerificationError:
                errors.append(forced)
        def failed_cli(*args, **kwargs):
            started.set()
            if not release.wait(5):
                raise AssertionError("Fixture did not release the verification.")
            raise subprocess.TimeoutExpired("gh", 10)
        with mock.patch.object(app, "ACCOUNT_LOGIN", "alice"), \
             mock.patch.object(app, "_ACCOUNT_CHECKED_AT", 100), \
             mock.patch.object(app.time, "monotonic", return_value=102), \
             mock.patch.object(app.subprocess, "run", side_effect=failed_cli) as runner:
            first, second = threading.Thread(target=verify, args=(True,)), threading.Thread(target=verify, args=(False,))
            first.start()
            try:
                self.assertTrue(started.wait(5))
                second.start()
                self.assertTrue(following.wait(5))
            finally:
                release.set()
                first.join(5)
                if second.ident is not None:
                    second.join(5)
            self.assertFalse(first.is_alive())
            self.assertFalse(second.is_alive())
            self.assertCountEqual(errors, [True, False])
            self.assertEqual(runner.call_count, 2)
            self.assertEqual(app._ACCOUNT_CHECKED_AT, float("-inf"))

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
