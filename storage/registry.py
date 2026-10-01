"""Repository registry SQL; callers supply connections and own transactions."""
from __future__ import annotations

import sqlite3
from collections.abc import Callable
from typing import Any

HistoryMover = Callable[[sqlite3.Connection, str, str], None]
LegacyArchiver = Callable[[sqlite3.Connection, set[str], str], None]


def merge_repository_history(
    connection: sqlite3.Connection,
    old_name: str,
    canonical_name: str,
) -> None:
    """Move an old repository name onto its current canonical GitHub name."""
    if old_name.casefold() == canonical_name.casefold():
        return

    connection.row_factory = sqlite3.Row
    traffic_rows = connection.execute(
        """
        SELECT day, views, unique_views, views_available, views_status, clones,
               unique_clones, clones_available, clones_status, collected_at
        FROM traffic_daily
        WHERE repo = ?
        """,
        (old_name,),
    ).fetchall()
    for row in traffic_rows:
        current = connection.execute(
            """
            SELECT collected_at, views_available, clones_available
            FROM traffic_daily
            WHERE repo = ? AND day = ?
            """,
            (canonical_name, row["day"]),
        ).fetchone()
        if current is None:
            connection.execute(
                "UPDATE traffic_daily SET repo = ? WHERE repo = ? AND day = ?",
                (canonical_name, old_name, row["day"]),
            )
        else:
            updates: list[str] = []
            values: list[Any] = []
            old_is_newer = str(row["collected_at"]) > str(current["collected_at"])
            if row["views_available"] == 1 and (
                current["views_available"] != 1 or old_is_newer
            ):
                # Provenance belongs to the selected observation, not its old name.
                updates.extend(("views = ?", "unique_views = ?", "views_available = 1", "views_status = ?"))
                values.extend((row["views"], row["unique_views"], row["views_status"]))
            if row["clones_available"] == 1 and (
                current["clones_available"] != 1 or old_is_newer
            ):
                updates.extend(("clones = ?", "unique_clones = ?", "clones_available = 1", "clones_status = ?"))
                values.extend((row["clones"], row["unique_clones"], row["clones_status"]))
            updates.append("collected_at = MAX(collected_at, ?)")
            values.extend((row["collected_at"], canonical_name, row["day"]))
            connection.execute(
                f"UPDATE traffic_daily SET {', '.join(updates)} WHERE repo = ? AND day = ?",  # noqa: S608 - assignments are fixed above
                values,
            )
            connection.execute(
                "DELETE FROM traffic_daily WHERE repo = ? AND day = ?",
                (old_name, row["day"]),
            )

    for table, fields in (
        (
            "traffic_snapshots",
            "collected_at, views_count, views_uniques, clones_count, clones_uniques",
        ),
        (
            "repo_snapshots",
            "collected_at, stars, forks, watchers, open_issues, private, archived, language, pushed_at",
        ),
        (
            "repo_metadata_snapshots",
            "collected_at, description, homepage, topics_json, license_id, license_status",
        ),
        (
            "repository_events",
            "event_type, title, occurred_at, detected_at, source, metadata_json",
        ),
    ):
        rows = connection.execute(
            f"SELECT {fields} FROM {table} WHERE repo = ?",  # noqa: S608 - fixed table names
            (old_name,),
        ).fetchall()
        field_names = [field.strip() for field in fields.split(",")]
        placeholders = ", ".join("?" for _ in range(len(field_names) + 1))
        columns = ", ".join(["repo", *field_names])
        for row in rows:
            values = [canonical_name, *(row[field] for field in field_names)]
            connection.execute(
                f"INSERT OR IGNORE INTO {table} ({columns}) VALUES ({placeholders})",  # noqa: S608 - fixed table names
                values,
            )
        connection.execute(
            f"DELETE FROM {table} WHERE repo = ?",  # noqa: S608 - fixed table names
            (old_name,),
        )


def archive_repository_history(
    connection: sqlite3.Connection,
    repo_name: str,
    archive_name: str,
) -> None:
    """Keep a deleted repository's history separate if its name is reused."""
    for table in (
        "traffic_daily",
        "traffic_snapshots",
        "repo_snapshots",
        "repo_metadata_snapshots",
        "repository_events",
    ):
        connection.execute(
            f"UPDATE {table} SET repo = ? WHERE repo = ?",  # noqa: S608 - fixed table names
            (archive_name, repo_name),
        )


