"""Characterize opportunity rules without real history, GitHub or AI calls."""
import copy
import subprocess
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

import app


NOW = datetime(2026, 8, 18, tzinfo=timezone.utc)
TARGET = "octocat/project"


class FrozenDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        return NOW.astimezone(tz) if tz else NOW.replace(tzinfo=None)


def repository(**changes):
    return {"full_name": TARGET, "name": "project", "description": "Useful project",
            "topics": ["python", "analytics"], "license": "MIT",
            "license_status": "recognized", "homepage": "https://example.test",
            "pushed_at": NOW.isoformat(), **changes}


def signal(**changes):
    return {"repo": TARGET, "views_7d": 24, "previous_views": 12, "clones_7d": 0,
            "net_stars": 0, "views_comparison_ready": True,
            "snapshot_period": {"is_full_window": True},
            "traffic_period": {"label": "the observed week"}, **changes}


class OpportunityCharacterizationTests(unittest.TestCase):
    def setUp(self):
        clock = mock.patch.object(app, "datetime", FrozenDateTime)
        clock.start()
        self.addCleanup(clock.stop)

    def analyze(self, repo=None, row=None):
        return app.analyze_opportunities([repository() if repo is None else repo],
                                         [signal() if row is None else row])

    def kinds(self, **changes):
        return {item["kind"] for item in self.analyze(row=signal(**changes))[0]}

    def test_empty_and_unmatched_inputs_preserve_readiness_without_traffic(self):
        self.assertEqual(app.analyze_opportunities([], []), ([], []))
        expected = ([], [{"repo": TARGET, "name": "project", "score": 100,
                          "gaps": [], "notes": [], "url": f"https://github.com/{TARGET}"}])
        self.assertEqual(app.analyze_opportunities([repository()], []), expected)
        self.assertEqual(app.analyze_opportunities([repository()], [signal(repo="other/repo")]), expected)

    def test_all_five_opportunities_preserve_entire_contract_and_order(self):
        repo = repository(description="", topics=[], license="", license_status="missing",
                          pushed_at=(NOW - timedelta(days=181)).isoformat())
        row = signal(adoption_signal={"clone_events": 18, "unique_cloners": 8,
                                      "repeat_factor": 2.2, "label": "Emerging cloning signal"})
        url = f"https://github.com/{TARGET}"
        expected = [
            {"kind": "discoverability", "priority": "high", "repo": TARGET,
             "title": "Review project's repository landing page",
             "detail": "24 page views in the observed week with no net star growth over a complete snapshot window.",
             "action": "Sharpen the README opening, demo and primary call to action.",
             "metric": "24 views · +0 net stars", "confidence": "medium", "score": 94, "url": url},
            {"kind": "foundation", "priority": "high", "repo": TARGET,
             "title": "Complete project's essentials",
             "detail": "Missing or weak repository metadata: description, topics, license.",
             "action": "Add the missing metadata so visitors understand and trust the project faster.",
             "metric": "Readiness 25/100", "confidence": "high", "score": 70, "url": url},
            {"kind": "freshness", "priority": "medium", "repo": TARGET,
             "title": "Refresh project while people still visit",
             "detail": "The repository still attracts traffic but was last pushed 181 days ago.",
             "action": "Confirm compatibility, refresh examples and publish maintenance notes.",
             "metric": "24 page views · 181d since push", "confidence": "medium", "score": 80, "url": url},
            {"kind": "developer_experience", "priority": "low", "repo": TARGET,
             "title": "Review project's cloning pattern",
             "detail": "GitHub recorded 18 full clone events from 8 unique cloners in the same 14-day window; identities and automation remain unknown.",
             "action": "Check automation patterns first, then improve the quick start if human setup friction is plausible.",
             "metric": "Emerging cloning signal · 2.2× repeat", "confidence": "low", "score": 73, "url": url},
            {"kind": "momentum", "priority": "low", "repo": TARGET,
             "title": "Capture project's momentum",
             "detail": "+100% traffic is creating a short window for discovery.",
             "action": "Publish a small release or update while attention is elevated.",
             "metric": "24 page views · +100% traffic", "confidence": "medium", "score": 64, "url": url},
        ]
        self.assertEqual(self.analyze(repo, row), (expected, [
            {"repo": TARGET, "name": "project", "score": 25,
             "gaps": ["description", "topics", "license", "recent activity"], "notes": [], "url": url}]))

    def test_foundation_only_uses_essential_gaps_and_license_priority(self):
        cases = (({"homepage": "", "pushed_at": ""}, None, None),
                 ({"description": ""}, "medium", 15),
                 ({"topics": []}, "medium", 10),
                 ({"license": "", "license_status": "missing"}, "high", 15),
                 ({"license": "", "license_status": "missing", "private": True}, None, None),
                 ({"license": "NOASSERTION", "license_status": "present_unrecognized"}, None, None))
        for changes, priority, score in cases:
            with self.subTest(changes=changes):
                opportunities, _ = app.analyze_opportunities([repository(**changes)], [])
                self.assertEqual([(item["priority"], item["score"]) for item in opportunities],
                                 [] if priority is None else [(priority, score)])

    def test_discoverability_thresholds_and_score_cap_are_preserved(self):
        for views, expected in ((9, None), (10, ("medium", 80)), (19, ("medium", 89)),
                                (20, ("high", 90)), (30, ("high", 100)), (100, ("high", 100))):
            with self.subTest(views=views):
                items = [item for item in self.analyze(row=signal(views_7d=views))[0]
                         if item["kind"] == "discoverability"]
                self.assertEqual([(item["priority"], item["score"]) for item in items],
                                 [] if expected is None else [expected])

    def test_discoverability_requires_full_star_window_and_known_nonpositive_delta(self):
        for stars, full, expected in ((None, True, False), (1, True, False), (0, True, True),
                                      (-2, True, True), ("0", True, True), (0, False, False),
                                      (0, None, False)):
            with self.subTest(stars=stars, full=full):
                self.assertEqual("discoverability" in self.kinds(
                    net_stars=stars, snapshot_period={"is_full_window": full}), expected)
        self.assertNotIn("discoverability", self.kinds(snapshot_period=None))

    def test_explicit_view_readiness_overrides_legacy_combined_flag(self):
        for views_ready, combined, expected in ((False, True, False), (None, True, False),
                                                (True, False, True), (True, None, True)):
            with self.subTest(views_ready=views_ready, combined=combined):
                kinds = self.kinds(views_comparison_ready=views_ready, traffic_comparison_ready=combined)
                self.assertEqual("discoverability" in kinds, expected)
                self.assertEqual("momentum" in kinds, expected)
        row = signal(traffic_comparison_ready=True)
        del row["views_comparison_ready"]
        self.assertIn("discoverability", {item["kind"] for item in self.analyze(row=row)[0]})
        row["traffic_comparison_ready"] = False
        self.assertEqual(self.analyze(row=row)[0], [])

    def test_momentum_growth_new_traffic_thresholds_and_cap_are_preserved(self):
        cases = ((4, 0, None), (5, 0, ("5 page views · new traffic", 45)),
                 (0, 0, None), (149, 100, None),
                 (150, 100, ("150 page views · +50% traffic", 70)),
                 (6, 4, ("6 page views · +50% traffic", 46)), (5, 4, None),
                 (5, None, ("5 page views · new traffic", 45)))
        for views, previous, expected in cases:
            with self.subTest(views=views, previous=previous):
                items = [item for item in self.analyze(row=signal(views_7d=views, previous_views=previous))[0]
                         if item["kind"] == "momentum"]
                self.assertEqual([(item["metric"], item["score"]) for item in items],
                                 [] if expected is None else [expected])
        self.assertNotIn("momentum", self.kinds(views_7d=5, previous_views=0, views_comparison_ready=False))

    def test_freshness_age_view_thresholds_and_cap_are_preserved(self):
        for days, views, score in ((120, 3, None), (121, 2, None), (121, 3, 63),
                                   (181, 20, 80), (181, 100, 80)):
            with self.subTest(days=days, views=views):
                repo = repository(pushed_at=(NOW - timedelta(days=days)).isoformat())
                items = [item for item in self.analyze(repo, signal(views_7d=views))[0]
                         if item["kind"] == "freshness"]
                self.assertEqual([item["score"] for item in items], [] if score is None else [score])
        for timestamp in ("", "invalid"):
            self.assertNotIn("freshness", {item["kind"] for item in self.analyze(repository(pushed_at=timestamp))[0]})
        repo = repository(pushed_at=(NOW - timedelta(days=150)).isoformat())
        self.assertNotIn("freshness", {item["kind"] for item in self.analyze(repo, signal(views_comparison_ready=False))[0]})

    def test_clone_opportunity_uses_native_adoption_window_not_weekly_clones(self):
        for events, uniques, expected in ((None, 8, None), (5, None, None), (4, 4, None),
                                          (5, 0, 60), (5, 4, 60), (30, 8, 85), (100, 8, 85)):
            with self.subTest(events=events, uniques=uniques):
                row = signal(views_7d=None, clones_7d=999, views_comparison_ready=False,
                             adoption_signal={"clone_events": events, "unique_cloners": uniques})
                items = self.analyze(row=row)[0]
                self.assertEqual([item["score"] for item in items], [] if expected is None else [expected])
                if items:
                    self.assertEqual(items[0]["metric"], "Cloning signal")
                    self.assertEqual(items[0]["confidence"], "low")
        self.assertEqual(self.analyze(row=signal(views_7d=0, clones_7d=999,
                                                native_clones_14d=999, unique_cloners_14d=99))[0], [])

    def test_excluded_repositories_do_not_evaluate_health_or_bad_counts(self):
        repos = [{}, repository(full_name=""), repository(archived=True), repository(fork=True),
                 repository(full_name="OctoCat/octocat")]
        rows = [signal(repo=repo.get("full_name", ""), views_7d="bad") for repo in repos]
        with mock.patch.object(app, "repository_health", side_effect=AssertionError("excluded health")):
            self.assertEqual(app.analyze_opportunities(repos, rows), ([], []))

    def test_signal_matching_is_case_insensitive_and_last_duplicate_wins(self):
        rows = [signal(repo="OCTOCAT/PROJECT", views_7d=100), signal(repo=TARGET, views_7d=0)]
        self.assertEqual(app.analyze_opportunities([repository()], rows)[0], [])
        opportunities, _ = app.analyze_opportunities([repository()], list(reversed(rows)))
        self.assertEqual(opportunities[0]["metric"], "100 views · +0 net stars")

    def test_names_urls_periods_and_notes_keep_fallbacks(self):
        repo = repository(name="", html_url="", license="NOASSERTION", license_status="present_unrecognized")
        items, health = self.analyze(repo, signal(traffic_period=None, previous_views=24))
        self.assertIn("the current window", items[0]["detail"])
        self.assertEqual(items[0]["url"], f"https://github.com/{TARGET}")
        self.assertEqual(health[0]["name"], "project")
        self.assertEqual(health[0]["notes"], ["license present · GitHub does not recognize its SPDX type"])
        repo.update(name="Named project", html_url="https://example.test/repo")
        items, health = self.analyze(repo)
        self.assertIn("Named project", items[0]["title"])
        self.assertEqual(items[0]["url"], "https://example.test/repo")
        self.assertEqual(health[0]["url"], "https://example.test/repo")

    def test_priority_score_and_stable_ties_preserve_input_order(self):
        repos = [repository(full_name="octocat/z", name="z"), repository(full_name="octocat/a", name="a")]
        rows = [signal(repo=repo["full_name"], adoption_signal={"clone_events": 100, "unique_cloners": 8})
                for repo in repos]
        items, health = app.analyze_opportunities(repos, rows)
        self.assertEqual([(item["kind"], item["repo"]) for item in items], [
            (kind, repo["full_name"]) for kind in ("discoverability", "developer_experience", "momentum")
            for repo in repos])
        self.assertEqual([row["name"] for row in health], ["a", "z"])

    def test_health_order_is_score_then_casefolded_name_with_stable_ties(self):
        repos = [repository(full_name="octocat/z", name="z"),
                 repository(full_name="octocat/b", name="b", description=""),
                 repository(full_name="octocat/a1", name="A"),
                 repository(full_name="octocat/a2", name="a")]
        _, health = app.analyze_opportunities(repos, [])
        self.assertEqual([item["repo"] for item in health], ["octocat/b", "octocat/a1", "octocat/a2", "octocat/z"])

    def test_profile_and_health_hooks_remain_patchable_and_in_order(self):
        repo = repository()
        health = {"score": 100, "gaps": [], "notes": ["supplied note"],
                  "pushed_days_ago": 150, "applicable": False}
        with mock.patch.object(app, "is_profile_repository", return_value=False) as profile, \
             mock.patch.object(app, "repository_health", return_value=health) as readiness:
            items, rows = self.analyze(repo)
        profile.assert_called_once_with(repo)
        readiness.assert_called_once_with(repo)
        self.assertEqual(rows, [])
        self.assertIn("freshness", {item["kind"] for item in items})
        with mock.patch.object(app, "is_profile_repository", return_value=True), \
             mock.patch.object(app, "repository_health", side_effect=AssertionError("profile health")):
            self.assertEqual(self.analyze(repo), ([], []))

    def test_invalid_inputs_preserve_failures_and_evaluation_order(self):
        with mock.patch.object(app, "repository_health", wraps=app.repository_health) as health:
            with self.assertRaises(KeyError):
                app.analyze_opportunities([repository()], [{}])
            health.assert_not_called()
        for changes in ({"views_7d": "bad"}, {"clones_7d": "bad"}, {"previous_views": "bad"},
                        {"net_stars": "bad"}, {"adoption_signal": {"clone_events": "bad"}}):
            with self.subTest(changes=changes), \
                 mock.patch.object(app, "repository_health", wraps=app.repository_health) as health:
                with self.assertRaises(ValueError):
                    app.analyze_opportunities([repository(), repository(full_name="octocat/second")], [signal(**changes)])
                self.assertEqual(health.call_count, 1)

    def test_inputs_are_not_mutated_and_repeated_results_are_independent(self):
        repos = [repository(description="", license="NOASSERTION", license_status="present_unrecognized")]
        rows = [signal(adoption_signal={"clone_events": 8, "unique_cloners": 4, "repeat_factor": 2.0})]
        before = copy.deepcopy((repos, rows))
        first = app.analyze_opportunities(repos, rows)
        expected = copy.deepcopy(first)
        first[0][0]["metric"] = "caller mutation"
        first[1][0]["gaps"].clear()
        first[1][0]["notes"].clear()
        self.assertEqual(app.analyze_opportunities(repos, rows), expected)
        self.assertEqual((repos, rows), before)


