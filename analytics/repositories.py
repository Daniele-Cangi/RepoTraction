"""Repository metadata, readiness and adoption calculations without I/O or clocks."""
from __future__ import annotations

from typing import Any


def repository_license_metadata(repo: dict[str, Any]) -> dict[str, str]:
    license_value = repo.get("license")
    if not isinstance(license_value, dict):
        return {"spdx_id": "", "name": "", "status": "missing"}
    spdx_id = str(license_value.get("spdx_id") or "")
    return {
        "spdx_id": spdx_id,
        "name": str(license_value.get("name") or ""),
        "status": (
            "recognized"
            if spdx_id and spdx_id != "NOASSERTION"
            else "present_unrecognized"
        ),
    }


def build_adoption_signal(
    clone_events: Any,
    unique_cloners: Any,
) -> dict[str, Any]:
    """Describe same-window GitHub cloning without implying conversion."""
    if clone_events is None or unique_cloners is None:
        return {
            "key": "unavailable",
            "label": "Cloning data unavailable",
            "detail": "GitHub's native 14-day clone totals are not available.",
            "clone_events": clone_events,
            "unique_cloners": unique_cloners,
            "breadth_pct": None,
            "repeat_factor": None,
            "confidence": "unavailable",
        }

    events = max(0, int(clone_events))
    uniques = max(0, int(unique_cloners))
    breadth_pct = round((uniques / events) * 100, 1) if events else None
    repeat_factor = round(events / uniques, 1) if uniques else None

    if events == 0:
        key, label = "quiet", "No cloning activity"
        confidence = "high"
    elif uniques == 0:
        key, label = "uncertain", "Clone events need context"
        confidence = "low"
    elif events >= 10 and uniques >= 8 and (breadth_pct or 0) >= 60:
        key, label = "broad", "Broad cloning signal"
        confidence = "medium"
    elif events >= 10 and (repeat_factor or 0) >= 3:
        key, label = "repeat_heavy", "Repeat-heavy cloning"
        confidence = "low"
    elif events >= 5:
        key, label = "emerging", "Emerging cloning signal"
        confidence = "medium"
    else:
        key, label = "early", "Early cloning activity"
        confidence = "low"

    if events == 0:
        detail = "GitHub recorded no full clone events in its current 14-day window."
    elif uniques == 0:
        detail = (
            f"GitHub recorded {events} full clone events but no usable unique "
            "cloner total in the same window."
        )
    else:
        detail = (
            f"{events} full clone events from {uniques} unique cloners in "
            f"GitHub's current 14-day window ({repeat_factor:g}× repeat factor)."
        )

    return {
        "key": key,
        "label": label,
        "detail": detail,
        "clone_events": events,
        "unique_cloners": uniques,
        "breadth_pct": breadth_pct,
        "repeat_factor": repeat_factor,
        "confidence": confidence,
    }


def repository_health(
    repo: dict[str, Any],
    *,
    is_profile: bool,
    pushed_days_ago: int | None,
) -> dict[str, Any]:
    """Score metadata using caller-supplied profile applicability and activity age."""
    score = 100
    gaps: list[str] = []
    notes: list[str] = []

    if is_profile:
        return {
            "score": None,
            "gaps": [],
            "notes": ["profile repository · project readiness does not apply"],
            "pushed_days_ago": pushed_days_ago,
            "applicable": False,
        }

    if not str(repo.get("description") or "").strip():
        score -= 20
        gaps.append("description")
    if len(repo.get("topics") or []) < 2:
        score -= 15
        gaps.append("topics")
    license_id = str(repo.get("license") or "")
    license_status = str(repo.get("license_status") or "")
    if not license_status:
        license_status = (
            "present_unrecognized"
            if license_id == "NOASSERTION"
            else "recognized"
            if license_id
            else "missing"
        )
    if not repo.get("private") and license_status == "missing":
        score -= 20
        gaps.append("license")
    elif license_status == "present_unrecognized":
        notes.append("license present · GitHub does not recognize its SPDX type")
    if not str(repo.get("homepage") or "").strip():
        score -= 5
        gaps.append("homepage")

    if pushed_days_ago is None:
        score -= 10
        gaps.append("recent activity")
    elif pushed_days_ago > 180:
        score -= 20
        gaps.append("recent activity")
    elif pushed_days_ago > 90:
        score -= 10
        gaps.append("recent activity")

    return {
        "score": max(0, score),
        "gaps": gaps,
        "notes": notes,
        "pushed_days_ago": pushed_days_ago,
        "applicable": True,
    }
