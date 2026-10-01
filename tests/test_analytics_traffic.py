"""Characterization of traffic calculations before and after modular extraction."""
import copy
import sqlite3
import unittest
from datetime import datetime, timezone

import app as traffic


class TrafficCalculationTests(unittest.TestCase):
    def test_percentage_change_preserves_zero_baselines_and_rounding(self):
        for current, previous, expected in ((0, 0, 0.0), (5, 0, None), (0, 5, -100.0),
                                             (15, 10, 50.0), (4, 3, 33.3), (3, 4, -25.0)):
            with self.subTest(current=current, previous=previous):
                self.assertEqual(traffic.percentage_change(current, previous), expected)

    def test_period_labels_preserve_partial_full_and_invalid_dates(self):
        for end, days, expected in ((None, 0, "no traffic window yet"),
                                     ("2026-08-25", 7, "7d ending Aug 25 UTC"),
                                     ("2026-08-25", 2, "2/7 days through Aug 25 UTC"),
                                     ("invalid", 3, "3/7 days through invalid UTC")):
            with self.subTest(end=end, days=days):
                self.assertEqual(traffic.traffic_period_label(end, days), expected)

    def test_empty_periods_preserve_unknown_not_zero_evidence(self):
        expected = {"from": None, "to": None, "days_available": 0,
                    "is_complete": False, "label": "no traffic window yet"}
        for rows in ([], [{}], [{"traffic_period": {"from": "2026-08-19", "to": None}}]):
            self.assertEqual(traffic.summarize_traffic_period(rows), expected)

    def test_shared_period_uses_minimum_coverage_without_mutating_inputs(self):
        rows = [{"traffic_period": {"from": "2026-08-19", "to": "2026-08-25",
                                    "days_available": days, "is_complete": complete}}
                for days, complete in ((7, True), (3, False))]
        before = copy.deepcopy(rows)
        self.assertEqual(traffic.summarize_traffic_period(rows), {
            "from": "2026-08-19", "to": "2026-08-25", "days_available": 3,
            "is_complete": False, "label": "3/7 days through Aug 25 UTC"})
        self.assertEqual(rows, before)

    def test_different_periods_do_not_claim_a_shared_date_range(self):
        rows = [{"traffic_period": {"from": start, "to": end, "days_available": 7, "is_complete": True}}
                for start, end in (("2026-08-19", "2026-08-25"), ("2026-08-18", "2026-08-24"))]
        self.assertEqual(traffic.summarize_traffic_period(rows), {
            "from": None, "to": None, "days_available": 7,
            "is_complete": True, "label": "per-repository rolling 7d"})

    def test_timestamp_parsing_preserves_utc_naive_and_invalid_inputs(self):
        expected = datetime(2026, 8, 25, tzinfo=timezone.utc)
        for value in ("2026-08-25T00:00:00Z", "2026-08-25T02:00:00+02:00", "2026-08-25"):
            self.assertEqual(traffic.parse_utc_timestamp(value), expected)
        for value in (None, "", "not a date", "2026-02-30"):
            self.assertIsNone(traffic.parse_utc_timestamp(value))

    def test_comparison_with_no_valid_rows_and_single_observation(self):
        latest, baseline, period = traffic.select_comparison_window(
            [{"collected_at": "invalid"}, {}], first_label="first observation")
        self.assertEqual((latest, baseline), ({}, {}))
        self.assertEqual(period, {"from": None, "to": None, "days_observed": 0.0,
            "is_full_window": False, "has_baseline": False, "label": "no comparison yet"})
        row = {"collected_at": "2026-08-25T02:00:00+02:00", "stars": 5}
        latest, baseline, period = traffic.select_comparison_window([row], first_label="first observation")
        self.assertEqual(latest, row)
        self.assertEqual(baseline, {})
        self.assertEqual(period["to"], "2026-08-25T00:00:00+00:00")
        self.assertFalse(period["has_baseline"])

    def test_comparison_chooses_latest_baseline_at_or_before_cutoff(self):
        rows = [{"collected_at": f"2026-08-{day:02d}T00:00:00Z", "stars": day}
                for day in (25, 17, 19, 18)] + [{"collected_at": "invalid"}]
        before = copy.deepcopy(rows)
        latest, baseline, period = traffic.select_comparison_window(rows, first_label="first observation")
        self.assertEqual((latest["stars"], baseline["stars"]), (25, 18))
        self.assertEqual(period["days_observed"], 7.0)
        self.assertTrue(period["is_full_window"])
        self.assertTrue(period["has_baseline"])
        self.assertEqual(period["label"], "last 7 days")
        self.assertEqual(rows, before)

    def test_comparison_preserves_early_hours_days_and_long_window_labels(self):
        for timestamp, days, full, label in (
            ("2026-08-25T00:00:00Z", 0.0, False, "first observation"),
            ("2026-08-24T22:00:00Z", 0.1, False, "first observation · 2h"),
            ("2026-08-23T00:00:00Z", 2.0, False, "first observation · 2d"),
            ("2026-08-17T00:00:00Z", 8.0, True, "over 8 days"),
        ):
            with self.subTest(timestamp=timestamp):
                _, _, period = traffic.select_comparison_window([
                    {"collected_at": timestamp}, {"collected_at": "2026-08-25T00:00:00Z"}],
                    first_label="first observation")
                self.assertEqual((period["days_observed"], period["is_full_window"], period["label"]),
                                 (days, full, label))
                self.assertEqual(period["has_baseline"], days > 0)

    def test_custom_comparison_duration_remains_supported(self):
        _, _, period = traffic.select_comparison_window([
            {"collected_at": "2026-08-23"}, {"collected_at": "2026-08-25"}],
            first_label="first observation", target_days=2)
        self.assertEqual(period["label"], "last 2 days")
        self.assertTrue(period["is_full_window"])

    def test_comparison_accepts_sqlite_rows(self):
        with sqlite3.connect(":memory:") as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute("SELECT '2026-08-18' AS collected_at, 3 AS stars "
                                      "UNION ALL SELECT '2026-08-25', 5").fetchall()
            latest, baseline, period = traffic.select_comparison_window(rows, first_label="first observation")
        self.assertEqual((latest["stars"], baseline["stars"]), (5, 3))
        self.assertTrue(period["is_full_window"])
