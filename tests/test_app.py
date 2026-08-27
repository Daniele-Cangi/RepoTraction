import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app  # noqa: E402


def user(login: str) -> dict[str, str]:
    return {
        "login": login,
        "avatar_url": f"https://avatars.example/{login}",
        "html_url": f"https://github.com/{login}",
    }


class RelationshipTests(unittest.TestCase):
    def test_classifies_relationships_case_insensitively(self) -> None:
        result = app.classify_relationships(
            [user("Alice"), user("Bob")],
            [user("alice"), user("Carol")],
        )

        self.assertEqual([item["login"] for item in result["mutual"]], ["Alice"])
        self.assertEqual(
            [item["login"] for item in result["not_following_back"]], ["Carol"]
        )
        self.assertEqual(
            [item["login"] for item in result["followers_not_followed"]], ["Bob"]
        )
        self.assertEqual(len(result["all"]), 3)

    def test_empty_relationships(self) -> None:
        result = app.classify_relationships([], [])
        self.assertTrue(all(items == [] for items in result.values()))


class ValidationTests(unittest.TestCase):
    def test_accepts_valid_repo(self) -> None:
        self.assertEqual(
            app.validate_repo("octocat/hello-world"),
            "octocat/hello-world",
        )

    def test_rejects_path_or_query_injection(self) -> None:
        for invalid in ("", "owner", "../repo", "owner/repo?x=1", "owner/repo/extra"):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    app.validate_repo(invalid)

    def test_account_database_is_scoped_by_login(self) -> None:
        root = Path("data")
        self.assertEqual(
            app.account_database_path("Octo-Cat", root),
            root / "github-pulse-octo-cat.sqlite3",
        )
        with self.assertRaises(app.GitHubCLIError):
            app.account_database_path("../invalid", root)


class SignalTests(unittest.TestCase):
    def test_percentage_change_handles_growth_and_new_signal(self) -> None:
        self.assertEqual(app.percentage_change(15, 10), 50.0)
        self.assertEqual(app.percentage_change(0, 0), 0.0)
        self.assertIsNone(app.percentage_change(5, 0))


class OpportunityTests(unittest.TestCase):
    def test_finds_foundation_discoverability_and_setup_opportunities(
        self,
    ) -> None:
        repositories = [
            {
                "full_name": "octocat/hello-world",
                "name": "hello-world",
                "private": False,
                "archived": False,
                "fork": False,
                "html_url": "https://github.com/octocat/hello-world",
                "description": "",
                "homepage": "",
                "topics": [],
                "license": "",
                "pushed_at": app.utc_now(),
            }
        ]
        signals = [
            {
                "repo": "octocat/hello-world",
                "views_7d": 24,
                "previous_views": 12,
                "clones_7d": 10,
                "net_stars": 0,
                "clone_view_ratio": 41.7,
            }
        ]

        opportunities, health = app.analyze_opportunities(repositories, signals)

        self.assertEqual(health[0]["repo"], "octocat/hello-world")
        self.assertLess(health[0]["score"], 100)
        self.assertTrue(
            {"foundation", "discoverability", "developer_experience"}.issubset(
                {item["kind"] for item in opportunities}
            )
        )
        copy = " ".join(
            str(item[field])
            for item in opportunities
            for field in ("title", "detail", "metric")
        ).casefold()
        self.assertNotIn("intent", copy)
        self.assertNotIn("conversion", copy)

    def test_builds_markdown_digest(self) -> None:
        signals = {
            "totals": {
                "views_7d": 42,
                "clones_7d": 12,
                "net_stars": 3,
                "net_forks": 1,
            },
            "relationship_delta": {"followers": 2},
            "repository_ranking": [
                {
                    "name": "hello-world",
                    "views_7d": 24,
                    "clones_7d": 10,
                    "signal_score": 88,
                }
            ],
            "notifications": [
                {"title": "Traffic spike", "detail": "24 page views"}
            ],
        }
        center = {
            "opportunities": [
                {
                    "title": "Improve the README",
                    "action": "Add a quick start.",
                    "metric": "24 visitors",
                }
            ]
        }

        digest = app.build_digest_markdown(
            "octocat",
            signals,
            center,
            generated_at="2026-08-21T12:00:00+00:00",
        )

        self.assertIn("# GitHub Pulse Weekly Digest", digest)
        self.assertIn("@octocat", digest)
        self.assertIn("Improve the README", digest)
        self.assertIn("Traffic spike", digest)
        self.assertIn("42 repository page views", digest)
        self.assertNotIn("unique visitors across", digest)


class PersistenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.original_db_path = app.DB_PATH
        app.DB_PATH = Path(self.tempdir.name) / "github-pulse-test.sqlite3"
        app.ensure_database()

    def tearDown(self) -> None:
        app.DB_PATH = self.original_db_path
        self.tempdir.cleanup()

    def test_relationship_movements_start_after_initial_snapshot(self) -> None:
        initial = app.classify_relationships([user("Alice")], [user("Bob")])
        app.save_relation_snapshot(initial, "2026-08-20T08:00:00+00:00")
        self.assertEqual(app.get_relation_movements(), [])

        changed = app.classify_relationships([user("Carol")], [user("Bob")])
        app.save_relation_snapshot(changed, "2026-08-20T09:00:00+00:00")
        movements = app.get_relation_movements()

        self.assertEqual(
            {(item["login"], item["event_type"]) for item in movements},
            {("Alice", "lost_follower"), ("Carol", "new_follower")},
        )

    def test_relationship_window_reports_available_history(self) -> None:
        first = app.classify_relationships([user("Alice")], [])
        second = app.classify_relationships([user("Alice"), user("Bob")], [])
        third = app.classify_relationships(
            [user("Alice"), user("Bob"), user("Carol")], []
        )
        app.save_relation_snapshot(first, "2026-08-20T08:00:00+00:00")
        app.save_relation_snapshot(second, "2026-08-22T08:00:00+00:00")

        latest, baseline, period = app.get_latest_relation_counts()

        self.assertEqual(latest["followers"] - baseline["followers"], 1)
        self.assertEqual(period["days_observed"], 2.0)
        self.assertFalse(period["is_full_window"])
        self.assertEqual(period["label"], "since first collection · 2d")

        app.save_relation_snapshot(third, "2026-08-29T08:00:00+00:00")
        latest, baseline, period = app.get_latest_relation_counts()

        self.assertEqual(latest["followers"] - baseline["followers"], 1)
        self.assertTrue(period["is_full_window"])
        self.assertEqual(period["label"], "last 7 days")

    def test_repository_net_changes_include_snapshot_period(self) -> None:
        now = app.datetime.now(app.timezone.utc)
        repository = {
            "full_name": "octocat/hello-world",
            "stars": 3,
            "forks": 1,
            "watchers": 2,
            "open_issues": 0,
            "private": False,
            "archived": False,
            "language": "Python",
            "pushed_at": now.isoformat(),
        }
        app.save_repo_snapshots(
            [repository], (now - app.timedelta(days=2)).isoformat()
        )
        repository["stars"] = 5
        app.save_repo_snapshots([repository], now.isoformat())

        row = app.get_repository_signal_rows()[0]

        self.assertEqual(row["net_stars"], 2)
        self.assertEqual(row["snapshot_period"]["days_observed"], 2.0)
        self.assertEqual(
            row["snapshot_period"]["label"], "since first snapshot · 2d"
        )

    def test_repository_registry_merges_a_renamed_repository(self) -> None:
        collected_at = "2026-08-21T10:00:00+00:00"
        app.save_traffic(
            "octocat/old-name",
            {
                "count": 5,
                "uniques": 2,
                "views": [
                    {
                        "timestamp": collected_at,
                        "count": 5,
                        "uniques": 2,
                    }
                ],
            },
            None,
            collected_at=collected_at,
        )
        app.save_repo_snapshots(
            [
                {
                    "full_name": "octocat/old-name",
                    "stars": 3,
                    "forks": 1,
                }
            ],
            collected_at,
        )

        with mock.patch.object(
            app,
            "run_gh_json",
            return_value={"id": 7, "full_name": "octocat/new-name"},
        ):
            app.reconcile_repository_registry(
                [{"id": 7, "full_name": "octocat/new-name"}],
                "2026-08-22T10:00:00+00:00",
            )

        self.assertEqual(
            app.get_traffic_history("octocat/new-name")[0]["views"],
            5,
        )
        self.assertEqual(app.get_traffic_history("octocat/old-name"), [])
        rows = app.get_repository_signal_rows()
        self.assertEqual([row["repo"] for row in rows], ["octocat/new-name"])

        with app.database_connection() as connection:
            alias = connection.execute(
                "SELECT canonical_name, status FROM repository_aliases WHERE alias = ?",
                ("octocat/old-name",),
            ).fetchone()
        self.assertEqual(alias, ("octocat/new-name", "renamed"))

    def test_partial_traffic_updates_preserve_previous_valid_metrics(self) -> None:
        timestamp = "2026-08-21T10:00:00+00:00"
        views = {
            "views": [
                {
                    "timestamp": timestamp,
                    "count": 20,
                    "uniques": 8,
                }
            ]
        }
        clones = {
            "clones": [
                {
                    "timestamp": timestamp,
                    "count": 6,
                    "uniques": 3,
                }
            ]
        }
        app.save_traffic(
            "octocat/hello-world",
            views,
            clones,
            collected_at=timestamp,
        )

        updated_views = {
            "views": [
                {
                    "timestamp": timestamp,
                    "count": 25,
                    "uniques": 10,
                }
            ]
        }
        app.save_traffic(
            "octocat/hello-world",
            updated_views,
            None,
            collected_at="2026-08-21T11:00:00+00:00",
        )
        row = app.get_traffic_history("octocat/hello-world")[0]
        self.assertEqual(
            (row["views"], row["unique_views"], row["clones"], row["unique_clones"]),
            (25, 10, 6, 3),
        )

        updated_clones = {
            "clones": [
                {
                    "timestamp": timestamp,
                    "count": 9,
                    "uniques": 4,
                }
            ]
        }
        app.save_traffic(
            "octocat/hello-world",
            None,
            updated_clones,
            collected_at="2026-08-21T12:00:00+00:00",
        )
        row = app.get_traffic_history("octocat/hello-world")[0]
        self.assertEqual(
            (row["views"], row["unique_views"], row["clones"], row["unique_clones"]),
            (25, 10, 9, 4),
        )

    def test_signal_rows_separate_visitor_days_from_native_uniques(self) -> None:
        now = app.datetime.now(app.timezone.utc)
        views = {
            "count": 70,
            "uniques": 12,
            "views": [
                {
                    "timestamp": (now - app.timedelta(days=offset)).isoformat(),
                    "count": 10,
                    "uniques": 5,
                }
                for offset in range(7)
            ],
        }
        clones = {
            "count": 14,
            "uniques": 4,
            "clones": [
                {
                    "timestamp": (now - app.timedelta(days=offset)).isoformat(),
                    "count": 2,
                    "uniques": 1,
                }
                for offset in range(7)
            ],
        }
        app.save_traffic("octocat/hello-world", views, clones)

        row = app.get_repository_signal_rows()[0]

        self.assertEqual(row["views_7d"], 70)
        self.assertEqual(row["visitor_days_7d"], 35)
        self.assertEqual(row["clones_7d"], 14)
        self.assertEqual(row["cloner_days_7d"], 7)
        self.assertEqual(row["unique_visitors_14d"], 12)
        self.assertEqual(row["unique_cloners_14d"], 4)
        self.assertEqual(row["clone_view_ratio"], 20.0)

    def test_traffic_windows_end_on_the_latest_available_github_day(self) -> None:
        latest = app.datetime(2026, 8, 25, tzinfo=app.timezone.utc)
        daily = [
            {
                "timestamp": (latest - app.timedelta(days=offset)).isoformat(),
                "count": offset + 1,
                "uniques": 1,
            }
            for offset in range(14)
        ]
        app.save_traffic(
            "octocat/hello-world",
            {"count": 105, "uniques": 14, "views": daily},
            None,
            collected_at="2026-08-27T00:00:00+00:00",
        )

        row = app.get_repository_signal_rows()[0]

        self.assertEqual(row["traffic_period"]["from"], "2026-08-19")
        self.assertEqual(row["traffic_period"]["to"], "2026-08-25")
        self.assertEqual(row["views_7d"], sum(range(1, 8)))
        self.assertEqual(row["previous_views"], sum(range(8, 15)))
        self.assertTrue(row["traffic_period"]["is_complete"])
        self.assertTrue(row["traffic_comparison_ready"])


if __name__ == "__main__":
    unittest.main()
