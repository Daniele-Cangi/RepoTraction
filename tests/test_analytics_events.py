"""Characterize event calculations without real history, GitHub or AI calls."""
import copy
import sqlite3
import subprocess
import sys
import unittest
from contextlib import closing
from contextlib import nullcontext
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

import app


TODAY = date(2026, 8, 18)
EVENT_DAY = date(2026, 8, 10)
TARGET = "octocat/target"


class FrozenDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        value = datetime(2026, 8, 18, tzinfo=timezone.utc)
        return value.astimezone(tz) if tz else value.replace(tzinfo=None)


class EventCharacterizationTests(unittest.TestCase):
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

    def add_window(self, repo=TARGET, *, event_day=EVENT_DAY, pre=None, post=None,
                   views_available=1, clones_available=1):
        pre = [10] * 7 if pre is None else pre
        post = [20] * 7 if post is None else post
        for offset, value in list(zip(range(-len(pre), 0), pre)) + list(enumerate(post)):
            self.connection.execute("INSERT INTO traffic_daily VALUES (?, ?, ?, ?, ?, ?)",
                (repo, (event_day + timedelta(days=offset)).isoformat(), value,
                 views_available, value, clones_available))

    def analyze(self, *, event_day=EVENT_DAY, metric="views"):
        return app.analyze_event_metric(self.connection, repo=TARGET,
                                        event_day=event_day, metric=metric)

    def controls(self, *, count=3, event_day=EVENT_DAY, days=7):
        for index in range(count):
            self.add_window(f"octocat/control-{index}", event_day=event_day,
                            pre=[5] * days, post=[5] * days)

    def test_complete_metric_preserves_entire_result_contract(self):
        self.add_window()
        self.controls()
        expected = {
            "metric": "views", "status": "complete", "window_days": 7,
            "latest_day": "2026-08-16",
            "period": {"pre_from": "2026-08-03", "pre_to": "2026-08-09",
                       "post_from": "2026-08-10", "post_to": "2026-08-16"},
            "pre": 70, "post": 140, "change_pct": 100.0, "change_kind": "measured",
            "portfolio_change_pct": 0.0, "portfolio_repositories": 3,
            "lift_pct_points": 100.0, "confidence": "high",
        }
        self.assertEqual(self.analyze(), expected)
        self.assertEqual(self.analyze(metric="clones"), {**expected, "metric": "clones"})

    def test_portfolio_uses_median_and_excludes_invalid_controls(self):
        self.add_window()
        for repo, pre, post in (
            ("octocat/a", [10] * 7, [5] * 7),
            ("octocat/b", [10] * 7, [10] * 7),
            ("octocat/c", [10] * 7, [20] * 7),
            ("octocat/d", [10] * 7, [30] * 7),
            ("octocat/octocat", [1] * 7, [100] * 7),
            ("octocat/zero", [0] * 7, [100] * 7),
            ("octocat/incomplete", [10] * 6, [100] * 7),
        ):
            self.add_window(repo, pre=pre, post=post)
        result = self.analyze()
        self.assertEqual(result["portfolio_change_pct"], 50.0)
        self.assertEqual(result["portfolio_repositories"], 4)
        self.assertEqual(result["lift_pct_points"], 50.0)

    def test_zero_and_new_baselines_remain_distinct(self):
        for post_value, change, kind in ((0, 0.0, "measured"), (5, None, "new")):
            with self.subTest(post_value=post_value):
                self.connection.execute("DELETE FROM traffic_daily")
                self.add_window(pre=[0] * 7, post=[post_value] * 7)
                self.controls()
                result = self.analyze()
                self.assertEqual((result["pre"], result["post"]), (0, post_value * 7))
                self.assertEqual((result["change_pct"], result["change_kind"]), (change, kind))
                self.assertEqual(result["lift_pct_points"], change)
                self.assertEqual(result["status"], "complete")

    def test_confidence_thresholds_depend_on_window_and_control_count(self):
        for days, controls, confidence in ((7, 3, "high"), (7, 2, "medium"),
                                          (4, 2, "medium"), (3, 3, "low"), (4, 1, "low")):
            with self.subTest(days=days, controls=controls):
                self.connection.execute("DELETE FROM traffic_daily")
                event_day = TODAY - timedelta(days=days)
                self.add_window(event_day=event_day, pre=[10] * days, post=[20] * days)
                self.controls(count=controls, event_day=event_day, days=days)
                result = self.analyze(event_day=event_day)
                self.assertEqual(result["confidence"], confidence)
                self.assertEqual(result["window_days"], days)
                self.assertEqual(result["status"], "complete" if days == 7 else "collecting")

    def test_post_gap_stops_contiguous_window_instead_of_counting_later_days(self):
        self.add_window()
        self.connection.execute("DELETE FROM traffic_daily WHERE day = '2026-08-12'")
        result = self.analyze()
        self.assertEqual((result["window_days"], result["pre"], result["post"]), (2, 20, 40))
        self.assertEqual(result["period"]["post_to"], "2026-08-11")
        self.assertEqual(result["latest_day"], "2026-08-16")

    def test_incomplete_baseline_remains_unavailable_not_zero(self):
        self.add_window(pre=[10] * 6)
        result = self.analyze()
        self.assertEqual(result["status"], "waiting")
        self.assertEqual(result["window_days"], 7)
        for key in ("pre", "post", "change_pct", "portfolio_change_pct", "lift_pct_points"):
            self.assertIsNone(result[key])
        self.assertNotIn("period", result)
        self.assertIn("complete pre-event baseline", result["message"])

    def test_empty_evidence_preserves_waiting_contract(self):
        self.assertEqual(self.analyze(), {
            "metric": "views", "status": "waiting",
            "message": "Waiting for GitHub traffic data; no daily bucket is available for this event yet.",
            "window_days": 0, "latest_day": None, "pre": None, "post": None,
            "change_pct": None, "change_kind": "waiting", "portfolio_change_pct": None,
            "portfolio_repositories": 0, "lift_pct_points": None, "confidence": "low",
        })

    def test_metric_availability_is_independent(self):
        self.add_window(views_available=0)
        self.assertEqual(self.analyze()["status"], "waiting")
        self.assertIsNone(self.analyze()["latest_day"])
        self.assertEqual(self.analyze(metric="clones")["post"], 140)

    def test_creation_day_and_current_day_are_not_valid_evidence(self):
        event_day = TODAY - timedelta(days=1)
        self.add_window(event_day=event_day, pre=[10], post=[20, 30])
        self.connection.execute("INSERT INTO repository_registry VALUES (?, ?)",
                                (TARGET.upper(), "2026-08-17T10:00:00Z"))
        result = self.analyze(event_day=event_day)
        self.assertEqual(result["status"], "waiting")
        self.assertIsNone(result["latest_day"])
        self.assertEqual(result["window_days"], 0)

    def test_stale_partial_window_is_not_certified_as_an_early_read(self):
        event_day = date(2026, 8, 12)
        self.add_window(event_day=event_day, pre=[10] * 3, post=[0] * 3)
        result = self.analyze(event_day=event_day)
        self.assertEqual(result["status"], "stale_upstream")
        self.assertEqual(result["window_days"], 3)
        self.assertEqual(result["latest_day"], "2026-08-14")
        self.assertIsNone(result["pre"])
        self.assertIsNone(result["post"])
        self.assertIn("4 days old", result["message"])

    def test_complete_historical_window_remains_measurable(self):
        event_day = date(2026, 8, 6)
        self.add_window(event_day=event_day)
        self.assertEqual(self.analyze(event_day=event_day)["status"], "complete")

    def test_unsupported_metric_fails_before_database_query(self):
        with self.assertRaisesRegex(ValueError, "Unsupported impact metric"):
            self.analyze(metric="unique_views")
        self.assertIsNone(self.connection.row_factory)

    def test_event_dates_normalize_to_utc_and_reject_invalid_dates(self):
        for value in ("2026-08-10", "2026-08-10T01:00:00Z",
                      "2026-08-11T01:00:00+02:00", "2026-08-10T02:00:00"):
            self.assertEqual(app._utc_date(value), EVENT_DAY)
        with self.assertRaises(ValueError):
            app._utc_date("invalid")

    def render_metrics(self, metrics):
        event = {"repo": TARGET, "event_type": "release", "title": "Release v2",
                 "occurred_at": "2026-08-10T10:00:00Z", "metadata": {}}
        before = copy.deepcopy(metrics)
        with mock.patch.object(app, "get_repository_events", return_value=[event]), \
             mock.patch.object(app, "get_active_repository_names", return_value=None), \
             mock.patch.object(app, "database_connection", return_value=nullcontext(self.connection)), \
             mock.patch.object(app, "analyze_event_metric", side_effect=lambda *args, **kw: metrics[kw["metric"]]):
            result = app.build_impact_lab()
        self.assertEqual(metrics, before)
        return result

    @staticmethod
    def metric(name, *, lift=None, confidence="low", status="waiting"):
        return {"metric": name, "lift_pct_points": lift, "confidence": confidence,
                "status": status, "change_pct": lift, "portfolio_change_pct": 0.0}

    def test_outcome_preserves_thresholds_and_importance(self):
        for lift, outcome, important in ((25, "outperformed", False), (-25, "underperformed", False),
                                         (24.9, "matched", False), (-24.9, "matched", False),
                                         (50, "outperformed", True), (-50, "underperformed", True)):
            with self.subTest(lift=lift):
                result = self.render_metrics({"views": self.metric("views", lift=lift, confidence="high"),
                                              "clones": self.metric("clones")})
                event = result["events"][0]
                self.assertEqual((event["outcome_key"], event["important"]), (outcome, important))
                self.assertEqual(event["confidence"], "high")
                self.assertEqual(result["summary"]["important"], int(important))
                self.assertEqual(result["summary"]["measured"], 1)

    def test_headline_and_confidence_use_same_strongest_metric(self):
        result = self.render_metrics({"views": self.metric("views", lift=100, confidence="high"),
                                      "clones": self.metric("clones", lift=300, confidence="low")})
        event = result["events"][0]
        self.assertEqual(event["summary"], "Clone events changed +300% versus a +0% portfolio median.")
        self.assertEqual(event["confidence"], "low")
        self.assertFalse(event["important"])

    def test_equal_lifts_keep_first_metric_and_zero_lift_is_measured(self):
        for lift in (0, 50):
            with self.subTest(lift=lift):
                result = self.render_metrics({"views": self.metric("views", lift=lift, confidence="medium"),
                                              "clones": self.metric("clones", lift=-lift, confidence="high")})
                event = result["events"][0]
                self.assertTrue(event["summary"].startswith("Page views changed"))
                self.assertEqual(event["confidence"], "medium")
                self.assertEqual(event["important"], lift == 50)

    def test_unmeasured_outcome_distinguishes_stale_from_waiting(self):
        for status, outcome in (("waiting", "collecting"), ("stale_upstream", "stale_upstream")):
            with self.subTest(status=status):
                result = self.render_metrics({"views": self.metric("views", status=status),
                                              "clones": self.metric("clones")})
                event = result["events"][0]
                self.assertEqual(event["outcome_key"], outcome)
                self.assertEqual(event["confidence"], "low")
                self.assertFalse(event["important"])
                self.assertEqual(result["summary"]["measured"], 0)

    def test_measured_metric_takes_precedence_over_other_stale_metric(self):
        result = self.render_metrics({"views": self.metric("views", lift=30, confidence="medium"),
                                      "clones": self.metric("clones", status="stale_upstream")})
        self.assertEqual(result["events"][0]["outcome_key"], "outperformed")
        self.assertEqual(result["events"][0]["confidence"], "medium")

    def test_adapter_delegates_with_rows_and_explicit_profile_predicate(self):
        from analytics import events
        self.add_window()
        self.controls()
        with mock.patch.object(app, "build_event_metric_result", wraps=events.build_event_metric_result) as delegate:
            result = self.analyze()
        delegate.assert_called_once()
        supplied = delegate.call_args.kwargs
        self.assertEqual((supplied["metric"], supplied["event_day"], supplied["window_days"]),
                         ("views", EVENT_DAY, 7))
        self.assertEqual(len(supplied["pre_rows"]), 7)
        self.assertEqual(len(supplied["portfolio_rows"]), 3)
        self.assertIs(supplied["is_profile_repository_name"], app.is_profile_repository_name)
        self.assertEqual(result["portfolio_repositories"], 3)
        with mock.patch.object(app, "is_profile_repository_name", return_value=True):
            self.assertEqual(self.analyze()["portfolio_repositories"], 0)


