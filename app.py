from __future__ import annotations

import argparse
import csv
import ipaddress
import io
import json
import math
import re
import shutil
import sqlite3
import subprocess
import threading
import time
import webbrowser
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

# Compatibility names during migration; calculation bodies live in analytics.
from analytics.events import (
    _utc_date,
    build_event_metric_result,
    describe_event_outcome,
)
from analytics.opportunities import build_repository_opportunities, rank_opportunities
from analytics.repositories import (
    build_adoption_signal,
    repository_health as calculate_repository_health,
    repository_license_metadata,
)
from analytics.traffic import (
    parse_utc_timestamp,
    percentage_change,
    select_comparison_window,
    summarize_traffic_period,
    traffic_period_label,
)


APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"
DATA_DIR = APP_DIR / "data"
APP_NAME = "RepoTraction"
APP_SLUG = "repotraction"
LEGACY_APP_SLUG = "github-pulse"
LEGACY_DB_PATH = DATA_DIR / f"{LEGACY_APP_SLUG}.sqlite3"
DB_PATH = DATA_DIR / f"{APP_SLUG}.sqlite3"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
GITHUB_API_VERSION = "2022-11-28"
REPO_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
LOGIN_PATTERN = re.compile(r"^[A-Za-z0-9-]{1,39}$")
COLLECTION_INTERVAL_SECONDS = 24 * 60 * 60
COLLECTION_STALE_SECONDS = 20 * 60 * 60
ACCOUNT_CHECK_INTERVAL_SECONDS = 5
ACCOUNT_LOGIN: str | None = None
_ACCOUNT_CHECK_LOCK = threading.Lock()
_ACCOUNT_CHECKED_AT = 0.0
GH_REQUEST_SEMAPHORE = threading.BoundedSemaphore(4)
_MISSING_LINK_LOCK = threading.Lock()
_MISSING_LINK_SERVICES: dict[tuple[str, str], Any] = {}


def missing_link_service() -> Any:
    """Lazy optional feature; analytics and collect-only never load its provider."""
    from missing_link.service import Service

    account = get_account_login()
    verify_active_account()
    key = (account.casefold(), str(DB_PATH.resolve()))
    with _MISSING_LINK_LOCK:
        if key not in _MISSING_LINK_SERVICES:
            _MISSING_LINK_SERVICES[key] = Service(
                DB_PATH, account, run_gh_json, verify_active_account
            )
        return _MISSING_LINK_SERVICES[key]


class GitHubCLIError(RuntimeError):
    pass


class ActiveAccountChangedError(GitHubCLIError):
    pass


class GitHubRateLimitError(GitHubCLIError):
    pass


def validate_local_host(host: str) -> str:
    """Reject non-loopback bind addresses; RepoTraction has no remote auth layer."""
    if host.casefold() == "localhost":
        return host
    try:
        if ipaddress.ip_address(host).is_loopback:
            return host
    except ValueError:
        pass
    raise argparse.ArgumentTypeError(
        "RepoTraction can only bind to localhost or a loopback IP address."
    )


class MemoryCache:
    def __init__(self) -> None:
        self._items: dict[str, tuple[float, Any]] = {}
        self._lock = threading.Lock()

    def get(self, key: str, max_age: int) -> Any | None:
        with self._lock:
            item = self._items.get(key)
            if not item or time.time() - item[0] > max_age:
                return None
            return item[1]

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._items[key] = (time.time(), value)


