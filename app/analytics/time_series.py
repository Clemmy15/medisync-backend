"""Helpers for chart-ready time series labels and buckets."""

from datetime import date, datetime, timedelta, timezone


def last_n_day_labels(n: int = 14) -> list[str]:
    """Return ISO date strings for the last *n* days (oldest first)."""
    today = datetime.now(timezone.utc).date()
    return [
        (today - timedelta(days=n - 1 - i)).isoformat()
        for i in range(n)
    ]


def day_key(dt: datetime | date | None) -> str | None:
    if dt is None:
        return None
    if isinstance(dt, datetime):
        return dt.date().isoformat()
    return dt.isoformat()


def empty_daily_counts(labels: list[str]) -> dict[str, int]:
    return {label: 0 for label in labels}


def merge_daily_counts(
    labels: list[str],
    rows: list[tuple[str | None, int]],
) -> list[int]:
    counts = empty_daily_counts(labels)
    for raw_day, count in rows:
        key = raw_day if isinstance(raw_day, str) else day_key(raw_day)
        if key in counts:
            counts[key] = count
    return [counts[label] for label in labels]


def cumulative_series(daily: list[int]) -> list[int]:
    total = 0
    result: list[int] = []
    for value in daily:
        total += value
        result.append(total)
    return result
