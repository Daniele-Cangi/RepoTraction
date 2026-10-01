"""Characterize repository readiness and adoption without GitHub or user data."""
import copy
import subprocess
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

import app


NOW = datetime(2026, 8, 18, tzinfo=timezone.utc)


class FrozenDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        return NOW.astimezone(tz) if tz else NOW.replace(tzinfo=None)


def healthy_repository(**changes):
    return {"full_name": "octocat/project", "description": "A useful project",
            "topics": ["python", "analytics"], "license": "MIT",
            "license_status": "recognized", "homepage": "https://example.test",
            "pushed_at": NOW.isoformat(), "private": False, **changes}


class RepositoryCharacterizationTests(unittest.TestCase):
    def setUp(self):
        clock = mock.patch.object(app, "datetime", FrozenDateTime)
        clock.start()
        self.addCleanup(clock.stop)

    def test_broad_adoption_preserves_entire_result_contract(self):
        self.assertEqual(app.build_adoption_signal(36, 31), {
            "key": "broad", "label": "Broad cloning signal",
            "detail": "36 full clone events from 31 unique cloners in GitHub's current 14-day window (1.2× repeat factor).",
            "clone_events": 36, "unique_cloners": 31, "breadth_pct": 86.1,
            "repeat_factor": 1.2, "confidence": "medium",
        })

    def test_unavailable_adoption_preserves_partial_inputs_not_zero(self):
        for events, uniques in ((None, None), (3, None), (None, 4)):
            with self.subTest(events=events, uniques=uniques):
                self.assertEqual(app.build_adoption_signal(events, uniques), {
                    "key": "unavailable", "label": "Cloning data unavailable",
                    "detail": "GitHub's native 14-day clone totals are not available.",
                    "clone_events": events, "unique_cloners": uniques,
                    "breadth_pct": None, "repeat_factor": None, "confidence": "unavailable",
                })

    def test_adoption_thresholds_and_branch_order_are_unchanged(self):
        cases = ((0, 0, "quiet", "high"), (0, 3, "quiet", "high"),
                 (4, 1, "early", "low"), (5, 1, "emerging", "medium"),
                 (9, 8, "emerging", "medium"), (10, 7, "emerging", "medium"),
                 (10, 8, "broad", "medium"), (10, 3, "repeat_heavy", "low"),
                 (9, 3, "emerging", "medium"), (12, 4, "repeat_heavy", "low"),
                 (12, 5, "emerging", "medium"), (10, 6, "emerging", "medium"),
                 (20, 12, "broad", "medium"), (20, 11, "emerging", "medium"),
                 (10, 0, "uncertain", "low"))
        for events, uniques, key, confidence in cases:
            with self.subTest(events=events, uniques=uniques):
                result = app.build_adoption_signal(events, uniques)
                self.assertEqual((result["key"], result["confidence"]), (key, confidence))
                self.assertNotIn("conversion", result["detail"].lower())

    def test_adoption_preserves_normalization_rounding_and_detail(self):
        for events, uniques, expected_events, expected_uniques, breadth, repeat in (
            ("36", "31", 36, 31, 86.1, 1.2), (-2, -3, 0, 0, None, None),
            (0, 2, 0, 2, None, 0.0), (3, 2, 3, 2, 66.7, 1.5),
        ):
            with self.subTest(events=events, uniques=uniques):
                result = app.build_adoption_signal(events, uniques)
                self.assertEqual((result["clone_events"], result["unique_cloners"],
                                  result["breadth_pct"], result["repeat_factor"]),
                                 (expected_events, expected_uniques, breadth, repeat))
        self.assertEqual(app.build_adoption_signal(0, 0)["detail"],
                         "GitHub recorded no full clone events in its current 14-day window.")
        self.assertEqual(app.build_adoption_signal(8, 0)["detail"],
                         "GitHub recorded 8 full clone events but no usable unique cloner total in the same window.")

    def test_invalid_adoption_inputs_keep_existing_failures(self):
        with self.assertRaises(ValueError):
            app.build_adoption_signal("not a count", 1)
        with self.assertRaises(TypeError):
            app.build_adoption_signal([], 1)

    def test_license_metadata_distinguishes_absent_from_unrecognized(self):
        for license_value in (None, "MIT", [], False):
            self.assertEqual(app.repository_license_metadata({"license": license_value}),
                             {"spdx_id": "", "name": "", "status": "missing"})
        for license_value, expected in (
            ({}, {"spdx_id": "", "name": "", "status": "present_unrecognized"}),
            ({"spdx_id": "NOASSERTION", "name": "Other"},
             {"spdx_id": "NOASSERTION", "name": "Other", "status": "present_unrecognized"}),
            ({"spdx_id": "MIT", "name": "MIT License"},
             {"spdx_id": "MIT", "name": "MIT License", "status": "recognized"}),
        ):
            with self.subTest(license_value=license_value):
                self.assertEqual(app.repository_license_metadata({"license": license_value}), expected)

    def test_healthy_repository_preserves_entire_result_contract(self):
        self.assertEqual(app.repository_health(healthy_repository()), {
            "score": 100, "gaps": [], "notes": [], "pushed_days_ago": 0, "applicable": True,
        })

    def test_health_weights_and_gap_order_are_preserved(self):
        changes = (({"description": "  "}, 80, ["description"]),
                   ({"topics": ["python"]}, 85, ["topics"]),
                   ({"license": "", "license_status": "missing"}, 80, ["license"]),
                   ({"homepage": "\t"}, 95, ["homepage"]),
                   ({"pushed_at": ""}, 90, ["recent activity"]))
        for changed, score, gaps in changes:
            with self.subTest(changed=changed):
                result = app.repository_health(healthy_repository(**changed))
                self.assertEqual((result["score"], result["gaps"]), (score, gaps))
        self.assertEqual(app.repository_health({}), {
            "score": 30, "gaps": ["description", "topics", "license", "homepage", "recent activity"],
            "notes": [], "pushed_days_ago": None, "applicable": True,
        })

    def test_health_activity_age_boundaries_are_preserved(self):
        for days, score in ((0, 100), (90, 100), (91, 90), (180, 90), (181, 80), (500, 80)):
            with self.subTest(days=days):
                result = app.repository_health(healthy_repository(pushed_at=(NOW - timedelta(days=days)).isoformat()))
                self.assertEqual(result["score"], score)
                self.assertEqual(result["pushed_days_ago"], days)
                self.assertEqual(result["gaps"], [] if score == 100 else ["recent activity"])

    def test_private_missing_and_present_unrecognized_licenses_are_not_missing(self):
        for changed, score, notes in (
            ({"license": "", "license_status": "missing", "private": True}, 100, []),
            ({"license": "NOASSERTION", "license_status": ""}, 100,
             ["license present · GitHub does not recognize its SPDX type"]),
            ({"license": "", "license_status": "present_unrecognized"}, 100,
             ["license present · GitHub does not recognize its SPDX type"]),
            ({"license": "MIT", "license_status": ""}, 100, []),
            ({"license": "", "license_status": ""}, 80, []),
        ):
            with self.subTest(changed=changed):
                result = app.repository_health(healthy_repository(**changed))
                self.assertEqual(result["score"], score)
                self.assertEqual(result["notes"], notes)
                self.assertEqual("license" in result["gaps"], score < 100)

    def test_profile_repository_is_not_scored_but_retains_activity_age(self):
        for identity in ({"full_name": "OctoCat/octocat"}, {"repo": "octocat/octocat"}):
            with self.subTest(identity=identity):
                self.assertEqual(app.repository_health({**identity, "pushed_at": (NOW - timedelta(days=5)).isoformat()}), {
                    "score": None, "gaps": [],
                    "notes": ["profile repository · project readiness does not apply"],
                    "pushed_days_ago": 5, "applicable": False,
                })

    def test_invalid_future_naive_and_offset_timestamps_keep_existing_semantics(self):
        for value, days, score in (("invalid", None, 90),
                                   ((NOW + timedelta(days=5)).isoformat(), 0, 100),
                                   ("2026-08-18T00:00:00", 0, 100),
                                   ("2026-08-18T02:00:00+02:00", 0, 100)):
            with self.subTest(value=value):
                result = app.repository_health(healthy_repository(pushed_at=value))
                self.assertEqual((result["pushed_days_ago"], result["score"]), (days, score))

    def test_health_preserves_entrypoint_age_and_profile_dependencies(self):
        repo = healthy_repository()
        with mock.patch.object(app, "days_since_timestamp", return_value=181) as age:
            self.assertEqual(app.repository_health(repo)["score"], 80)
        age.assert_called_once_with(repo["pushed_at"])
        with mock.patch.object(app, "is_profile_repository", return_value=True), \
             mock.patch.object(app, "days_since_timestamp", return_value=None):
            self.assertFalse(app.repository_health(repo)["applicable"])

    def test_metadata_and_health_do_not_mutate_supplied_repository(self):
        raw = {"license": {"spdx_id": "NOASSERTION", "name": "Other"}}
        repo = healthy_repository(topics=["python"], license="NOASSERTION", license_status="")
        before = copy.deepcopy((raw, repo))
        app.repository_license_metadata(raw)
        first = app.repository_health(repo)
        first["gaps"].append("caller-owned change")
        second = app.repository_health(repo)
        self.assertNotIn("caller-owned change", second["gaps"])
        self.assertEqual((raw, repo), before)

    def test_health_adapter_supplies_profile_and_age_to_pure_calculation(self):
        from analytics import repositories
        repo = healthy_repository()
        with mock.patch.object(app, "calculate_repository_health", wraps=repositories.repository_health) as delegate, \
             mock.patch.object(app, "is_profile_repository", return_value=True) as profile, \
             mock.patch.object(app, "days_since_timestamp", return_value=7) as age:
            result = app.repository_health(repo)
        delegate.assert_called_once_with(repo, is_profile=True, pushed_days_ago=7)
        profile.assert_called_once_with(repo)
        age.assert_called_once_with(repo["pushed_at"])
        self.assertFalse(result["applicable"])
        self.assertEqual(result["pushed_days_ago"], 7)


