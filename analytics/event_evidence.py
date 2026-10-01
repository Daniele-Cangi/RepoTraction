"""Event evidence eligibility and window decisions without storage or clocks."""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any


def filter_event_evidence_rows(
    rows: Any,
    *,
    today: date,
    created_day: date | None,
) -> list[Any]:
    """Exclude creation/current days from already observed metric buckets.

    The caller checks metric availability before supplying rows. This function
    does not infer missing buckets, normalize stored day strings or change rows.
    """
    return [
        row
        for row in rows
        if str(row["day"]) < today.isoformat()
        and (created_day is None or str(row["day"]) > created_day.isoformat())
    ]


def select_event_post_rows(
    rows: Any,
    *,
    event_day: date,
    today: date,
    created_day: date | None,
) -> list[Any]:
    """Select up to seven contiguous observed days, beginning at the event."""
    post_by_day = {
        str(row["day"]): row
        for row in filter_event_evidence_rows(rows, today=today, created_day=created_day)
    }
    window_days = 0
    for offset in range(7):
        if (event_day + timedelta(days=offset)).isoformat() not in post_by_day:
            break
        window_days += 1
    return [
        post_by_day[(event_day + timedelta(days=offset)).isoformat()]
        for offset in range(window_days)
    ]


def event_window_dates(event_day: date, window_days: int) -> tuple[date, date, date]:
    """Return before-start, before-end and after-end for a nonempty window."""
    pre_start = event_day - timedelta(days=window_days)
    pre_end = event_day - timedelta(days=1)
    effective_post_end = event_day + timedelta(days=window_days - 1)
    return pre_start, pre_end, effective_post_end


def event_evidence_unavailable(
    *,
    metric: str,
    today: date,
    latest_day: str | None,
    window_days: int,
    baseline_days: int | None = None,
) -> dict[str, Any] | None:
    """Return the existing waiting/stale payload, or permit the next phase.

    Call first after post selection, without a baseline count. If a post window
    exists, load/filter its equally sized baseline and call again with that count.
    Partial-window staleness is checked in this second phase, preserving the
    adapter's query order. Complete historical windows remain valid when stale.
    The metric, latest bucket and available-day counts are supplied by the caller.
    """
    def unavailable(
        status: str,
        message: str,
        *,
        window_days: int = 0,
        latest_day: str | None = None,
    ) -> dict[str, Any]:
        return {
            "metric": metric,
            "status": status,
            "message": message,
            "window_days": window_days,
            "latest_day": latest_day,
            "pre": None,
            "post": None,
            "change_pct": None,
            "change_kind": status,
            "portfolio_change_pct": None,
            "portfolio_repositories": 0,
            "lift_pct_points": None,
            "confidence": "low",
        }

    latest_is_stale = bool(
        latest_day and latest_day < (today - timedelta(days=2)).isoformat()
    )
    if window_days == 0:
        if latest_is_stale:
            age_days = (today - date.fromisoformat(latest_day)).days
            return unavailable(
                "stale_upstream",
                f"GitHub traffic data is stale: the latest observed bucket is {age_days} days old.",
                latest_day=latest_day,
            )
        return unavailable(
            "waiting",
            "Waiting for GitHub traffic data; no daily bucket is available for this event yet.",
            latest_day=latest_day,
        )

    if baseline_days is not None and (
        baseline_days != window_days or (window_days < 7 and latest_is_stale)
    ):
        if latest_is_stale:
            age_days = (today - date.fromisoformat(latest_day)).days
            return unavailable(
                "stale_upstream",
                f"GitHub traffic data is stale: the latest observed bucket is {age_days} days old.",
                window_days=window_days,
                latest_day=latest_day,
            )
        return unavailable(
            "waiting",
            "Waiting for a complete pre-event baseline; this repository does not have enough valid days yet.",
            window_days=window_days,
            latest_day=latest_day,
        )
    return None
