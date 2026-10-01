"""Pure event result calculations; callers supply valid observed evidence."""
from __future__ import annotations

import statistics
from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable

from .traffic import percentage_change


def _utc_date(value: str) -> date:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).date()


def build_event_metric_result(
    *,
    metric: str,
    event_day: date,
    window_days: int,
    latest_day: str | None,
    pre_rows: list[Any],
    post_rows: list[Any],
    portfolio_rows: list[Any],
    is_profile_repository_name: Callable[[str], bool],
) -> dict[str, Any]:
    """Summarize valid equal windows and supplied per-repository aggregates.

    Availability, creation dates, current-day exclusion and window completeness
    are checked by the caller. This function does not read storage or the clock.
    The profile-repository predicate is an explicit dependency, not app state.
    """
    pre_start = event_day - timedelta(days=window_days)
    pre_end = event_day - timedelta(days=1)
    effective_post_end = event_day + timedelta(days=window_days - 1)
    pre_total = sum(int(row["value"] or 0) for row in pre_rows)
    post_total = sum(int(row["value"] or 0) for row in post_rows)
    target_change = percentage_change(post_total, pre_total)
    change_kind = "new" if pre_total == 0 and post_total > 0 else "measured"

    portfolio_changes = []
    for row in portfolio_rows:
        if is_profile_repository_name(str(row["repo"])):
            continue
        if int(row["pre_days"] or 0) < window_days or int(row["post_days"] or 0) < window_days:
            continue
        previous = int(row["pre"] or 0)
        current = int(row["post"] or 0)
        if previous <= 0:
            continue
        change = percentage_change(current, previous)
        if change is not None:
            portfolio_changes.append(float(change))

    portfolio_change = (
        round(float(statistics.median(portfolio_changes)), 1)
        if portfolio_changes
        else None
    )
    lift = (
        round(float(target_change) - portfolio_change, 1)
        if target_change is not None and portfolio_change is not None
        else None
    )
    if window_days == 7 and len(portfolio_changes) >= 3:
        confidence = "high"
    elif window_days >= 4 and len(portfolio_changes) >= 2:
        confidence = "medium"
    else:
        confidence = "low"

    return {
        "metric": metric,
        "status": "complete" if window_days == 7 else "collecting",
        "window_days": window_days,
        "latest_day": latest_day,
        "period": {
            "pre_from": pre_start.isoformat(),
            "pre_to": pre_end.isoformat(),
            "post_from": event_day.isoformat(),
            "post_to": effective_post_end.isoformat(),
        },
        "pre": pre_total,
        "post": post_total,
        "change_pct": target_change,
        "change_kind": change_kind,
        "portfolio_change_pct": portfolio_change,
        "portfolio_repositories": len(portfolio_changes),
        "lift_pct_points": lift,
        "confidence": confidence,
    }


def describe_event_outcome(metrics: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Use the strongest measured metric for both the headline and confidence."""
    measured = [
        row
        for row in metrics.values()
        if row.get("lift_pct_points") is not None
    ]
    strongest = max(
        measured,
        key=lambda row: abs(float(row["lift_pct_points"])),
        default=None,
    )
    if strongest is None:
        if any(metric.get("status") == "stale_upstream" for metric in metrics.values()):
            outcome_key = "stale_upstream"
            outcome = "Traffic data unavailable"
            summary = "GitHub traffic data is stale; no reliable before/after read is available."
        else:
            outcome_key = "collecting"
            outcome = "Collecting evidence"
            summary = "A comparable before/after window is not available yet."
    else:
        lift = float(strongest["lift_pct_points"])
        metric_label = "page views" if strongest["metric"] == "views" else "clone events"
        if lift >= 25:
            outcome_key = "outperformed"
            outcome = "Outperformed portfolio baseline"
        elif lift <= -25:
            outcome_key = "underperformed"
            outcome = "Underperformed portfolio baseline"
        else:
            outcome_key = "matched"
            outcome = "Moved with portfolio baseline"
        summary = (
            f"{metric_label.capitalize()} changed "
            f"{float(strongest['change_pct']):+g}% versus a "
            f"{float(strongest['portfolio_change_pct']):+g}% portfolio median."
        )
    confidence = str(strongest.get("confidence") or "low") if strongest else "low"
    return {
        "outcome_key": outcome_key,
        "outcome": outcome,
        "summary": summary,
        "confidence": confidence,
        "important": bool(
            strongest
            and abs(float(strongest["lift_pct_points"])) >= 50
            and confidence in {"medium", "high"}
        ),
    }
