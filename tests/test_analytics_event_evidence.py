"""Characterize Impact Lab evidence using isolated in-memory SQLite history."""
import copy
import sqlite3
import subprocess
import sys
import unittest
from contextlib import closing
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

import app


TODAY = date(2026, 8, 18)
TARGET = "octocat/target"


class FrozenDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        value = datetime(2026, 8, 18, tzinfo=timezone.utc)
        return value.astimezone(tz) if tz else value.replace(tzinfo=None)


class EventEvidenceCharacterizationTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.addCleanup(self.connection.close)
        self.connection.executescript("""
            CREATE TABLE repository_registry (full_name TEXT, created_at TEXT);
            CREATE TABLE traffic_daily (
                repo TEXT, day TEXT, views INTEGER, views_available INTEGER,
                clones INTEGER, clones_available INTEGER, PRIMARY KEY (repo, day)
            );
        """)
        clock = mock.patch.object(app, "datetime", FrozenDateTime)
        clock.start()
        self.addCleanup(clock.stop)

    def add(self, day, *, repo=TARGET, views=10, clones=20, views_available=1, clones_available=1):
        self.connection.execute("INSERT INTO traffic_daily VALUES (?, ?, ?, ?, ?, ?)",
                                (repo, day.isoformat(), views, views_available, clones, clones_available))

    def window(self, event_day, *, pre=7, post=7, **values):
        for offset in range(-pre, post):
            self.add(event_day + timedelta(days=offset), **values)

    def analyze(self, event_day, metric="views"):
        return app.analyze_event_metric(self.connection, repo=TARGET, event_day=event_day, metric=metric)

    @staticmethod
    def unavailable(*, metric="views", status="waiting", message, days=0, latest=None):
        return {"metric": metric, "status": status, "message": message, "window_days": days,
                "latest_day": latest, "pre": None, "post": None, "change_pct": None,
                "change_kind": status, "portfolio_change_pct": None, "portfolio_repositories": 0,
                "lift_pct_points": None, "confidence": "low"}

    def test_unobserved_zero_window_preserves_entire_waiting_contract(self):
        event_day = TODAY - timedelta(days=7)
        self.window(event_day, views=0, clones=0, views_available=0, clones_available=0)
        for metric in ("views", "clones"):
            with self.subTest(metric=metric):
                self.assertEqual(self.analyze(event_day, metric), self.unavailable(metric=metric,
                    message="Waiting for GitHub traffic data; no daily bucket is available for this event yet."))

    def test_observed_zero_is_measurable_but_unavailable_baseline_zero_is_not(self):
        event_day = TODAY - timedelta(days=7)
        self.window(event_day, views=0, clones=0)
        result = self.analyze(event_day)
        self.assertEqual((result["status"], result["pre"], result["post"], result["change_pct"]),
                         ("complete", 0, 0, 0.0))
        self.connection.execute("UPDATE traffic_daily SET views_available = 0 WHERE day = ?",
                                ((event_day - timedelta(days=3)).isoformat(),))
        self.assertEqual(self.analyze(event_day), self.unavailable(days=7, latest="2026-08-17",
            message="Waiting for a complete pre-event baseline; this repository does not have enough valid days yet."))
        self.assertEqual(self.analyze(event_day, "clones")["status"], "complete")

    def test_no_post_bucket_staleness_boundary_is_strictly_more_than_two_days(self):
        for age, status in ((1, "waiting"), (2, "waiting"), (3, "stale_upstream")):
            with self.subTest(age=age):
                self.connection.execute("DELETE FROM traffic_daily")
                latest = TODAY - timedelta(days=age)
                self.add(latest)
                message = (f"GitHub traffic data is stale: the latest observed bucket is {age} days old."
                           if status == "stale_upstream" else
                           "Waiting for GitHub traffic data; no daily bucket is available for this event yet.")
                self.assertEqual(self.analyze(TODAY), self.unavailable(status=status, message=message,
                                                                     latest=latest.isoformat()))

    def test_partial_zero_window_is_measured_at_two_days_but_stale_at_three(self):
        for age, status in ((2, "collecting"), (3, "stale_upstream")):
            with self.subTest(age=age):
                self.connection.execute("DELETE FROM traffic_daily")
                event_day = TODAY - timedelta(days=age)
                self.window(event_day, pre=1, post=1, views=0)
                result = self.analyze(event_day)
                self.assertEqual((result["status"], result["window_days"]), (status, 1))
                self.assertEqual(result["pre"], 0 if status == "collecting" else None)
                self.assertEqual(result["post"], 0 if status == "collecting" else None)
                self.assertEqual(result["change_pct"], 0.0 if status == "collecting" else None)

    def test_latest_observation_after_window_keeps_contiguous_early_read_fresh(self):
        event_day = TODAY - timedelta(days=10)
        self.window(event_day, pre=2, post=2)
        self.add(TODAY - timedelta(days=1), views=999)
        result = self.analyze(event_day)
        self.assertEqual((result["status"], result["window_days"], result["latest_day"]),
                         ("collecting", 2, "2026-08-17"))
        self.assertEqual((result["pre"], result["post"]), (20, 20))
        self.assertEqual(result["period"]["post_to"], "2026-08-09")

    def test_missing_event_day_does_not_start_window_at_later_bucket(self):
        event_day = TODAY - timedelta(days=2)
        self.add(event_day + timedelta(days=1))
        self.assertEqual(self.analyze(event_day), self.unavailable(latest="2026-08-17",
            message="Waiting for GitHub traffic data; no daily bucket is available for this event yet."))

    def test_hole_in_post_window_stops_at_first_unavailable_metric_day(self):
        event_day = TODAY - timedelta(days=7)
        self.window(event_day)
        self.connection.execute("UPDATE traffic_daily SET views_available = 0 WHERE day = ?",
                                ((event_day + timedelta(days=2)).isoformat(),))
        result = self.analyze(event_day)
        self.assertEqual((result["status"], result["window_days"], result["pre"], result["post"]),
                         ("collecting", 2, 20, 20))
        self.assertEqual(result["period"], {"pre_from": "2026-08-09", "pre_to": "2026-08-10",
                                            "post_from": "2026-08-11", "post_to": "2026-08-12"})
        self.assertEqual(self.analyze(event_day, "clones")["window_days"], 7)

    def test_current_and_future_buckets_do_not_extend_window_or_freshen_latest(self):
        event_day = TODAY - timedelta(days=1)
        self.window(event_day, pre=1, post=3)
        result = self.analyze(event_day)
        self.assertEqual((result["window_days"], result["latest_day"], result["post"]),
                         (1, "2026-08-17", 10))
        self.connection.execute("DELETE FROM traffic_daily WHERE day < ?", (TODAY.isoformat(),))
        self.assertIsNone(self.analyze(event_day)["latest_day"])
        self.assertEqual(self.analyze(event_day)["status"], "waiting")

    def test_creation_lookup_is_case_insensitive_and_baseline_excludes_creation_day(self):
        event_day = TODAY - timedelta(days=2)
        self.window(event_day, pre=2, post=2)
        self.connection.execute("INSERT INTO repository_registry VALUES (?, ?)",
                                (TARGET.upper(), "2026-08-14T12:00:00Z"))
        self.assertEqual(self.analyze(event_day), self.unavailable(days=2, latest="2026-08-17",
            message="Waiting for a complete pre-event baseline; this repository does not have enough valid days yet."))
        self.connection.execute("UPDATE repository_registry SET created_at = '2026-08-13T12:00:00Z'")
        self.assertEqual(self.analyze(event_day)["status"], "collecting")

    def test_creation_timestamp_utc_normalization_remains_separate_from_sql_cutoff(self):
        event_day = TODAY - timedelta(days=2)
        self.window(event_day, pre=2, post=2)
        self.connection.execute("INSERT INTO repository_registry VALUES (?, ?)",
                                (TARGET, "2026-08-15T00:30:00+02:00"))
        result = self.analyze(event_day)
        self.assertEqual((result["status"], result["window_days"]), ("waiting", 2))
        self.connection.execute("UPDATE repository_registry SET created_at = '2026-08-14T00:30:00+02:00'")
        self.assertEqual(self.analyze(event_day)["status"], "collecting")

    def test_missing_or_invalid_creation_date_preserves_existing_fallback(self):
        event_day = TODAY - timedelta(days=7)
        self.window(event_day)
        for created_at in (None, "", "2026-08-01-invalid", "invalid"):
            with self.subTest(created_at=created_at):
                self.connection.execute("DELETE FROM repository_registry")
                self.connection.execute("INSERT INTO repository_registry VALUES (?, ?)", (TARGET, created_at))
                result = self.analyze(event_day)
                self.assertEqual((result["status"], result["pre"], result["post"]), ("complete", 70, 70))
                self.assertEqual(result["latest_day"], None if created_at == "invalid" else "2026-08-17")

    def test_stale_status_wins_when_baseline_is_incomplete(self):
        event_day = TODAY - timedelta(days=10)
        self.window(event_day, pre=1, post=3)
        result = self.analyze(event_day)
        self.assertEqual(result, self.unavailable(status="stale_upstream", days=3, latest="2026-08-10",
            message="GitHub traffic data is stale: the latest observed bucket is 8 days old."))

    def test_complete_historical_window_is_valid_even_with_stale_latest_bucket(self):
        event_day = TODAY - timedelta(days=30)
        self.window(event_day)
        result = self.analyze(event_day)
        self.assertEqual((result["status"], result["window_days"], result["pre"], result["post"]),
                         ("complete", 7, 70, 70))

    def test_unavailable_paths_skip_baseline_and_portfolio_queries_as_before(self):
        for post, pre, expected_queries in ((0, 0, 3), (2, 0, 4), (2, 2, 5)):
            with self.subTest(post=post, pre=pre):
                self.connection.execute("DELETE FROM traffic_daily")
                event_day = TODAY - timedelta(days=2)
                self.window(event_day, pre=pre, post=post)
                queries = []
                self.connection.set_trace_callback(queries.append)
                try:
                    self.analyze(event_day)
                finally:
                    self.connection.set_trace_callback(None)
                self.assertEqual(len(queries), expected_queries)

    def test_unsupported_metric_does_not_touch_connection(self):
        connection = mock.Mock()
        with self.assertRaisesRegex(ValueError, "Unsupported impact metric"):
            app.analyze_event_metric(connection, repo=TARGET, event_day=TODAY, metric="stars")
        connection.execute.assert_not_called()
        self.assertNotEqual(connection.row_factory, sqlite3.Row)

    def test_analysis_does_not_write_history_or_commit_transaction(self):
        event_day = TODAY - timedelta(days=7)
        self.window(event_day)
        before = self.connection.execute("SELECT * FROM traffic_daily ORDER BY repo, day").fetchall()
        changes = self.connection.total_changes
        self.assertTrue(self.connection.in_transaction)
        self.analyze(event_day)
        self.assertEqual(self.connection.total_changes, changes)
        self.assertTrue(self.connection.in_transaction)
        after = [tuple(row) for row in self.connection.execute("SELECT * FROM traffic_daily ORDER BY repo, day")]
        self.assertEqual(after, before)

    def test_adapter_delegates_with_explicit_clock_creation_and_baseline_counts(self):
        from analytics import event_evidence
        event_day = TODAY - timedelta(days=2)
        self.window(event_day, pre=2, post=2)
        self.connection.execute("INSERT INTO repository_registry VALUES (?, ?)",
                                (TARGET, "2026-08-13T12:00:00Z"))
        with mock.patch.object(app, "select_event_post_rows", wraps=event_evidence.select_event_post_rows) as select, \
             mock.patch.object(app, "filter_event_evidence_rows", wraps=event_evidence.filter_event_evidence_rows) as filter_rows, \
             mock.patch.object(app, "event_window_dates", wraps=event_evidence.event_window_dates) as bounds, \
             mock.patch.object(app, "event_evidence_unavailable", wraps=event_evidence.event_evidence_unavailable) as status:
            result = self.analyze(event_day)
        self.assertEqual(result["status"], "collecting")
        self.assertEqual(select.call_count, 1)
        self.assertEqual(select.call_args.kwargs, {"event_day": event_day, "today": TODAY,
                                                  "created_day": date(2026, 8, 13)})
        self.assertEqual(filter_rows.call_count, 1)
        self.assertEqual(filter_rows.call_args.kwargs, {"today": TODAY, "created_day": date(2026, 8, 13)})
        bounds.assert_called_once_with(event_day, 2)
        self.assertEqual(status.call_args_list, [
            mock.call(metric="views", today=TODAY, latest_day="2026-08-17", window_days=2),
            mock.call(metric="views", today=TODAY, latest_day="2026-08-17", window_days=2, baseline_days=2)])


