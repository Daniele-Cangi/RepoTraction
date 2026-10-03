"""Safe identity observation for owned reports; no auth checks or raw responses."""
from github_cli import GitHubAccountVerificationError


def safe_identity_observation(state):
    """Project only typed flags and a known diagnostic, without inferring recovery.

    Unknown categories remain unclassified. Reconstructing the diagnostic from
    its known code drops arbitrary messages, timeout values and nested payloads.
    Callers should persist this before asserting that a received state is verified.
    """
    result = {key: state.get(key) if type(state.get(key)) is bool else None
        for key in ("diagnostic_only", "identity_verified", "actions_available")}
    result["identity_diagnostic"] = None
    diagnostic = state.get("identity_diagnostic")
    if isinstance(diagnostic, dict) and isinstance(diagnostic.get("code"), str):
        try:
            result["identity_diagnostic"] = GitHubAccountVerificationError(diagnostic["code"]).diagnostic()
        except ValueError:
            pass  # An unknown code is not a raw diagnostic or a verified identity.
    return result
