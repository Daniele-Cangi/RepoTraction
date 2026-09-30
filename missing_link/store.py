"""Per-account persistent investigation state. A service captures one immutable DB path."""
from __future__ import annotations

import json
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

from .sources import SECRET_TEXT


def redact_payload(value):
    if isinstance(value, str):
        return SECRET_TEXT.sub(lambda match: (match.group("assignment") or "") + "[REDACTED]", value)
    if isinstance(value, list):
        return [redact_payload(item) for item in value]
    if isinstance(value, dict):
        return {key: redact_payload(item) for key, item in value.items()}
    return value


class Store:
    def __init__(self, path: Path, account: str):
        self.path = Path(path)
        self.account = account.casefold()
        with self.connection() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS ml_identity (account TEXT PRIMARY KEY);
                CREATE TABLE IF NOT EXISTS ml_repositories (repo_id INTEGER PRIMARY KEY, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS ml_jobs (id TEXT PRIMARY KEY, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS ml_matches (id TEXT PRIMARY KEY, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS ml_discussions (id TEXT PRIMARY KEY, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS ml_corrections (repo_id INTEGER, capability_id TEXT, revision TEXT, payload TEXT,
                    PRIMARY KEY(repo_id, capability_id));
                CREATE TABLE IF NOT EXISTS ml_cache (key TEXT PRIMARY KEY, expires REAL NOT NULL, payload TEXT NOT NULL);
            """)
            identities = db.execute("SELECT account FROM ml_identity").fetchall()
            if identities and identities != [(self.account,)]:
                raise ValueError("Missing Link database belongs to a different account.")
            db.execute("INSERT OR IGNORE INTO ml_identity VALUES (?)", (self.account,))
        for job in self.list("jobs"):
            if job["status"] in {"queued", "running"}:
                job.update(status="paused", error="Server restarted. Resume explicitly; existing budgets and checkpoints are preserved.")
                self.put("jobs", job["id"], job)

    @contextmanager
    def connection(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=15)
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    @staticmethod
    def _table(kind):
        if kind not in {"repositories", "jobs", "matches", "discussions"}:
            raise ValueError("Unknown investigation record kind.")
        return "ml_" + kind

    def put(self, kind, key, payload):
        table = self._table(kind)
        column = "repo_id" if kind == "repositories" else "id"
        with self.connection() as db:
            db.execute(f"INSERT INTO {table} ({column},payload) VALUES (?,?) ON CONFLICT({column}) DO UPDATE SET payload=excluded.payload",
                (key, json.dumps(redact_payload(payload), ensure_ascii=False)))

    def get(self, kind, key):
        table = self._table(kind)
        column = "repo_id" if kind == "repositories" else "id"
        with self.connection() as db:
            row = db.execute(f"SELECT payload FROM {table} WHERE {column}=?", (key,)).fetchone()
        if not row:
            raise ValueError("Investigation record not found for this account.")
        return json.loads(row[0])

    def list(self, kind):
        with self.connection() as db:
            rows = db.execute(f"SELECT payload FROM {self._table(kind)} ORDER BY rowid DESC LIMIT 500").fetchall()
        return [json.loads(row[0]) for row in rows]

    def cache_get(self, key):
        with self.connection() as db:
            row = db.execute("SELECT payload FROM ml_cache WHERE key=? AND expires>?", (key, time.time())).fetchone()
        return json.loads(row[0]) if row else None

    def cache_put(self, key, payload, ttl):
        with self.connection() as db:
            db.execute("DELETE FROM ml_cache WHERE expires<?", (time.time(),))
            db.execute("INSERT INTO ml_cache VALUES (?,?,?) ON CONFLICT(key) DO UPDATE SET expires=excluded.expires,payload=excluded.payload",
                (key, time.time() + ttl, json.dumps(redact_payload(payload), ensure_ascii=False)))

    def correct(self, repo_id, capability_id, revision, payload):
        with self.connection() as db:
            db.execute("INSERT INTO ml_corrections VALUES (?,?,?,?) ON CONFLICT(repo_id,capability_id) DO UPDATE SET revision=excluded.revision,payload=excluded.payload",
                (repo_id, capability_id, revision, json.dumps(redact_payload(payload), ensure_ascii=False)))

    def corrections(self, repo_id):
        with self.connection() as db:
            rows = db.execute("SELECT capability_id,revision,payload FROM ml_corrections WHERE repo_id=?", (repo_id,)).fetchall()
        return [{"capability_id": row[0], "revision": row[1], "correction": json.loads(row[2])} for row in rows]
