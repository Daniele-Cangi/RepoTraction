"""Characterize repository snapshots and event writes with owned test history."""
import copy
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest import mock

import app


REPO = "octocat/project"
EARLY = "2026-08-20T10:00:00Z"
LATE = "2026-08-21T10:00:00Z"


class RepositorySnapshotCharacterizationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.path = self.root / "snapshots.sqlite3"
        for name, value in (("DB_PATH", self.path), ("DATA_DIR", self.root)):
            patch = mock.patch.object(app, name, value)
            patch.start()
            self.addCleanup(patch.stop)
        app.ensure_database()

    def rows(self, table):
        with closing(sqlite3.connect(self.path)) as connection:
            return connection.execute(f"SELECT * FROM {table} ORDER BY 1, 2").fetchall()

    def metadata(self, **overrides):
        return {"full_name": REPO, **overrides}

    def event(self, **overrides):
        return {"repo": REPO, "event_type": "release", "title": "v1", "occurred_at": EARLY,
                "source": "github_release", **overrides}

    def test_counter_snapshot_defaults_and_supplied_timestamp(self):
        self.assertIsNone(app.save_repo_snapshots([{"full_name": REPO}], EARLY))
        self.assertEqual(self.rows("repo_snapshots"), [(REPO, EARLY, 0, 0, 0, 0, 0, 0, "", "")])

    def test_counter_conversions_retain_existing_truthiness_and_int_rules(self):
        app.save_repo_snapshots([{"full_name": REPO, "stars": "7", "forks": -2, "watchers": 3.9,
                                 "open_issues": True, "private": "false", "archived": [],
                                 "language": None, "pushed_at": "custom timestamp"}], EARLY)
        self.assertEqual(self.rows("repo_snapshots"), [(REPO, EARLY, 7, -2, 3, 1, 1, 0, "", "custom timestamp")])

    def test_counter_duplicate_key_uses_last_input_but_preserves_other_timestamps(self):
        app.save_repo_snapshots([{"full_name": REPO, "stars": 1}], EARLY)
        app.save_repo_snapshots([{"full_name": REPO, "stars": 2}, {"full_name": REPO, "stars": 3}], LATE)
        self.assertEqual([row[:3] for row in self.rows("repo_snapshots")], [(REPO, EARLY, 1), (REPO, LATE, 3)])

    def test_counter_storage_does_not_add_name_validation_or_case_normalization(self):
        app.save_repo_snapshots([{"full_name": "invalid display name"}, {"full_name": "Octocat/Project"},
                                 {"full_name": REPO}], EARLY)
        self.assertEqual(len(self.rows("repo_snapshots")), 3)

    def test_counter_batch_failure_rolls_back_earlier_replacements(self):
        app.save_repo_snapshots([{"full_name": REPO, "stars": 1}], EARLY)
        before = self.rows("repo_snapshots")
        for invalid in ({"full_name": REPO, "stars": None}, {"stars": 2},
                        {"full_name": REPO, "forks": "invalid"}):
            with self.subTest(invalid=invalid):
                with self.assertRaises((ValueError, TypeError, KeyError)):
                    app.save_repo_snapshots([{"full_name": REPO, "stars": 5}, invalid], EARLY)
                self.assertEqual(self.rows("repo_snapshots"), before)

    def test_empty_batches_still_use_patchable_database_factory(self):
        with mock.patch.object(app, "database_connection", wraps=app.database_connection) as factory:
            self.assertIsNone(app.save_repo_snapshots([], EARLY))
            self.assertEqual(app.save_repo_metadata_snapshots([], EARLY), 0)
        self.assertEqual(factory.call_count, 2)

    def test_initial_metadata_normalizes_fields_and_does_not_create_event(self):
        created = app.save_repo_metadata_snapshots([self.metadata(description=123, homepage=False,
                    topics=["z", 4, "é", "z"], license=None, license_status="")], EARLY)
        self.assertEqual(created, 0)
        self.assertEqual(self.rows("repo_metadata_snapshots"),
                         [(REPO, EARLY, "123", "", '["4","z","z","\\u00e9"]', "", "missing")])
        self.assertEqual(self.rows("repository_events"), [])

    def test_metadata_change_event_records_all_fields_in_existing_order(self):
        app.save_repo_metadata_snapshots([self.metadata()], EARLY)
        changed = self.metadata(description="new", homepage="https://example.test", topics=["python"],
                                license="MIT", license_status="recognized")
        self.assertEqual(app.save_repo_metadata_snapshots([changed], LATE), 1)
        row = self.rows("repository_events")[0]
        self.assertEqual(row[1:7], (REPO, "metadata", "Repository metadata updated", LATE, LATE, "repository_snapshot"))
        self.assertEqual(row[7], '{"changed_fields":["description","homepage","topics_json","license_id","license_status"]}')

    def test_topics_reordering_does_not_create_event(self):
        app.save_repo_metadata_snapshots([self.metadata(topics=["z", "a", "z"])], EARLY)
        self.assertEqual(app.save_repo_metadata_snapshots([self.metadata(topics=["z", "z", "a"])], LATE), 0)
        self.assertEqual(self.rows("repository_events"), [])

    def test_metadata_compares_latest_stored_snapshot_even_for_older_incoming_time(self):
        app.save_repo_metadata_snapshots([self.metadata(description="first")], EARLY)
        app.save_repo_metadata_snapshots([self.metadata(description="latest")], LATE)
        older = "2026-08-19T10:00:00Z"
        self.assertEqual(app.save_repo_metadata_snapshots([self.metadata(description="latest")], older), 0)
        self.assertEqual(len(self.rows("repo_metadata_snapshots")), 3)
        self.assertEqual(len(self.rows("repository_events")), 1)

    def test_metadata_same_timestamp_replaces_snapshot_but_deduplicates_event_identity(self):
        app.save_repo_metadata_snapshots([self.metadata()], EARLY)
        self.assertEqual(app.save_repo_metadata_snapshots([self.metadata(description="changed")], LATE), 1)
        self.assertEqual(app.save_repo_metadata_snapshots([self.metadata(description="changed", homepage="new")], LATE), 0)
        self.assertEqual(self.rows("repo_metadata_snapshots")[-1][2:4], ("changed", "new"))
        self.assertEqual(self.rows("repository_events")[0][-1], '{"changed_fields":["description"]}')

    def test_invalid_later_metadata_rolls_back_snapshots_and_events(self):
        app.save_repo_metadata_snapshots([self.metadata()], EARLY)
        before = self.rows("repo_metadata_snapshots")
        with self.assertRaisesRegex(ValueError, "Invalid repository name"):
            app.save_repo_metadata_snapshots([self.metadata(description="new"), {"full_name": "invalid name"}], LATE)
        self.assertEqual(self.rows("repo_metadata_snapshots"), before)
        self.assertEqual(self.rows("repository_events"), [])

    def test_metadata_event_hook_false_still_commits_snapshot(self):
        app.save_repo_metadata_snapshots([self.metadata()], EARLY)
        with mock.patch.object(app, "_record_repository_event", return_value=False) as record:
            self.assertEqual(app.save_repo_metadata_snapshots([self.metadata(description="new")], LATE), 0)
        self.assertEqual(record.call_args.kwargs["metadata"], {"changed_fields": ["description"]})
        self.assertEqual(record.call_args.kwargs["detected_at"], LATE)
        self.assertEqual(self.rows("repo_metadata_snapshots")[-1][2], "new")

    def test_metadata_event_hook_failure_rolls_back_snapshot(self):
        app.save_repo_metadata_snapshots([self.metadata()], EARLY)
        before = self.rows("repo_metadata_snapshots")
        with mock.patch.object(app, "_record_repository_event", side_effect=RuntimeError("event failure")):
            with self.assertRaisesRegex(RuntimeError, "event failure"):
                app.save_repo_metadata_snapshots([self.metadata(description="new")], LATE)
        self.assertEqual(self.rows("repo_metadata_snapshots"), before)

    def test_event_validation_happens_before_clock_fallback(self):
        with mock.patch.object(app, "utc_now") as clock:
            with self.assertRaisesRegex(ValueError, "Invalid repository name"):
                app.record_repository_event(**self.event(repo="invalid name"))
        clock.assert_not_called()
        self.assertEqual(self.rows("repository_events"), [])

    def test_event_duplicate_attempts_still_evaluate_fallback_clock(self):
        with mock.patch.object(app, "utc_now", side_effect=[EARLY, LATE]) as clock:
            self.assertTrue(app.record_repository_event(**self.event()))
            self.assertFalse(app.record_repository_event(**self.event(source="other", metadata={"new": 1})))
        self.assertEqual(clock.call_count, 2)
        self.assertEqual(self.rows("repository_events")[0][5:8], (EARLY, "github_release", "{}"))

    def test_explicit_detection_time_does_not_read_clock_but_empty_time_does(self):
        with mock.patch.object(app, "utc_now", return_value=LATE) as clock:
            self.assertTrue(app.record_repository_event(**self.event(detected_at=EARLY)))
            clock.assert_not_called()
            self.assertTrue(app.record_repository_event(**self.event(title="v2", detected_at="")))
        clock.assert_called_once_with()

    def test_event_metadata_is_compact_sorted_json_and_uniqueness_excludes_payload(self):
        data = {"z": "é", "a": {"b": 2, "a": 1}}
        self.assertTrue(app.record_repository_event(**self.event(metadata=data, detected_at=LATE)))
        self.assertEqual(self.rows("repository_events")[0][-1], '{"a":{"a":1,"b":2},"z":"\\u00e9"}')
        self.assertFalse(app.record_repository_event(**self.event(metadata={}, detected_at=EARLY, source="other")))
        for overrides in ({"event_type": "readme"}, {"title": "v2"}, {"occurred_at": LATE}):
            self.assertTrue(app.record_repository_event(**self.event(**overrides, detected_at=LATE)))
        self.assertEqual(len(self.rows("repository_events")), 4)

    def test_unserializable_metadata_fails_after_clock_without_inserting(self):
        with mock.patch.object(app, "utc_now", return_value=LATE) as clock:
            with self.assertRaises(TypeError):
                app.record_repository_event(**self.event(metadata={"bad": object()}))
        clock.assert_called_once_with()
        self.assertEqual(self.rows("repository_events"), [])

    def test_supplied_connection_event_write_leaves_rollback_to_caller(self):
        with app.database_connection() as connection:
            self.assertTrue(app._record_repository_event(connection, **self.event(detected_at=EARLY)))
            self.assertTrue(connection.in_transaction)
            connection.rollback()
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM repository_events").fetchone(), (0,))

    def test_writes_use_currently_selected_account_database(self):
        app.save_repo_snapshots([{"full_name": REPO, "stars": 1}], EARLY)
        other = self.root / "other-account.sqlite3"
        with mock.patch.object(app, "DB_PATH", other):
            app.ensure_database()
            app.save_repo_snapshots([{"full_name": "other/project", "stars": 2}], LATE)
            app.save_repo_metadata_snapshots([{"full_name": "other/project"}], LATE)
            app.record_repository_event(**self.event(repo="other/project", detected_at=LATE))
        self.assertEqual(self.rows("repo_snapshots"), [(REPO, EARLY, 1, 0, 0, 0, 0, 0, "", "")])
        self.assertEqual(self.rows("repo_metadata_snapshots"), [])
        self.assertEqual(self.rows("repository_events"), [])

    def test_savers_do_not_mutate_input(self):
        repositories = [self.metadata(stars="7", topics=["z", "a"])]
        before = copy.deepcopy(repositories)
        app.save_repo_snapshots(repositories, EARLY)
        app.save_repo_metadata_snapshots(repositories, EARLY)
        self.assertEqual(repositories, before)


if __name__ == "__main__":
    unittest.main()