class PureOpportunityCalculationTests(unittest.TestCase):
    def test_entrypoint_delegates_calculation_and_ranking_with_prepared_health(self):
        from analytics import opportunities
        repo = repository()
        row = signal()
        health = {"score": 100, "gaps": [], "notes": [], "pushed_days_ago": 0, "applicable": True}
        self.assertIs(app.build_repository_opportunities, opportunities.build_repository_opportunities)
        self.assertIs(app.rank_opportunities, opportunities.rank_opportunities)
        with mock.patch.object(app, "repository_health", return_value=health) as readiness, \
             mock.patch.object(app, "build_repository_opportunities", wraps=opportunities.build_repository_opportunities) as build, \
             mock.patch.object(app, "rank_opportunities", wraps=opportunities.rank_opportunities) as rank:
            result = app.analyze_opportunities([repo], [row])
        readiness.assert_called_once_with(repo)
        build.assert_called_once_with(repo, row, health)
        self.assertEqual(rank.call_count, 1)
        self.assertEqual(result, opportunities.rank_opportunities(*opportunities.build_repository_opportunities(repo, row, health)))

    def test_direct_calculation_uses_supplied_health_without_parsing_timestamp(self):
        from analytics import opportunities
        repo = repository(pushed_at="not parsed here", description="")
        health = {"score": 100, "gaps": [], "notes": ["supplied"], "pushed_days_ago": 121, "applicable": True}
        items, rows = opportunities.build_repository_opportunities(repo, signal(views_7d=3, previous_views=3), health)
        self.assertEqual([item["kind"] for item in items], ["freshness"])
        self.assertEqual(rows[0]["score"], 100)
        self.assertEqual(rows[0]["notes"], ["supplied"])
        self.assertIs(rows[0]["notes"], health["notes"])
        self.assertIs(rows[0]["gaps"], health["gaps"])
        health.update(applicable=False, pushed_days_ago=None)
        self.assertEqual(opportunities.build_repository_opportunities(repo, {}, health), ([], []))

    def test_direct_calculation_does_not_mutate_inputs_or_share_opportunity_dicts(self):
        from analytics import opportunities
        repo = repository()
        row = signal(adoption_signal={"clone_events": 8, "unique_cloners": 4, "repeat_factor": 2.0})
        health = {"score": 80, "gaps": ["description"], "notes": [], "pushed_days_ago": 0, "applicable": True}
        before = copy.deepcopy((repo, row, health))
        first = opportunities.build_repository_opportunities(repo, row, health)
        expected = copy.deepcopy(first)
        first[0][0]["metric"] = "caller mutation"
        self.assertEqual(opportunities.build_repository_opportunities(repo, row, health), expected)
        self.assertEqual((repo, row, health), before)

    def test_ranking_preserves_input_lists_row_identity_and_stable_ties(self):
        from analytics import opportunities
        items = [{"priority": "low", "score": 99}, {"priority": "high", "score": 1},
                 {"priority": "high", "score": 1}, {"priority": "medium", "score": 100}]
        health = [{"score": 100, "name": "z"}, {"score": 100, "name": "A"},
                  {"score": 100, "name": "a"}, {"score": 80, "name": "z"}]
        before = copy.deepcopy((items, health))
        ranked, readiness = opportunities.rank_opportunities(items, health)
        self.assertEqual((items, health), before)
        self.assertIsNot(ranked, items)
        self.assertIsNot(readiness, health)
        for actual, expected in zip(ranked, (items[1], items[2], items[3], items[0])):
            self.assertIs(actual, expected)
        for actual, expected in zip(readiness, (health[3], health[1], health[2], health[0])):
            self.assertIs(actual, expected)

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
    from analytics import opportunities
    repo = {'full_name': 'octocat/project', 'pushed_at': 'not parsed'}
    signal = {'views_7d': 5, 'previous_views': 0, 'views_comparison_ready': True,
              'adoption_signal': {'clone_events': 8, 'unique_cloners': 4}}
    health = {'score': 100, 'gaps': [], 'notes': [], 'pushed_days_ago': 150, 'applicable': True}
    items, readiness = opportunities.build_repository_opportunities(repo, signal, health)
    ranked, rows = opportunities.rank_opportunities(items, readiness)
    assert [item['kind'] for item in ranked] == ['freshness', 'developer_experience', 'momentum']
    assert rows[0]['score'] == 100
    assert 'app' not in sys.modules
    assert not any(name == 'missing_link' or name.startswith('missing_link.') for name in sys.modules)
