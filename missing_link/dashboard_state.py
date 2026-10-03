"""Opt-in polling projection; stored evidence and the legacy full view are unchanged."""
import re


_REPOSITORY = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})/[A-Za-z0-9_.-]{1,100}")


def dashboard_selection(query):
    """None selects the existing full contract; an empty string selects the index."""
    query = query or {}
    if "view" not in query:
        return None
    if query["view"] != ["dashboard"]:
        raise ValueError("Unknown Missing Link polling view.")
    values = query.get("repo", [""])
    if len(values) != 1 or not isinstance(values[0], str):
        raise ValueError("Choose a single public repository for dashboard polling.")
    repository = values[0]
    if repository and not _REPOSITORY.fullmatch(repository):
        raise ValueError("Choose a repository in OWNER/REPO form.")
    return repository


def project_dashboard(state, repository):
    """Keep complete selected evidence, all job results and explicit projection metadata.

    Matching uses current repository IDs, not historic names. This mirrors the UI
    boundary across renames/name reuse. Superseded/stale records stay available.
    No truncation, pagination, DB write or new qualification occurs here.
    """
    if state.get("diagnostic_only"):
        return state  # Never broaden the minimal unverified-identity response.
    repositories = state.get("repositories", [])
    selected = next((repo for repo in repositories
        if repo.get("full_name", "").casefold() == repository.casefold()), None)
    selected_id = selected.get("id") if selected else None
    matches = [match for match in state.get("matches", []) if selected_id is not None
        and match.get("repo_id") is not None and str(match["repo_id"]) == str(selected_id)]
    summaries = [repo if repo is selected else {
        "id": repo.get("id"), "full_name": repo.get("full_name"), "revision": repo.get("revision"),
        "capability_count": len(repo.get("capabilities", [])), "evidence_loaded": False,
    } for repo in repositories]
    # The page renders result warnings/details, budgets and actions for every job.
    # Only provider trace contexts, unused by the page, are excluded. They remain
    # in the default full-state representation; source-context exports are unchanged.
    jobs = [{key: value for key, value in job.items() if key != "ai_trace"} for job in state.get("jobs", [])]
    return {**state, "repositories": summaries, "matches": matches, "jobs": jobs,
        "dashboard": {"version": 1, "selected_repo": repository,
            "selected_repo_id": selected_id, "total_matches": len(state.get("matches", [])),
            "total_repositories": len(repositories), "full_state_url": "/api/missing-link"}}
