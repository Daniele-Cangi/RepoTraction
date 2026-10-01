"""Pure traffic and snapshot comparisons, independent of HTTP, storage and GitHub."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any


def percentage_change(current: int, previous: int) -> float | None:
    if previous == 0:
        return 0.0 if current == 0 else None
    return round(((current - previous) / previous) * 100, 1)


def traffic_period_label(window_to: Any, days_available: int) -> str:
    if not window_to:
        return "no traffic window yet"
    try:
        parsed = datetime.strptime(str(window_to), "%Y-%m-%d")
        through = f"{parsed.strftime('%b')} {parsed.day} UTC"
    except ValueError:
        through = f"{window_to} UTC"
    if days_available == 7:
        return f"7d ending {through}"
    return f"{days_available}/7 days through {through}"


def summarize_traffic_period(rows: list[dict[str, Any]]) -> dict[str, Any]:
    periods = [
        row.get("traffic_period") or {}
        for row in rows
        if (row.get("traffic_period") or {}).get("to")
    ]
    if not periods:
        return {
            "from": None,
            "to": None,
            "days_available": 0,
            "is_complete": False,
            "label": "no traffic window yet",
        }
    boundaries = {(period.get("from"), period.get("to")) for period in periods}
    complete = all(bool(period.get("is_complete")) for period in periods)
    if len(boundaries) == 1:
        start, end = next(iter(boundaries))
        days_available = min(int(period.get("days_available") or 0) for period in periods)
        return {
            "from": start,
            "to": end,
            "days_available": days_available,
            "is_complete": complete,
            "label": traffic_period_label(end, days_available),
        }
    return {
        "from": None,
        "to": None,
        "days_available": min(int(period.get("days_available") or 0) for period in periods),
        "is_complete": complete,
        "label": "per-repository rolling 7d",
    }


def parse_utc_timestamp(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def select_comparison_window(
    rows: list[Any],
    *,
    first_label: str,
    target_days: int = 7,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    parsed_rows: list[tuple[datetime, dict[str, Any]]] = []
    for row in rows:
        item = dict(row)
        collected_at = parse_utc_timestamp(item.get("collected_at"))
        if collected_at is not None:
            parsed_rows.append((collected_at, item))
    parsed_rows.sort(key=lambda item: item[0])

    if not parsed_rows:
        return {}, {}, {
            "from": None,
            "to": None,
            "days_observed": 0.0,
            "is_full_window": False,
            "has_baseline": False,
            "label": "no comparison yet",
        }

    latest_time, latest = parsed_rows[-1]
    if len(parsed_rows) == 1:
        return latest, {}, {
            "from": None,
            "to": latest_time.isoformat(),
            "days_observed": 0.0,
            "is_full_window": False,
            "has_baseline": False,
            "label": "no comparison yet",
        }

    cutoff = latest_time - timedelta(days=target_days)
    eligible = [item for item in parsed_rows if item[0] <= cutoff]
    baseline_time, baseline = eligible[-1] if eligible else parsed_rows[0]
    days_observed = max(
        0.0, (latest_time - baseline_time).total_seconds() / (24 * 60 * 60)
    )
    is_full_window = days_observed >= target_days
    rounded_days = round(days_observed, 1)

    if rounded_days == target_days:
        label = f"last {target_days} days"
    elif is_full_window:
        label = f"over {rounded_days:g} days"
    elif days_observed >= 1:
        label = f"{first_label} · {rounded_days:g}d"
    elif days_observed > 0:
        hours = max(1, round(days_observed * 24))
        label = f"{first_label} · {hours}h"
    else:
        label = first_label

    return latest, baseline, {
        "from": baseline_time.isoformat(),
        "to": latest_time.isoformat(),
        "days_observed": rounded_days,
        "is_full_window": is_full_window,
        "has_baseline": days_observed > 0,
        "label": label,
    }