class PureEventEvidenceTests(unittest.TestCase):
    def test_entrypoint_keeps_same_pure_helper_objects(self):
        from analytics import event_evidence
        for name in ("filter_event_evidence_rows", "select_event_post_rows", "event_window_dates",
                     "event_evidence_unavailable"):
            self.assertIs(getattr(app, name), getattr(event_evidence, name))

    def test_filter_uses_supplied_boundaries_without_mutation_or_inventing_days(self):
        from analytics import event_evidence
        rows = [{"day": "2026-08-14", "value": 10}, {"day": "2026-08-15", "value": 0},
                {"day": "2026-08-16", "value": None}, {"day": "2026-08-18", "value": 99},
                {"day": "2026-08-19", "value": 100}]
        before = copy.deepcopy(rows)
        result = event_evidence.filter_event_evidence_rows(rows, today=TODAY, created_day=date(2026, 8, 14))
        self.assertEqual(result, rows[1:3])
        self.assertIs(result[0], rows[1])
        self.assertIs(result[1], rows[2])
        self.assertEqual(rows, before)
        self.assertEqual(event_evidence.filter_event_evidence_rows([], today=TODAY, created_day=None), [])
        self.assertEqual(event_evidence.filter_event_evidence_rows(rows, today=TODAY, created_day=None), rows[:3])

    def test_post_selection_orders_caps_and_stops_at_first_gap_without_mutating_rows(self):
        from analytics import event_evidence
        event_day = date(2026, 8, 1)
        rows = [{"day": (event_day + timedelta(days=i)).isoformat(), "value": i} for i in range(9)]
        reversed_rows = list(reversed(rows))
        before = copy.deepcopy(reversed_rows)
        self.assertEqual(event_evidence.select_event_post_rows(reversed_rows, event_day=event_day,
                                                              today=TODAY, created_day=None), rows[:7])
        self.assertEqual(reversed_rows, before)
        self.assertEqual(event_evidence.select_event_post_rows(rows[:2] + rows[3:], event_day=event_day,
                                                              today=TODAY, created_day=None), rows[:2])
        self.assertEqual(event_evidence.select_event_post_rows(rows[1:], event_day=event_day,
                                                              today=TODAY, created_day=None), [])
        self.assertEqual(event_evidence.select_event_post_rows(rows, event_day=event_day,
                                                              today=TODAY, created_day=event_day), [])

    def test_post_selection_preserves_last_duplicate_and_row_identity(self):
        from analytics import event_evidence
        first = {"day": "2026-08-16", "value": 10}
        last = {"day": "2026-08-16", "value": 0}
        next_day = {"day": "2026-08-17", "value": 5}
        selected = event_evidence.select_event_post_rows([next_day, first, last], event_day=date(2026, 8, 16),
                                                        today=TODAY, created_day=None)
        self.assertEqual(selected, [last, next_day])
        self.assertIs(selected[0], last)
        self.assertIs(selected[1], next_day)

    def test_window_dates_preserve_equal_before_after_windows(self):
        from analytics import event_evidence
        event_day = date(2026, 8, 10)
        for days in range(1, 8):
            with self.subTest(days=days):
                self.assertEqual(event_evidence.event_window_dates(event_day, days),
                                 (event_day - timedelta(days=days), event_day - timedelta(days=1),
                                  event_day + timedelta(days=days - 1)))

    def test_two_phase_status_preserves_stale_waiting_and_historical_rules(self):
        from analytics import event_evidence
        for latest, days, baseline, expected in (
            (None, 0, None, "waiting"), ("2026-08-16", 0, None, "waiting"),
            ("2026-08-15", 0, None, "stale_upstream"),
            ("2026-08-10", 2, None, None), ("2026-08-10", 2, 2, "stale_upstream"),
            ("2026-08-16", 2, 1, "waiting"), ("2026-08-16", 2, 2, None),
            (None, 2, 2, None), ("2026-08-10", 7, 7, None),
            ("2026-08-10", 7, 6, "stale_upstream"), ("2026-08-16", 7, 6, "waiting"),
        ):
            with self.subTest(latest=latest, days=days, baseline=baseline):
                result = event_evidence.event_evidence_unavailable(metric="clones", today=TODAY,
                    latest_day=latest, window_days=days, baseline_days=baseline)
                if expected is None:
                    self.assertIsNone(result)
                else:
                    self.assertEqual((result["metric"], result["status"], result["change_kind"], result["window_days"]),
                                     ("clones", expected, expected, days))
                    for field in ("pre", "post", "change_pct", "portfolio_change_pct", "lift_pct_points"):
                        self.assertIsNone(result[field])
                    self.assertNotIn("period", result)

    def test_unavailable_results_are_fresh_and_never_contain_measured_zero(self):
        from analytics import event_evidence
        kwargs = {"metric": "views", "today": TODAY, "latest_day": None, "window_days": 0}
        first = event_evidence.event_evidence_unavailable(**kwargs)
        first["pre"] = 0
        second = event_evidence.event_evidence_unavailable(**kwargs)
        self.assertIsNone(second["pre"])
        self.assertEqual(second["portfolio_repositories"], 0)
        self.assertEqual(second["confidence"], "low")

    def test_direct_helpers_accept_sqlite_rows_after_connection_is_closed(self):
        from analytics import event_evidence
        with closing(sqlite3.connect(":memory:")) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute("SELECT '2026-08-16' AS day, 0 AS value UNION ALL "
                                      "SELECT '2026-08-17', 3").fetchall()
        selected = event_evidence.select_event_post_rows(rows, event_day=date(2026, 8, 16),
                                                        today=TODAY, created_day=None)
        self.assertEqual([row["value"] for row in selected], [0, 3])
        self.assertIs(selected[0], rows[0])

    def test_fresh_import_and_decisions_need_no_entrypoint_provider_io_or_clock(self):
        code = """
import sys
from datetime import date, datetime
from unittest.mock import patch
sys.path.insert(0, sys.argv[1])
class NoClock(datetime):
    @classmethod
    def now(cls, *args, **kwargs):
        raise AssertionError('wall clock access')
with patch('sqlite3.connect', side_effect=AssertionError('database access')), \\
     patch('threading.Thread.start', side_effect=AssertionError('thread start')), \\
     patch('subprocess.run', side_effect=AssertionError('external command')), \\
     patch('socket.create_connection', side_effect=AssertionError('network access')), \\
     patch('datetime.datetime', NoClock), \\
     patch('time.time', side_effect=AssertionError('wall clock access')):
    from analytics import event_evidence
    today = date(2026, 8, 18)
    event = date(2026, 8, 16)
    rows = [{'day': '2026-08-16', 'value': 0}, {'day': '2026-08-17', 'value': 3}]
    selected = event_evidence.select_event_post_rows(rows, event_day=event, today=today, created_day=None)
    assert selected == rows
    assert event_evidence.event_window_dates(event, len(selected)) == (date(2026, 8, 14), date(2026, 8, 15), date(2026, 8, 17))
    assert event_evidence.event_evidence_unavailable(metric='views', today=today,
        latest_day='2026-08-17', window_days=2, baseline_days=2) is None
    stale = event_evidence.event_evidence_unavailable(metric='views', today=today,
        latest_day='2026-08-15', window_days=2, baseline_days=2)
    assert stale['status'] == 'stale_upstream'
    assert stale['pre'] is None and stale['post'] is None
    assert 'app' not in sys.modules
    assert not any(name == 'missing_link' or name.startswith('missing_link.') for name in sys.modules)
"""
        result = subprocess.run([sys.executable, "-I", "-c", code, str(Path(__file__).resolve().parents[1])],
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
