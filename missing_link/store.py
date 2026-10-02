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
                CREATE TABLE IF NOT EXISTS ml_cancellations (job_id TEXT PRIMARY KEY);
                CREATE TABLE IF NOT EXISTS ml_match_snapshots (match_id TEXT PRIMARY KEY, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS ml_proofs (id TEXT PRIMARY KEY, match_id TEXT NOT NULL, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS ml_ai_allowances (id TEXT PRIMARY KEY, reserved REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS ml_ai_reservations (id INTEGER PRIMARY KEY, allowance_id TEXT NOT NULL,
                    job_id TEXT NOT NULL, cost REAL NOT NULL, created REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS ml_corrections (repo_id INTEGER, capability_id TEXT, revision TEXT, payload TEXT,
                    PRIMARY KEY(repo_id, capability_id));
                CREATE TABLE IF NOT EXISTS ml_cache (key TEXT PRIMARY KEY, expires REAL NOT NULL, payload TEXT NOT NULL);
            """)
            identities = db.execute("SELECT account FROM ml_identity").fetchall()
            if identities and identities != [(self.account,)]:
                raise ValueError("Missing Link database belongs to a different account.")
            db.execute("INSERT OR IGNORE INTO ml_identity VALUES (?)", (self.account,))
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
            if kind == "matches":
                # Refreshes must not overwrite annotations written by another request/process.
                db.execute("BEGIN IMMEDIATE")
                payload = self._merge_annotations(db, key, payload)
            db.execute(f"INSERT INTO {table} ({column},payload) VALUES (?,?) ON CONFLICT({column}) DO UPDATE SET payload=excluded.payload",
                (key, json.dumps(redact_payload(payload), ensure_ascii=False)))

    @staticmethod
    def _merge_annotations(db, key, payload):
        payload = dict(payload)
        previous = db.execute("SELECT payload FROM ml_matches WHERE id=?", (key,)).fetchone()
        if previous:
            previous = json.loads(previous[0])
            payload["feedback"] = previous.get("feedback", [])
            if previous.get("superseded"):
                payload["superseded"] = True
        return payload

    def save_matches(self, matches, repository, *, job=None, non_demand=None):
        """Commit results, pinned reproduction context and supersession atomically."""
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            if non_demand is not None:
                # Reviewed zero-match imports supersede only structural placeholders
                # for this exact pinned context, just like other reviewed imports.
                for peer_id, raw in db.execute("SELECT id,payload FROM ml_matches").fetchall():
                    peer = json.loads(raw)
                    same = (peer.get("repo_id"), peer.get("revision"), peer.get("source_fingerprint"), peer.get("request", {}).get("id")) == (
                        repository["id"], repository["revision"], non_demand["fingerprint"], non_demand["id"])
                    if same and peer.get("analysis_source") == "structural":
                        peer["superseded"] = True
                        db.execute("UPDATE ml_matches SET payload=? WHERE id=?", (json.dumps(peer), peer_id))
            for incoming in matches:
                match = self._merge_annotations(db, incoming["id"], incoming)
                # A previously reviewed interpretation continues to supersede a
                # structural result even when that result is first regenerated later.
                peers = db.execute("SELECT id,payload FROM ml_matches").fetchall()
                for peer_id, raw in peers:
                    peer = json.loads(raw)
                    same = (peer.get("repo_id"), peer.get("revision"), peer.get("source_fingerprint")) == (
                        match["repo_id"], match["revision"], match["source_fingerprint"])
                    if not same:
                        continue
                    if match["analysis_source"] == "structural" and peer.get("analysis_source") != "structural":
                        match["superseded"] = True
                    elif match["analysis_source"] != "structural" and peer.get("analysis_source") == "structural":
                        peer["superseded"] = True
                        db.execute("UPDATE ml_matches SET payload=? WHERE id=?", (json.dumps(peer), peer_id))
                db.execute("INSERT INTO ml_matches VALUES (?,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload",
                    (match["id"], json.dumps(redact_payload(match), ensure_ascii=False)))
                # Unlike a scan of the most recent jobs, this snapshot cannot select
                # a different interpretation of the same revision or age out at 500.
                snapshot = {"repository": repository, "issue": match.get("source_issue", {})}
                db.execute("INSERT INTO ml_match_snapshots VALUES (?,?) ON CONFLICT(match_id) DO UPDATE SET payload=excluded.payload",
                    (match["id"], json.dumps(redact_payload(snapshot), ensure_ascii=False)))
            if job is not None:
                db.execute("UPDATE ml_jobs SET payload=? WHERE id=?",
                    (json.dumps(redact_payload(job), ensure_ascii=False), job["id"]))

    def match_snapshot(self, match_id):
        with self.connection() as db:
            row = db.execute("SELECT payload FROM ml_match_snapshots WHERE match_id=?", (match_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def pause_abandoned_jobs(self, updated_at):
        """Caller must hold the worker lease; preserve checkpoints and budgets."""
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            rows = db.execute("""SELECT id,payload FROM ml_jobs
                WHERE json_extract(payload, '$.status') IN ('queued', 'running')""").fetchall()
            for job_id, raw in rows:
                job = json.loads(raw)
                job.update(status="paused", updated_at=updated_at,
                           error="Previous worker exited. Resume explicitly; checkpoints and used budgets remain.")
                db.execute("UPDATE ml_jobs SET payload=? WHERE id=?", (json.dumps(job, ensure_ascii=False), job_id))

    def save_proof(self, proof):
        # Separate from model/importable match payloads: only the runner writes receipts.
        with self.connection() as db:
            db.execute("INSERT INTO ml_proofs VALUES (?,?,?)", (proof["id"], proof["match_id"],
                json.dumps(redact_payload(proof), ensure_ascii=False)))

    def proofs(self, match_id):
        with self.connection() as db:
            rows = db.execute("SELECT payload FROM ml_proofs WHERE match_id=? ORDER BY rowid DESC LIMIT 20", (match_id,)).fetchall()
        return [json.loads(row[0]) for row in rows]

    def reserve_ai_allowance(self, allowance_id, job_id, cost, ceiling):
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT reserved FROM ml_ai_allowances WHERE id=?", (allowance_id,)).fetchone()
            total = (row[0] if row else 0) + cost
            if total > ceiling:
                raise ValueError("Persisted AI allowance would exceed the explicit total dollar budget.")
            db.execute("INSERT INTO ml_ai_allowances VALUES (?,?) ON CONFLICT(id) DO UPDATE SET reserved=excluded.reserved",
                (allowance_id, total))
            db.execute("INSERT INTO ml_ai_reservations (allowance_id,job_id,cost,created) VALUES (?,?,?,?)",
                (allowance_id, job_id, cost, time.time()))
        return total

    def ai_reserved(self, allowance_id):
        with self.connection() as db:
            row = db.execute("SELECT reserved FROM ml_ai_allowances WHERE id=?", (allowance_id,)).fetchone()
        return row[0] if row else 0.0

    def append_feedback(self, match_id, annotation):
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT payload FROM ml_matches WHERE id=?", (match_id,)).fetchone()
            if not row:
                raise ValueError("Investigation record not found for this account.")
            match = json.loads(row[0])
            match["feedback"] = (match.get("feedback", []) + [redact_payload(annotation)])[-50:]
            db.execute("UPDATE ml_matches SET payload=? WHERE id=?", (json.dumps(match, ensure_ascii=False), match_id))
        return match

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

    def latest_discussions(self):
        """Index by immutable GitHub ID, including legacy URL-keyed records.

        A rename can leave multiple old URL keys for one issue. Prefer the
        latest acquisition, not URL or insertion order (upserts keep rowid).
        Do not apply the polling list's 500-record limit to freshness checks.
        """
        with self.connection() as db:
            rows = db.execute("""SELECT payload FROM ml_discussions
                ORDER BY COALESCE(json_extract(payload, '$.fetched_at'), '') DESC,
                    COALESCE(json_extract(payload, '$.updated_at'), '') DESC,
                    rowid DESC""").fetchall()
        latest = {}
        for (raw,) in rows:
            issue = json.loads(raw)
            if issue.get("id") is not None:
                latest.setdefault(str(issue["id"]), issue)
        return latest

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

    def request_cancel(self, job_id):
        with self.connection() as db:
            db.execute("INSERT OR IGNORE INTO ml_cancellations VALUES (?)", (job_id,))

    def is_cancelled(self, job_id):
        with self.connection() as db:
            return db.execute("SELECT 1 FROM ml_cancellations WHERE job_id=?", (job_id,)).fetchone() is not None

    def clear_cancel(self, job_id):
        with self.connection() as db:
            db.execute("DELETE FROM ml_cancellations WHERE job_id=?", (job_id,))
