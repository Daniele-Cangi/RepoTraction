"""Safe job-stop descriptions, separate from source analysis and retry policy."""
from github_cli import ActiveAccountChangedError, GitHubAccountVerificationError


def job_failure(exc):
    if isinstance(exc, GitHubAccountVerificationError):
        return {"status": "paused", "error": str(exc), "error_diagnostic": exc.diagnostic()}
    if isinstance(exc, ActiveAccountChangedError):
        return {"status": "paused",
            "error": "GitHub account changed. Switch back or restart for the new account's separate history.",
            "error_diagnostic": {"category": "github_identity", "code": "github_identity_changed"}}
    message = str(exc)
    if "rate limit" in message.casefold():
        return {"status": "paused", "error": "GitHub rate limit. No automatic retry. Resume after the upstream reset.",
            "error_diagnostic": None}
    if "account" in message.casefold():
        # Compatibility for injected/older verifiers; text cannot prove a switch.
        return {"status": "paused",
            "error": "GitHub account verification failed; the cause is unavailable. No account change is confirmed. Check gh auth status before explicitly resuming.",
            "error_diagnostic": {"category": "github_identity", "code": "github_identity_unclassified"}}
    return {"status": "failed", "error": message[:500], "error_diagnostic": None}
