"""Repository snapshots and event writes with explicit connection ownership."""
from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable
from typing import Any


def save_repo_snapshots(
    connection: sqlite3.Connection,
    repositories: list[dict[str, Any]],
    collected_at: str,
) -> None:
    """Write counter snapshots; the caller owns commit, rollback and closure."""
    connection.executemany(
        """
            INSERT OR REPLACE INTO repo_snapshots (
                repo, collected_at, stars, forks, watchers, open_issues,
                private, archived, language, pushed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
        (
            (
                repo["full_name"],
                collected_at,
                int(repo.get("stars", 0)),
                int(repo.get("forks", 0)),
                int(repo.get("watchers", 0)),
                int(repo.get("open_issues", 0)),
                int(bool(repo.get("private"))),
                int(bool(repo.get("archived"))),
                repo.get("language") or "",
                repo.get("pushed_at") or "",
            )
            for repo in repositories
        ),
    )


def record_repository_event(
    connection: sqlite3.Connection,
    *,
    repo: str,
    event_type: str,
    title: str,
    occurred_at: str,
    source: str,
    metadata: dict[str, Any] | None = None,
    detected_at: str | None = None,
    validate_repo: Callable[[str], str],
    utc_now: Callable[[], str],
) -> bool:
    cursor = connection.execute(
        """
        INSERT OR IGNORE INTO repository_events (
            repo, event_type, title, occurred_at, detected_at, source,
            metadata_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            validate_repo(repo),
            event_type,
            title,
            occurred_at,
            detected_at or utc_now(),
            source,
            json.dumps(metadata or {}, sort_keys=True, separators=(",", ":")),
        ),
    )
    return cursor.rowcount > 0


def save_repo_metadata_snapshots(
    connection: sqlite3.Connection,
    repositories: list[dict[str, Any]],
    collected_at: str,
    *,
    validate_repo: Callable[[str], str],
    record_event: Callable[..., bool],
) -> int:
    """Write metadata and detected changes in the caller's transaction."""
    events_created = 0
    connection.row_factory = sqlite3.Row
    for repo in repositories:
        full_name = validate_repo(str(repo["full_name"]))
        current = {
            "description": str(repo.get("description") or ""),
            "homepage": str(repo.get("homepage") or ""),
            "topics_json": json.dumps(
                sorted(str(topic) for topic in (repo.get("topics") or [])),
                separators=(",", ":"),
            ),
            "license_id": str(repo.get("license") or ""),
            "license_status": str(repo.get("license_status") or "missing"),
        }
        previous = connection.execute(
            """
                SELECT description, homepage, topics_json, license_id,
                       license_status
                FROM repo_metadata_snapshots
                WHERE repo = ?
                ORDER BY collected_at DESC
                LIMIT 1
                """,
            (full_name,),
        ).fetchone()
        changes = [
            field
            for field, value in current.items()
            if previous is not None and str(previous[field]) != value
        ]
        connection.execute(
            """
                INSERT OR REPLACE INTO repo_metadata_snapshots (
                    repo, collected_at, description, homepage, topics_json,
                    license_id, license_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
            (full_name, collected_at, *current.values()),
        )
        if changes and record_event(
            connection,
            repo=full_name,
            event_type="metadata",
            title="Repository metadata updated",
            occurred_at=collected_at,
            detected_at=collected_at,
            source="repository_snapshot",
            metadata={"changed_fields": changes},
        ):
            events_created += 1
    return events_created
