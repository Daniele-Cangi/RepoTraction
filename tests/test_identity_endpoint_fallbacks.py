"""Identity failures are global stops, not endpoint defaults; no upstream calls."""
from contextlib import contextmanager
import unittest
from unittest import mock

import app
from github_cli import GitHubAccountVerificationError, GitHubCLIError
import test_storage_registry as fixtures


CODES = (
    "github_identity_cli_missing", "github_identity_cli_timeout",
    "github_identity_cli_error", "github_identity_cli_failed",
    "github_identity_invalid_response", "github_identity_unavailable",
    "github_identity_ambiguous",
)
REPO = "octocat/project"


@contextmanager
def owned_registry():
    case = fixtures.RegistryCharacterizationTests("test_case_only_merge_does_not_access_connection")
    case.setUp()
    try:
        yield case
    finally:
        case.doCleanups()


def traffic_reply(endpoint):
    metric = endpoint.rsplit("/", 1)[-1]
    if metric in {"views", "clones"}:
        return {"count": 3, "uniques": 2, metric: [
            {"timestamp": "2026-08-20T00:00:00Z", "count": 3, "uniques": 2}]}
    return []


class IdentityEndpointFallbackTests(unittest.TestCase):
    def setUp(self):
        cache_patch = mock.patch.object(app, "CACHE", app.MemoryCache())
        cache_patch.start()
        self.addCleanup(cache_patch.stop)
        verify_patch = mock.patch.object(app, "verify_active_account", return_value="octocat")
        self.verify = verify_patch.start()
        self.addCleanup(verify_patch.stop)

    def test_registry_identity_failure_never_creates_inactive_alias_or_changes_history(self):
        for code in CODES:
            with self.subTest(code=code), owned_registry() as case:
                case.seed()
                history = {table: case.rows(table) for table in fixtures.HISTORY_TABLES}
                failure = GitHubAccountVerificationError(code)
                with mock.patch.object(app, "run_gh_json", side_effect=failure):
                    with self.assertRaises(GitHubAccountVerificationError) as raised:
                        app.reconcile_repository_registry([], fixtures.LATE)
                self.assertIs(raised.exception, failure)
                self.assertEqual(case.rows("repository_aliases"), [])
                self.assertEqual({table: case.rows(table) for table in fixtures.HISTORY_TABLES}, history)
                # Recovery may resolve the original name; the failed identity
                # check must not leave an alias that suppresses this lookup.
                with mock.patch.object(app, "run_gh_json", return_value={"id": 1, "full_name": fixtures.NEW}) as recovered:
                    app.reconcile_repository_registry([{"id": 1, "full_name": fixtures.NEW}], fixtures.LATE)
                recovered.assert_called_once_with(f"repos/{fixtures.OLD}")
                self.assertEqual(case.rows("repository_aliases"), [(fixtures.OLD, 1, fixtures.NEW, "renamed", fixtures.LATE)])
                self.assertEqual(case.rows("traffic_daily")[0][0], fixtures.NEW)

    def test_registry_retains_prior_successful_commit_but_stops_before_failed_alias(self):
        for code in CODES:
            with self.subTest(code=code), owned_registry() as case:
                case.seed("octocat/a")
                case.seed("octocat/b")
                case.seed("octocat/c")
                failure = GitHubAccountVerificationError(code)

                def resolve(endpoint):
                    if endpoint == "repos/octocat/b":
                        raise failure
                    return {}

                with mock.patch.object(app, "run_gh_json", side_effect=resolve) as reader:
                    with self.assertRaises(GitHubAccountVerificationError):
                        app.reconcile_repository_registry([], fixtures.LATE)
                self.assertEqual(reader.call_args_list, [mock.call("repos/octocat/a"), mock.call("repos/octocat/b")])
                self.assertEqual([row[0] for row in case.rows("repository_aliases")], ["octocat/a"])

    def test_safe_traffic_call_propagates_identity_failure_instead_of_default(self):
        for code in CODES:
            with self.subTest(code=code):
                failure = GitHubAccountVerificationError(code)
                with mock.patch.object(app, "run_gh_json", side_effect=failure):
                    with self.assertRaises(GitHubAccountVerificationError) as raised:
                        app._safe_traffic_call(f"repos/{REPO}/traffic/views", {"fallback": True})
                self.assertIs(raised.exception, failure)

    def test_parallel_traffic_identity_failure_cannot_persist_or_cache_partial_payload(self):
        for code in CODES:
            for failed_endpoint in ("views", "clones", "referrers", "paths"):
                with self.subTest(code=code, endpoint=failed_endpoint):
                    failure = GitHubAccountVerificationError(code)

                    def read(endpoint):
                        if endpoint.rsplit("/", 1)[-1] == failed_endpoint:
                            raise failure
                        return traffic_reply(endpoint)

                    with mock.patch.object(app, "run_gh_json", side_effect=read), \
                         mock.patch.object(app, "save_traffic") as save, \
                         mock.patch.object(app, "get_traffic_history", return_value=[]) as history, \
                         mock.patch.object(app.CACHE, "set") as cache:
                        with self.assertRaises(GitHubAccountVerificationError) as raised:
                            app.build_traffic(REPO, force=True)
                        self.assertIs(raised.exception, failure)
                        save.assert_not_called()
                        history.assert_not_called()
                        cache.assert_not_called()
                        self.verify.assert_not_called()

    def test_all_failed_traffic_endpoints_preserve_the_typed_identity_diagnostic(self):
        for code in CODES:
            with self.subTest(code=code):
                failure = GitHubAccountVerificationError(code)
                with mock.patch.object(app, "run_gh_json", side_effect=failure), \
                     mock.patch.object(app, "save_traffic") as save:
                    with self.assertRaises(GitHubAccountVerificationError) as raised:
                        app.build_traffic(REPO, force=True)
                    self.assertIs(raised.exception, failure)
                    save.assert_not_called()

    def test_event_identity_failure_cannot_become_empty_or_partial_success(self):
        release = [{"published_at": fixtures.EARLY, "tag_name": "v1", "html_url": "https://github.com/octocat/project/releases/tag/v1"}]
        readme = [{"sha": "a" * 40, "commit": {"author": {"date": fixtures.EARLY}, "message": "README"}}]
        for code in CODES:
            for failed_endpoint in ("releases", "commits"):
                with self.subTest(code=code, endpoint=failed_endpoint), owned_registry() as case:
                    case.seed()
                    history = {table: case.rows(table) for table in fixtures.HISTORY_TABLES}
                    failure = GitHubAccountVerificationError(code)

                    def read(endpoint, **_kwargs):
                        if endpoint.endswith("/" + failed_endpoint):
                            raise failure
                        return release if endpoint.endswith("/releases") else readme

                    with mock.patch.object(app, "run_gh_json", side_effect=read), \
                         mock.patch.object(app, "_record_repository_event") as record:
                        with self.assertRaises(GitHubAccountVerificationError) as raised:
                            app.collect_repository_events(REPO)
                        self.assertIs(raised.exception, failure)
                        record.assert_not_called()
                        self.verify.assert_not_called()
                    self.assertEqual({table: case.rows(table) for table in fixtures.HISTORY_TABLES}, history)

    def test_collector_stops_at_identity_failure_without_counting_repo_or_continuing(self):
        names = ["octocat/first", "octocat/second", "octocat/third"]
        dashboard = {"repositories": [{"full_name": name, "archived": False} for name in names]}
        for code in CODES:
            for stage in ("traffic", "events"):
                for fail_index in (0, 1):
                    with self.subTest(code=code, stage=stage, index=fail_index), owned_registry() as case:
                        case.seed()
                        history = {table: case.rows(table) for table in fixtures.HISTORY_TABLES}
                        failure = GitHubAccountVerificationError(code)

                        def traffic(repo, **_kwargs):
                            if stage == "traffic" and repo == names[fail_index]:
                                raise failure
                            return {"partial_errors": []}

                        def events(repo):
                            if stage == "events" and repo == names[fail_index]:
                                raise failure
                            return {"errors": []}

                        with mock.patch.dict(app.COLLECTION_STATE, {"running": False}, clear=True), \
                             mock.patch.object(app, "build_dashboard", return_value=dashboard), \
                             mock.patch.object(app, "build_traffic", side_effect=traffic) as collect_traffic, \
                             mock.patch.object(app, "collect_repository_events", side_effect=events) as collect_events:
                            result = app.collect_all_data()
                        self.assertEqual(result["last_status"], "failed")
                        self.assertFalse(result["running"])
                        self.assertEqual(result["repos_completed"], fail_index)
                        self.assertEqual(result["errors"], [str(failure)])
                        self.assertEqual(collect_traffic.call_count, fail_index + 1)
                        self.assertEqual(collect_events.call_count, fail_index + (stage == "events"))
                        self.assertEqual({table: case.rows(table) for table in fixtures.HISTORY_TABLES}, history)
                        self.assertEqual(case.rows("collection_runs")[0][-1], "failed")

    def test_identity_guard_stops_api_before_subprocess_endpoint_request(self):
        for code in CODES:
            with self.subTest(code=code):
                failure = GitHubAccountVerificationError(code)
                with mock.patch.object(app, "verify_active_account", side_effect=failure), \
                     mock.patch.object(app.subprocess, "run") as runner:
                    with self.assertRaises(GitHubAccountVerificationError) as raised:
                        app.run_gh_json(f"repos/{REPO}/traffic/views")
                    self.assertIs(raised.exception, failure)
                    runner.assert_not_called()

    def test_ordinary_endpoint_failures_keep_existing_defaults_and_partial_results(self):
        failure = GitHubCLIError("fixture endpoint permission denied")
        default = {"fallback": True}
        with mock.patch.object(app, "run_gh_json", side_effect=failure):
            self.assertIs(app._safe_traffic_call(f"repos/{REPO}/traffic/views", default), default)
        with owned_registry() as case:
            case.seed()

            def read(endpoint):
                if endpoint.endswith("/clones"):
                    raise failure
                return traffic_reply(endpoint)

            with mock.patch.object(app, "run_gh_json", side_effect=read):
                payload = app.build_traffic(REPO, force=True)
            self.assertTrue(payload["views"]["available"])
            self.assertFalse(payload["clones"]["available"])
            self.assertEqual(payload["partial_errors"], ["clones: fixture endpoint permission denied"])
            self.assertIs(app.CACHE.get(f"traffic:{REPO}", 300), payload)
            self.assertEqual(case.rows("traffic_daily")[0][0], fixtures.OLD)

            def events(endpoint, **_kwargs):
                if endpoint.endswith("/releases"):
                    raise failure
                return [{"sha": "a" * 40, "commit": {"author": {"date": fixtures.EARLY}, "message": "README"}}]

            with mock.patch.object(app, "run_gh_json", side_effect=events):
                event_result = app.collect_repository_events(REPO)
            self.assertEqual(event_result, {"repo": REPO, "created": 1,
                "errors": ["releases: fixture endpoint permission denied"]})


if __name__ == "__main__":
    unittest.main()
