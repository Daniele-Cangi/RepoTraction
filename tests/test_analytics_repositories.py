"""Characterize repository readiness and adoption without GitHub or user data."""
import copy
import unittest
from datetime import datetime, timedelta, timezone
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
