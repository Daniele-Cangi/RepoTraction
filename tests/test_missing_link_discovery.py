"""Offline retrieval/qualification regressions, not a discovery-quality benchmark."""
import copy
import unittest
from unittest import mock

from missing_link.discovery import problem_queries, select_candidates
import test_missing_link as fixtures

repository, issue = fixtures.repository, fixtures.issue


def hit(repo, number=1, title="shorten string", state="open"):
    return {"url": f"https://github.com/{repo}/issues/{number}", "title": title, "state": state}


class RetrievalTests(unittest.TestCase):
    def test_remove_package_tokens_but_keep_problem_words(self):
        repo = repository()
        repo["full_name"] = "sindresorhus/p-limit"
        repo["capabilities"][0]["search_terms"] = ["pLimit promise concurrency", "p-limit", "p limit concurrency limit"]
        query = problem_queries(repo)[0]
        self.assertTrue(query.startswith("promise concurrency is:open in:title,body -repo:sindresorhus/p-limit"))
        self.assertLessEqual(len(query) + len(" is:issue is:public"), 256)
        repo["capabilities"][0]["search_terms"] = ["p-limit", "function"]
        with self.assertRaisesRegex(ValueError, "No problem-oriented"):
            problem_queries(repo)

    def test_diversify_modules_and_prefer_implementation(self):
        repo = repository()
        cap = repo["capabilities"][0]
        repo["capabilities"] = [dict(cap, entrypoint=path + ":f", search_terms=[term]) for path, term in [
            ("tools/check.py", "check dependencies"), ("src/one.py", "shorten string"),
            ("src/one.py", "word boundaries"), ("src/two.py", "validate unicode"), ("src/three.py", "parse text")]]
        queries = problem_queries(repo)
        self.assertEqual([q.split(" is:open")[0] for q in queries], ["shorten string", "validate unicode", "parse text"])

    def test_generated_scope_and_phrase_fit_github_query_limit(self):
        repo = repository()
        repo["full_name"] = "o" * 39 + "/" + "r" * 100
        repo["capabilities"][0]["search_terms"] = ["shorten strings without splitting multibyte unicode characters"]
        query = problem_queries(repo)[0]
        self.assertLessEqual(len(query + " is:issue is:public"), 256)
        self.assertIn("-repo:" + repo["full_name"], query)

    def test_rank_open_external_diverse_projects_and_queries_before_first_hits(self):
        batches = [[hit("example/words"), hit("a/site", state="closed"), hit("b/site"), hit("b/site", 2)],
                   [hit("c/site", title="word boundaries"), hit("d/site", title="nothing relevant")]]
        selected, count = select_candidates(batches, ["shorten string", "word boundaries"], repository(), 3)
        self.assertEqual(count, 6)
        self.assertEqual({c["repo"] for c in selected[:2]}, {"b/site", "c/site"})
        self.assertEqual(selected[2]["repo"], "d/site")
        other_query = next(c for c in selected if c["repo"] == "c/site")
        self.assertEqual(other_query["retrieval"], [{"query_index": 1, "upstream_rank": 1}])
        self.assertEqual(other_query["title_term_overlap"], 2)

    def test_dedup_case_insensitive_and_validate_url_not_supplied_repo(self):
        batches = [[dict(hit("A/site"), repo="wrong/name"), hit("a/site"),
                    {"url": "https://github.com/a/site/pull/1"}, {"url": "https://evil.example/a/site/issues/1"}],
                   [hit("a/site")]]
        selected, count = select_candidates(batches, ["shorten string", "word boundaries"], repository(), 5)
        self.assertEqual(count, 1)
        self.assertEqual(selected[0]["repo"], "A/site")
        self.assertEqual(len(selected[0]["retrieval"]), 3)


class DiscoveryServiceTests(unittest.TestCase):
    setUp = fixtures.ServiceTests.setUp
    fake_sources = fixtures.ServiceTests.fake_sources

    def test_query_override_and_candidate_decision_are_persisted(self):
        source = self.fake_sources()
        source.search_issues.return_value = {"items": [hit("a/site", state="closed"), hit("b/site")]}
        source.fetch_issue.return_value = issue()
        with mock.patch("missing_link.service.PublicGitHub", return_value=source), \
             mock.patch("missing_link.service.extract_structure", return_value=repository()["capabilities"]):
            result = self.service.start({"repo": "example/words", "query": "custom is:closed", "max_candidates": 1}, background=False)
        source.search_issues.assert_called_once_with("custom is:closed", max_pages=2, page_size=20)
        job = self.service.store.get("jobs", result["job_id"])
        self.assertFalse(job["result"]["search"]["automatic_query"])
        self.assertEqual(job["checkpoint"]["candidates"], job["result"]["search"]["selected_candidates"])
        self.assertEqual(job["checkpoint"]["candidates"][0]["repo"], "b/site")
        self.assertEqual(job["ai_calls_used"], 0)

    def test_resume_keeps_candidate_order_without_retrieval_or_reranking(self):
        source = self.fake_sources()
        source.search_issues.return_value = {"items": [hit("b/site"), hit("a/site")]}
        source.fetch_issue.side_effect = fixtures.Paused("fixture pause before interpretation")
        with mock.patch("missing_link.service.PublicGitHub", return_value=source), \
             mock.patch("missing_link.service.extract_structure", return_value=repository()["capabilities"]):
            result = self.service.start({"repo": "example/words", "query": "shorten string"}, background=False)
        paused = self.service.store.get("jobs", result["job_id"])
        self.assertEqual(paused["status"], "paused")
        source.search_issues.side_effect = AssertionError("Retrieval must not rerun")
        source.fetch_issue.side_effect = None
        source.fetch_issue.return_value = issue()
        with mock.patch("missing_link.service.PublicGitHub", return_value=source), \
             mock.patch("missing_link.service.select_candidates", side_effect=AssertionError("Must not rerank")):
            self.service.resume({"job_id": result["job_id"]}, background=False)
        resumed = self.service.store.get("jobs", result["job_id"])
        self.assertEqual(resumed["status"], "completed")
        self.assertEqual(paused["checkpoint"]["candidates"], resumed["checkpoint"]["candidates"])
