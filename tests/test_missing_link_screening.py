"""Bounded retrieval filtering: no paid calls, no compatibility/novelty claims."""
import unittest
from unittest import mock

from missing_link.discovery import screen_candidate, problem_queries
from missing_link.provider import Provider
import test_missing_link as fixtures


def code_dump():
    return dict(fixtures.issue(), title="functions.php", body="<?php\n" + "function f() { return true; }\n" * 100,
                comments=[], context_complete=False)


class ScreeningTests(unittest.TestCase):
    def test_acquired_php_dump_gets_a_hint_not_a_rejection(self):
        screening = screen_candidate(code_dump())
        self.assertTrue(screening["skip"])
        self.assertEqual(screening["code"], "source_file_dump_hint")
        self.assertFalse(screening["proves_absence_of_demand"])
        self.assertFalse(screening["discussion_complete"])

    def test_precise_exam_preparation_signature_not_generic_manual_words(self):
        issue = dict(fixtures.issue(), title="Cloud Lab Preparation Manual", comments=[],
            body="# Cloud & Big Data Lab — Exam Preparation Manual\nCovers Problem Sheets 7–12. In your syllabus.")
        self.assertTrue(screen_candidate(issue)["skip"])
        for title, body in (("Generate a manual", "I need a user manual generator."),
                            (issue["title"], issue["body"] + "\nPlease fix the byte formatter."),
                            ("Bug in functions.php", code_dump()["body"]),
                            ("functions.php", "<?php\n" + "return true;\n" * 30)):
            self.assertFalse(screen_candidate(dict(issue, title=title, body=body))["skip"])

    def test_discussion_or_independent_request_prose_preserves_candidate(self):
        for issue in (dict(code_dump(), comments=[{"body": "Can we fix this?"}]),
                      dict(code_dump(), body=code_dump()["body"] + "\nExpected behavior: format byte counts."),
                      fixtures.issue()):
            self.assertFalse(screen_candidate(issue)["skip"])

    def test_request_prose_in_php_comments_is_not_screened_out(self):
        for comment in ("// Please fix the formatter", "/* I need help formatting */",
                        "/** I would like human-readable sizes */", " * Expected behavior: readable byte sizes",
                        "# Please add byte formatting", "/// Could you support formatting?",
                        "$size = 1024; // Please fix the formatter", "$size = 1024; /* I need byte formatting */",
                        "/*\n * I need help formatting\n */"):
            with self.subTest(comment=comment):
                demand = dict(code_dump(), body=code_dump()["body"] + "\n" + comment)
                original = demand["body"]
                self.assertFalse(screen_candidate(demand)["skip"])
                self.assertEqual(demand["body"], original)
        self.assertTrue(screen_candidate(code_dump())["skip"])  # A genuine dump still gets the bounded hint.

    def test_language_name_stays_whole_while_camelcase_mechanisms_still_split(self):
        repo = fixtures.repository()
        for term in ("JavaScript human byte formatting", "java script human byte formatting"):
            repo["capabilities"][0]["search_terms"] = [term]
            self.assertTrue(problem_queries(repo)[0].startswith("javascript human byte formatting is:open"))
        repo["capabilities"][0]["search_terms"] = ["TypeScript byteSize formatter"]
        self.assertTrue(problem_queries(repo)[0].startswith("typescript byte size formatter is:open"))


class ScreeningServiceTests(unittest.TestCase):
    setUp = fixtures.ServiceTests.setUp
    fake_sources = fixtures.ServiceTests.fake_sources

    def run_screening(self, demand=None, **input_override):
        source = self.fake_sources()
        source.fetch_issue.return_value = demand or code_dump()
        with mock.patch("missing_link.service.PublicGitHub", return_value=source), \
             mock.patch("missing_link.service.extract_structure", return_value=fixtures.repository()["capabilities"]):
            result = self.service.start({"repo": "example/words", **input_override}, background=False)
        return self.service.store.get("jobs", result["job_id"]), source

    def test_automatic_skip_is_persisted_and_does_not_interpret_or_fetch_target(self):
        provider = mock.Mock()
        provider.describe.return_value = {"configured": True}
        provider.interpret_capabilities.return_value = fixtures.repository()["capabilities"]
        self.service.provider = provider
        job, source = self.run_screening(use_ai=True)
        self.assertEqual(job["status"], "completed")
        self.assertEqual(len(job["result"]["candidate_skips"]), 1)
        self.assertEqual(len(job["checkpoint"]["candidate_screening"]), 1)
        self.assertEqual(job["result"]["match_ids"], [])
        self.assertNotIn("candidate_errors", job["result"])
        provider.interpret_request.assert_not_called()
        provider.evaluate.assert_not_called()
        source.fetch_reference_context.assert_not_called()
        self.assertEqual(job["ai_calls_used"], 0)

    def test_manual_issue_or_query_bypasses_automatic_screening(self):
        for override in ({"issue_url": fixtures.issue()["url"]}, {"query": "custom functions.php"}):
            with self.subTest(override=override):
                self.service.provider = Provider({})
                job, source = self.run_screening(**override)
                self.assertEqual(job["status"], "completed")
                self.assertNotIn("candidate_skips", job["result"])
                self.assertTrue(job["result"]["match_ids"])
                source.fetch_reference_context.assert_called_once()

    def test_automatic_php_comment_request_reaches_analysis_without_replacement(self):
        demand = dict(code_dump(), body=code_dump()["body"] + "\n// Please fix the formatter")
        job, source = self.run_screening(demand=demand)
        self.assertEqual(job["status"], "completed")
        self.assertNotIn("candidate_skips", job["result"])
        self.assertTrue(job["result"]["match_ids"])
        self.assertEqual(job["checkpoint"]["evaluated"], ["0"])
        source.fetch_issue.assert_called_once()
        source.fetch_reference_context.assert_called_once()
        self.assertEqual(job["ai_calls_used"], 0)

    def test_resume_keeps_skip_and_does_not_refill_frozen_selection(self):
        job, source = self.run_screening()
        job.update(status="paused", error="Fixture pause after screening")
        self.service.store.put("jobs", job["id"], job)
        source.fetch_issue.side_effect = AssertionError("Must not refetch skipped discussion")
        source.search_issues.side_effect = AssertionError("Must not rerank or refill")
        with mock.patch("missing_link.service.PublicGitHub", return_value=source):
            self.service.resume({"job_id": job["id"]}, background=False)
        resumed = self.service.store.get("jobs", job["id"])
        self.assertEqual(resumed["status"], "completed")
        self.assertEqual(resumed["result"]["candidate_skips"], job["result"]["candidate_skips"])
        self.assertEqual(resumed["checkpoint"]["candidates"], job["checkpoint"]["candidates"])