class PureEventCalculationTests(unittest.TestCase):
    @staticmethod
    def calculate(*, days=7, pre=10, post=20, portfolio_rows=None):
        from analytics import events
        return events.build_event_metric_result(
            metric="views", event_day=EVENT_DAY, window_days=days, latest_day="2026-08-16",
            pre_rows=[{"value": pre}] * days, post_rows=[{"value": post}] * days,
            portfolio_rows=[] if portfolio_rows is None else portfolio_rows,
            is_profile_repository_name=lambda name: name == "octocat/octocat",
        )

    def test_entrypoint_exposes_same_calculation_objects(self):
        from analytics import events
        for name in ("_utc_date", "build_event_metric_result", "describe_event_outcome"):
            self.assertIs(getattr(app, name), getattr(events, name))

    def test_direct_results_preserve_rounding_zero_and_immutable_controls(self):
        controls = [{"repo": "octocat/a", "pre": 3, "post": 4, "pre_days": 7, "post_days": 7},
                    {"repo": "octocat/octocat", "pre": 1, "post": 100, "pre_days": 7, "post_days": 7},
                    {"repo": "octocat/partial", "pre": 1, "post": 100, "pre_days": 6, "post_days": 7},
                    {"repo": "octocat/new", "pre": 0, "post": 100, "pre_days": 7, "post_days": 7}]
        before = copy.deepcopy(controls)
        for pre, post, change, kind, lift in ((3, 4, 33.3, "measured", 0.0),
                                            (0, 0, 0.0, "measured", -33.3),
                                            (0, 5, None, "new", None),
                                            (5, 0, -100.0, "measured", -133.3)):
            with self.subTest(pre=pre, post=post):
                result = self.calculate(pre=pre, post=post, portfolio_rows=controls)
                self.assertEqual((result["change_pct"], result["change_kind"], result["lift_pct_points"]),
                                 (change, kind, lift))
                self.assertEqual(result["portfolio_repositories"], 1)
                self.assertEqual(result["portfolio_change_pct"], 33.3)
        self.assertEqual(controls, before)
        self.assertIsNone(self.calculate()["portfolio_change_pct"])
        self.assertIsNone(self.calculate()["lift_pct_points"])

    def test_direct_confidence_preserves_thresholds(self):
        for days, count, confidence in ((7, 3, "high"), (7, 2, "medium"),
                                        (4, 2, "medium"), (3, 3, "low"), (4, 1, "low")):
            with self.subTest(days=days, count=count):
                controls = [{"repo": f"octocat/{index}", "pre": 5, "post": 5,
                             "pre_days": days, "post_days": days} for index in range(count)]
                self.assertEqual(self.calculate(days=days, portfolio_rows=controls)["confidence"], confidence)

    def test_direct_calculation_accepts_sqlite_rows_without_storage_dependency(self):
        from analytics import events
        with closing(sqlite3.connect(":memory:")) as connection:
            connection.row_factory = sqlite3.Row
            pre = connection.execute("SELECT 2 AS value").fetchall()
            post = connection.execute("SELECT 3 AS value").fetchall()
            controls = connection.execute("SELECT 'octocat/a' AS repo, 2 AS pre, 2 AS post, "
                                          "1 AS pre_days, 1 AS post_days").fetchall()
        result = events.build_event_metric_result(
            metric="clones", event_day=EVENT_DAY, window_days=1, latest_day="2026-08-10",
            pre_rows=pre, post_rows=post, portfolio_rows=controls,
            is_profile_repository_name=lambda name: False,
        )
        self.assertEqual((result["pre"], result["post"], result["lift_pct_points"]), (2, 3, 50.0))
        self.assertEqual(result["status"], "collecting")
        self.assertEqual(result["period"]["post_to"], "2026-08-10")

    def test_direct_headline_preserves_weak_confidence_and_input_metrics(self):
        from analytics import events
        metrics = {"views": EventCharacterizationTests.metric("views", lift=100, confidence="high"),
                   "clones": EventCharacterizationTests.metric("clones", lift=300, confidence="low")}
        before = copy.deepcopy(metrics)
        self.assertEqual(events.describe_event_outcome(metrics), {
            "outcome_key": "outperformed", "outcome": "Outperformed portfolio baseline",
            "summary": "Clone events changed +300% versus a +0% portfolio median.",
            "confidence": "low", "important": False,
        })
        self.assertEqual(metrics, before)
        self.assertEqual(events.describe_event_outcome({})["outcome_key"], "collecting")

    def test_fresh_import_and_calculations_need_no_entrypoint_provider_storage_or_clock(self):
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
     patch('socket.create_connection', side_effect=AssertionError('network access')):
    from analytics import events
    with patch.object(events, 'datetime', NoClock):
        assert events._utc_date('2026-08-11T01:00:00+02:00') == date(2026, 8, 10)
        result = events.build_event_metric_result(
            metric='views', event_day=date(2026, 8, 10), window_days=1,
            latest_day='2026-08-10', pre_rows=[{'value': 2}], post_rows=[{'value': 3}],
            portfolio_rows=[], is_profile_repository_name=lambda name: False)
        assert result['change_pct'] == 50.0
        assert events.describe_event_outcome({'views': result})['outcome_key'] == 'collecting'
    assert 'app' not in sys.modules
    assert not any(name == 'missing_link' or name.startswith('missing_link.') for name in sys.modules)
"""
        result = subprocess.run([sys.executable, "-I", "-c", code, str(Path(__file__).resolve().parents[1])],
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
