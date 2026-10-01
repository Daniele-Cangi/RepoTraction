"""Opportunity calculations and ranking using supplied readiness and signals."""
from __future__ import annotations

from typing import Any

from .traffic import percentage_change


def build_repository_opportunities(
    repo: dict[str, Any],
    signal: dict[str, Any],
    health: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Calculate rows for one eligible repository without I/O or clock access.

    The caller excludes profiles, archives, forks and unnamed repositories and
    supplies readiness with an already calculated activity age. Process one
    repository at a time so validation failures do not evaluate later adapters.
    Readiness gap/note lists retain their existing reference semantics.
    """
    full_name = str(repo.get("full_name") or "")
    opportunities: list[dict[str, Any]] = []
    health_rows: list[dict[str, Any]] = []
    if health["applicable"]:
        health_rows.append(
            {
                "repo": full_name,
                "name": repo.get("name") or full_name.split("/", 1)[-1],
                "score": health["score"],
                "gaps": health["gaps"],
                "notes": health["notes"],
                "url": repo.get("html_url") or f"https://github.com/{full_name}",
            }
        )

    repo_name = str(repo.get("name") or full_name.split("/", 1)[-1])
    repo_url = str(repo.get("html_url") or f"https://github.com/{full_name}")
    views = int(signal.get("views_7d") or 0)
    # Retain the original validation, even though clone suggestions use native totals.
    clones = int(signal.get("clones_7d") or 0)
    net_stars = signal.get("net_stars")
    previous_views = int(signal.get("previous_views") or 0)
    adoption_signal = signal.get("adoption_signal") or {}
    native_clone_events = adoption_signal.get("clone_events")
    native_unique_cloners = adoption_signal.get("unique_cloners")
    clone_repeat_factor = adoption_signal.get("repeat_factor")
    views_comparison_ready = bool(
        signal.get(
            "views_comparison_ready", signal.get("traffic_comparison_ready")
        )
    )
    star_comparison_ready = bool(
        (signal.get("snapshot_period") or {}).get("is_full_window")
    )
    growth = (
        percentage_change(views, previous_views)
        if views_comparison_ready
        else None
    )

    essential_gaps = [
        gap for gap in health["gaps"] if gap in {"description", "topics", "license"}
    ]
    if health["applicable"] and essential_gaps:
        missing = ", ".join(essential_gaps)
        opportunities.append(
            {
                "kind": "foundation",
                "priority": "high" if "license" in essential_gaps else "medium",
                "repo": full_name,
                "title": f"Complete {repo_name}'s essentials",
                "detail": f"Missing or weak repository metadata: {missing}.",
                "action": "Add the missing metadata so visitors understand and trust the project faster.",
                "metric": f"Readiness {health['score']}/100",
                "confidence": "high",
                "score": 95 - health["score"],
                "url": repo_url,
            }
        )

    if (
        views >= 10
        and views_comparison_ready
        and star_comparison_ready
        and net_stars is not None
        and int(net_stars) <= 0
    ):
        opportunities.append(
            {
                "kind": "discoverability",
                "priority": "high" if views >= 20 else "medium",
                "repo": full_name,
                "title": f"Review {repo_name}'s repository landing page",
                "detail": (
                    f"{views} page views in "
                    f"{(signal.get('traffic_period') or {}).get('label', 'the current window')} "
                    "with no net star growth over a complete snapshot window."
                ),
                "action": "Sharpen the README opening, demo and primary call to action.",
                "metric": f"{views} views · {int(net_stars):+d} net stars",
                "confidence": "medium",
                "score": 70 + min(views, 30),
                "url": repo_url,
            }
        )

    if (
        native_clone_events is not None
        and int(native_clone_events) >= 5
        and native_unique_cloners is not None
    ):
        repeat_label = (
            f" · {clone_repeat_factor:g}× repeat"
            if clone_repeat_factor is not None
            else ""
        )
        opportunities.append(
            {
                "kind": "developer_experience",
                "priority": "low",
                "repo": full_name,
                "title": f"Review {repo_name}'s cloning pattern",
                "detail": (
                    f"GitHub recorded {int(native_clone_events)} full clone events "
                    f"from {int(native_unique_cloners)} unique cloners in the same "
                    "14-day window; identities and automation remain unknown."
                ),
                "action": "Check automation patterns first, then improve the quick start if human setup friction is plausible.",
                "metric": (
                    f"{adoption_signal.get('label', 'Cloning signal')}"
                    f"{repeat_label}"
                ),
                "confidence": "low",
                "score": 55 + min(int(native_clone_events), 30),
                "url": repo_url,
            }
        )

    is_new_traffic = views_comparison_ready and growth is None and views >= 5
    if is_new_traffic or (growth is not None and growth >= 50 and views >= 5):
        growth_label = "new traffic" if growth is None else f"+{growth:g}% traffic"
        opportunities.append(
            {
                "kind": "momentum",
                "priority": "low",
                "repo": full_name,
                "title": f"Capture {repo_name}'s momentum",
                "detail": f"{growth_label} is creating a short window for discovery.",
                "action": "Publish a small release or update while attention is elevated.",
                "metric": f"{views} page views · {growth_label}",
                "confidence": "medium",
                "score": 40 + min(views, 30),
                "url": repo_url,
            }
        )

    pushed_days_ago = health["pushed_days_ago"]
    if (
        views_comparison_ready
        and pushed_days_ago is not None
        and pushed_days_ago > 120
        and views >= 3
    ):
        opportunities.append(
            {
                "kind": "freshness",
                "priority": "medium",
                "repo": full_name,
                "title": f"Refresh {repo_name} while people still visit",
                "detail": f"The repository still attracts traffic but was last pushed {pushed_days_ago} days ago.",
                "action": "Confirm compatibility, refresh examples and publish maintenance notes.",
                "metric": f"{views} page views · {pushed_days_ago}d since push",
                "confidence": "medium",
                "score": 60 + min(views, 20),
                "url": repo_url,
            }
        )
    return opportunities, health_rows


def rank_opportunities(
    opportunities: list[dict[str, Any]],
    health_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return stable ranked lists without changing the supplied list order."""
    priority_rank = {"high": 3, "medium": 2, "low": 1}
    return (
        sorted(
            opportunities,
            key=lambda item: (priority_rank[item["priority"]], int(item["score"])),
            reverse=True,
        ),
        sorted(
            health_rows,
            key=lambda item: (int(item["score"]), str(item["name"]).casefold()),
        ),
    )