def archive_reused_legacy_aliases(
    connection: sqlite3.Connection,
    current_names: set[str],
    collected_at: str,
    *,
    archive_history: HistoryMover = archive_repository_history,
) -> None:
    """Keep ID-less legacy history separate when its old name is reused."""
    aliases = connection.execute(
        """SELECT alias FROM repository_aliases
           WHERE repo_id IS NULL AND status = 'inactive'"""
    ).fetchall()
    for row in aliases:
        alias = str(row[0])
        if alias.casefold() not in current_names:
            continue
        archive_name = f"{alias} (archived legacy history)"
        archive_history(connection, alias, archive_name)
        connection.execute(
            """UPDATE repository_aliases
               SET canonical_name = ?, status = 'reused', resolved_at = ?
               WHERE alias = ?""",
            (archive_name, collected_at, alias),
        )


def reconcile_current_repositories(
    connection: sqlite3.Connection,
    current_by_id: dict[int, str],
    created_at_by_id: dict[int, str | None],
    current_names: set[str],
    collected_at: str,
    *,
    merge_history: HistoryMover = merge_repository_history,
    archive_history: HistoryMover = archive_repository_history,
    archive_legacy_aliases: LegacyArchiver = archive_reused_legacy_aliases,
) -> tuple[set[str], set[str]]:
    """Update current IDs and return historical names and known aliases.

    This does not resolve aliases through GitHub or commit/close the connection.
    Supplied history delegates retain entry-point patch hooks during migration.
    """
    connection.row_factory = sqlite3.Row
    connection.execute("UPDATE repository_registry SET active = 0")
    archive_legacy_aliases(connection, current_names, collected_at)
    for repo_id, full_name in current_by_id.items():
        previous_ids = connection.execute(
            """SELECT repo_id, full_name FROM repository_registry
                   WHERE full_name = ? COLLATE NOCASE AND repo_id <> ?""",
            (full_name, repo_id),
        ).fetchall()
        for previous_id_row in previous_ids:
            previous_id = int(previous_id_row[0])
            former_name = str(previous_id_row[1])
            archive_name = (
                f"{former_name} (archived repository id {previous_id})"
            )
            archive_history(
                connection,
                former_name,
                archive_name,
            )
            connection.execute(
                "UPDATE repository_registry SET full_name = ? WHERE repo_id = ?",
                (archive_name, previous_id),
            )

        previous = connection.execute(
            "SELECT full_name FROM repository_registry WHERE repo_id = ?",
            (repo_id,),
        ).fetchone()
        if previous and str(previous["full_name"]).casefold() != full_name.casefold():
            old_name = str(previous["full_name"])
            merge_history(connection, old_name, full_name)
            connection.execute(
                """
                    INSERT OR REPLACE INTO repository_aliases (
                        alias, repo_id, canonical_name, status, resolved_at
                    ) VALUES (?, ?, ?, 'renamed', ?)
                    """,
                (old_name, repo_id, full_name, collected_at),
            )
        connection.execute(
            """
                INSERT INTO repository_registry (
                    repo_id, full_name, created_at, active, first_seen_at, last_seen_at
                ) VALUES (?, ?, ?, 1, ?, ?)
                ON CONFLICT(repo_id) DO UPDATE SET
                    full_name = excluded.full_name,
                    created_at = COALESCE(excluded.created_at, repository_registry.created_at),
                    active = 1,
                    last_seen_at = excluded.last_seen_at
                """,
            (
                repo_id,
                full_name,
                created_at_by_id.get(repo_id),
                collected_at,
                collected_at,
            ),
        )

    connection.execute(
        "UPDATE repository_registry_state SET initialized = 1 WHERE singleton = 1"
    )

    historical_names = {
        str(row[0])
        for row in connection.execute(
            """
                SELECT repo FROM traffic_daily
                UNION SELECT repo FROM traffic_snapshots
                UNION SELECT repo FROM repo_snapshots
                """
        ).fetchall()
    }
    known_aliases = {
        str(row[0]).casefold()
        for row in connection.execute("SELECT alias FROM repository_aliases")
    }
    return historical_names, known_aliases


def save_repository_alias(
    connection: sqlite3.Connection,
    old_name: str,
    repo_id: int,
    canonical_name: str,
    status: str,
    collected_at: str,
    *,
    merge_history: HistoryMover = merge_repository_history,
) -> None:
    """Persist one resolved alias within the caller's transaction."""
    if status == "renamed":
        merge_history(connection, old_name, canonical_name)
    connection.execute(
        """
                INSERT OR REPLACE INTO repository_aliases (
                    alias, repo_id, canonical_name, status, resolved_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
        (
            old_name,
            repo_id or None,
            canonical_name,
            status,
            collected_at,
        ),
    )


def read_active_repository_rows(
    connection: sqlite3.Connection,
) -> list[Any] | None:
    """Return active-name rows, or None until registry initialization."""
    initialized = connection.execute(
        "SELECT initialized FROM repository_registry_state WHERE singleton = 1"
    ).fetchone()
    if not initialized or not bool(initialized[0]):
        return None
    rows = connection.execute(
        "SELECT full_name FROM repository_registry WHERE active = 1"
    ).fetchall()
    return rows