class PureRepositoryCalculationTests(unittest.TestCase):
    def test_entrypoint_keeps_aliases_and_health_wrapper(self):
        from analytics import repositories
        self.assertIs(app.build_adoption_signal, repositories.build_adoption_signal)
        self.assertIs(app.repository_license_metadata, repositories.repository_license_metadata)
        self.assertIs(app.calculate_repository_health, repositories.repository_health)
        self.assertIsNot(app.repository_health, repositories.repository_health)

    def test_direct_health_uses_supplied_age_and_applicability(self):
        from analytics import repositories
        repo = healthy_repository(pushed_at="not parsed by the calculation")
        for days, score in ((None, 90), (0, 100), (90, 100), (91, 90), (180, 90), (181, 80)):
            with self.subTest(days=days):
                result = repositories.repository_health(repo, is_profile=False, pushed_days_ago=days)
                self.assertEqual((result["score"], result["pushed_days_ago"]), (score, days))
        result = repositories.repository_health(repo, is_profile=True, pushed_days_ago=None)
        self.assertEqual(result, {"score": None, "gaps": [],
                                 "notes": ["profile repository · project readiness does not apply"],
                                 "pushed_days_ago": None, "applicable": False})

    def test_direct_health_results_do_not_share_lists_or_mutate_inputs(self):
        from analytics import repositories
        repo = healthy_repository(topics=["python"], license="NOASSERTION", license_status="")
        before = copy.deepcopy(repo)
        first = repositories.repository_health(repo, is_profile=False, pushed_days_ago=0)
        first["gaps"].append("caller mutation")
        first["notes"].clear()
        second = repositories.repository_health(repo, is_profile=False, pushed_days_ago=0)
        self.assertEqual(second["score"], 85)
        self.assertEqual(second["gaps"], ["topics"])
        self.assertEqual(second["notes"], ["license present · GitHub does not recognize its SPDX type"])
        self.assertEqual(repo, before)

    def test_direct_license_and_adoption_preserve_unknown_not_zero(self):
        from analytics import repositories
        self.assertEqual(repositories.repository_license_metadata({})["status"], "missing")
        self.assertEqual(repositories.repository_license_metadata({"license": {}})["status"], "present_unrecognized")
        unknown = repositories.build_adoption_signal(None, 9)
        self.assertIsNone(unknown["clone_events"])
        self.assertEqual(unknown["unique_cloners"], 9)
        self.assertEqual(unknown["confidence"], "unavailable")
        zero = repositories.build_adoption_signal(0, 0)
        self.assertEqual(zero["key"], "quiet")
        self.assertEqual(zero["clone_events"], 0)
        self.assertEqual(zero["confidence"], "high")

    def test_fresh_import_and_calculations_need_no_entrypoint_provider_io_or_clock(self):
        code = """
import sys
from datetime import datetime
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
    from analytics import repositories
    assert repositories.build_adoption_signal(36, 31)['key'] == 'broad'
    assert repositories.repository_license_metadata({'license': {'spdx_id': 'NOASSERTION'}})['status'] == 'present_unrecognized'
    result = repositories.repository_health({}, is_profile=False, pushed_days_ago=None)
    assert result['score'] == 30
    assert result['pushed_days_ago'] is None
    assert 'app' not in sys.modules
    assert not any(name == 'missing_link' or name.startswith('missing_link.') for name in sys.modules)
"""
        result = subprocess.run([sys.executable, "-I", "-c", code, str(Path(__file__).resolve().parents[1])],
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
