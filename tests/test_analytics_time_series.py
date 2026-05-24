"""Unit tests for analytics time series helpers."""

from app.analytics.time_series import (
    cumulative_series,
    last_n_day_labels,
    merge_daily_counts,
)


def test_last_n_day_labels_count() -> None:
    labels = last_n_day_labels(7)
    assert len(labels) == 7


def test_merge_daily_counts() -> None:
    labels = ["2026-05-20", "2026-05-21", "2026-05-22"]
    rows = [("2026-05-21", 5)]
    assert merge_daily_counts(labels, rows) == [0, 5, 0]


def test_cumulative_series() -> None:
    assert cumulative_series([1, 2, 0, 3]) == [1, 3, 3, 6]
