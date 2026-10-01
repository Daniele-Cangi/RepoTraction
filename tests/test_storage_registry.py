"""Characterize registry transactions using owned databases and fake GitHub replies."""
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest import mock

import app


OLD = "octocat/old"
NEW = "octocat/new"
EARLY = "2026-08-20T10:00:00Z"
LATE = "2026-08-21T10:00:00Z"
HISTORY_TABLES = (
    "traffic_daily", "traffic_snapshots", "repo_snapshots",
    "repo_metadata_snapshots", "repository_events",
)


class RegistryCharacterizationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.path = self.root / "registry.sqlite3"
        for name, value in (("DB_PATH", self.path), ("DATA_DIR", self.root)):
            patch = mock.patch.object(app, name, value)
            patch.start()
            self.addCleanup(patch.stop)
        app.ensure_database()

    def rows(self, table):
        with closing(sqlite3.connect(self.path)) as connection:
            return connection.execute(f"SELECT * FROM {table} ORDER BY 1, 2").fetchall()

    def seed(self, name=OLD, value=7, timestamp=EARLY):
        with app.database_connection() as connection:
            connection.execute(
                "INSERT INTO traffic_daily (repo, day, views, unique_views, views_available, "
                "views_status, clones, unique_clones, clones_available, clones_status, collected_at) "
                "VALUES (?, '2026-08-20', ?, 2, 1, 'observed_value', ?, 3, 1, 'observed_value', ?)",
                (name, value, value + 1, timestamp),
            )
            connection.execute("INSERT INTO traffic_snapshots VALUES (?, ?, ?, 2, ?, 3)",
                               (name, timestamp, value, value + 1))
            connection.execute("INSERT INTO repo_snapshots (repo, collected_at, stars) VALUES (?, ?, ?)",
                               (name, timestamp, value))
            connection.execute("INSERT INTO repo_metadata_snapshots (repo, collected_at, description) "
                               "VALUES (?, ?, ?)", (name, timestamp, f"description {value}"))
            connection.execute("INSERT INTO repository_events (repo, event_type, title, occurred_at, "
                               "detected_at, source, metadata_json) VALUES (?, 'release', 'v1', ?, ?, "
                               "'github_release', ?)", (name, EARLY, timestamp, f'{{"value": {value}}}'))

    def test_case_only_merge_does_not_access_connection(self):
        app.merge_repository_history(None, "Octocat/Old", "octocat/old")

    def test_rename_moves_every_history_table_without_changing_payload(self):
        self.seed()
        before = {table: self.rows(table) for table in HISTORY_TABLES}
        with app.database_connection() as connection:
            app.merge_repository_history(connection, OLD, NEW)
            self.assertIs(connection.row_factory, sqlite3.Row)
        for table in HISTORY_TABLES:
            with self.subTest(table=table):
                after = self.rows(table)
                self.assertEqual(len(after), 1)
                if table == "repository_events":
                    self.assertEqual(after[0][1:], (NEW, *before[table][0][2:]))
                else:
                    self.assertEqual(after[0], (NEW, *before[table][0][1:]))

    def test_traffic_collisions_choose_each_metric_independently(self):
        for old_available in (None, 0, 1):
            for new_available in (None, 0, 1):
                for old_time in ("2026-08-19T10:00:00Z", EARLY, LATE):
                    with self.subTest(old=old_available, new=new_available, time=old_time):
                        with app.database_connection() as connection:
                            connection.execute("DELETE FROM traffic_daily")
                            for name, value, views_available, clones_available, timestamp in (
                                (OLD, 9, old_available, new_available, old_time),
                                (NEW, 2, new_available, old_available, EARLY),
                            ):
                                connection.execute("INSERT INTO traffic_daily (repo, day, views, "
                                                   "unique_views, views_available, clones, unique_clones, "
                                                   "clones_available, collected_at) VALUES (?, '2026-08-20', "
                                                   "?, ?, ?, ?, ?, ?, ?)",
                                                   (name, value, value, views_available, value, value,
                                                    clones_available, timestamp))
                            app.merge_repository_history(connection, OLD, NEW)
                        row = self.rows("traffic_daily")[0]
                        take_views = old_available == 1 and (new_available != 1 or old_time > EARLY)
                        take_clones = new_available == 1 and (old_available != 1 or old_time > EARLY)
                        self.assertEqual(row[0], NEW)
                        self.assertEqual(row[2:5], (9, 9, 1) if take_views else (2, 2, new_available))
                        self.assertEqual(row[6:9], (9, 9, 1) if take_clones else (2, 2, old_available))
                        self.assertEqual(row[10], max(old_time, EARLY))

    def test_snapshot_and_event_collisions_keep_canonical_payload(self):
        self.seed(OLD, 9)
        self.seed(NEW, 2)
        before = {table: [row for row in self.rows(table) if row[0 if table != "repository_events" else 1] == NEW]
                  for table in HISTORY_TABLES[1:]}
        with app.database_connection() as connection:
            app.merge_repository_history(connection, OLD, NEW)
        for table in HISTORY_TABLES[1:]:
            self.assertEqual(self.rows(table), before[table])

    def test_merge_uses_caller_transaction_without_committing(self):
        self.seed()
        before = {table: self.rows(table) for table in HISTORY_TABLES}
        with self.assertRaisesRegex(ValueError, "caller failure"):
            with app.database_connection() as connection:
                app.merge_repository_history(connection, OLD, NEW)
                raise ValueError("caller failure")
        self.assertEqual({table: self.rows(table) for table in HISTORY_TABLES}, before)

    def test_archive_moves_all_history_but_does_not_change_registry(self):
        app.reconcile_repository_registry([{"id": 1, "full_name": OLD}], EARLY)
        self.seed()
        registry = self.rows("repository_registry")
        with app.database_connection() as connection:
            app.archive_repository_history(connection, OLD, "archived history")
        self.assertEqual(self.rows("repository_registry"), registry)
        for table in HISTORY_TABLES:
            self.assertEqual(self.rows(table)[0][0 if table != "repository_events" else 1], "archived history")

    def test_archive_collision_rolls_back_prior_table_updates(self):
        self.seed()
        with app.database_connection() as connection:
            connection.execute("INSERT INTO repo_snapshots (repo, collected_at) VALUES ('archive', ?)", (EARLY,))
        before = {table: self.rows(table) for table in HISTORY_TABLES}
        with self.assertRaises(sqlite3.IntegrityError):
            with app.database_connection() as connection:
                app.archive_repository_history(connection, OLD, "archive")
        self.assertEqual({table: self.rows(table) for table in HISTORY_TABLES}, before)

    def test_legacy_reuse_only_archives_idless_inactive_matching_aliases(self):
        self.seed("Octocat/Old")
        with app.database_connection() as connection:
            connection.executemany("INSERT INTO repository_aliases VALUES (?, ?, ?, ?, ?)", [
                ("Octocat/Old", None, "Octocat/Old", "inactive", EARLY),
                ("octocat/not-current", None, "octocat/not-current", "inactive", EARLY),
                ("octocat/with-id", 8, "octocat/with-id", "inactive", EARLY),
                ("octocat/renamed", None, NEW, "renamed", EARLY),
            ])
            app.archive_reused_legacy_aliases(connection, {OLD, "octocat/with-id", "octocat/renamed"}, LATE)
        aliases = {row[0]: row for row in self.rows("repository_aliases")}
        self.assertEqual(aliases["Octocat/Old"][2:], ("Octocat/Old (archived legacy history)", "reused", LATE))
        self.assertEqual(aliases["octocat/with-id"][3], "inactive")
        self.assertEqual(aliases["octocat/renamed"][3], "renamed")
        self.assertEqual(aliases["octocat/not-current"][4], EARLY)

    def test_invalid_id_fails_before_opening_database(self):
        with mock.patch.object(app, "database_connection") as factory:
            with self.assertRaises(ValueError):
                app.reconcile_repository_registry([{"id": "invalid", "full_name": OLD}], EARLY)
        factory.assert_not_called()

    def test_duplicate_ids_use_last_valid_input_and_ignore_missing_identity(self):
        app.reconcile_repository_registry([
            {"id": 1, "full_name": OLD, "created_at": EARLY},
            {"id": 0, "full_name": "octocat/zero"}, {"id": 2}, {"full_name": "octocat/no-id"},
            {"id": "1", "full_name": NEW},
        ], LATE)
        self.assertEqual(self.rows("repository_registry"), [(1, NEW, None, 1, LATE, LATE)])

    def test_dates_preserve_first_seen_and_existing_creation_when_missing(self):
        app.reconcile_repository_registry([{"id": 1, "full_name": OLD, "created_at": EARLY}], EARLY)
        app.reconcile_repository_registry([{"id": 1, "full_name": OLD}], LATE)
        self.assertEqual(self.rows("repository_registry"), [(1, OLD, EARLY, 1, EARLY, LATE)])

    def test_case_only_registry_change_leaves_history_name_unchanged(self):
        app.reconcile_repository_registry([{"id": 1, "full_name": "Octocat/Old"}], EARLY)
        self.seed("Octocat/Old")
        with mock.patch.object(app, "run_gh_json") as resolver:
            app.reconcile_repository_registry([{"id": 1, "full_name": OLD}], LATE)
        resolver.assert_not_called()
        self.assertEqual(self.rows("traffic_daily")[0][0], "Octocat/Old")
        self.assertEqual(self.rows("repository_registry")[0][1], OLD)
        self.assertEqual(self.rows("repository_aliases"), [])

    def test_same_id_rename_merges_and_records_alias_without_network(self):
        app.reconcile_repository_registry([{"id": 1, "full_name": OLD}], EARLY)
        self.seed()
        with mock.patch.object(app, "run_gh_json") as resolver:
            app.reconcile_repository_registry([{"id": 1, "full_name": NEW}], LATE)
        resolver.assert_not_called()
        self.assertEqual(self.rows("repository_aliases"), [(OLD, 1, NEW, "renamed", LATE)])
        for table in HISTORY_TABLES:
            self.assertEqual(self.rows(table)[0][0 if table != "repository_events" else 1], NEW)

    def test_different_id_reusing_name_archives_all_old_history(self):
        app.reconcile_repository_registry([{"id": 1, "full_name": OLD}], EARLY)
        self.seed()
        app.reconcile_repository_registry([{"id": 2, "full_name": OLD}], LATE)
        archived = f"{OLD} (archived repository id 1)"
        for table in HISTORY_TABLES:
            self.assertEqual(self.rows(table)[0][0 if table != "repository_events" else 1], archived)
        self.assertEqual(self.rows("repository_registry"), [
            (1, archived, None, 0, EARLY, EARLY), (2, OLD, None, 1, LATE, LATE),
        ])

    def test_uninitialized_and_initialized_empty_registry_are_distinct(self):
        self.assertIsNone(app.get_active_repository_names())
        app.reconcile_repository_registry([], EARLY)
        self.assertEqual(app.get_active_repository_names(), set())
        app.reconcile_repository_registry([{"id": 1, "full_name": "Octocat/New"}], LATE)
        self.assertEqual(app.get_active_repository_names(), {NEW})
        app.reconcile_repository_registry([], LATE)
        self.assertEqual(app.get_active_repository_names(), set())

    def test_resolver_only_receives_sorted_unresolved_history_names(self):
        self.seed("octocat/zeta")
        self.seed("octocat/Alpha")
        self.seed("invalid display name")
        self.seed("octocat/known")
        self.seed(NEW)
        with app.database_connection() as connection:
            connection.execute("INSERT INTO repository_aliases VALUES ('OCTOCAT/KNOWN', NULL, "
                               "'octocat/known', 'inactive', ?)", (EARLY,))
            connection.execute("INSERT INTO repo_metadata_snapshots (repo, collected_at) "
                               "VALUES ('octocat/metadata-only', ?)", (EARLY,))
            connection.execute("INSERT INTO repository_events (repo, event_type, title, occurred_at, "
                               "detected_at, source) VALUES ('octocat/event-only', 'release', 'v1', ?, ?, 'test')",
                               (EARLY, EARLY))
        with mock.patch.object(app, "run_gh_json", return_value={}) as resolver:
            app.reconcile_repository_registry([{"id": 1, "full_name": NEW}], LATE)
        self.assertEqual(resolver.call_args_list, [mock.call("repos/octocat/Alpha"), mock.call("repos/octocat/zeta")])

    def test_resolution_of_current_id_uses_current_name_not_reply_name(self):
        self.seed()
        with mock.patch.object(app, "run_gh_json", return_value={"id": 1, "full_name": "octocat/stale-name"}):
            app.reconcile_repository_registry([{"id": 1, "full_name": NEW}], LATE)
        self.assertEqual(self.rows("repository_aliases"), [(OLD, 1, NEW, "renamed", LATE)])
        self.assertEqual(self.rows("traffic_daily")[0][0], NEW)

    def test_generic_cli_failure_records_inactive_alias_and_preserves_history(self):
        self.seed()
        with mock.patch.object(app, "run_gh_json", side_effect=app.GitHubCLIError("not found")):
            app.reconcile_repository_registry([], LATE)
        self.assertEqual(self.rows("repository_aliases"), [(OLD, None, OLD, "inactive", LATE)])
        self.assertEqual(self.rows("traffic_daily")[0][0], OLD)

    def test_account_change_and_rate_limit_propagate_after_initial_commit(self):
        self.seed()
        for exception_type in (app.ActiveAccountChangedError, app.GitHubRateLimitError):
            failure = exception_type("stop resolver")
            with self.subTest(error=exception_type), mock.patch.object(app, "run_gh_json", side_effect=failure):
                with self.assertRaises(exception_type) as raised:
                    app.reconcile_repository_registry([{"id": 1, "full_name": NEW}], LATE)
            self.assertIs(raised.exception, failure)
            self.assertEqual(app.get_active_repository_names(), {NEW})
            self.assertEqual(self.rows("repository_aliases"), [])

    def test_network_runs_outside_transaction_and_previous_alias_is_committed(self):
        self.seed("octocat/a")
        self.seed("octocat/b")
        failure = app.GitHubRateLimitError("second request")
        def resolve(endpoint):
            with closing(sqlite3.connect(self.path, timeout=0)) as reader:
                reader.execute("BEGIN IMMEDIATE")
                self.assertEqual(reader.execute("SELECT initialized FROM repository_registry_state").fetchone(), (1,))
                if endpoint.endswith("/b"):
                    self.assertEqual(reader.execute("SELECT alias FROM repository_aliases").fetchall(), [("octocat/a",)])
                    raise failure
            return {}
        with mock.patch.object(app, "run_gh_json", side_effect=resolve):
            with self.assertRaises(app.GitHubRateLimitError):
                app.reconcile_repository_registry([], LATE)
        self.assertEqual([row[0] for row in self.rows("repository_aliases")], ["octocat/a"])

    def test_alias_write_failure_rolls_back_rename_but_not_initial_registry_commit(self):
        self.seed()
        before = {table: self.rows(table) for table in HISTORY_TABLES}
        with app.database_connection() as connection:
            connection.execute("CREATE TRIGGER fail_alias BEFORE INSERT ON repository_aliases "
                               "BEGIN SELECT RAISE(ABORT, 'alias failure'); END")
        with mock.patch.object(app, "run_gh_json", return_value={"id": 1, "full_name": NEW}):
            with self.assertRaisesRegex(sqlite3.IntegrityError, "alias failure"):
                app.reconcile_repository_registry([{"id": 1, "full_name": NEW}], LATE)
        self.assertEqual({table: self.rows(table) for table in HISTORY_TABLES}, before)
        self.assertEqual(app.get_active_repository_names(), {NEW})
        self.assertEqual(self.rows("repository_aliases"), [])

    def test_initial_registry_failure_rolls_back_activation_and_history(self):
        app.reconcile_repository_registry([{"id": 1, "full_name": OLD}], EARLY)
        self.seed()
        with app.database_connection() as connection:
            connection.execute("INSERT INTO repo_snapshots (repo, collected_at) VALUES (?, ?)",
                               (f"{OLD} (archived repository id 1)", EARLY))
        before = {table: self.rows(table) for table in (*HISTORY_TABLES, "repository_registry")}
        with self.assertRaises(sqlite3.IntegrityError):
            app.reconcile_repository_registry([{"id": 2, "full_name": OLD}], LATE)
        self.assertEqual({table: self.rows(table) for table in before}, before)

    def test_registry_reads_and_writes_only_currently_selected_database(self):
        app.reconcile_repository_registry([{"id": 1, "full_name": OLD}], EARLY)
        other = self.root / "other-account.sqlite3"
        with mock.patch.object(app, "DB_PATH", other):
            app.ensure_database()
            self.assertIsNone(app.get_active_repository_names())
            app.reconcile_repository_registry([{"id": 2, "full_name": NEW}], LATE)
            self.assertEqual(app.get_active_repository_names(), {NEW})
        self.assertEqual(app.get_active_repository_names(), {OLD})


if __name__ == "__main__":
    unittest.main()