"""
        result = subprocess.run([sys.executable, "-I", "-c", code, str(Path(__file__).resolve().parents[1])],
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)


class OpportunityCenterContractTests(unittest.TestCase):
    def test_cache_hit_does_not_collect_or_recalculate(self):
        cached = {"cached": "opportunities"}
        with mock.patch.object(app.CACHE, "get", return_value=cached) as cache_get, \
             mock.patch.object(app.CACHE, "set") as cache_set, \
             mock.patch.object(app, "build_dashboard", side_effect=AssertionError("dashboard access")), \
             mock.patch.object(app, "get_repository_signal_rows", side_effect=AssertionError("signal access")):
            self.assertIs(app.build_opportunity_center(), cached)
        cache_get.assert_called_once_with("opportunities", 120)
        cache_set.assert_not_called()

    def test_forced_center_keeps_payload_limit_aliases_summary_and_cache(self):
        repos = [repository(full_name=f"octocat/project-{i}", name=f"project-{i}") for i in range(15)]
        repos.append(repository(full_name="octocat/octocat", name="octocat"))
        rows = [signal(repo=repo["full_name"], name=repo["name"], archived=False,
                       adoption_signal={"clone_events": 8, "unique_cloners": 4}) for repo in repos]
        with mock.patch.object(app, "datetime", FrozenDateTime), \
             mock.patch.object(app.CACHE, "get", side_effect=AssertionError("forced cache read")), \
             mock.patch.object(app.CACHE, "set") as cache_set, \
             mock.patch.object(app, "build_dashboard", return_value={"repositories": repos}), \
             mock.patch.object(app, "get_repository_signal_rows", return_value=rows), \
             mock.patch.object(app, "utc_now", return_value="2026-08-18T00:00:00Z"):
            payload = app.build_opportunity_center(force=True)
            expected_items, expected_health = app.analyze_opportunities(repos, rows)
        self.assertEqual(payload["generated_at"], "2026-08-18T00:00:00Z")
        self.assertEqual(payload["summary"], {"total": 45, "high": 15, "medium": 0,
                                             "health_average": 100, "readiness_average": 100,
                                             "repositories_analyzed": 15})
        self.assertEqual(payload["opportunities"], expected_items[:40])
        self.assertEqual(len(payload["opportunities"]), 40)
        self.assertEqual(payload["health"], expected_health)
        self.assertIs(payload["health"], payload["readiness"])
        self.assertEqual(payload["repositories"], [{"repo": row["repo"], "name": row["name"]} for row in rows[:-1]])
        self.assertEqual(payload["readiness_score"]["kind"], "local checklist")
        cache_set.assert_called_once_with("opportunities", payload)