CACHE = MemoryCache()
COLLECTION_LOCK = threading.Lock()
COLLECTION_STATE: dict[str, Any] = {
    "running": False,
    "started_at": None,
    "completed_at": None,
    "current_repo": None,
    "repos_total": 0,
    "repos_completed": 0,
    "errors": [],
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def account_database_path(login: str, data_dir: Path | None = None) -> Path:
    if not LOGIN_PATTERN.fullmatch(login):
        raise GitHubCLIError("GitHub CLI returned an invalid account name.")
    root = data_dir or DATA_DIR
    return root / f"{APP_SLUG}-{login.casefold()}.sqlite3"


def legacy_account_database_path(
    login: str, data_dir: Path | None = None
) -> Path:
    if not LOGIN_PATTERN.fullmatch(login):
        raise GitHubCLIError("GitHub CLI returned an invalid account name.")
    root = data_dir or DATA_DIR
    return root / f"{LEGACY_APP_SLUG}-{login.casefold()}.sqlite3"


def configure_account(login: str) -> str:
    """Select a per-account database and preserve data from the legacy version."""
    global ACCOUNT_LOGIN, DB_PATH, _ACCOUNT_CHECKED_AT
    target = account_database_path(login)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        migration_sources = (
            legacy_account_database_path(login),
            LEGACY_DB_PATH,
        )
        source = next((path for path in migration_sources if path.exists()), None)
        if source is not None:
            shutil.copy2(source, target)
    ACCOUNT_LOGIN = login
    DB_PATH = target
    _ACCOUNT_CHECKED_AT = 0.0
    return login


@contextmanager
def database_connection() -> Any:
    connection = sqlite3.connect(DB_PATH)
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def run_gh_json(
    endpoint: str,
    *,
    params: dict[str, str | int] | None = None,
    paginate: bool = False,
    timeout: int = 45,
    accept: str = "application/vnd.github+json",
) -> Any:
    """Read GitHub data through the already-authenticated GitHub CLI."""
    verify_active_account()
    command = [
        "gh",
        "api",
        "--method",
        "GET",
        endpoint,
        "-H",
        f"Accept: {accept}",
        "-H",
        f"X-GitHub-Api-Version: {GITHUB_API_VERSION}",
    ]
    if paginate:
        command.extend(["--paginate", "--slurp"])
    for key, value in (params or {}).items():
        command.extend(["-f", f"{key}={value}"])

    try:
        with GH_REQUEST_SEMAPHORE:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                check=False,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
    except FileNotFoundError as exc:
        raise GitHubCLIError(
            "GitHub CLI (gh) is not installed or is not available in PATH."
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise GitHubCLIError("GitHub did not respond before the request timed out.") from exc

    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "GitHub CLI error").strip()
        lowered = detail.casefold()
        if any(
            marker in lowered
            for marker in (
                "api rate limit exceeded",
                "secondary rate limit",
                "abuse detection",
                "rate limit exceeded",
            )
        ):
            raise GitHubRateLimitError(detail)
        raise GitHubCLIError(detail)

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise GitHubCLIError("GitHub CLI returned an invalid response.") from exc

    if paginate:
        if not isinstance(payload, list):
            return []
        flattened: list[Any] = []
        for page in payload:
            if isinstance(page, list):
                flattened.extend(page)
            else:
                flattened.append(page)
        return flattened
    return payload


def verify_active_account(*, force: bool = False) -> str | None:
    """Prevent cached account identity from being mixed with a switched gh session."""
    global _ACCOUNT_CHECKED_AT
    expected = ACCOUNT_LOGIN
    if not expected:
        return None

    with _ACCOUNT_CHECK_LOCK:
        now = time.monotonic()
        if not force and now - _ACCOUNT_CHECKED_AT < ACCOUNT_CHECK_INTERVAL_SECONDS:
            return expected
        try:
            result = subprocess.run(
                ["gh", "auth", "status", "--json", "hosts"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
                check=False,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
            raise GitHubCLIError(
                "Unable to verify the active GitHub CLI account; restart RepoTraction after checking gh auth status."
            ) from exc
        if result.returncode != 0:
            raise GitHubCLIError(
                "Unable to verify the active GitHub CLI account; restart RepoTraction after checking gh auth status."
            )
        try:
            hosts = json.loads(result.stdout).get("hosts", {})
            active_logins = [
                str(host.get("login") or "")
                for host in hosts.get("github.com", [])
                if host.get("active") and host.get("state") == "success"
            ]
        except (json.JSONDecodeError, AttributeError, TypeError):
            raise GitHubCLIError(
                "GitHub CLI could not report its active account. Update gh and restart RepoTraction."
            ) from None
        if len(active_logins) != 1 or active_logins[0].casefold() != expected.casefold():
            raise ActiveAccountChangedError(
                f"RepoTraction is scoped to @{expected}, but GitHub CLI's active account changed. "
                "Switch back or restart RepoTraction to use the new account's separate history."
            )
        _ACCOUNT_CHECKED_AT = now
        return expected


def get_account_login() -> str:
    if ACCOUNT_LOGIN:
        return ACCOUNT_LOGIN
    profile = run_gh_json("user")
    login = str(profile.get("login") or "")
    if not login:
        raise GitHubCLIError(
            "Unable to determine the account authenticated in GitHub CLI."
        )
    return configure_account(login)


def ensure_database() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with database_connection() as connection:
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
        SELECT day, views, unique_views, views_available, clones,
               unique_clones, clones_available, collected_at
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
                updates.extend(("views = ?", "unique_views = ?", "views_available = 1"))
                values.extend((row["views"], row["unique_views"]))
            if row["clones_available"] == 1 and (
                current["clones_available"] != 1 or old_is_newer
            ):
                updates.extend(("clones = ?", "unique_clones = ?", "clones_available = 1"))
                values.extend((row["clones"], row["unique_clones"]))
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
        archive_repository_history(connection, alias, archive_name)
        connection.execute(
            """UPDATE repository_aliases
               SET canonical_name = ?, status = 'reused', resolved_at = ?
               WHERE alias = ?""",
            (archive_name, collected_at, alias),
        )


def reconcile_repository_registry(
    repositories: list[dict[str, Any]],
    collected_at: str,
) -> None:
    """Track immutable GitHub IDs, merge renames, and mark stale repositories."""
    current_by_id = {
        int(repo["id"]): str(repo["full_name"])
        for repo in repositories
        if repo.get("id") and repo.get("full_name")
    }
    created_at_by_id = {
        int(repo["id"]): str(repo.get("created_at") or "") or None
        for repo in repositories
        if repo.get("id") and repo.get("full_name")
    }
    current_names = {name.casefold() for name in current_by_id.values()}

    with database_connection() as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("UPDATE repository_registry SET active = 0")
        archive_reused_legacy_aliases(connection, current_names, collected_at)
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
                archive_repository_history(
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
                merge_repository_history(connection, old_name, full_name)
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

    unresolved = [
        name
        for name in sorted(historical_names, key=str.casefold)
        if REPO_PATTERN.fullmatch(name)
        if name.casefold() not in current_names
        and name.casefold() not in known_aliases
    ]
    for old_name in unresolved:
        try:
            resolved = run_gh_json(f"repos/{old_name}")
        except (ActiveAccountChangedError, GitHubRateLimitError):
            raise
        except GitHubCLIError:
            resolved = {}
        repo_id = int(resolved.get("id") or 0)
        canonical_name = str(resolved.get("full_name") or old_name)
        status = "inactive"
        if repo_id in current_by_id:
            canonical_name = current_by_id[repo_id]
            status = "renamed"

        with database_connection() as connection:
            if status == "renamed":
                merge_repository_history(connection, old_name, canonical_name)
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


def get_active_repository_names() -> set[str] | None:
    with database_connection() as connection:
        initialized = connection.execute(
            "SELECT initialized FROM repository_registry_state WHERE singleton = 1"
        ).fetchone()
        if not initialized or not bool(initialized[0]):
            return None
        rows = connection.execute(
            "SELECT full_name FROM repository_registry WHERE active = 1"
        ).fetchall()
    return {str(row[0]).casefold() for row in rows}


def compact_user(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "login": user.get("login", ""),
        "avatar_url": user.get("avatar_url", ""),
        "html_url": user.get("html_url", ""),
    }


def classify_relationships(
    followers: list[dict[str, Any]], following: list[dict[str, Any]]
) -> dict[str, list[dict[str, Any]]]:
    follower_map = {
        str(item.get("login", "")).casefold(): compact_user(item)
        for item in followers
        if item.get("login")
    }
    following_map = {
        str(item.get("login", "")).casefold(): compact_user(item)
        for item in following
        if item.get("login")
    }

    follower_keys = set(follower_map)
    following_keys = set(following_map)

    def users(keys: set[str], source: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        return sorted(
            (source[key] for key in keys),
            key=lambda item: item["login"].casefold(),
        )

    union = follower_keys | following_keys
    all_users: list[dict[str, Any]] = []
    for key in union:
        item = dict(follower_map.get(key) or following_map[key])
        item["follows_you"] = key in follower_keys
        item["you_follow"] = key in following_keys
        all_users.append(item)
    all_users.sort(key=lambda item: item["login"].casefold())

    return {
        "all": all_users,
        "followers": users(follower_keys, follower_map),
        "following": users(following_keys, following_map),
        "mutual": users(follower_keys & following_keys, follower_map),
        "not_following_back": users(following_keys - follower_keys, following_map),
        "followers_not_followed": users(follower_keys - following_keys, follower_map),
    }


def save_relation_snapshot(
    categories: dict[str, list[dict[str, Any]]], collected_at: str | None = None
) -> list[dict[str, Any]]:
    """Persist counts and turn membership changes into a local event timeline."""
    timestamp = collected_at or utc_now()
    event_names = {
        "followers": ("new_follower", "lost_follower"),
        "following": ("started_following", "stopped_following"),
    }
    saved_events: list[dict[str, Any]] = []

    with database_connection() as connection:
        initialized = bool(
            connection.execute("SELECT 1 FROM relation_memberships LIMIT 1").fetchone()
        )
        for kind, (added_type, removed_type) in event_names.items():
            current = {
                item["login"].casefold(): item
                for item in categories[kind]
                if item.get("login")
            }
            previous_rows = connection.execute(
                """
                SELECT login, avatar_url, html_url
                FROM relation_memberships
                WHERE kind = ? AND active = 1
                """,
                (kind,),
            ).fetchall()
            previous = {
                str(row[0]).casefold(): {
                    "login": row[0],
                    "avatar_url": row[1],
                    "html_url": row[2],
                }
                for row in previous_rows
            }

            changes: list[tuple[dict[str, Any], str]] = []
            if initialized:
                changes.extend((current[key], added_type) for key in current.keys() - previous.keys())
                changes.extend((previous[key], removed_type) for key in previous.keys() - current.keys())

            for item, event_type in changes:
                connection.execute(
                    """
                    INSERT OR IGNORE INTO relation_events (
                        collected_at, login, avatar_url, html_url, event_type
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        timestamp,
                        item.get("login", ""),
                        item.get("avatar_url", ""),
                        item.get("html_url", ""),
                        event_type,
                    ),
                )
                saved_events.append(
                    {
                        "collected_at": timestamp,
                        "login": item.get("login", ""),
                        "avatar_url": item.get("avatar_url", ""),
                        "html_url": item.get("html_url", ""),
                        "event_type": event_type,
                    }
                )

            for item in current.values():
                connection.execute(
                    """
                    INSERT INTO relation_memberships (
                        login, kind, avatar_url, html_url,
                        first_seen_at, last_seen_at, active
                    ) VALUES (?, ?, ?, ?, ?, ?, 1)
                    ON CONFLICT(login, kind) DO UPDATE SET
                        avatar_url = excluded.avatar_url,
                        html_url = excluded.html_url,
                        last_seen_at = excluded.last_seen_at,
                        active = 1
                    """,
                    (
                        item["login"],
                        kind,
                        item.get("avatar_url", ""),
                        item.get("html_url", ""),
                        timestamp,
                        timestamp,
                    ),
                )

            removed_logins = [previous[key]["login"] for key in previous.keys() - current.keys()]
            if removed_logins:
                connection.executemany(
                    """
                    UPDATE relation_memberships
                    SET active = 0, last_seen_at = ?
                    WHERE login = ? AND kind = ?
                    """,
                    ((timestamp, login, kind) for login in removed_logins),
                )

        connection.execute(
            """
            INSERT OR REPLACE INTO relation_snapshots (
                collected_at, followers, following, mutual,
                not_following_back, followers_not_followed
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                timestamp,
                len(categories["followers"]),
                len(categories["following"]),
                len(categories["mutual"]),
                len(categories["not_following_back"]),
                len(categories["followers_not_followed"]),
            ),
        )
    return saved_events


def save_repo_snapshots(repositories: list[dict[str, Any]], collected_at: str) -> None:
    with database_connection() as connection:
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


def _record_repository_event(
    connection: sqlite3.Connection,
    *,
    repo: str,
    event_type: str,
    title: str,
    occurred_at: str,
    source: str,
    metadata: dict[str, Any] | None = None,
    detected_at: str | None = None,
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


def record_repository_event(
    *,
    repo: str,
    event_type: str,
    title: str,
    occurred_at: str,
    source: str,
    metadata: dict[str, Any] | None = None,
    detected_at: str | None = None,
) -> bool:
    with database_connection() as connection:
        return _record_repository_event(
            connection,
            repo=repo,
            event_type=event_type,
            title=title,
            occurred_at=occurred_at,
            source=source,
            metadata=metadata,
            detected_at=detected_at,
        )


def save_repo_metadata_snapshots(
    repositories: list[dict[str, Any]],
    collected_at: str,
) -> int:
    events_created = 0
    with database_connection() as connection:
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
            if changes and _record_repository_event(
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


def collect_repository_events(repo: str) -> dict[str, Any]:
    repo = validate_repo(repo)
    endpoints = {
        "releases": (
            f"repos/{repo}/releases",
            {"per_page": 20},
        ),
        "readme_commits": (
            f"repos/{repo}/commits",
            {"path": "README.md", "per_page": 20},
        ),
    }
    payloads: dict[str, Any] = {}
    errors: list[str] = []
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_map = {
            executor.submit(run_gh_json, endpoint, params=params): name
            for name, (endpoint, params) in endpoints.items()
        }
        for future in as_completed(future_map):
            name = future_map[future]
            try:
                payloads[name] = future.result()
            except GitHubRateLimitError:
                for pending in future_map:
                    pending.cancel()
                raise
            except ActiveAccountChangedError:
                raise
            except GitHubCLIError as exc:
                payloads[name] = []
                errors.append(f"{name}: {exc}")

    created = 0
    verify_active_account(force=True)
    with database_connection() as connection:
        for release in payloads.get("releases") or []:
            if not isinstance(release, dict):
                continue
            occurred_at = str(
                release.get("published_at")
                or release.get("created_at")
                or ""
            )
            if not occurred_at:
                continue
            tag = str(release.get("tag_name") or release.get("name") or "release")
            if _record_repository_event(
                connection,
                repo=repo,
                event_type="release",
                title=f"Release {tag}",
                occurred_at=occurred_at,
                source="github_release",
                metadata={
                    "tag": tag,
                    "url": str(release.get("html_url") or ""),
                    "prerelease": bool(release.get("prerelease")),
                },
            ):
                created += 1

        for row in payloads.get("readme_commits") or []:
            if not isinstance(row, dict):
                continue
            commit = row.get("commit") if isinstance(row.get("commit"), dict) else {}
            author = commit.get("author") if isinstance(commit.get("author"), dict) else {}
            committer = commit.get("committer") if isinstance(commit.get("committer"), dict) else {}
            occurred_at = str(author.get("date") or committer.get("date") or "")
            if not occurred_at:
                continue
            message = str(commit.get("message") or "README updated").splitlines()[0]
            if _record_repository_event(
                connection,
                repo=repo,
                event_type="readme",
                title="README updated",
                occurred_at=occurred_at,
                source="github_commit",
                metadata={
                    "sha": str(row.get("sha") or ""),
                    "message": message[:240],
                    "url": str(row.get("html_url") or ""),
                },
            ):
                created += 1

    return {"repo": repo, "created": created, "errors": errors}


def get_repository_events(limit: int = 80) -> list[dict[str, Any]]:
    with database_connection() as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT id, repo, event_type, title, occurred_at, detected_at,
                   source, metadata_json
            FROM repository_events
            ORDER BY occurred_at DESC, id DESC
            LIMIT ?
            """,
            (max(1, min(limit, 300)),),
        ).fetchall()
    events = []
    for row in rows:
        item = dict(row)
        try:
            item["metadata"] = json.loads(item.pop("metadata_json"))
        except (json.JSONDecodeError, TypeError):
            item["metadata"] = {}
            item.pop("metadata_json", None)
        events.append(item)
    return events


def analyze_event_metric(
    connection: sqlite3.Connection,
    *,
    repo: str,
    event_day: date,
    metric: str,
) -> dict[str, Any]:
    if metric not in {"views", "clones"}:
        raise ValueError("Unsupported impact metric.")
    connection.row_factory = sqlite3.Row
    available_column = f"{metric}_available"

    created_row = connection.execute(
        """SELECT created_at FROM repository_registry
           WHERE full_name = ? COLLATE NOCASE LIMIT 1""",
        (repo,),
    ).fetchone()
    try:
        created_day = (
            _utc_date(str(created_row[0])) if created_row and created_row[0] else None
        )
    except ValueError:
        created_day = None
    today = datetime.now(timezone.utc).date()

    def after_creation(rows: Any) -> list[Any]:
        return [
            row
            for row in rows
            if str(row["day"]) < today.isoformat()
            and (created_day is None or str(row["day"]) > created_day.isoformat())
        ]

    def unavailable(
        status: str,
        message: str,
        *,
        window_days: int = 0,
        latest_day: str | None = None,
    ) -> dict[str, Any]:
        return {
            "metric": metric,
            "status": status,
            "message": message,
            "window_days": window_days,
            "latest_day": latest_day,
            "pre": None,
            "post": None,
            "change_pct": None,
            "change_kind": status,
            "portfolio_change_pct": None,
            "portfolio_repositories": 0,
            "lift_pct_points": None,
            "confidence": "low",
        }

    latest_row = connection.execute(
        f"""SELECT MAX(day) FROM traffic_daily
            WHERE repo = ? AND {available_column} = 1
              AND day < ?
              AND day > COALESCE((
                  SELECT substr(created_at, 1, 10)
                  FROM repository_registry
                  WHERE full_name = ? COLLATE NOCASE LIMIT 1
              ), '0000-01-01')""",  # noqa: S608 - metric validated above
        (repo, today.isoformat(), repo),
    ).fetchone()
    latest_day = str(latest_row[0]) if latest_row and latest_row[0] else None
    latest_is_stale = bool(
        latest_day and latest_day < (today - timedelta(days=2)).isoformat()
    )

    post_end = event_day + timedelta(days=6)
    post_rows = connection.execute(
        f"""
        SELECT day, {metric} AS value
        FROM traffic_daily
        WHERE repo = ? AND {available_column} = 1 AND day BETWEEN ? AND ?
        ORDER BY day ASC
        """,  # noqa: S608 - metric is validated above
        (repo, event_day.isoformat(), post_end.isoformat()),
    ).fetchall()
    post_by_day = {str(row["day"]): row for row in after_creation(post_rows)}
    window_days = 0
    for offset in range(7):
        if (event_day + timedelta(days=offset)).isoformat() not in post_by_day:
            break
        window_days += 1
    if window_days == 0:
        if latest_is_stale:
            age_days = (today - date.fromisoformat(latest_day)).days
            return unavailable(
                "stale_upstream",
                f"GitHub traffic data is stale: the latest observed bucket is {age_days} days old.",
                latest_day=latest_day,
            )
        return unavailable(
            "waiting",
            "Waiting for GitHub traffic data; no daily bucket is available for this event yet.",
            latest_day=latest_day,
        )

    pre_start = event_day - timedelta(days=window_days)
    pre_end = event_day - timedelta(days=1)
    effective_post_end = event_day + timedelta(days=window_days - 1)
    pre_rows = after_creation(
        connection.execute(
            f"""
            SELECT day, {metric} AS value
            FROM traffic_daily
            WHERE repo = ? AND {available_column} = 1 AND day BETWEEN ? AND ?
            ORDER BY day ASC
            """,  # noqa: S608 - metric is validated above
            (repo, pre_start.isoformat(), pre_end.isoformat()),
        ).fetchall()
    )
    post_rows = [
        post_by_day[(event_day + timedelta(days=offset)).isoformat()]
        for offset in range(window_days)
    ]
    if len(pre_rows) != window_days or (window_days < 7 and latest_is_stale):
        if latest_is_stale:
            age_days = (today - date.fromisoformat(latest_day)).days
            return unavailable(
                "stale_upstream",
                f"GitHub traffic data is stale: the latest observed bucket is {age_days} days old.",
                window_days=window_days,
                latest_day=latest_day,
            )
        return unavailable(
            "waiting",
            "Waiting for a complete pre-event baseline; this repository does not have enough valid days yet.",
            window_days=window_days,
            latest_day=latest_day,
        )

    portfolio_rows = connection.execute(
        f"""
        SELECT traffic.repo AS repo,
            SUM(CASE WHEN {available_column} = 1 AND traffic.day BETWEEN ? AND ? THEN traffic.{metric} ELSE 0 END) AS pre,
            SUM(CASE WHEN {available_column} = 1 AND traffic.day BETWEEN ? AND ? THEN traffic.{metric} ELSE 0 END) AS post,
            COUNT(CASE WHEN {available_column} = 1 AND traffic.day BETWEEN ? AND ? THEN 1 END) AS pre_days,
            COUNT(CASE WHEN {available_column} = 1 AND traffic.day BETWEEN ? AND ? THEN 1 END) AS post_days
        FROM traffic_daily AS traffic
        WHERE traffic.repo <> ? AND traffic.day BETWEEN ? AND ?
          AND traffic.day < ?
          AND traffic.day > COALESCE((
              SELECT substr(registry.created_at, 1, 10)
              FROM repository_registry AS registry
              WHERE registry.full_name = traffic.repo COLLATE NOCASE
              LIMIT 1
          ), '0000-01-01')
        GROUP BY traffic.repo
        """,  # noqa: S608 - metric is validated above
        (
            pre_start.isoformat(),
            pre_end.isoformat(),
            event_day.isoformat(),
            effective_post_end.isoformat(),
            pre_start.isoformat(),
            pre_end.isoformat(),
            event_day.isoformat(),
            effective_post_end.isoformat(),
            repo,
            pre_start.isoformat(),
            effective_post_end.isoformat(),
            today.isoformat(),
        ),
    ).fetchall()
    return build_event_metric_result(
        metric=metric,
        event_day=event_day,
        window_days=window_days,
        latest_day=latest_day,
        pre_rows=pre_rows,
        post_rows=post_rows,
        portfolio_rows=portfolio_rows,
        is_profile_repository_name=is_profile_repository_name,
    )


def build_impact_lab(*, limit: int = 30) -> dict[str, Any]:
    events = get_repository_events(max(limit * 3, 80))
    active_repositories = get_active_repository_names()
    if active_repositories is not None:
        events = [
            event
            for event in events
            if str(event["repo"]).casefold() in active_repositories
            and not is_profile_repository_name(str(event["repo"]))
        ]

    analyses: list[dict[str, Any]] = []
    with database_connection() as connection:
        connection.row_factory = sqlite3.Row
        for event in events[:limit]:
            try:
                event_day = _utc_date(str(event["occurred_at"]))
            except ValueError:
                continue
            metrics = {
                metric: analyze_event_metric(
                    connection,
                    repo=str(event["repo"]),
                    event_day=event_day,
                    metric=metric,
                )
                for metric in ("views", "clones")
            }
            analyses.append(
                {
                    **event,
                    "name": str(event["repo"]).split("/", 1)[-1],
                    "url": str((event.get("metadata") or {}).get("url") or f"https://github.com/{event['repo']}"),
                    "metrics": metrics,
                    **describe_event_outcome(metrics),
                }
            )

    return {
        "generated_at": utc_now(),
        "summary": {
            "events": len(analyses),
            "releases": sum(1 for row in analyses if row["event_type"] == "release"),
            "readme_changes": sum(1 for row in analyses if row["event_type"] == "readme"),
            "metadata_changes": sum(1 for row in analyses if row["event_type"] == "metadata"),
            "measured": sum(
                1
                for row in analyses
                if any(
                    metric.get("change_pct") is not None
                    for metric in row["metrics"].values()
                )
            ),
            "important": sum(1 for row in analyses if row["important"]),
        },
        "events": analyses,
        "method": {
            "name": "Portfolio Baseline",
            "description": (
                "Compares up to seven observed days before and after each event, "
                "then subtracts the median change across other repositories in "
                "the same portfolio."
            ),
            "limitation": (
                "This is observational evidence, not proof that the repository "
                "change caused the measured traffic movement."
            ),
        },
    }


def get_relation_movements(limit: int = 50) -> list[dict[str, Any]]:
    with database_connection() as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT collected_at, login, avatar_url, html_url, event_type
            FROM relation_events
            ORDER BY collected_at DESC, id DESC
            LIMIT ?
            """,
            (max(1, min(limit, 200)),),
        ).fetchall()
    return [dict(row) for row in rows]


def get_relation_history(days: int = 30) -> list[dict[str, Any]]:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    with database_connection() as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT collected_at, followers, following, mutual,
                   not_following_back, followers_not_followed
            FROM relation_snapshots
            WHERE collected_at >= ?
            ORDER BY collected_at ASC
            """,
            (cutoff,),
        ).fetchall()
    return [dict(row) for row in rows]


def build_dashboard(*, force: bool = False) -> dict[str, Any]:
    cached = None if force else CACHE.get("dashboard", 60)
    if cached is not None:
        return cached
    account = get_account_login()

    with ThreadPoolExecutor(max_workers=4) as executor:
        jobs = {
            "profile": executor.submit(
                run_gh_json,
                f"users/{account}",
            ),
            "followers": executor.submit(
                run_gh_json,
                f"users/{account}/followers",
                params={"per_page": 100},
                paginate=True,
            ),
            "following": executor.submit(
                run_gh_json,
                f"users/{account}/following",
                params={"per_page": 100},
                paginate=True,
            ),
            "repos": executor.submit(
                run_gh_json,
                "user/repos",
                params={
                    "per_page": 100,
                    "affiliation": "owner",
                    "sort": "updated",
                },
                paginate=True,
            ),
        }
        result = {name: job.result() for name, job in jobs.items()}

    categories = classify_relationships(result["followers"], result["following"])
    repositories = [
        {
            "id": int(repo.get("id") or 0),
            "full_name": repo.get("full_name", ""),
            "name": repo.get("name", ""),
            "created_at": repo.get("created_at", ""),
            "private": bool(repo.get("private")),
            "archived": bool(repo.get("archived")),
            "fork": bool(repo.get("fork")),
            "html_url": repo.get("html_url", ""),
            "description": repo.get("description") or "",
            "homepage": repo.get("homepage") or "",
            "topics": [
                str(topic)
                for topic in (repo.get("topics") or [])
                if isinstance(topic, str)
            ],
            "license": repository_license_metadata(repo)["spdx_id"],
            "license_name": repository_license_metadata(repo)["name"],
            "license_status": repository_license_metadata(repo)["status"],
            "default_branch": repo.get("default_branch") or "main",
            "updated_at": repo.get("updated_at", ""),
            "pushed_at": repo.get("pushed_at", ""),
            "language": repo.get("language") or "",
            "stars": int(repo.get("stargazers_count", 0)),
            "forks": int(repo.get("forks_count", 0)),
            "watchers": int(repo.get("subscribers_count", repo.get("watchers_count", 0))),
            "open_issues": int(repo.get("open_issues_count", 0)),
            "size": int(repo.get("size", 0)),
        }
        for repo in result["repos"]
        if repo.get("permissions", {}).get("push") and repo.get("full_name")
    ]

    verify_active_account(force=True)
    collected_at = utc_now()
    reconcile_repository_registry(repositories, collected_at)
    save_relation_snapshot(categories, collected_at)
    save_repo_snapshots(repositories, collected_at)
    save_repo_metadata_snapshots(repositories, collected_at)
    portfolio_repositories = portfolio_repository_rows(repositories)
    payload = {
        "collected_at": collected_at,
        "profile": {
            "login": result["profile"].get("login", account),
            "name": result["profile"].get("name") or result["profile"].get("login", ""),
            "avatar_url": result["profile"].get("avatar_url", ""),
            "html_url": result["profile"].get("html_url", ""),
            "bio": result["profile"].get("bio") or "",
            "public_repos": int(result["profile"].get("public_repos", 0)),
            "created_at": result["profile"].get("created_at", ""),
        },
        "counts": {name: len(items) for name, items in categories.items()},
        "relationships": categories,
        "relationship_movements": get_relation_movements(),
        "relationship_history": get_relation_history(),
        "repositories": repositories,
        "portfolio": {
            "repositories": len(portfolio_repositories),
            "stars": sum(int(repo.get("stars") or 0) for repo in repositories),
            "stars_include_profile_repositories": True,
            "excluded_profile_repositories": [
                str(repo["full_name"])
                for repo in repositories
                if is_profile_repository(repo)
            ],
        },
    }
    CACHE.set("dashboard", payload)
    return payload


def validate_repo(repo: str) -> str:
    if not REPO_PATTERN.fullmatch(repo):
        raise ValueError("Invalid repository name.")
    owner, name = repo.split("/", 1)
    if owner in {".", ".."} or name in {".", ".."}:
        raise ValueError("Invalid repository name.")
    return repo


def _safe_traffic_call(endpoint: str, default: Any) -> Any:
    try:
        return run_gh_json(endpoint)
    except (ActiveAccountChangedError, GitHubRateLimitError):
        raise
    except GitHubCLIError:
        return default


def save_traffic(
    repo: str,
    views: dict[str, Any] | None,
    clones: dict[str, Any] | None,
    *,
    collected_at: str | None = None,
) -> str:
    timestamp = collected_at or utc_now()
    view_days = {
        str(item.get("timestamp", ""))[:10]: item
        for item in (views or {}).get("views", [])
        if item.get("timestamp")
    }
    clone_days = {
        str(item.get("timestamp", ""))[:10]: item
        for item in (clones or {}).get("clones", [])
        if item.get("timestamp")
    }

    with database_connection() as connection:
        created_row = connection.execute(
            "SELECT created_at FROM repository_registry WHERE full_name = ? COLLATE NOCASE LIMIT 1",
            (repo,),
        ).fetchone()
        created_day = (
            str(created_row[0])[:10]
            if created_row and created_row[0]
            else None
        )
        for day, view in sorted(view_days.items()):
            # GitHub sometimes returns zero-filled buckets for dates before a
            # repository existed. They are not traffic observations.
            if created_day and day <= created_day:
                continue
            count = int(view.get("count", 0))
            uniques = int(view.get("uniques", 0))
            observation_status = (
                "observed_zero" if count == 0 and uniques == 0 else "observed_value"
            )
            connection.execute(
                """
                INSERT INTO traffic_daily (
                    repo, day, views, unique_views, views_available, views_status,
                    clones_status, collected_at
                ) VALUES (?, ?, ?, ?, 1, ?, 'missing', ?)
                ON CONFLICT(repo, day) DO UPDATE SET
                    views = excluded.views,
                    unique_views = excluded.unique_views,
                    views_available = 1,
                    views_status = excluded.views_status,
                    collected_at = excluded.collected_at
                WHERE julianday(excluded.collected_at) >=
                      julianday(traffic_daily.collected_at)
                  AND NOT (
                      excluded.views = 0 AND excluded.unique_views = 0
                      AND (traffic_daily.views <> 0 OR traffic_daily.unique_views <> 0)
                  )
                """,
                (
                    repo,
                    day,
                    count,
                    uniques,
                    observation_status,
                    timestamp,
                ),
            )
        for day, clone in sorted(clone_days.items()):
            if created_day and day <= created_day:
                continue
            count = int(clone.get("count", 0))
            uniques = int(clone.get("uniques", 0))
            observation_status = (
                "observed_zero" if count == 0 and uniques == 0 else "observed_value"
            )
            connection.execute(
                """
                INSERT INTO traffic_daily (
                    repo, day, clones, unique_clones, clones_available,
                    views_status, clones_status, collected_at
                ) VALUES (?, ?, ?, ?, 1, 'missing', ?, ?)
                ON CONFLICT(repo, day) DO UPDATE SET
                    clones = excluded.clones,
                    unique_clones = excluded.unique_clones,
                    clones_available = 1,
                    clones_status = excluded.clones_status,
                    collected_at = excluded.collected_at
                WHERE julianday(excluded.collected_at) >=
                      julianday(traffic_daily.collected_at)
                  AND NOT (
                      excluded.clones = 0 AND excluded.unique_clones = 0
                      AND (traffic_daily.clones <> 0 OR traffic_daily.unique_clones <> 0)
                  )
                """,
                (
                    repo,
                    day,
                    count,
                    uniques,
                    observation_status,
                    timestamp,
                ),
            )
        connection.execute(
            """
            INSERT OR REPLACE INTO traffic_snapshots (
                repo, collected_at, views_count, views_uniques,
                clones_count, clones_uniques
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                repo,
                timestamp,
                int(views["count"])
                if views is not None and views.get("count") is not None
                else None,
                int(views["uniques"])
                if views is not None and views.get("uniques") is not None
                else None,
                int(clones["count"])
                if clones is not None and clones.get("count") is not None
                else None,
                int(clones["uniques"])
                if clones is not None and clones.get("uniques") is not None
                else None,
            ),
        )
    return timestamp


def get_traffic_history(repo: str) -> list[dict[str, Any]]:
    with database_connection() as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT day, views, unique_views, views_available, views_status,
                   clones, unique_clones, clones_available, clones_status
            FROM traffic_daily
            WHERE repo = ?
            ORDER BY day ASC
            """,
            (repo,),
        ).fetchall()
    return [dict(row) for row in rows]


def traffic_availability_refresh_needed() -> bool:
    """Refresh unknown traffic only for repositories the collector can reach."""
    active_repositories = get_active_repository_names()
    if active_repositories == set():
        return False

    active_filter = ""
    parameters: list[str] = []
    if active_repositories is not None:
        active_filter = "AND traffic.repo COLLATE NOCASE IN ("
        active_filter += ", ".join("?" for _ in active_repositories) + ")"
        parameters = sorted(active_repositories)

    with database_connection() as connection:
        row = connection.execute(
            f"""WITH bounds AS (
                   SELECT repo, MAX(day) AS latest_day
                   FROM traffic_daily
                   GROUP BY repo
               )
               SELECT 1
               FROM traffic_daily AS traffic
               JOIN bounds ON bounds.repo = traffic.repo
               WHERE traffic.day BETWEEN date(bounds.latest_day, '-13 days')
                                     AND bounds.latest_day
                 AND COALESCE((
                     SELECT snapshot.archived
                     FROM repo_snapshots AS snapshot
                     WHERE snapshot.repo = traffic.repo COLLATE NOCASE
                     ORDER BY snapshot.collected_at DESC
                     LIMIT 1
                 ), 0) = 0
                 AND (traffic.views_available IS NULL
                      OR traffic.clones_available IS NULL)
                 {active_filter}
               LIMIT 1""",
            parameters,
        ).fetchone()
    return row is not None


def get_repository_signal_rows() -> list[dict[str, Any]]:
    with database_connection() as connection:
        connection.row_factory = sqlite3.Row
        traffic_rows = connection.execute(
            """
            WITH bounds AS (
                SELECT repo, MAX(day) AS latest_day
                FROM traffic_daily
                GROUP BY repo
            )
            SELECT traffic.repo,
                bounds.latest_day AS traffic_window_to,
                date(bounds.latest_day, '-6 days') AS traffic_window_from,
                date(bounds.latest_day, '-7 days') AS previous_window_to,
                date(bounds.latest_day, '-13 days') AS previous_window_from,
                COUNT(CASE WHEN (traffic.views_available = 1 OR traffic.clones_available = 1) AND traffic.day BETWEEN date(bounds.latest_day, '-6 days') AND bounds.latest_day THEN 1 END) AS traffic_days_available,
                COUNT(CASE WHEN (traffic.views_available = 1 OR traffic.clones_available = 1) AND traffic.day BETWEEN date(bounds.latest_day, '-13 days') AND date(bounds.latest_day, '-7 days') THEN 1 END) AS previous_days_available,
                COUNT(CASE WHEN traffic.views_available = 1 AND traffic.day BETWEEN date(bounds.latest_day, '-6 days') AND bounds.latest_day THEN 1 END) AS views_days_7d,
                COUNT(CASE WHEN traffic.clones_available = 1 AND traffic.day BETWEEN date(bounds.latest_day, '-6 days') AND bounds.latest_day THEN 1 END) AS clones_days_7d,
                COUNT(CASE WHEN traffic.views_available = 1 AND traffic.day BETWEEN date(bounds.latest_day, '-13 days') AND date(bounds.latest_day, '-7 days') THEN 1 END) AS previous_views_days,
                COUNT(CASE WHEN traffic.clones_available = 1 AND traffic.day BETWEEN date(bounds.latest_day, '-13 days') AND date(bounds.latest_day, '-7 days') THEN 1 END) AS previous_clones_days,
                SUM(CASE WHEN traffic.views_available = 1 AND traffic.day BETWEEN date(bounds.latest_day, '-6 days') AND bounds.latest_day THEN views ELSE 0 END) AS views_7d,
                SUM(CASE WHEN traffic.views_available = 1 AND traffic.day BETWEEN date(bounds.latest_day, '-6 days') AND bounds.latest_day THEN unique_views ELSE 0 END) AS visitor_days_7d,
                SUM(CASE WHEN traffic.clones_available = 1 AND traffic.day BETWEEN date(bounds.latest_day, '-6 days') AND bounds.latest_day THEN clones ELSE 0 END) AS clones_7d,
                SUM(CASE WHEN traffic.clones_available = 1 AND traffic.day BETWEEN date(bounds.latest_day, '-6 days') AND bounds.latest_day THEN unique_clones ELSE 0 END) AS cloner_days_7d,
                SUM(CASE WHEN traffic.views_available = 1 AND traffic.day BETWEEN date(bounds.latest_day, '-13 days') AND date(bounds.latest_day, '-7 days') THEN views ELSE 0 END) AS previous_views,
                SUM(CASE WHEN traffic.views_available = 1 AND traffic.day BETWEEN date(bounds.latest_day, '-13 days') AND date(bounds.latest_day, '-7 days') THEN unique_views ELSE 0 END) AS previous_visitor_days,
                SUM(CASE WHEN traffic.clones_available = 1 AND traffic.day BETWEEN date(bounds.latest_day, '-13 days') AND date(bounds.latest_day, '-7 days') THEN clones ELSE 0 END) AS previous_clones,
                SUM(CASE WHEN traffic.clones_available = 1 AND traffic.day BETWEEN date(bounds.latest_day, '-13 days') AND date(bounds.latest_day, '-7 days') THEN unique_clones ELSE 0 END) AS previous_cloner_days,
                COUNT(CASE WHEN traffic.views_available = 1 AND traffic.day BETWEEN date(bounds.latest_day, '-13 days') AND bounds.latest_day THEN 1 END) AS views_days_14d,
                COUNT(CASE WHEN traffic.clones_available = 1 AND traffic.day BETWEEN date(bounds.latest_day, '-13 days') AND bounds.latest_day THEN 1 END) AS clones_days_14d,
                SUM(CASE WHEN traffic.views_available = 1 AND traffic.day BETWEEN date(bounds.latest_day, '-13 days') AND bounds.latest_day THEN views ELSE 0 END) AS views_14d,
                SUM(CASE WHEN traffic.views_available = 1 AND traffic.day BETWEEN date(bounds.latest_day, '-13 days') AND bounds.latest_day THEN unique_views ELSE 0 END) AS visitor_days_14d,
                SUM(CASE WHEN traffic.clones_available = 1 AND traffic.day BETWEEN date(bounds.latest_day, '-13 days') AND bounds.latest_day THEN clones ELSE 0 END) AS clones_14d,
                SUM(CASE WHEN traffic.clones_available = 1 AND traffic.day BETWEEN date(bounds.latest_day, '-13 days') AND bounds.latest_day THEN unique_clones ELSE 0 END) AS cloner_days_14d,
                MAX(traffic.collected_at) AS traffic_collected_at
            FROM traffic_daily AS traffic
            JOIN bounds ON bounds.repo = traffic.repo
            GROUP BY traffic.repo, bounds.latest_day
            """
        ).fetchall()
        native_rows = connection.execute(
            """
            SELECT repositories.repo,
                (
                    SELECT views_count
                    FROM traffic_snapshots AS snapshot
                    WHERE snapshot.repo = repositories.repo
                      AND snapshot.views_count IS NOT NULL
                    ORDER BY snapshot.collected_at DESC
                    LIMIT 1
                ) AS views_count,
                (
                    SELECT views_uniques
                    FROM traffic_snapshots AS snapshot
                    WHERE snapshot.repo = repositories.repo
                      AND snapshot.views_uniques IS NOT NULL
                    ORDER BY snapshot.collected_at DESC
                    LIMIT 1
                ) AS views_uniques,
                (
                    SELECT MAX(collected_at)
                    FROM traffic_snapshots AS snapshot
                    WHERE snapshot.repo = repositories.repo
                      AND snapshot.views_count IS NOT NULL
                ) AS views_collected_at,
                (
                    SELECT clones_count
                    FROM traffic_snapshots AS snapshot
                    WHERE snapshot.repo = repositories.repo
                      AND snapshot.clones_count IS NOT NULL
                    ORDER BY snapshot.collected_at DESC
                    LIMIT 1
                ) AS clones_count,
                (
                    SELECT clones_uniques
                    FROM traffic_snapshots AS snapshot
                    WHERE snapshot.repo = repositories.repo
                      AND snapshot.clones_uniques IS NOT NULL
                    ORDER BY snapshot.collected_at DESC
                    LIMIT 1
                ) AS clones_uniques,
                (
                    SELECT MAX(collected_at)
                    FROM traffic_snapshots AS snapshot
                    WHERE snapshot.repo = repositories.repo
                      AND snapshot.clones_count IS NOT NULL
                ) AS clones_collected_at
            FROM (SELECT DISTINCT repo FROM traffic_snapshots) AS repositories
            """
        ).fetchall()
        snapshot_rows = connection.execute(
            """
            SELECT repo, collected_at, stars, forks, watchers, open_issues,
                   private, archived, language, pushed_at
            FROM repo_snapshots
            WHERE collected_at >= datetime('now', '-15 days')
               OR collected_at = (
                   SELECT MAX(inner_snapshot.collected_at)
                   FROM repo_snapshots AS inner_snapshot
                   WHERE inner_snapshot.repo = repo_snapshots.repo
               )
               OR collected_at = (
                   SELECT MIN(inner_snapshot.collected_at)
                   FROM repo_snapshots AS inner_snapshot
                   WHERE inner_snapshot.repo = repo_snapshots.repo
               )
            ORDER BY repo, collected_at ASC
            """
        ).fetchall()

    traffic = {row["repo"]: dict(row) for row in traffic_rows}
    native = {row["repo"]: dict(row) for row in native_rows}
    snapshots: dict[str, list[dict[str, Any]]] = {}
    for row in snapshot_rows:
        snapshots.setdefault(row["repo"], []).append(dict(row))

    active_repositories = get_active_repository_names()
    repository_names = set(traffic) | set(native) | set(snapshots)
    if active_repositories is not None:
        repository_names = {
            repo for repo in repository_names if repo.casefold() in active_repositories
        }

    rows: list[dict[str, Any]] = []
    for repo in sorted(repository_names, key=str.casefold):
        repo_traffic = traffic.get(repo, {})
        repo_native = native.get(repo, {})
        repo_snapshots = snapshots.get(repo, [])
        latest, baseline, snapshot_period = select_comparison_window(
            repo_snapshots,
            first_label="since first snapshot",
        )
        views_days = int(repo_traffic.get("views_days_7d") or 0)
        clones_days = int(repo_traffic.get("clones_days_7d") or 0)
        previous_views_days = int(repo_traffic.get("previous_views_days") or 0)
        previous_clones_days = int(repo_traffic.get("previous_clones_days") or 0)
        views_comparison_ready = views_days == 7 and previous_views_days == 7
        clones_comparison_ready = clones_days == 7 and previous_clones_days == 7
        views = int(repo_traffic.get("views_7d") or 0) if views_days else None
        clones = int(repo_traffic.get("clones_7d") or 0) if clones_days else None
        visitor_days = int(repo_traffic.get("visitor_days_7d") or 0) if views_days else None
        cloner_days = int(repo_traffic.get("cloner_days_7d") or 0) if clones_days else None
        traffic_days_available = int(repo_traffic.get("traffic_days_available") or 0)
        previous_days_available = int(repo_traffic.get("previous_days_available") or 0)
        traffic_period = {
            "from": repo_traffic.get("traffic_window_from"),
            "to": repo_traffic.get("traffic_window_to"),
            "days_available": traffic_days_available,
            "is_complete": traffic_days_available == 7,
            "label": traffic_period_label(
                repo_traffic.get("traffic_window_to"),
                traffic_days_available,
            ),
        }
        traffic_comparison_ready = views_comparison_ready and clones_comparison_ready
        has_snapshot_baseline = bool(snapshot_period.get("has_baseline"))
        net_stars = (
            int(latest.get("stars", 0)) - int(baseline.get("stars", 0))
            if has_snapshot_baseline
            else None
        )
        net_forks = (
            int(latest.get("forks", 0)) - int(baseline.get("forks", 0))
            if has_snapshot_baseline
            else None
        )
        score = (
            round(
                min(
                    100,
                    math.log1p(views or 0) * 7
                    + math.log1p(clones or 0) * 9
                    + max(0, net_stars or 0) * 10
                    + max(0, net_forks or 0) * 12,
                )
            )
            if views_days == 7 and clones_days == 7
            else None
        )
        native_clone_events = repo_native.get("clones_count")
        native_unique_cloners = repo_native.get("clones_uniques")
        adoption_signal = build_adoption_signal(
            native_clone_events,
            native_unique_cloners,
        )
        rows.append(
            {
                "repo": repo,
                "name": repo.split("/", 1)[-1],
                "views_7d": views,
                "views_available_days_7d": views_days,
                "views_comparison_ready": views_comparison_ready,
                "visitor_days_7d": visitor_days,
                "clones_7d": clones,
                "clones_available_days_7d": clones_days,
                "clones_comparison_ready": clones_comparison_ready,
                "cloner_days_7d": cloner_days,
                "previous_views": int(repo_traffic.get("previous_views") or 0) if previous_views_days else None,
                "previous_views_available_days": previous_views_days,
                "previous_visitor_days": int(repo_traffic.get("previous_visitor_days") or 0) if previous_views_days else None,
                "previous_clones": int(repo_traffic.get("previous_clones") or 0) if previous_clones_days else None,
                "previous_clones_available_days": previous_clones_days,
                "previous_cloner_days": int(repo_traffic.get("previous_cloner_days") or 0) if previous_clones_days else None,
                "traffic_period": traffic_period,
                "traffic_comparison_ready": traffic_comparison_ready,
                "views_14d": int(repo_traffic.get("views_14d") or 0) if int(repo_traffic.get("views_days_14d") or 0) else None,
                "views_available_days_14d": int(repo_traffic.get("views_days_14d") or 0),
                "visitor_days_14d": int(repo_traffic.get("visitor_days_14d") or 0) if int(repo_traffic.get("views_days_14d") or 0) else None,
                "clones_14d": int(repo_traffic.get("clones_14d") or 0) if int(repo_traffic.get("clones_days_14d") or 0) else None,
                "clones_available_days_14d": int(repo_traffic.get("clones_days_14d") or 0),
                "cloner_days_14d": int(repo_traffic.get("cloner_days_14d") or 0) if int(repo_traffic.get("clones_days_14d") or 0) else None,
                "unique_visitors_14d": repo_native.get("views_uniques"),
                "unique_cloners_14d": repo_native.get("clones_uniques"),
                "native_views_14d": repo_native.get("views_count"),
                "native_clones_14d": repo_native.get("clones_count"),
                "native_views_collected_at": repo_native.get("views_collected_at"),
                "native_clones_collected_at": repo_native.get("clones_collected_at"),
                "traffic_collected_at": repo_traffic.get("traffic_collected_at"),
                "stars": int(latest.get("stars", 0)),
                "net_stars": net_stars,
                "forks": int(latest.get("forks", 0)),
                "net_forks": net_forks,
                "watchers": int(latest.get("watchers", 0)),
                "open_issues": int(latest.get("open_issues", 0)),
                "private": bool(latest.get("private", 0)),
                "archived": bool(latest.get("archived", 0)),
                "language": latest.get("language") or "",
                "pushed_at": latest.get("pushed_at") or "",
                "snapshot_period": snapshot_period,
                "clone_breadth_pct": adoption_signal["breadth_pct"],
                "clone_repeat_factor": adoption_signal["repeat_factor"],
                "adoption_signal": adoption_signal,
                "signal_score": score,
            }
        )
    rows.sort(
        key=lambda item: (
            item["signal_score"] or 0,
            item["views_7d"] or 0,
            item["stars"],
        ),
        reverse=True,
    )
    return rows


def days_since_timestamp(value: str, *, now: datetime | None = None) -> int | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    reference = now or datetime.now(timezone.utc)
    return max(0, (reference - parsed.astimezone(timezone.utc)).days)


def is_profile_repository_name(full_name: str) -> bool:
    if "/" not in full_name:
        return False
    owner, name = full_name.split("/", 1)
    return owner.casefold() == name.casefold()


def is_profile_repository(repo: dict[str, Any]) -> bool:
    return is_profile_repository_name(
        str(repo.get("full_name") or repo.get("repo") or "")
    )


def portfolio_repository_rows(
    repositories: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [repo for repo in repositories if not is_profile_repository(repo)]


def repository_health(repo: dict[str, Any]) -> dict[str, Any]:
    return calculate_repository_health(
        repo,
        is_profile=is_profile_repository(repo),
        pushed_days_ago=days_since_timestamp(str(repo.get("pushed_at") or "")),
    )


def analyze_opportunities(
    repositories: list[dict[str, Any]],
    signal_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    signals = {str(row["repo"]).casefold(): row for row in signal_rows}
    opportunities: list[dict[str, Any]] = []
    health_rows: list[dict[str, Any]] = []

    for repo in repositories:
        full_name = str(repo.get("full_name") or "")
        if not full_name or repo.get("archived") or repo.get("fork"):
            continue
        if is_profile_repository(repo):
            continue
        signal = signals.get(full_name.casefold(), {})
        health = repository_health(repo)
        repo_opportunities, repo_health = build_repository_opportunities(
            repo, signal, health
        )
        opportunities.extend(repo_opportunities)
        health_rows.extend(repo_health)

    return rank_opportunities(opportunities, health_rows)


def build_opportunity_center(*, force: bool = False) -> dict[str, Any]:
    cached = None if force else CACHE.get("opportunities", 120)
    if cached is not None:
        return cached
    dashboard = build_dashboard()
    repositories = portfolio_repository_rows(get_repository_signal_rows())
    opportunities, health = analyze_opportunities(
        dashboard["repositories"], repositories
    )
    average_health = (
        round(sum(int(item["score"]) for item in health) / len(health))
        if health
        else 0
    )
    payload = {
        "generated_at": utc_now(),
        "readiness_score": {
            "name": "Project Readiness",
            "kind": "local checklist",
            "formula": "100 − 20 missing description − 15 fewer than 2 topics − 20 missing public license − 5 missing homepage − 10/20 stale activity",
            "description": "Custom or unrecognized licenses count as present; profile repositories are not scored.",
        },
        "summary": {
            "total": len(opportunities),
            "high": sum(1 for item in opportunities if item["priority"] == "high"),
            "medium": sum(
                1 for item in opportunities if item["priority"] == "medium"
            ),
            "health_average": average_health,
            "readiness_average": average_health,
            "repositories_analyzed": len(health),
        },
        "opportunities": opportunities[:40],
        "health": health,
        "readiness": health,
        "repositories": [
            {"repo": row["repo"], "name": row["name"]}
            for row in repositories
            if not row["archived"]
        ],
    }
    CACHE.set("opportunities", payload)
    return payload


def build_repository_comparison(selected_repos: list[str]) -> dict[str, Any]:
    selected: list[str] = []
    seen: set[str] = set()
    for value in selected_repos:
        repo = validate_repo(value.strip())
        key = repo.casefold()
        if key not in seen:
            selected.append(repo)
            seen.add(key)
    if not 2 <= len(selected) <= 4:
        raise ValueError("Choose between 2 and 4 different repositories.")

    available = {
        str(row["repo"]).casefold(): row
        for row in portfolio_repository_rows(get_repository_signal_rows())
    }
    items: list[dict[str, Any]] = []
    for requested in selected:
        row = available.get(requested.casefold())
        if row is None:
            raise ValueError(f"Repository is not available for comparison: {requested}")
        item = dict(row)
        item.update(
            {
                "view_change": (
                    percentage_change(
                        int(row["views_7d"]), int(row["previous_views"])
                    )
                    if row.get("views_comparison_ready")
                    else None
                ),
                "history": get_traffic_history(str(row["repo"]))[-30:],
            }
        )
        items.append(item)
    return {"generated_at": utc_now(), "repositories": items}


def build_digest_markdown(
    account: str,
    signals: dict[str, Any],
    opportunity_center: dict[str, Any],
    *,
    generated_at: str | None = None,
) -> str:
    reference = datetime.fromisoformat((generated_at or utc_now()).replace("Z", "+00:00"))
    totals = signals["totals"]
    traffic_period = signals.get("traffic_period") or {}
    period_start = traffic_period.get("from") or (
        reference.date() - timedelta(days=6)
    ).isoformat()
    period_end = traffic_period.get("to") or reference.date().isoformat()
    traffic_label = traffic_period.get("label") or "rolling 7 days"
    relationship_delta = signals.get("relationship_delta") or {}
    relationship_period = signals.get("relationship_period") or {
        "label": "no comparison yet"
    }
    lines = [
        f"# {APP_NAME} Weekly Digest",
        "",
        f"**Account:** @{account}",
        f"**Traffic period:** {period_start} to {period_end} UTC",
        "",
        f"## Traffic · {traffic_label}",
        "",
        f"- {totals['views_7d'] if totals['views_7d'] is not None else 'unavailable'} repository page views",
        f"- {totals['clones_7d'] if totals['clones_7d'] is not None else 'unavailable'} full clone events",
        "",
        "## Snapshot changes",
        "",
        f"- {totals['net_stars']:+d} net stars and {totals['net_forks']:+d} net forks across per-repository snapshot windows",
        f"- {int(relationship_delta.get('followers', 0)):+d} followers · {relationship_period['label']}",
        "",
        "## Top repositories",
        "",
    ]
    for row in signals["repository_ranking"][:5]:
        lines.append(
            f"- **{row['name']}** — "
            f"{row['views_7d'] if row['views_7d'] is not None else 'unavailable'} page views, "
            f"{row['clones_7d'] if row['clones_7d'] is not None else 'unavailable'} clone events, "
            f"activity score {row['signal_score'] if row['signal_score'] is not None else 'unavailable'}"
        )
    if not signals["repository_ranking"]:
        lines.append("- No repository traffic collected yet.")

    lines.extend(["", "## Opportunities", ""])
    opportunities = opportunity_center["opportunities"][:5]
    for item in opportunities:
        lines.append(
            f"- **{item['title']}** — {item['action']} ({item['metric']})"
        )
    if not opportunities:
        lines.append("- No urgent opportunities detected.")

    lines.extend(["", "## Alerts", ""])
    notifications = signals["notifications"][:5]
    for item in notifications:
        lines.append(f"- **{item['title']}** — {item['detail']}")
    if not notifications:
        lines.append("- No important alerts in this digest.")

    lines.extend(["", "---", f"Generated locally by {APP_NAME}.", ""])
    return "\n".join(lines)


def build_weekly_digest(*, force: bool = False) -> dict[str, Any]:
    generated_at = utc_now()
    signals = build_signals()
    opportunity_center = build_opportunity_center(force=force)
    markdown = build_digest_markdown(
        get_account_login(),
        signals,
        opportunity_center,
        generated_at=generated_at,
    )
    traffic_period = signals.get("traffic_period") or {}
    reference = datetime.fromisoformat(generated_at)
    return {
        "generated_at": generated_at,
        "period": {
            "from": traffic_period.get("from")
            or (reference.date() - timedelta(days=6)).isoformat(),
            "to": traffic_period.get("to") or reference.date().isoformat(),
            "label": traffic_period.get("label") or "rolling 7 days",
        },
        "totals": signals["totals"],
        "relationship_delta": signals["relationship_delta"],
        "relationship_period": signals["relationship_period"],
        "top_repositories": signals["repository_ranking"][:5],
        "opportunities": opportunity_center["opportunities"][:5],
        "alerts": signals["notifications"][:5],
        "markdown": markdown,
    }


def get_latest_relation_counts() -> tuple[
    dict[str, int], dict[str, int], dict[str, Any]
]:
    with database_connection() as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT collected_at, followers, following, mutual,
                   not_following_back, followers_not_followed
            FROM relation_snapshots
            ORDER BY collected_at DESC
            LIMIT 300
            """
        ).fetchall()
    if not rows:
        empty = {
            "followers": 0,
            "following": 0,
            "mutual": 0,
            "not_following_back": 0,
            "followers_not_followed": 0,
        }
        return empty, empty, {
            "from": None,
            "to": None,
            "days_observed": 0.0,
            "is_full_window": False,
            "label": "no comparison yet",
        }

    latest, baseline, period = select_comparison_window(
        list(rows),
        first_label="since first collection",
    )
    keys = (
        "followers",
        "following",
        "mutual",
        "not_following_back",
        "followers_not_followed",
    )
    baseline_values = baseline if period.get("has_baseline") else latest
    return (
        {key: int(latest[key]) for key in keys},
        {key: int(baseline_values[key]) for key in keys},
        period,
    )


def collection_status() -> dict[str, Any]:
    with COLLECTION_LOCK:
        status = dict(COLLECTION_STATE)
        status["errors"] = list(COLLECTION_STATE["errors"])
    if not status["running"] and not status.get("last_status"):
        try:
            with database_connection() as connection:
                row = connection.execute(
                    """
                    SELECT started_at, completed_at, repos_total, repos_completed,
                           errors, status, error_details
                    FROM collection_runs
                    ORDER BY started_at DESC
                    LIMIT 1
                    """
                ).fetchone()
        except sqlite3.Error:
            row = None
        if row:
            try:
                last_errors = json.loads(row[6] or "[]")
            except (json.JSONDecodeError, TypeError):
                last_errors = []
            status.update(
                {
                    "started_at": row[0],
                    "completed_at": row[1],
                    "repos_total": row[2],
                    "repos_completed": row[3],
                    "last_error_count": row[4],
                    "last_status": row[5],
                    "errors": last_errors,
                }
            )
    return status


def build_signals() -> dict[str, Any]:
    all_repositories = get_repository_signal_rows()
    repositories = portfolio_repository_rows(all_repositories)
    traffic_rows = [repo for repo in repositories if not repo.get("archived")]
    traffic_period = summarize_traffic_period(traffic_rows)
    views_comparison_ready = bool(traffic_rows) and all(
        bool(repo.get("views_comparison_ready")) for repo in traffic_rows
    )
    clones_comparison_ready = bool(traffic_rows) and all(
        bool(repo.get("clones_comparison_ready")) for repo in traffic_rows
    )
    traffic_comparison_ready = views_comparison_ready and clones_comparison_ready
    star_comparisons = [
        repo for repo in repositories if repo.get("net_stars") is not None
    ]
    latest_counts, baseline_counts, relationship_period = (
        get_latest_relation_counts()
    )
    movements = get_relation_movements(30)

    totals = {
        key: sum(int(repo.get(key) or 0) for repo in repositories)
        for key in ("net_stars", "forks", "net_forks")
    }
    totals.update(
        {
            key: sum(int(repo.get(key) or 0) for repo in traffic_rows)
            for key in (
                "views_7d",
                "visitor_days_7d",
                "clones_7d",
                "cloner_days_7d",
                "previous_views",
                "previous_clones",
            )
        }
    )
    totals["stars"] = sum(int(repo.get("stars") or 0) for repo in all_repositories)
    views_data_available = bool(traffic_rows) and all(
        int(repo.get("views_available_days_7d") or 0) > 0 for repo in traffic_rows
    )
    clones_data_available = bool(traffic_rows) and all(
        int(repo.get("clones_available_days_7d") or 0) > 0 for repo in traffic_rows
    )
    if not views_data_available:
        totals["views_7d"] = None
    if not clones_data_available:
        totals["clones_7d"] = None
    follower_delta = latest_counts["followers"] - baseline_counts["followers"]
    cards = [
        {
            "key": "reach",
            "label": "Page views",
            "value": totals["views_7d"],
            "unit": f"repository views · {traffic_period['label']}" if views_data_available else "waiting for daily view data",
            "delta": (
                percentage_change(totals["views_7d"], totals["previous_views"])
                if views_comparison_ready
                else None
            ),
            "delta_available": views_comparison_ready,
        },
        {
            "key": "clone_activity",
            "label": "Clone activity",
            "value": totals["clones_7d"],
            "unit": f"full clone events · {traffic_period['label']}" if clones_data_available else "waiting for daily clone data",
            "delta": (
                percentage_change(totals["clones_7d"], totals["previous_clones"])
                if clones_comparison_ready
                else None
            ),
            "delta_available": clones_comparison_ready,
        },
        {
            "key": "stars",
            "label": "Stars",
            "value": totals["stars"],
            "unit": (
                f"total · net across {len(star_comparisons)} observed baselines"
                if star_comparisons
                else "total · waiting for a second snapshot"
            ),
            "delta_absolute": totals["net_stars"],
            "delta_available": bool(star_comparisons),
        },
        {
            "key": "community",
            "label": "Community",
            "value": latest_counts["followers"],
            "unit": f"followers · {relationship_period['label']}",
            "delta_absolute": follower_delta,
        },
    ]

    notifications: list[dict[str, Any]] = []
    movement_copy = {
        "new_follower": ("New follower", "positive"),
        "lost_follower": ("No longer follows you", "warning"),
        "started_following": ("You started following", "info"),
        "stopped_following": ("You stopped following", "info"),
    }
    for movement in movements[:8]:
        title, tone = movement_copy.get(movement["event_type"], ("Network change", "info"))
        notifications.append(
            {
                "type": movement["event_type"],
                "tone": tone,
                "title": title,
                "detail": f'@{movement["login"]}',
                "occurred_at": movement["collected_at"],
                "url": movement["html_url"],
            }
        )

    for repo in repositories:
        current = int(repo.get("views_7d") or 0)
        previous = int(repo.get("previous_views") or 0)
        if (
            repo.get("views_comparison_ready")
            and current >= 5
            and current >= max(3, previous * 1.5)
        ):
            change = percentage_change(current, previous)
            detail = (
                f"{current} page views · +{change:g}%"
                if change is not None
                else f"{current} page views · new traffic"
            )
            notifications.append(
                {
                    "type": "traffic_spike",
                    "tone": "positive",
                    "title": f'Traffic spike on {repo["name"]}',
                    "detail": detail,
                    "occurred_at": repo["traffic_collected_at"],
                    "url": f'https://github.com/{repo["repo"]}',
                }
            )
        if int(repo.get("net_stars") or 0) > 0:
            notifications.append(
                {
                    "type": "net_star_growth",
                    "tone": "positive",
                    "title": f'Net star growth on {repo["name"]}',
                    "detail": f'+{repo["net_stars"]} · {repo["snapshot_period"]["label"]}',
                    "occurred_at": repo["traffic_collected_at"],
                    "url": f'https://github.com/{repo["repo"]}/stargazers',
                }
            )

    notifications.sort(
        key=lambda item: str(item.get("occurred_at") or ""), reverse=True
    )
    active_repositories = [
        repo for repo in traffic_rows if repo["views_14d"] or repo["clones_14d"]
    ]
    return {
        "generated_at": utc_now(),
        "traffic_period": traffic_period,
        "traffic_comparison_ready": traffic_comparison_ready,
        "activity_score": {
            "name": "Activity Score",
            "kind": "local heuristic",
            "formula": "min(100, 7×ln(1+views) + 9×ln(1+clones) + 10×positive net stars + 12×positive net forks)",
            "description": "Ranks observed repository activity; it is not a GitHub health or quality score.",
        },
        "cards": cards,
        "totals": totals,
        "repository_ranking": repositories,
        "notifications": notifications[:16],
        "important_signals": sum(
            1
            for item in notifications
            if item["type"] in {"traffic_spike", "net_star_growth", "new_follower"}
        ),
        "tracked_repositories": len(active_repositories),
        "statistics_scope": {
            "profile_repositories_excluded": True,
            "description": "Profile README repositories are excluded from activity analysis; their current stars remain in the account total.",
        },
        "relationship_counts": latest_counts,
        "relationship_delta": {
            key: latest_counts[key] - baseline_counts[key] for key in latest_counts
        },
        "relationship_period": relationship_period,
        "collection": collection_status(),
    }


def build_traffic(repo: str, *, force: bool = False) -> dict[str, Any]:
    repo = validate_repo(repo)
    cache_key = f"traffic:{repo.casefold()}"
    cached = None if force else CACHE.get(cache_key, 300)
    if cached is not None:
        return cached

    endpoints = {
        "views": f"repos/{repo}/traffic/views",
        "clones": f"repos/{repo}/traffic/clones",
        "referrers": f"repos/{repo}/traffic/popular/referrers",
        "paths": f"repos/{repo}/traffic/popular/paths",
    }
    defaults: dict[str, Any] = {
        "views": {"count": None, "uniques": None, "views": [], "available": False},
        "clones": {"count": None, "uniques": None, "clones": [], "available": False},
        "referrers": [],
        "paths": [],
    }

    data: dict[str, Any] = {}
    errors: list[str] = []
    failed_endpoints: set[str] = set()
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_map = {
            executor.submit(run_gh_json, endpoint): name
            for name, endpoint in endpoints.items()
        }
        for future in as_completed(future_map):
            name = future_map[future]
            try:
                data[name] = future.result()
                if name in {"views", "clones"} and isinstance(data[name], dict):
                    data[name]["available"] = True
            except GitHubRateLimitError:
                for pending in future_map:
                    pending.cancel()
                raise
            except ActiveAccountChangedError:
                raise
            except GitHubCLIError as exc:
                data[name] = defaults[name]
                failed_endpoints.add(name)
                errors.append(f"{name}: {exc}")

    if len(errors) == len(endpoints):
        raise GitHubCLIError(
            "Unable to read repository traffic. Make sure you have push access and "
            "that the GitHub CLI token can access the repository."
        )

    verify_active_account(force=True)
    save_traffic(
        repo,
        None if "views" in failed_endpoints else data["views"],
        None if "clones" in failed_endpoints else data["clones"],
    )
    payload = {
        "repo": repo,
        "collected_at": utc_now(),
        "views": data["views"],
        "clones": data["clones"],
        "referrers": data["referrers"],
        "paths": data["paths"],
        "history": get_traffic_history(repo),
        "partial_errors": errors,
    }
    CACHE.set(cache_key, payload)
    return payload


def build_star_timeline(repo: str, *, force: bool = False) -> dict[str, Any]:
    repo = validate_repo(repo)
    cache_key = f"stars:{repo.casefold()}"
    cached = None if force else CACHE.get(cache_key, 600)
    if cached is not None:
        return cached
    rows = run_gh_json(
        f"repos/{repo}/stargazers",
        params={"per_page": 100},
        paginate=True,
        accept="application/vnd.github.star+json",
    )
    stars = []
    for row in rows:
        user = row.get("user") if isinstance(row, dict) else None
        user = user if isinstance(user, dict) else row
        if not isinstance(user, dict) or not user.get("login"):
            continue
        stars.append(
            {
                "login": user.get("login", ""),
                "avatar_url": user.get("avatar_url", ""),
                "html_url": user.get("html_url", ""),
                "starred_at": row.get("starred_at") if isinstance(row, dict) else None,
            }
        )
    stars.sort(key=lambda item: str(item.get("starred_at") or ""), reverse=True)
    payload = {"repo": repo, "count": len(stars), "stars": stars[:100]}
    CACHE.set(cache_key, payload)
    return payload


def normalize_activity_event(event: dict[str, Any]) -> dict[str, Any]:
    event_type = event.get("type", "Event")
    payload = event.get("payload") or {}
    repo = (event.get("repo") or {}).get("name", "")
    title = {
        "PushEvent": "Push",
        "PullRequestEvent": "Pull request",
        "IssuesEvent": "Issue",
        "IssueCommentEvent": "Comment",
        "CreateEvent": "Created",
        "ReleaseEvent": "Release",
        "ForkEvent": "Fork",
        "WatchEvent": "Starred",
        "PublicEvent": "Repository made public",
        "DeleteEvent": "Reference deleted",
    }.get(event_type, event_type.removesuffix("Event"))
    detail = repo
    if event_type == "PushEvent":
        size = payload.get("size", len(payload.get("commits") or []))
        detail = f"{repo} · {size} commit"
    elif event_type in {"PullRequestEvent", "IssuesEvent"}:
        detail = f'{repo} · {payload.get("action", "updated")}'
    elif event_type == "CreateEvent":
        detail = f'{repo} · {payload.get("ref_type", "resource")}'
    elif event_type == "ReleaseEvent":
        detail = f'{repo} · {(payload.get("release") or {}).get("tag_name", "release")}'
    return {
        "id": str(event.get("id", "")),
        "type": event_type,
        "title": title,
        "detail": detail,
        "repo": repo,
        "created_at": event.get("created_at", ""),
        "url": f"https://github.com/{repo}" if repo else "https://github.com",
    }


def build_activity(*, force: bool = False) -> dict[str, Any]:
    cached = None if force else CACHE.get("activity", 600)
    if cached is not None:
        return cached
    account = get_account_login()
    with ThreadPoolExecutor(max_workers=2) as executor:
        events_job = executor.submit(
            run_gh_json,
            f"users/{account}/events/public",
            params={"per_page": 100},
        )
        merged_job = executor.submit(
            run_gh_json,
            "search/issues",
            params={"q": f"author:{account} is:pr is:merged", "per_page": 1},
        )
        events = events_job.result()
        merged_result = merged_job.result()

    normalized = [
        normalize_activity_event(event)
        for event in events
        if isinstance(event, dict)
    ]
    counts: dict[str, int] = {}
    for item in normalized:
        counts[item["type"]] = counts.get(item["type"], 0) + 1

    quickdraw_candidates = []
    for event in events:
        if event.get("type") not in {"IssuesEvent", "PullRequestEvent"}:
            continue
        payload = event.get("payload") or {}
        subject = payload.get("issue") or payload.get("pull_request") or {}
        if payload.get("action") != "closed":
            continue
        try:
            created = datetime.fromisoformat(str(subject["created_at"]).replace("Z", "+00:00"))
            closed = datetime.fromisoformat(str(subject["closed_at"]).replace("Z", "+00:00"))
        except (KeyError, TypeError, ValueError):
            continue
        if (closed - created).total_seconds() <= 300:
            quickdraw_candidates.append(subject.get("html_url", ""))

    repo_rows = get_repository_signal_rows()
    top_starred = max(repo_rows, key=lambda item: item["stars"], default=None)
    top_stars = int(top_starred["stars"]) if top_starred else 0
    merged_prs = int(merged_result.get("total_count", 0))
    achievements = [
        {
            "name": "Starstruck",
            "status": "candidate" if top_stars >= 16 else "progress",
            "progress": min(top_stars, 16),
            "target": 16,
            "detail": (
                f'{top_starred["name"]}: {top_stars} stars'
                if top_starred
                else "No repositories detected"
            ),
            "confidence": "high",
        },
        {
            "name": "Pull Shark",
            "status": "candidate" if merged_prs >= 2 else "progress",
            "progress": min(merged_prs, 2),
            "target": 2,
            "detail": f"{merged_prs} merged pull requests found",
            "confidence": "medium",
        },
        {
            "name": "Quickdraw",
            "status": "candidate" if quickdraw_candidates else "open",
            "progress": 1 if quickdraw_candidates else 0,
            "target": 1,
            "detail": (
                "Found an item closed within 5 minutes in recent events"
                if quickdraw_candidates
                else "Close an issue or pull request within 5 minutes of creation"
            ),
            "confidence": "medium",
        },
        {
            "name": "Pair Extraordinaire",
            "status": "open",
            "progress": 0,
            "target": 1,
            "detail": "Co-authored commits require a dedicated check",
            "confidence": "manual",
        },
    ]
    payload = {
        "generated_at": utc_now(),
        "events": normalized,
        "counts": counts,
        "achievements": achievements,
        "achievement_note": (
            "These are eligibility indicators, not an authoritative record of "
            "achievements awarded by GitHub."
        ),
    }
    CACHE.set("activity", payload)
    return payload


def collect_all_data() -> dict[str, Any]:
    started_at = utc_now()
    with COLLECTION_LOCK:
        if COLLECTION_STATE["running"]:
            return dict(COLLECTION_STATE)
        COLLECTION_STATE.update(
            {
                "running": True,
                "started_at": started_at,
                "completed_at": None,
                "current_repo": None,
                "repos_total": 0,
                "repos_completed": 0,
                "errors": [],
            }
        )

    completed = 0
    total = 0
    errors: list[str] = []
    status = "completed"
    try:
        dashboard = build_dashboard(force=True)
        repositories = [
            repo for repo in dashboard["repositories"] if not repo.get("archived")
        ]
        total = len(repositories)
        with COLLECTION_LOCK:
            COLLECTION_STATE["repos_total"] = total
        for repository in repositories:
            repo = repository["full_name"]
            with COLLECTION_LOCK:
                COLLECTION_STATE["current_repo"] = repo
            try:
                traffic_result = build_traffic(repo, force=True)
                errors.extend(
                    f"{repo} traffic: {detail}"
                    for detail in traffic_result.get("partial_errors", [])
                )
            except ActiveAccountChangedError:
                raise
            except GitHubRateLimitError as exc:
                errors.append(f"{repo}: {exc}")
                status = "partial" if completed else "failed"
                break
            except (GitHubCLIError, ValueError) as exc:
                errors.append(f"{repo}: {exc}")
            try:
                event_result = collect_repository_events(repo)
                errors.extend(
                    f"{repo} events: {detail}"
                    for detail in event_result.get("errors", [])
                )
            except ActiveAccountChangedError:
                raise
            except GitHubRateLimitError as exc:
                errors.append(f"{repo} events: {exc}")
                status = "partial" if completed else "failed"
                break
            except (GitHubCLIError, ValueError) as exc:
                errors.append(f"{repo} events: {exc}")
            completed += 1
            with COLLECTION_LOCK:
                COLLECTION_STATE["repos_completed"] = completed
                COLLECTION_STATE["errors"] = errors[-20:]
    except Exception as exc:
        status = "failed"
        errors.append(str(exc))
    completed_at = utc_now()
    if errors and status == "completed":
        status = "partial"
    try:
        with database_connection() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO collection_runs (
                    started_at, completed_at, repos_total, repos_completed,
                    errors, error_details, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    started_at,
                    completed_at,
                    total,
                    completed,
                    len(errors),
                    json.dumps(errors[-20:], ensure_ascii=False),
                    status,
                ),
            )
    except Exception as exc:
        status = "failed"
        errors.append(f"Could not save collection status: {exc}")
    with COLLECTION_LOCK:
        COLLECTION_STATE.update(
            {
                "running": False,
                "completed_at": completed_at,
                "current_repo": None,
                "repos_total": total,
                "repos_completed": completed,
                "errors": errors[-20:],
                "last_status": status,
                "last_error_count": len(errors),
            }
        )
    return collection_status()


def start_collection() -> bool:
    with COLLECTION_LOCK:
        if COLLECTION_STATE["running"]:
            return False
    threading.Thread(
        target=collect_all_data,
        daemon=True,
        name=f"{APP_SLUG}-collector",
    ).start()
    return True


def automatic_collection_loop() -> None:
    time.sleep(20)
    while True:
        with database_connection() as connection:
            row = connection.execute(
                """
                SELECT completed_at, status
                FROM collection_runs
                WHERE completed_at IS NOT NULL
                ORDER BY completed_at DESC
                LIMIT 1
                """
            ).fetchone()
        refresh_needed = traffic_availability_refresh_needed()
        stale = True
        if row and row[0] and row[1] == "completed":
            try:
                last_run = datetime.fromisoformat(str(row[0]))
                stale = refresh_needed or (
                    datetime.now(timezone.utc) - last_run
                ).total_seconds() >= COLLECTION_STALE_SECONDS
            except ValueError:
                stale = True
        if stale:
            start_collection()
        time.sleep(60 * 60)


def build_export_payload() -> dict[str, Any]:
    with database_connection() as connection:
        connection.row_factory = sqlite3.Row
        traffic = [
            dict(row)
            for row in connection.execute(
                """
                SELECT repo, day, views, unique_views, views_available, views_status,
                       clones, unique_clones, clones_available, clones_status, collected_at
                FROM traffic_daily
                ORDER BY day DESC, repo
                """
            ).fetchall()
        ]
    return {
        "exported_at": utc_now(),
        "account": get_account_login(),
        "signals": build_signals(),
        "movements": get_relation_movements(200),
        "repository_events": get_repository_events(300),
        "relationship_history": get_relation_history(3650),
        "traffic": traffic,
    }


def build_csv_export(dataset: str) -> tuple[str, bytes]:
    output = io.StringIO(newline="")
    if dataset == "movements":
        rows = get_relation_movements(200)
        fields = ["collected_at", "event_type", "login", "html_url"]
        filename = f"{APP_SLUG}-movements.csv"
    else:
        with database_connection() as connection:
            connection.row_factory = sqlite3.Row
            rows = [
                dict(row)
                for row in connection.execute(
                    """
                    SELECT repo, day, views, unique_views, views_available, views_status,
                           clones, unique_clones, clones_available, clones_status, collected_at
                    FROM traffic_daily
                    ORDER BY day DESC, repo
                    """
                ).fetchall()
            ]
        fields = [
            "repo",
            "day",
            "views",
            "unique_views",
            "views_available",
            "views_status",
            "clones",
            "unique_clones",
            "clones_available",
            "clones_status",
            "collected_at",
        ]
        filename = f"{APP_SLUG}-traffic.csv"
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return filename, output.getvalue().encode("utf-8-sig")


class DashboardHandler(BaseHTTPRequestHandler):
    server_version = "RepoTraction/3.1.0"

    def _is_trusted_local_request(self, *, require_origin: bool = False) -> bool:
        host_header = self.headers.get("Host", "")
        try:
            request_host = urlparse(f"//{host_header}")
            request_port = request_host.port
            if request_port is None:
                request_port = 80
            is_loopback = bool(
                request_host.hostname
                and not request_host.username
                and not request_host.password
                and request_host.path == ""
                and not request_host.query
                and not request_host.fragment
                and validate_local_host(request_host.hostname) == request_host.hostname
                and request_port == self.server.server_port
            )
        except (ValueError, argparse.ArgumentTypeError):
            return False
        if not is_loopback:
            return False

        origin_header = self.headers.get("Origin")
        if require_origin and not origin_header:
            return False
        if origin_header:
            try:
                origin = urlparse(origin_header)
                origin_port = origin.port
                if origin_port is None and origin.scheme == "http":
                    origin_port = 80
                if (
                    origin.scheme != "http"
                    or not origin.hostname
                    or origin.hostname.casefold() != request_host.hostname.casefold()
                    or origin_port != request_port
                    or origin.path not in {"", "/"}
                    or origin.query
                    or origin.fragment
                    or origin.username
                    or origin.password
                ):
                    return False
            except ValueError:
                return False

        return self.headers.get("Sec-Fetch-Site", "").casefold() != "cross-site"

    def do_GET(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        if not self._is_trusted_local_request():
            self.send_error(HTTPStatus.FORBIDDEN, "Local same-origin request required.")
            return
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)

        if parsed.path.startswith("/api/"):
            try:
                verify_active_account()
            except GitHubCLIError as exc:
                self.send_json({"error": str(exc)}, status=HTTPStatus.CONFLICT)
                return

        if parsed.path == "/api/health":
            self.send_json(
                {"ok": True, "app": APP_NAME, "account": get_account_login()}
            )
            return
        if parsed.path == "/api/missing-link":
            self.handle_api(lambda: missing_link_service().state())
            return
        if parsed.path in {"/api/missing-link/export", "/api/missing-link/package", "/api/missing-link/context"}:
            try:
                service = missing_link_service()
                if parsed.path.endswith("/context"):
                    payload = service.context(query.get("job_id", [""])[0])
                    body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
                    self.send_download(body, "application/json; charset=utf-8", "missing-link-context.json")
                else:
                    match_id = query.get("match_id", [""])[0]
                    package = parsed.path.endswith("/package")
                    payload = service.export(match_id, package=package)
                    body = payload if package else json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
                    self.send_download(body, "application/zip" if package else "application/json; charset=utf-8",
                        "missing-link-package.zip" if package else "missing-link-handoff.json")
            except (GitHubCLIError, ValueError) as exc:
                self.send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return
        if parsed.path == "/api/dashboard":
            self.handle_api(lambda: build_dashboard(force=query.get("refresh") == ["1"]))
            return
        if parsed.path == "/api/signals":
            self.handle_api(build_signals)
            return
        if parsed.path == "/api/opportunities":
            self.handle_api(
                lambda: build_opportunity_center(
                    force=query.get("refresh") == ["1"]
                )
            )
            return
        if parsed.path == "/api/impact":
            self.handle_api(build_impact_lab)
            return
        if parsed.path == "/api/compare":
            self.handle_api(
                lambda: build_repository_comparison(query.get("repos", []))
            )
            return
        if parsed.path == "/api/digest":
            self.handle_api(
                lambda: build_weekly_digest(force=query.get("refresh") == ["1"])
            )
            return
        if parsed.path == "/api/activity":
            self.handle_api(
                lambda: build_activity(force=query.get("refresh") == ["1"])
            )
            return
        if parsed.path == "/api/collection":
            self.send_json(collection_status())
            return
        if parsed.path == "/api/traffic":
            repo = query.get("repo", [""])[0]
            self.handle_api(
                lambda: build_traffic(repo, force=query.get("refresh") == ["1"])
            )
            return
        if parsed.path == "/api/stars":
            repo = query.get("repo", [""])[0]
            self.handle_api(
                lambda: build_star_timeline(
                    repo, force=query.get("refresh") == ["1"]
                )
            )
            return
        if parsed.path == "/api/export":
            dataset = query.get("dataset", ["traffic"])[0]
            if dataset == "digest":
                body = build_weekly_digest()["markdown"].encode("utf-8")
                self.send_download(
                    body,
                    "text/markdown; charset=utf-8",
                    f"{APP_SLUG}-weekly-digest.md",
                )
                return
            if dataset == "summary":
                body = json.dumps(
                    build_export_payload(), ensure_ascii=False, indent=2
                ).encode("utf-8")
                self.send_download(
                    body,
                    "application/json; charset=utf-8",
                    f"{APP_SLUG}-export.json",
                )
                return
            if dataset not in {"traffic", "movements"}:
                self.send_json(
                    {"error": "Invalid export dataset."},
                    status=HTTPStatus.BAD_REQUEST,
                )
                return
            filename, body = build_csv_export(dataset)
            self.send_download(body, "text/csv; charset=utf-8", filename)
            return
        if parsed.path == "/favicon.ico":
            self.send_response(HTTPStatus.NO_CONTENT)
            self.end_headers()
            return

        self.serve_static(parsed.path)

    def do_POST(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        if not self._is_trusted_local_request(require_origin=True):
            self.send_error(HTTPStatus.FORBIDDEN, "Local same-origin request required.")
            return
        try:
            verify_active_account()
        except GitHubCLIError as exc:
            self.send_json({"error": str(exc)}, status=HTTPStatus.CONFLICT)
            return
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/missing-link/"):
            try:
                # Bounded JSON only; optional proof execution uses approved public
                # text in WASI, never local paths or native project execution.
                length = int(self.headers.get("Content-Length", "0"))
                if length <= 0 or length > 512000 or self.headers.get("Transfer-Encoding"):
                    raise ValueError("A bounded JSON request body is required (maximum 512 KB).")
                if self.headers.get_content_type() != "application/json":
                    raise ValueError("Content-Type must be application/json.")
                data = json.loads(self.rfile.read(length))
                if not isinstance(data, dict):
                    raise ValueError("Request body must be a JSON object.")
                service = missing_link_service()
                actions = {
                    "/api/missing-link/jobs": service.start,
                    "/api/missing-link/cancel": lambda body: service.cancel(body.get("job_id", "")),
                    "/api/missing-link/resume": service.resume,
                    "/api/missing-link/capability": service.correct_capability,
                    "/api/missing-link/feedback": service.feedback,
                    "/api/missing-link/analysis": service.import_analysis,
                    "/api/missing-link/example": service.execute_example,
                }
                if parsed.path not in actions:
                    self.send_json({"error": "Endpoint not found."}, status=HTTPStatus.NOT_FOUND)
                    return
                self.send_json(actions[parsed.path](data), status=HTTPStatus.ACCEPTED if parsed.path.endswith("/jobs") else HTTPStatus.OK)
            except (ValueError, GitHubCLIError, KeyError, TypeError) as exc:
                self.send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return
        if parsed.path == "/api/collect":
            started = start_collection()
            self.send_json(
                {
                    "started": started,
                    "message": (
                        "Collection started."
                        if started
                        else "A collection is already running."
                    ),
                    "collection": collection_status(),
                },
                status=HTTPStatus.ACCEPTED if started else HTTPStatus.OK,
            )
            return
        self.send_json(
            {"error": "Endpoint not found."}, status=HTTPStatus.NOT_FOUND
        )

    def handle_api(self, callback: Any) -> None:
        try:
            self.send_json(callback())
        except (GitHubCLIError, ValueError) as exc:
            self.send_json(
                {"error": str(exc)}, status=HTTPStatus.BAD_GATEWAY
            )
        except Exception as exc:  # Keep the local UI usable and avoid a broken socket.
            self.send_json(
                {"error": f"Unexpected error: {exc}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def serve_static(self, request_path: str) -> None:
        relative = "index.html" if request_path in {"", "/"} else request_path.lstrip("/")
        candidate = (STATIC_DIR / relative).resolve()
        try:
            candidate.relative_to(STATIC_DIR.resolve())
        except ValueError:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        if not candidate.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        content_types = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".svg": "image/svg+xml",
        }
        body = candidate.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_types.get(candidate.suffix, "application/octet-stream"))
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, payload: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def send_download(self, body: bytes, content_type: str, filename: str) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, message: str, *args: Any) -> None:
        print(f"[{self.log_date_time_string()}] {message % args}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="RepoTraction local-first GitHub growth analytics"
    )
    parser.add_argument("--host", type=validate_local_host, default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--no-open", action="store_true", help="Do not open the browser")
    parser.add_argument(
        "--collect-only",
        action="store_true",
        help="Collect one complete snapshot without starting the web server",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not shutil.which("gh"):
        raise SystemExit("GitHub CLI (gh) was not found in PATH.")
    account = get_account_login()
    ensure_database()
    if args.collect_only:
        result = collect_all_data()
        print(json.dumps(result, indent=2))
        exit_code = {
            "completed": 0,
            "partial": 2,
            "failed": 1,
        }.get(result.get("last_status"), 1)
        raise SystemExit(exit_code)
    threading.Thread(
        target=automatic_collection_loop,
        daemon=True,
        name=f"{APP_SLUG}-scheduler",
    ).start()
    server = ThreadingHTTPServer((args.host, args.port), DashboardHandler)
    display_host = f"[{args.host}]" if ":" in args.host else args.host
    url = f"http://{display_host}:{args.port}"
    print(f"{APP_NAME} is available at {url} for @{account}")
    print("Press Ctrl+C to stop the server.")
    if not args.no_open:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print(f"\nStopping {APP_NAME}…")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
