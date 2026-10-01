"""Characterize registry transactions using owned databases and fake GitHub replies."""
import csv
import io
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import closing, nullcontext
from pathlib import Path
from unittest import mock

import app
from storage import registry
from storage.migrations import migrate_database


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

    def seed_daily(self, name, views, clones, timestamp=EARLY):
        """Insert explicitly supplied metric evidence; do not infer provenance."""
        with app.database_connection() as connection:
            connection.execute(
                "INSERT INTO traffic_daily (repo, day, views, unique_views, views_available, "
                "views_status, clones, unique_clones, clones_available, clones_status, collected_at) "
                "VALUES (?, '2026-08-20', ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (name, *views, *clones, timestamp),
            )

    def test_collision_copies_observed_value_status_with_selected_counts(self):
        self.seed_daily(OLD, (7, 2, 1, "observed_value"), (9, 3, 1, "observed_value"))
        self.seed_daily(NEW, (0, 0, None, "missing"), (0, 0, None, "missing"), LATE)
        with app.database_connection() as connection:
            app.merge_repository_history(connection, OLD, NEW)
        row = app.get_traffic_history(NEW)[0]
        self.assertEqual((row["views"], row["unique_views"], row["views_available"], row["views_status"]),
                         (7, 2, 1, "observed_value"))
        self.assertEqual((row["clones"], row["unique_clones"], row["clones_available"], row["clones_status"]),
                         (9, 3, 1, "observed_value"))

    def test_collision_copies_explicit_observed_zero_without_inventing_missing_metric(self):
        self.seed_daily(OLD, (0, 0, 1, "observed_zero"), (0, 0, None, "missing"))
        self.seed_daily(NEW, (0, 0, None, "missing"), (0, 0, None, "missing"), LATE)
        with app.database_connection() as connection:
            app.merge_repository_history(connection, OLD, NEW)
        row = app.get_traffic_history(NEW)[0]
        self.assertEqual((row["views_available"], row["views_status"]), (1, "observed_zero"))
        self.assertEqual((row["clones_available"], row["clones_status"]), (None, "missing"))

    def test_collision_keeps_unique_only_observation_status_even_when_count_is_zero(self):
        self.seed_daily(OLD, (0, 2, 1, "observed_value"), (0, 3, 1, "observed_value"))
        self.seed_daily(NEW, (0, 0, None, "missing"), (0, 0, None, "missing"))
        with app.database_connection() as connection:
            app.merge_repository_history(connection, OLD, NEW)
        row = app.get_traffic_history(NEW)[0]
        self.assertEqual((row["views"], row["unique_views"], row["views_status"]), (0, 2, "observed_value"))
        self.assertEqual((row["clones"], row["unique_clones"], row["clones_status"]), (0, 3, "observed_value"))

    def test_collision_transfers_each_metric_status_independently(self):
        for copied_metric in ("views", "clones"):
            with self.subTest(metric=copied_metric):
                with app.database_connection() as connection:
                    connection.execute("DELETE FROM traffic_daily")
                observed = (7, 2, 1, "observed_value")
                missing = (0, 0, None, "missing")
                retained = (0, 0, 1, "observed_zero")
                self.seed_daily(OLD, observed if copied_metric == "views" else missing,
                                observed if copied_metric == "clones" else missing)
                self.seed_daily(NEW, missing if copied_metric == "views" else retained,
                                missing if copied_metric == "clones" else retained, LATE)
                with app.database_connection() as connection:
                    app.merge_repository_history(connection, OLD, NEW)
                row = app.get_traffic_history(NEW)[0]
                other = "clones" if copied_metric == "views" else "views"
                self.assertEqual((row[copied_metric], row[f"{copied_metric}_status"]), (7, "observed_value"))
                self.assertEqual((row[other], row[f"{other}_status"]), (0, "observed_zero"))

    def test_newer_selected_observation_copies_status_without_changing_precedence(self):
        for source, target in (
            ((7, 2, 1, "observed_value"), (0, 0, 1, "observed_zero")),
            ((0, 0, 1, "observed_zero"), (7, 2, 1, "observed_value")),
        ):
            with self.subTest(source=source):
                with app.database_connection() as connection:
                    connection.execute("DELETE FROM traffic_daily")
                self.seed_daily(OLD, source, source, LATE)
                self.seed_daily(NEW, target, target)
                with app.database_connection() as connection:
                    app.merge_repository_history(connection, OLD, NEW)
                row = app.get_traffic_history(NEW)[0]
                self.assertEqual((row["views"], row["unique_views"], row["views_available"], row["views_status"]), source)
                self.assertEqual((row["clones"], row["unique_clones"], row["clones_available"], row["clones_status"]), source)

    def test_retained_canonical_observation_keeps_status_for_older_or_tied_source(self):
        for timestamp in (EARLY, LATE):
            with self.subTest(timestamp=timestamp):
                with app.database_connection() as connection:
                    connection.execute("DELETE FROM traffic_daily")
                self.seed_daily(OLD, (7, 2, 1, "observed_value"), (9, 3, 1, "observed_value"), timestamp)
                self.seed_daily(NEW, (0, 0, 1, "observed_zero"), (0, 0, 1, "observed_zero"), LATE)
                with app.database_connection() as connection:
                    app.merge_repository_history(connection, OLD, NEW)
                row = app.get_traffic_history(NEW)[0]
                self.assertEqual((row["views"], row["views_status"], row["clones"], row["clones_status"]),
                                 (0, "observed_zero", 0, "observed_zero"))

    def test_unavailable_legacy_or_missing_source_does_not_replace_observed_status(self):
        for available, status in ((None, "missing"), (None, "legacy_unknown"), (0, "missing")):
            with self.subTest(available=available, status=status):
                with app.database_connection() as connection:
                    connection.execute("DELETE FROM traffic_daily")
                self.seed_daily(OLD, (7, 2, available, status), (9, 3, available, status), LATE)
                self.seed_daily(NEW, (0, 0, 1, "observed_zero"), (0, 0, 1, "observed_zero"))
                with app.database_connection() as connection:
                    app.merge_repository_history(connection, OLD, NEW)
                row = app.get_traffic_history(NEW)[0]
                self.assertEqual((row["views"], row["views_available"], row["views_status"]), (0, 1, "observed_zero"))
                self.assertEqual((row["clones"], row["clones_available"], row["clones_status"]), (0, 1, "observed_zero"))

    def test_collision_status_update_rolls_back_with_failed_source_delete(self):
        self.seed_daily(OLD, (7, 2, 1, "observed_value"), (0, 0, 1, "observed_zero"))
        self.seed_daily(NEW, (0, 0, None, "missing"), (0, 0, None, "missing"))
        before = self.rows("traffic_daily")
        with app.database_connection() as connection:
            connection.execute("CREATE TRIGGER fail_delete BEFORE DELETE ON traffic_daily "
                               "BEGIN SELECT RAISE(ABORT, 'delete failure'); END")
        with self.assertRaisesRegex(sqlite3.IntegrityError, "delete failure"):
            with app.database_connection() as connection:
                app.merge_repository_history(connection, OLD, NEW)
        self.assertEqual(self.rows("traffic_daily"), before)

    def test_registry_rename_exposes_correct_provenance_in_history_and_exports(self):
        app.reconcile_repository_registry([{"id": 1, "full_name": OLD}], EARLY)
        bucket = {"timestamp": EARLY, "count": 7, "uniques": 2}
        app.save_traffic(OLD, {"views": [bucket]}, None, collected_at=EARLY)
        app.save_traffic(NEW, None, {"clones": [{**bucket, "count": 0, "uniques": 0}]}, collected_at=LATE)
        with mock.patch.object(app, "run_gh_json", side_effect=AssertionError("unexpected network")):
            app.reconcile_repository_registry([{"id": 1, "full_name": NEW}], LATE)
        row = app.get_traffic_history(NEW)[0]
        self.assertEqual((row["views_status"], row["clones_status"]), ("observed_value", "observed_zero"))
        self.assertEqual(app.get_traffic_history(OLD), [])
        filename, content = app.build_csv_export("traffic")
        exported = list(csv.DictReader(io.StringIO(content.decode("utf-8-sig"))))[0]
        self.assertTrue(filename.endswith("-traffic.csv"))
        self.assertEqual((exported["views"], exported["views_status"], exported["clones"], exported["clones_status"]),
                         ("7", "observed_value", "0", "observed_zero"))
        with mock.patch.object(app, "get_account_login", return_value="octocat"), \
             mock.patch.object(app, "build_signals", return_value={}), \
             mock.patch.object(app, "get_relation_movements", return_value=[]), \
             mock.patch.object(app, "get_repository_events", return_value=[]), \
             mock.patch.object(app, "get_relation_history", return_value=[]):
            json_row = app.build_export_payload()["traffic"][0]
        self.assertEqual((json_row["views_status"], json_row["clones_status"]),
                         ("observed_value", "observed_zero"))

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


class RegistryModuleTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.addCleanup(self.connection.close)
        migrate_database(self.connection)
        self.connection.commit()

    def test_current_registry_uses_supplied_data_without_mutating_inputs(self):
        names = {1: NEW}
        created = {1: EARLY}
        folded = {NEW}
        result = registry.reconcile_current_repositories(self.connection, names, created, folded, LATE)
        self.assertEqual(result, (set(), set()))
        self.assertEqual((names, created, folded), ({1: NEW}, {1: EARLY}, {NEW}))
        self.assertTrue(self.connection.in_transaction)
        self.connection.rollback()
        self.assertIsNone(registry.read_active_repository_rows(self.connection))
        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM repository_registry").fetchone()[0], 0)

    def test_current_registry_returns_existing_historical_names_and_folded_aliases(self):
        self.connection.execute("INSERT INTO traffic_snapshots (repo, collected_at) VALUES (?, ?)", (OLD, EARLY))
        self.connection.execute("INSERT INTO repository_aliases VALUES (?, NULL, ?, 'inactive', ?)",
                                ("Octocat/Alias", OLD, EARLY))
        self.assertEqual(registry.reconcile_current_repositories(self.connection, {}, {}, set(), LATE),
                         ({OLD}, {"octocat/alias"}))

    def test_active_rows_respect_caller_row_factory_and_empty_initialization(self):
        self.assertIsNone(registry.read_active_repository_rows(self.connection))
        registry.reconcile_current_repositories(self.connection, {}, {}, set(), EARLY)
        self.assertEqual(registry.read_active_repository_rows(self.connection), [])
        registry.reconcile_current_repositories(self.connection, {1: NEW}, {}, {NEW}, LATE)
        self.connection.row_factory = None
        self.assertEqual(registry.read_active_repository_rows(self.connection), [(NEW,)])
        self.connection.row_factory = sqlite3.Row
        self.assertEqual(registry.read_active_repository_rows(self.connection)[0]["full_name"], NEW)

    def test_alias_writer_does_not_own_connection_lifecycle(self):
        registry.save_repository_alias(self.connection, OLD, 0, OLD, "inactive", LATE)
        self.assertTrue(self.connection.in_transaction)
        self.assertEqual(self.connection.execute("SELECT repo_id FROM repository_aliases").fetchone(), (None,))
        self.connection.rollback()
        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM repository_aliases").fetchone(), (0,))

    def test_alias_writer_uses_explicit_merge_delegate_only_for_rename(self):
        merge = mock.Mock()
        registry.save_repository_alias(self.connection, OLD, 1, NEW, "renamed", LATE, merge_history=merge)
        merge.assert_called_once_with(self.connection, OLD, NEW)
        merge.reset_mock()
        registry.save_repository_alias(self.connection, OLD, 1, NEW, "inactive", LATE, merge_history=merge)
        merge.assert_not_called()

    def test_legacy_archiver_uses_explicit_history_delegate(self):
        self.connection.execute("INSERT INTO repository_aliases VALUES (?, NULL, ?, 'inactive', ?)", (OLD, OLD, EARLY))
        archive = mock.Mock()
        registry.archive_reused_legacy_aliases(self.connection, {OLD}, LATE, archive_history=archive)
        archive.assert_called_once_with(self.connection, OLD, f"{OLD} (archived legacy history)")

    def test_entry_point_reexports_history_functions_and_passes_patch_hooks(self):
        self.assertIs(app.merge_repository_history, registry.merge_repository_history)
        self.assertIs(app.archive_repository_history, registry.archive_repository_history)
        with mock.patch.object(app, "archive_repository_history") as archive:
            self.connection.execute("INSERT INTO repository_aliases VALUES (?, NULL, ?, 'inactive', ?)", (OLD, OLD, EARLY))
            app.archive_reused_legacy_aliases(self.connection, {OLD}, LATE)
        archive.assert_called_once_with(self.connection, OLD, f"{OLD} (archived legacy history)")

    def test_entry_point_passes_connection_and_history_hooks_to_storage(self):
        with mock.patch.object(app, "database_connection", return_value=nullcontext(self.connection)), \
             mock.patch.object(app, "reconcile_current_repositories", return_value=(set(), set())) as reconcile:
            app.reconcile_repository_registry([{"id": 1, "full_name": NEW, "created_at": EARLY}], LATE)
        reconcile.assert_called_once_with(
            self.connection, {1: NEW}, {1: EARLY}, {NEW}, LATE,
            merge_history=app.merge_repository_history,
            archive_history=app.archive_repository_history,
            archive_legacy_aliases=app.archive_reused_legacy_aliases,
        )
    def test_fresh_import_performs_no_io_and_loads_no_entry_point_or_provider(self):
        code = """
import pathlib, sqlite3, sys, threading
from unittest import mock
sys.path.insert(0, sys.argv[1])
with mock.patch.object(sqlite3, 'connect', side_effect=AssertionError('database opened')), \
     mock.patch.object(pathlib.Path, 'mkdir', side_effect=AssertionError('directory created')), \
     mock.patch.object(threading.Thread, 'start', side_effect=AssertionError('thread started')):
    from storage import registry
assert not any(name == 'app' or name.startswith('missing_link') for name in sys.modules)
assert pathlib.Path(registry.__file__).resolve().parent == pathlib.Path(sys.argv[1]).resolve() / 'storage'
"""
        result = subprocess.run([sys.executable, "-I", "-c", code, str(Path(app.__file__).parent)],
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
