"""Characterize database lifecycle and migrations using owned test databases."""
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import closing, nullcontext
from pathlib import Path
from unittest import mock

import app


LEGACY_TRAFFIC_SCHEMA = """
CREATE TABLE traffic_daily (
    repo TEXT NOT NULL, day TEXT NOT NULL, views INTEGER NOT NULL DEFAULT 0,
    unique_views INTEGER NOT NULL DEFAULT 0, clones INTEGER NOT NULL DEFAULT 0,
    unique_clones INTEGER NOT NULL DEFAULT 0, collected_at TEXT NOT NULL,
    PRIMARY KEY (repo, day)
);
"""


class DatabaseCharacterizationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.data_dir = self.root / "configured-data"
        self.path = self.root / "test.sqlite3"
        for name, value in (("DATA_DIR", self.data_dir), ("DB_PATH", self.path)):
            patch = mock.patch.object(app, name, value)
            patch.start()
            self.addCleanup(patch.stop)

    def schema(self):
        with closing(sqlite3.connect(self.path)) as connection:
            return connection.execute("SELECT type, name, tbl_name, sql FROM sqlite_master "
                                      "ORDER BY type, name").fetchall()

    def test_connection_is_lazy_and_reads_selected_path_when_entered(self):
        manager = app.database_connection()
        self.assertFalse(self.path.exists())
        selected = self.root / "second-account.sqlite3"
        with mock.patch.object(app, "DB_PATH", selected), manager as connection:
            connection.execute("CREATE TABLE fixture (value TEXT)")
            connection.execute("INSERT INTO fixture VALUES ('second account')")
        self.assertFalse(self.path.exists())
        with closing(sqlite3.connect(selected)) as reader:
            self.assertEqual(reader.execute("SELECT value FROM fixture").fetchall(), [("second account",)])

    def test_connection_commits_success_and_always_closes(self):
        with app.database_connection() as connection:
            connection.execute("CREATE TABLE fixture (value TEXT)")
            connection.execute("INSERT INTO fixture VALUES ('committed')")
            self.assertTrue(connection.in_transaction)
        with self.assertRaises(sqlite3.ProgrammingError):
            connection.execute("SELECT 1")
        with closing(sqlite3.connect(self.path)) as reader:
            self.assertEqual(reader.execute("SELECT value FROM fixture").fetchall(), [("committed",)])

    def test_connection_rolls_back_body_failure_and_preserves_original_exception(self):
        with app.database_connection() as connection:
            connection.execute("CREATE TABLE fixture (value TEXT)")
        failure = ValueError("caller failure")
        with self.assertRaises(ValueError) as raised:
            with app.database_connection() as connection:
                connection.execute("INSERT INTO fixture VALUES ('not committed')")
                raise failure
        self.assertIs(raised.exception, failure)
        with self.assertRaises(sqlite3.ProgrammingError):
            connection.execute("SELECT 1")
        with closing(sqlite3.connect(self.path)) as reader:
            self.assertEqual(reader.execute("SELECT * FROM fixture").fetchall(), [])

    def test_connection_keeps_default_sqlite_options(self):
        with app.database_connection() as connection:
            self.assertIsNone(connection.row_factory)
            self.assertEqual(connection.isolation_level, "")
            self.assertFalse(connection.in_transaction)
            self.assertEqual(connection.execute("PRAGMA busy_timeout").fetchone()[0], 5000)
            self.assertEqual(connection.execute("PRAGMA foreign_keys").fetchone()[0], 0)
            self.assertEqual(connection.execute("PRAGMA journal_mode").fetchone()[0], "delete")

    def test_connection_error_paths_keep_commit_rollback_close_order(self):
        for body_error, commit_error, rollback_error, expected in (
            (None, None, None, ["commit", "close"]),
            (ValueError("body"), None, None, ["rollback", "close"]),
            (None, sqlite3.OperationalError("commit"), None, ["commit", "rollback", "close"]),
            (ValueError("body"), None, RuntimeError("rollback"), ["rollback", "close"]),
            (KeyboardInterrupt(), None, None, ["close"]),
        ):
            with self.subTest(expected=expected, body_error=body_error):
                connection = mock.Mock()
                if commit_error:
                    connection.commit.side_effect = commit_error
                if rollback_error:
                    connection.rollback.side_effect = rollback_error
                with mock.patch.object(app.sqlite3, "connect", return_value=connection) as connect:
                    if body_error is None and commit_error is None:
                        with app.database_connection() as supplied:
                            self.assertIs(supplied, connection)
                    else:
                        expected_error = rollback_error or commit_error or body_error
                        with self.assertRaises(type(expected_error)) as raised:
                            with app.database_connection():
                                if body_error is not None:
                                    raise body_error
                        self.assertIs(raised.exception, expected_error)
                    connect.assert_called_once_with(self.path)
                self.assertEqual([call[0] for call in connection.mock_calls], expected)

    def test_connect_failure_is_not_retried_and_missing_parent_is_not_created(self):
        failure = sqlite3.OperationalError("cannot open")
        with mock.patch.object(app.sqlite3, "connect", side_effect=failure) as connect:
            with self.assertRaises(sqlite3.OperationalError) as raised:
                with app.database_connection():
                    self.fail("connection should not be yielded")
        self.assertIs(raised.exception, failure)
        connect.assert_called_once_with(self.path)
        missing = self.root / "missing-parent" / "test.sqlite3"
        with mock.patch.object(app, "DB_PATH", missing), self.assertRaises(sqlite3.OperationalError):
            with app.database_connection():
                self.fail("missing parent should not be created")
        self.assertFalse(missing.parent.exists())

    def test_ensure_creates_configured_directory_but_only_opens_selected_database(self):
        with mock.patch.object(app.sqlite3, "connect", wraps=sqlite3.connect) as connect:
            app.ensure_database()
        connect.assert_called_once_with(self.path)
        self.assertTrue(self.data_dir.is_dir())
        self.assertFalse((self.data_dir / "repotraction.sqlite3").exists())
        tables = {name for kind, name, _, _ in self.schema() if kind == "table"}
        self.assertEqual(tables, {"relation_snapshots", "traffic_daily", "traffic_snapshots",
            "relation_memberships", "relation_events", "repo_snapshots", "repository_registry",
            "repository_registry_state", "repository_aliases", "collection_runs",
            "repo_metadata_snapshots", "repository_events", "sqlite_sequence"})

    def test_ensure_idempotence_preserves_history_unknown_tables_and_sequences(self):
        app.ensure_database()
        with app.database_connection() as connection:
            connection.execute("INSERT INTO traffic_daily (repo, day, views, views_available, views_status, "
                "clones, clones_available, clones_status, collected_at) VALUES "
                "('octocat/project', '2026-08-10', 0, 1, 'observed_zero', 0, 1, 'observed_zero', '2026-08-11')")
            connection.execute("INSERT INTO repository_events (id, repo, event_type, title, occurred_at, detected_at, source) "
                               "VALUES (42, 'octocat/project', 'release', 'v1', '2026-08-10', '2026-08-11', 'fixture')")
            connection.execute("CREATE TABLE extension_history (value TEXT)")
            connection.execute("INSERT INTO extension_history VALUES ('preserve')")
            before = sorted(connection.iterdump())
        schema = self.schema()
        app.ensure_database()
        app.ensure_database()
        self.assertEqual(self.schema(), schema)
        with app.database_connection() as connection:
            self.assertEqual(sorted(connection.iterdump()), before)
            self.assertEqual(connection.execute("SELECT seq FROM sqlite_sequence WHERE name = 'repository_events'").fetchone()[0], 42)

    def test_old_traffic_schema_preserves_counts_and_only_marks_proven_nonzero_values(self):
        with closing(sqlite3.connect(self.path)) as connection:
            connection.executescript(LEGACY_TRAFFIC_SCHEMA)
            connection.executemany("INSERT INTO traffic_daily VALUES (?, '2026-08-10', ?, ?, ?, ?, '2026-08-11')", [
                ("octocat/zero", 0, 0, 0, 0), ("octocat/views", 10, 0, 0, 0),
                ("octocat/unique-views", 0, 2, 0, 0), ("octocat/clones", 0, 0, 8, 0),
                ("octocat/unique-clones", 0, 0, 0, 3)])
            connection.commit()
        app.ensure_database()
        with app.database_connection() as connection:
            rows = connection.execute("SELECT repo, views, unique_views, clones, unique_clones, "
                "views_available, views_status, clones_available, clones_status FROM traffic_daily ORDER BY repo").fetchall()
        self.assertEqual(rows, [
            ("octocat/clones", 0, 0, 8, 0, None, "missing", 1, "observed_value"),
            ("octocat/unique-clones", 0, 0, 0, 3, None, "missing", 1, "observed_value"),
            ("octocat/unique-views", 0, 2, 0, 0, 1, "observed_value", None, "missing"),
            ("octocat/views", 10, 0, 0, 0, 1, "observed_value", None, "missing"),
            ("octocat/zero", 0, 0, 0, 0, None, "missing", None, "missing")])

    def test_legacy_available_zeros_keep_values_but_lose_unproven_availability(self):
        with closing(sqlite3.connect(self.path)) as connection:
            connection.executescript(LEGACY_TRAFFIC_SCHEMA)
            connection.execute("ALTER TABLE traffic_daily ADD COLUMN views_available INTEGER")
            connection.execute("ALTER TABLE traffic_daily ADD COLUMN clones_available INTEGER")
            connection.execute("INSERT INTO traffic_daily VALUES ('octocat/project', '2026-08-10', 0, 0, 0, 0, '2026-08-11', 1, 1)")
            connection.commit()
        app.ensure_database()
        with app.database_connection() as connection:
            self.assertEqual(connection.execute("SELECT views, clones, views_available, views_status, "
                "clones_available, clones_status FROM traffic_daily").fetchall(),
                [(0, 0, None, "legacy_unknown", None, "legacy_unknown")])
        app.ensure_database()
        with app.database_connection() as connection:
            self.assertEqual(connection.execute("SELECT views_available, clones_available FROM traffic_daily").fetchall(), [(None, None)])

    def test_explicit_provenance_is_not_overwritten_by_migration(self):
        app.ensure_database()
        with app.database_connection() as connection:
            connection.executemany("INSERT INTO traffic_daily (repo, day, views, views_available, views_status, "
                "clones, clones_available, clones_status, collected_at) VALUES "
                "(?, '2026-08-10', ?, ?, ?, ?, ?, ?, '2026-08-11')", [
                ("octocat/observed-zero", 0, 1, "observed_zero", 0, 1, "observed_zero"),
                ("octocat/missing", 5, 0, "missing", 8, 0, "missing"),
                ("octocat/legacy", 0, 1, "legacy_unknown", 0, 1, "legacy_unknown")])
        app.ensure_database()
        with app.database_connection() as connection:
            rows = connection.execute("SELECT repo, views_available, views_status, clones_available, clones_status "
                                      "FROM traffic_daily ORDER BY repo").fetchall()
        self.assertEqual(rows, [("octocat/legacy", None, "legacy_unknown", None, "legacy_unknown"),
            ("octocat/missing", 0, "missing", 0, "missing"),
            ("octocat/observed-zero", 1, "observed_zero", 1, "observed_zero")])

    def test_legacy_registry_and_run_migrations_keep_rows_and_initialization(self):
        with closing(sqlite3.connect(self.path)) as connection:
            connection.executescript("""
                CREATE TABLE repository_registry (repo_id INTEGER PRIMARY KEY, full_name TEXT NOT NULL UNIQUE,
                    active INTEGER NOT NULL DEFAULT 1, first_seen_at TEXT NOT NULL, last_seen_at TEXT NOT NULL);
                INSERT INTO repository_registry VALUES (7, 'octocat/project', 1, 'first', 'last');
                CREATE TABLE collection_runs (started_at TEXT PRIMARY KEY, completed_at TEXT,
                    repos_total INTEGER NOT NULL DEFAULT 0, repos_completed INTEGER NOT NULL DEFAULT 0,
                    errors INTEGER NOT NULL DEFAULT 0, status TEXT NOT NULL);
                INSERT INTO collection_runs VALUES ('started', 'completed', 3, 2, 1, 'partial');
            """)
        app.ensure_database()
        with app.database_connection() as connection:
            self.assertEqual(connection.execute("SELECT * FROM repository_registry").fetchall(),
                             [(7, "octocat/project", None, 1, "first", "last")])
            self.assertEqual(connection.execute("SELECT * FROM collection_runs").fetchall(),
                             [("started", "completed", 3, 2, 1, "partial", "[]")])
            self.assertEqual(connection.execute("SELECT initialized FROM repository_registry_state").fetchone(), (1,))
            self.assertIsNone(connection.execute("SELECT name FROM sqlite_master WHERE name='repository_registry_legacy'").fetchone())

    def test_registry_unique_index_only_restricts_active_case_insensitive_names(self):
        app.ensure_database()
        with app.database_connection() as connection:
            connection.execute("INSERT INTO repository_registry VALUES (1, 'Octocat/Project', NULL, 1, 'first', 'last')")
            connection.execute("INSERT INTO repository_registry VALUES (2, 'octocat/project', NULL, 0, 'first', 'last')")
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute("INSERT INTO repository_registry VALUES (3, 'OCTOCAT/PROJECT', NULL, 1, 'first', 'last')")
        app.ensure_database()
        with app.database_connection() as connection:
            self.assertEqual(connection.execute("SELECT repo_id, active FROM repository_registry ORDER BY repo_id").fetchall(), [(1, 1), (2, 0)])

    def test_empty_registry_state_stays_uninitialized_until_existing_run_is_seen(self):
        app.ensure_database()
        with app.database_connection() as connection:
            self.assertEqual(connection.execute("SELECT * FROM repository_registry_state").fetchall(), [(1, 0)])
            connection.execute("INSERT INTO collection_runs (started_at, status) VALUES ('fixture', 'partial')")
        app.ensure_database()
        with app.database_connection() as connection:
            self.assertEqual(connection.execute("SELECT * FROM repository_registry_state").fetchall(), [(1, 1)])

    def test_migration_failure_rolls_back_and_closes_without_retry(self):
        connection = mock.Mock()
        failure = sqlite3.OperationalError("schema failure")
        connection.executescript.side_effect = failure
        with mock.patch.object(app.sqlite3, "connect", return_value=connection) as connect:
            with self.assertRaises(sqlite3.OperationalError) as raised:
                app.ensure_database()
        self.assertIs(raised.exception, failure)
        connect.assert_called_once_with(self.path)
        self.assertEqual([call[0] for call in connection.mock_calls], ["executescript", "rollback", "close"])

    def test_two_selected_account_databases_do_not_share_history(self):
        paths = [app.account_database_path(login, self.root) for login in ("Octocat", "Other")]
        for path, value in zip(paths, ("first account", "second account")):
            with mock.patch.object(app, "DB_PATH", path):
                app.ensure_database()
                with app.database_connection() as connection:
                    connection.execute("INSERT INTO collection_runs (started_at, status) VALUES (?, 'complete')", (value,))
        for path, expected in zip(paths, ("first account", "second account")):
            with closing(sqlite3.connect(path)) as connection:
                self.assertEqual(connection.execute("SELECT started_at FROM collection_runs").fetchall(), [(expected,)])

    def test_failed_migration_keeps_existing_script_transaction_semantics(self):
        with closing(sqlite3.connect(self.path)) as connection:
            connection.execute("CREATE TABLE traffic_daily (repo TEXT, day TEXT)")
            connection.execute("INSERT INTO traffic_daily VALUES ('preserve', '2026-08-10')")
            connection.commit()
        with self.assertRaises(sqlite3.OperationalError):
            app.ensure_database()
        with closing(sqlite3.connect(self.path)) as connection:
            self.assertEqual(connection.execute("SELECT repo, day FROM traffic_daily").fetchall(),
                             [("preserve", "2026-08-10")])
            # executescript/DDL may persist before a later migration fails. The
            # extraction must not silently introduce a different atomicity model.
            self.assertIsNotNone(connection.execute("SELECT name FROM sqlite_master "
                "WHERE name = 'relation_snapshots'").fetchone())
            columns = {row[1] for row in connection.execute("PRAGMA table_info(traffic_daily)")}
            self.assertTrue({"views_available", "clones_available"}.issubset(columns))


