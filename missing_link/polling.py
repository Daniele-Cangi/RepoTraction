"""Read-only identity-stop polling; never an unverified full-state bypass."""
from __future__ import annotations

import json
from pathlib import Path
import re
import sqlite3

from github_cli import ActiveAccountChangedError, GitHubAccountVerificationError
from .job_errors import job_failure


def _saved_stop(record_id, raw):
    """Project only an opaque ID, stopped status and a fixed safe diagnostic."""
    if not isinstance(record_id, str) or not re.fullmatch(r"[0-9a-f]{32}", record_id):
        return None
    try:
        job = json.loads(raw)
    except (TypeError, ValueError):
        return None
    if not isinstance(job, dict) or job.get("id") != record_id or job.get("status") != "paused":
        return None
    diagnostic = job.get("error_diagnostic")
    if not isinstance(diagnostic, dict) or diagnostic.get("category") != "github_identity":
        return None
    code = diagnostic.get("code")
    if not isinstance(code, str):
        return None
    if code == "github_identity_changed":
        failure = job_failure(ActiveAccountChangedError())
    elif code == "github_identity_unclassified":
        failure = job_failure(RuntimeError("account verification"))
    else:
        try:
            failure = job_failure(GitHubAccountVerificationError(code))
        except ValueError:
            return None
    return {"id": record_id, **failure}


def _read_saved_stops(database, account):
    # mode=ro cannot create a missing DB. Do not use Store.connection(), which
    # creates directories/DBs, or Service.state(), which reconciles worker leases.
    db = sqlite3.connect(database.as_uri() + "?mode=ro", uri=True, timeout=2)
    try:
        db.execute("BEGIN")
        if db.execute("SELECT account FROM ml_identity").fetchall() != [(account,)]:
            raise ValueError("Unverified database binding.")
        rows = db.execute("SELECT id, payload FROM ml_jobs ORDER BY rowid DESC LIMIT 500").fetchall()
        return [stop for key, raw in rows if (stop := _saved_stop(key, raw)) is not None]
    finally:
        db.close()


def poll_state(*, verify, get_service, account, database, services, binding_lock):
    """Keep full-state verification; only typed outages admit a minimal view.

    An existing service must have been bound during verified operation in this
    process. Never initialize a service/provider/Store to satisfy a failed poll.
    Confirmed switches, ambiguous identities and unknown exceptions still fail.
    """
    try:
        verify()
        return get_service().state()
    except GitHubAccountVerificationError as exc:
        if exc.code == "github_identity_ambiguous" or not account:
            raise
        bound_account = account.casefold()
        database = Path(database).resolve()
        with binding_lock:
            service = services.get((bound_account, str(database)))
            if (service is None or service.account.casefold() != bound_account
                    or service.store.account != bound_account
                    or service.store.path.resolve() != database):
                raise exc from None
        try:
            jobs = _read_saved_stops(database, bound_account)
        except (OSError, sqlite3.Error, ValueError):
            # Do not expose storage errors or probe an unbound account's history.
            raise exc from None
        return {
            "account": account,
            "diagnostic_only": True,
            "identity_verified": False,
            "actions_available": False,
            "identity_error": str(exc),
            "identity_diagnostic": exc.diagnostic(),
            "jobs": jobs,
        }
