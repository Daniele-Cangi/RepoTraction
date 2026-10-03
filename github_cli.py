"""Fail-closed CLI identity checks; no startup work or raw CLI diagnostics."""
from __future__ import annotations

import json
import re
import subprocess


class GitHubCLIError(RuntimeError):
    pass


class ActiveAccountChangedError(GitHubCLIError):
    """A verified identity differs; never a candidate-local validation error."""


class GitHubRateLimitError(GitHubCLIError):
    pass


_IDENTITY_MESSAGES = {
    "github_identity_cli_missing": "GitHub CLI is unavailable; account identity cannot be verified. Restore gh before explicitly resuming.",
    "github_identity_cli_timeout": "GitHub account verification timed out (10 seconds). No account change is confirmed. Check gh auth status and connectivity before explicitly resuming.",
    "github_identity_cli_error": "GitHub CLI could not run the account-verification check. No account change is confirmed.",
    "github_identity_cli_failed": "GitHub CLI account verification failed. No account change is confirmed. Check gh auth status and connectivity before explicitly resuming.",
    "github_identity_invalid_response": "GitHub CLI returned an invalid account-verification response. Identity is unverified; no account change is confirmed.",
    "github_identity_unavailable": "GitHub CLI did not report a verified active account. No account change is confirmed. Check gh auth status before explicitly resuming.",
    "github_identity_ambiguous": "GitHub CLI reported multiple verified active accounts. Identity is ambiguous; no account change is confirmed.",
}


class GitHubAccountVerificationError(GitHubCLIError):
    def __init__(self, code: str):
        if code not in _IDENTITY_MESSAGES:
            raise ValueError("Unknown identity failure category.")
        self.code = code
        super().__init__(_IDENTITY_MESSAGES[code])

    def diagnostic(self):
        result = {"category": "github_identity", "code": self.code}
        if self.code == "github_identity_cli_timeout":
            result["timeout_seconds"] = 10
        return result


def verify_cli_account(expected: str, *, run, creationflags: int = 0) -> str:
    """One bounded read, injected runner; never reuse unknown identity as success."""
    try:
        result = run(
            ["gh", "auth", "status", "--json", "hosts"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=10, check=False, creationflags=creationflags,
        )
    except FileNotFoundError:
        raise GitHubAccountVerificationError("github_identity_cli_missing") from None
    except subprocess.TimeoutExpired:
        raise GitHubAccountVerificationError("github_identity_cli_timeout") from None
    except OSError:
        raise GitHubAccountVerificationError("github_identity_cli_error") from None
    if result.returncode != 0:
        raise GitHubAccountVerificationError("github_identity_cli_failed")
    try:
        payload = json.loads(result.stdout)
        if not isinstance(payload, dict) or not isinstance(payload.get("hosts"), dict):
            raise ValueError
        entries = payload["hosts"].get("github.com", [])
        if not isinstance(entries, list) or any(not isinstance(entry, dict) for entry in entries):
            raise ValueError
        active = []
        for entry in entries:
            flag = entry.get("active")
            if flag is not None and not isinstance(flag, bool):
                raise ValueError
            if flag is True and entry.get("state") == "success":
                login = entry.get("login")
                if not isinstance(login, str) or not re.fullmatch(r"[A-Za-z0-9-]{1,39}", login):
                    raise ValueError
                active.append(login)
    except (ValueError, TypeError):
        raise GitHubAccountVerificationError("github_identity_invalid_response") from None
    if not active:
        raise GitHubAccountVerificationError("github_identity_unavailable")
    if len(active) != 1:
        raise GitHubAccountVerificationError("github_identity_ambiguous")
    if active[0].casefold() != expected.casefold():
        raise ActiveAccountChangedError(
            "GitHub account changed. Switch back or restart RepoTraction for the new account's separate history."
        )
    return expected
