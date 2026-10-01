"""Existing SQLite schema updates; the caller owns the connection lifecycle."""
from __future__ import annotations

import sqlite3


def migrate_database(connection: sqlite3.Connection) -> None:
    """Apply existing schema/migrations without selecting an account or path.

    This function does not commit, roll back or close the supplied connection.
    SQLite executescript/DDL transaction semantics are retained, so callers must
    not assume all migration steps are atomic. No stored history is reset.
    """
    connection.executescript(
        """
            CREATE TABLE IF NOT EXISTS relation_snapshots (
                collected_at TEXT PRIMARY KEY,
                followers INTEGER NOT NULL,
                following INTEGER NOT NULL,
                mutual INTEGER NOT NULL,
                not_following_back INTEGER NOT NULL,
                followers_not_followed INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS traffic_daily (
                repo TEXT NOT NULL,
                day TEXT NOT NULL,
                views INTEGER NOT NULL DEFAULT 0,
                unique_views INTEGER NOT NULL DEFAULT 0,
                views_available INTEGER,
                views_status TEXT NOT NULL DEFAULT 'missing',
                clones INTEGER NOT NULL DEFAULT 0,
                unique_clones INTEGER NOT NULL DEFAULT 0,
                clones_available INTEGER,
                clones_status TEXT NOT NULL DEFAULT 'missing',
                collected_at TEXT NOT NULL,
                PRIMARY KEY (repo, day)
            );

            CREATE TABLE IF NOT EXISTS traffic_snapshots (
                repo TEXT NOT NULL,
                collected_at TEXT NOT NULL,
                views_count INTEGER,
                views_uniques INTEGER,
                clones_count INTEGER,
                clones_uniques INTEGER,
                PRIMARY KEY (repo, collected_at)
            );

            CREATE TABLE IF NOT EXISTS relation_memberships (
                login TEXT NOT NULL,
                kind TEXT NOT NULL,
                avatar_url TEXT NOT NULL DEFAULT '',
                html_url TEXT NOT NULL DEFAULT '',
                first_seen_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1,
                PRIMARY KEY (login, kind)
            );

            CREATE TABLE IF NOT EXISTS relation_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                collected_at TEXT NOT NULL,
                login TEXT NOT NULL,
                avatar_url TEXT NOT NULL DEFAULT '',
                html_url TEXT NOT NULL DEFAULT '',
                event_type TEXT NOT NULL,
                UNIQUE (collected_at, login, event_type)
            );

            CREATE TABLE IF NOT EXISTS repo_snapshots (
                repo TEXT NOT NULL,
                collected_at TEXT NOT NULL,
                stars INTEGER NOT NULL DEFAULT 0,
                forks INTEGER NOT NULL DEFAULT 0,
                watchers INTEGER NOT NULL DEFAULT 0,
                open_issues INTEGER NOT NULL DEFAULT 0,
                private INTEGER NOT NULL DEFAULT 0,
                archived INTEGER NOT NULL DEFAULT 0,
                language TEXT NOT NULL DEFAULT '',
                pushed_at TEXT NOT NULL DEFAULT '',
                PRIMARY KEY (repo, collected_at)
            );

            CREATE TABLE IF NOT EXISTS repository_registry (
                repo_id INTEGER PRIMARY KEY,
                full_name TEXT NOT NULL,
                created_at TEXT,
                active INTEGER NOT NULL DEFAULT 1,
                first_seen_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS repository_registry_state (
                singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
                initialized INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS repository_aliases (
                alias TEXT PRIMARY KEY,
                repo_id INTEGER,
                canonical_name TEXT NOT NULL,
                status TEXT NOT NULL,
                resolved_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS collection_runs (
                started_at TEXT PRIMARY KEY,
                completed_at TEXT,
                repos_total INTEGER NOT NULL DEFAULT 0,
                repos_completed INTEGER NOT NULL DEFAULT 0,
                errors INTEGER NOT NULL DEFAULT 0,
                error_details TEXT NOT NULL DEFAULT '[]',
                status TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS repo_metadata_snapshots (
                repo TEXT NOT NULL,
                collected_at TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                homepage TEXT NOT NULL DEFAULT '',
                topics_json TEXT NOT NULL DEFAULT '[]',
                license_id TEXT NOT NULL DEFAULT '',
                license_status TEXT NOT NULL DEFAULT 'missing',
                PRIMARY KEY (repo, collected_at)
            );

            CREATE TABLE IF NOT EXISTS repository_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                repo TEXT NOT NULL,
                event_type TEXT NOT NULL,
                title TEXT NOT NULL,
                occurred_at TEXT NOT NULL,
                detected_at TEXT NOT NULL,
                source TEXT NOT NULL,
                metadata_json TEXT NOT NULL DEFAULT '{}',
                UNIQUE (repo, event_type, title, occurred_at)
            );

            CREATE INDEX IF NOT EXISTS idx_relation_events_time
                ON relation_events (collected_at DESC);
            CREATE INDEX IF NOT EXISTS idx_repo_snapshots_repo_time
                ON repo_snapshots (repo, collected_at DESC);
            CREATE INDEX IF NOT EXISTS idx_traffic_snapshots_repo_time
                ON traffic_snapshots (repo, collected_at DESC);
            CREATE INDEX IF NOT EXISTS idx_repository_events_time
                ON repository_events (occurred_at DESC, repo);
            CREATE INDEX IF NOT EXISTS idx_repo_metadata_repo_time
                ON repo_metadata_snapshots (repo, collected_at DESC);
            """
    )

    traffic_columns = {
        str(row[1]) for row in connection.execute("PRAGMA table_info(traffic_daily)")
    }
    for column in ("views_available", "clones_available"):
        if column not in traffic_columns:
            connection.execute(
                f"ALTER TABLE traffic_daily ADD COLUMN {column} INTEGER"  # noqa: S608
            )
    connection.execute(
        """UPDATE traffic_daily SET views_available = 1
               WHERE views_available IS NULL
                 AND (views <> 0 OR unique_views <> 0)"""
    )
    connection.execute(
        """UPDATE traffic_daily SET clones_available = 1
               WHERE clones_available IS NULL
                 AND (clones <> 0 OR unique_clones <> 0)"""
    )

    traffic_columns = {
        str(row[1]) for row in connection.execute("PRAGMA table_info(traffic_daily)")
    }
    for column in ("views_status", "clones_status"):
        if column not in traffic_columns:
            connection.execute(
                f"ALTER TABLE traffic_daily ADD COLUMN {column} TEXT"  # noqa: S608
            )
    # Historical available zeroes have no provenance: earlier versions also
    # synthesized them when GitHub returned an empty daily array. Keep their
    # values for audit/export, but remove them from evidentiary queries until
    # a fresh daily bucket is observed.
    for metric, available_column, value_column, unique_column in (
        ("views", "views_available", "views", "unique_views"),
        ("clones", "clones_available", "clones", "unique_clones"),
    ):
        connection.execute(
            f"""UPDATE traffic_daily
                    SET {metric}_status = CASE
                        WHEN {available_column} = 1
                         AND ({value_column} <> 0 OR {unique_column} <> 0)
                            THEN 'observed_value'
                        WHEN {available_column} = 1 THEN 'legacy_unknown'
                        ELSE 'missing'
                    END
                    WHERE {metric}_status IS NULL""",  # noqa: S608
        )
        connection.execute(
            f"""UPDATE traffic_daily SET {available_column} = NULL
                    WHERE {metric}_status = 'legacy_unknown'""",  # noqa: S608
        )

    registry_columns = {
        str(row[1]) for row in connection.execute("PRAGMA table_info(repository_registry)")
    }
    if "created_at" not in registry_columns:
        connection.execute("ALTER TABLE repository_registry ADD COLUMN created_at TEXT")

    run_columns = {
        str(row[1]) for row in connection.execute("PRAGMA table_info(collection_runs)")
    }
    if "error_details" not in run_columns:
        connection.execute(
            "ALTER TABLE collection_runs ADD COLUMN error_details TEXT NOT NULL DEFAULT '[]'"
        )

    registry_schema = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'repository_registry'"
    ).fetchone()
    if registry_schema and "full_name TEXT NOT NULL UNIQUE" in str(registry_schema[0]):
        connection.execute(
            "ALTER TABLE repository_registry RENAME TO repository_registry_legacy"
        )
        connection.execute(
            """CREATE TABLE repository_registry (
                    repo_id INTEGER PRIMARY KEY,
                    full_name TEXT NOT NULL,
                    created_at TEXT,
                    active INTEGER NOT NULL DEFAULT 1,
                    first_seen_at TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL
                )"""
        )
        connection.execute(
            """INSERT INTO repository_registry (
                    repo_id, full_name, created_at, active, first_seen_at, last_seen_at
                ) SELECT repo_id, full_name, created_at, active, first_seen_at, last_seen_at
                  FROM repository_registry_legacy"""
        )
        connection.execute("DROP TABLE repository_registry_legacy")

    connection.execute(
        "INSERT OR IGNORE INTO repository_registry_state (singleton, initialized) VALUES (1, 0)"
    )
    connection.execute(
        """UPDATE repository_registry_state SET initialized = 1
               WHERE singleton = 1 AND (
                   EXISTS (SELECT 1 FROM repository_registry)
                   OR EXISTS (SELECT 1 FROM collection_runs)
               )"""
    )
    connection.execute("DROP INDEX IF EXISTS idx_repository_registry_active")
    connection.execute(
        "CREATE INDEX idx_repository_registry_active ON repository_registry (active, full_name)"
    )
    connection.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_repository_registry_active_name "
        "ON repository_registry (full_name COLLATE NOCASE) WHERE active = 1"
    )