class ExtractedStorageTests(unittest.TestCase):
    def test_connection_adapter_delegates_current_path_and_lifecycle(self):
        from storage import database
        self.assertIs(app.open_database_connection, database.database_connection)
        with tempfile.TemporaryDirectory() as temporary:
            selected = Path(temporary) / "selected.sqlite3"
            with mock.patch.object(app, "DB_PATH", selected), \
                 mock.patch.object(app, "open_database_connection", wraps=database.database_connection) as delegate:
                with app.database_connection() as connection:
                    connection.execute("CREATE TABLE fixture (value TEXT)")
                    connection.execute("INSERT INTO fixture VALUES ('committed')")
            delegate.assert_called_once_with(selected)
            with closing(sqlite3.connect(selected)) as reader:
                self.assertEqual(reader.execute("SELECT value FROM fixture").fetchall(), [("committed",)])

    def test_ensure_retains_patchable_connection_factory_and_supplies_connection_only(self):
        from storage import migrations
        self.assertIs(app.migrate_database, migrations.migrate_database)
        connection = mock.sentinel.connection
        with tempfile.TemporaryDirectory() as temporary:
            data_dir = Path(temporary) / "data"
            unused_path = data_dir / "not-opened.sqlite3"
            with mock.patch.object(app, "DATA_DIR", data_dir), \
                 mock.patch.object(app, "DB_PATH", unused_path), \
                 mock.patch.object(app, "database_connection", return_value=nullcontext(connection)) as factory, \
                 mock.patch.object(app, "migrate_database") as migrate:
                app.ensure_database()
            factory.assert_called_once_with()
            migrate.assert_called_once_with(connection)
            self.assertTrue(data_dir.is_dir())
            self.assertFalse(unused_path.exists())

    def test_direct_connection_uses_explicit_path_despite_entrypoint_state(self):
        from storage import database
        with tempfile.TemporaryDirectory() as temporary:
            supplied = Path(temporary) / "supplied.sqlite3"
            wrong = Path(temporary) / "entrypoint.sqlite3"
            with mock.patch.object(app, "DB_PATH", wrong), database.database_connection(supplied) as connection:
                connection.execute("CREATE TABLE fixture (value TEXT)")
            self.assertTrue(supplied.exists())
            self.assertFalse(wrong.exists())
            with self.assertRaises(sqlite3.ProgrammingError):
                connection.execute("SELECT 1")

    def test_direct_connection_rollback_closes_and_does_not_commit_failed_write(self):
        from storage import database
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "fixture.sqlite3"
            with database.database_connection(path) as connection:
                connection.execute("CREATE TABLE fixture (value TEXT)")
            with self.assertRaisesRegex(ValueError, "caller failure"):
                with database.database_connection(path) as connection:
                    connection.execute("INSERT INTO fixture VALUES ('uncommitted')")
                    raise ValueError("caller failure")
            with self.assertRaises(sqlite3.ProgrammingError):
                connection.execute("SELECT 1")
            with closing(sqlite3.connect(path)) as reader:
                self.assertEqual(reader.execute("SELECT * FROM fixture").fetchall(), [])

    def test_migration_does_not_explicitly_manage_supplied_connection_lifecycle(self):
        from storage import migrations
        connection = mock.Mock()
        connection.execute.return_value = mock.MagicMock()
        connection.execute.return_value.fetchone.return_value = None
        migrations.migrate_database(connection)
        connection.executescript.assert_called_once()
        self.assertGreater(connection.execute.call_count, 10)
        connection.commit.assert_not_called()
        connection.rollback.assert_not_called()
        connection.close.assert_not_called()

    def test_direct_migration_keeps_caller_row_factory_and_connection_open(self):
        from storage import migrations
        with closing(sqlite3.connect(":memory:")) as connection:
            connection.row_factory = sqlite3.Row
            migrations.migrate_database(connection)
            self.assertIs(connection.row_factory, sqlite3.Row)
            self.assertTrue(connection.in_transaction)
            connection.execute("CREATE TABLE extension_history (value TEXT)")
            connection.execute("INSERT INTO extension_history VALUES ('preserve')")
            migrations.migrate_database(connection)
            self.assertEqual(connection.execute("SELECT value FROM extension_history").fetchone()[0], "preserve")

    def test_closed_connection_failure_never_opens_replacement_database(self):
        from storage import migrations
        connection = sqlite3.connect(":memory:")
        connection.close()
        with mock.patch.object(sqlite3, "connect", side_effect=AssertionError("unexpected reconnect")):
            with self.assertRaises(sqlite3.ProgrammingError):
                migrations.migrate_database(connection)

    def test_fresh_storage_imports_do_not_access_disk_account_provider_clock_or_network(self):
        code = """
import sqlite3
import sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, sys.argv[1])
connection = sqlite3.connect(':memory:')
try:
    with patch('sqlite3.connect', side_effect=AssertionError('implicit database open')), \\
         patch.object(Path, 'mkdir', side_effect=AssertionError('directory creation')), \\
         patch('threading.Thread.start', side_effect=AssertionError('thread start')), \\
         patch('subprocess.run', side_effect=AssertionError('external command')), \\
         patch('socket.create_connection', side_effect=AssertionError('network access')), \\
         patch('time.time', side_effect=AssertionError('wall clock access')):
        from storage import database, migrations
        migrations.migrate_database(connection)
        assert connection.execute('SELECT initialized FROM repository_registry_state').fetchone() == (0,)
        assert connection.in_transaction
        assert 'app' not in sys.modules
        assert not any(name == 'missing_link' or name.startswith('missing_link.') for name in sys.modules)
finally:
    connection.close()
"""
        result = subprocess.run([sys.executable, "-I", "-c", code, str(Path(__file__).resolve().parents[1])],
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
