"""Characterize repository snapshots and event writes with owned test history."""
import copy
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import closing, nullcontext
from pathlib import Path
from unittest import mock

import app
from storage import repository_snapshots
from storage.migrations import migrate_database


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


class RepositorySnapshotModuleTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.addCleanup(self.connection.close)
        migrate_database(self.connection)
        self.connection.commit()

    def test_counter_writer_leaves_commit_rollback_and_closure_to_caller(self):
        repositories = [{"full_name": REPO, "stars": 7}]
        repository_snapshots.save_repo_snapshots(self.connection, repositories, EARLY)
        self.assertTrue(self.connection.in_transaction)
        self.assertEqual(repositories, [{"full_name": REPO, "stars": 7}])
        self.connection.rollback()
        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM repo_snapshots").fetchone(), (0,))

    def test_metadata_hook_receives_same_connection_after_snapshot_write(self):
        repository_snapshots.save_repo_metadata_snapshots(
            self.connection, [{"full_name": REPO}], EARLY,
            validate_repo=str.casefold, record_event=mock.Mock(),
        )
        self.connection.commit()
        def record(connection, **event):
            self.assertIs(connection, self.connection)
            self.assertTrue(connection.in_transaction)
            self.assertEqual(connection.execute("SELECT description FROM repo_metadata_snapshots "
                                               "WHERE collected_at = ?", (LATE,)).fetchone()[0], "new")
            self.assertEqual(event["metadata"], {"changed_fields": ["description"]})
            return False
        count = repository_snapshots.save_repo_metadata_snapshots(
            self.connection, [{"full_name": REPO, "description": "new"}], LATE,
            validate_repo=str.casefold, record_event=record,
        )
        self.assertEqual(count, 0)
        self.connection.rollback()
        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM repo_metadata_snapshots").fetchone()[0], 1)

    def test_metadata_failure_does_not_implicitly_rollback_caller_transaction(self):
        record = mock.Mock(side_effect=RuntimeError("event failure"))
        repository_snapshots.save_repo_metadata_snapshots(
            self.connection, [{"full_name": REPO}], EARLY, validate_repo=str.casefold, record_event=record,
        )
        record.assert_not_called()
        self.connection.commit()
        with self.assertRaisesRegex(RuntimeError, "event failure"):
            repository_snapshots.save_repo_metadata_snapshots(
                self.connection, [{"full_name": REPO, "description": "new"}], LATE,
                validate_repo=str.casefold, record_event=record,
            )
        self.assertTrue(self.connection.in_transaction)
        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM repo_metadata_snapshots").fetchone()[0], 2)
        self.connection.rollback()
        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM repo_metadata_snapshots").fetchone()[0], 1)

    def test_metadata_uses_supplied_validation_and_preserves_input(self):
        repositories = [{"full_name": "Octocat/Project", "topics": ["z", "a"]}]
        before = copy.deepcopy(repositories)
        validate = mock.Mock(side_effect=str.casefold)
        repository_snapshots.save_repo_metadata_snapshots(
            self.connection, repositories, EARLY, validate_repo=validate, record_event=mock.Mock(),
        )
        validate.assert_called_once_with("Octocat/Project")
        row = self.connection.execute("SELECT repo, topics_json FROM repo_metadata_snapshots").fetchone()
        self.assertEqual(tuple(row), (REPO, '["a","z"]'))
        self.assertEqual(repositories, before)

    def test_event_uses_supplied_validation_and_clock_in_existing_order(self):
        calls = []
        def validate(value):
            calls.append(("validate", value))
            return value.casefold()
        def clock():
            calls.append(("clock",))
            return LATE
        event = {"repo": "Octocat/Project", "event_type": "release", "title": "v1",
                 "occurred_at": EARLY, "source": "test", "validate_repo": validate, "utc_now": clock}
        self.assertTrue(repository_snapshots.record_repository_event(self.connection, **event))
        self.assertFalse(repository_snapshots.record_repository_event(self.connection, **event))
        self.assertEqual(calls, [("validate", "Octocat/Project"), ("clock",)] * 2)
        self.assertTrue(self.connection.in_transaction)
        self.connection.rollback()
        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM repository_events").fetchone(), (0,))

    def test_event_does_not_read_supplied_clock_for_explicit_time_or_validation_failure(self):
        clock = mock.Mock(side_effect=AssertionError("unexpected clock"))
        event = {"repo": REPO, "event_type": "release", "title": "v1", "occurred_at": EARLY,
                 "source": "test", "validate_repo": str.casefold, "utc_now": clock, "detected_at": LATE}
        self.assertTrue(repository_snapshots.record_repository_event(self.connection, **event))
        event.update(detected_at=None, validate_repo=mock.Mock(side_effect=ValueError("invalid")))
        with self.assertRaisesRegex(ValueError, "invalid"):
            repository_snapshots.record_repository_event(self.connection, **event)
        clock.assert_not_called()

    def test_entry_point_adapters_pass_connection_and_current_patch_hooks(self):
        repositories = [{"full_name": REPO}]
        event = {"repo": REPO, "event_type": "release", "title": "v1", "occurred_at": EARLY, "source": "test"}
        with mock.patch.object(app, "database_connection", return_value=nullcontext(self.connection)), \
             mock.patch.object(app, "persist_repo_snapshots") as counters, \
             mock.patch.object(app, "persist_repo_metadata_snapshots", return_value=2) as metadata, \
             mock.patch.object(app, "persist_repository_event", return_value=True) as record:
            app.save_repo_snapshots(repositories, EARLY)
            self.assertEqual(app.save_repo_metadata_snapshots(repositories, EARLY), 2)
            self.assertTrue(app.record_repository_event(**event))
        counters.assert_called_once_with(self.connection, repositories, EARLY)
        metadata.assert_called_once_with(self.connection, repositories, EARLY,
                                         validate_repo=app.validate_repo, record_event=app._record_repository_event)
        record.assert_called_once_with(self.connection, **event, metadata=None, detected_at=None,
                                       validate_repo=app.validate_repo, utc_now=app.utc_now)

    def test_fresh_import_opens_no_database_and_loads_no_entry_point_or_provider(self):
        code = """
import pathlib, sqlite3, sys, threading
from unittest import mock
sys.path.insert(0, sys.argv[1])
with mock.patch.object(sqlite3, 'connect', side_effect=AssertionError('database opened')), \
     mock.patch.object(pathlib.Path, 'mkdir', side_effect=AssertionError('directory created')), \
     mock.patch.object(threading.Thread, 'start', side_effect=AssertionError('thread started')):
    from storage import repository_snapshots
assert not any(name == 'app' or name.startswith('missing_link') for name in sys.modules)
assert pathlib.Path(repository_snapshots.__file__).resolve().parent == pathlib.Path(sys.argv[1]).resolve() / 'storage'
"""
        result = subprocess.run([sys.executable, "-I", "-c", code, str(Path(app.__file__).parent)],
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
