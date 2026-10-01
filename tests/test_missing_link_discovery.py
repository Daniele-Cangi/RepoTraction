"""Offline retrieval/qualification regressions, not a discovery-quality benchmark."""
import copy
import io
import json
import unittest
import zipfile
from unittest import mock

from missing_link.discovery import problem_queries, select_candidates
from missing_link.analysis import validate_matches, validate_request, extension_groups
from missing_link.proofs import export_handoff, build_package
import test_missing_link as fixtures

repository, issue = fixtures.repository, fixtures.issue


def hit(repo, number=1, title="shorten string", state="open"):
    return {"url": f"https://github.com/{repo}/issues/{number}", "title": title, "state": state}


class RetrievalTests(unittest.TestCase):
    def test_specific_single_word_terms_work_for_enrichment_and_maintainer_corrections(self):
        for metadata in ({"claim_source": "model"}, {"maintainer_correction": {"revision": "a" * 40}}):
            for term in ("pagination", "backpressure", "serialization", "throttling", "fft"):
                with self.subTest(metadata=metadata, term=term):
                    repo = repository()
                    repo["capabilities"][0].update(metadata, search_terms=[term])
                    self.assertEqual(problem_queries(repo), [f"{term} is:open in:title,body -repo:example/words"])

    def test_singleton_package_names_and_generic_helpers_cannot_create_queries(self):
        for term in ("words", "function", "unknown", "run", "main", "helper", "get", "set", "next", "12345", "x"):
            with self.subTest(term=term):
                repo = repository()
                repo["capabilities"][0].update(claim_source="model", search_terms=[term])
                with self.assertRaisesRegex(ValueError, "No problem-oriented"):
                    problem_queries(repo)

    def test_contextual_phrase_remains_preferred_to_single_word(self):
        repo = repository()
        repo["capabilities"][0]["search_terms"] = ["pagination", "cursor pagination"]
        self.assertTrue(problem_queries(repo)[0].startswith("cursor pagination is:open"))

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

    def test_fragmented_project_names_are_removed_after_combining_terms(self):
        repo = repository()
        for name, terms, expected in (
                ("chalk/strip-ansi", ["chalk", "strip", "ansi", "escape", "removal"], "escape removal"),
                ("sindresorhus/p-limit", ["p", "limit", "promise", "concurrency"], "promise concurrency")):
            with self.subTest(name=name):
                repo["full_name"] = name
                repo["capabilities"][0]["search_terms"] = terms
                self.assertTrue(problem_queries(repo)[0].startswith(expected + " is:open"))
        repo["full_name"] = "chalk/strip-ansi"
        repo["capabilities"][0]["search_terms"] = ["chalk", "strip", "ansi"]
        with self.assertRaisesRegex(ValueError, "No problem-oriented"):
            problem_queries(repo)

    def test_unreviewed_readme_filler_does_not_become_a_second_problem_query(self):
        repo = repository()
        cap = repo["capabilities"][0]
        repo["full_name"] = "chalk/strip-ansi"
        cap.update(entrypoint="index.js:stripAnsi", search_terms=["javascript ansi escape removal"])
        repo["capabilities"].append(dict(cap, entrypoint="README.md:product", claim_source="structural",
            search_terms=["chalk", "strip", "ansi", "documentation", "states", "escape"]))
        self.assertEqual(problem_queries(repo), ["javascript ansi escape removal is:open in:title,body -repo:chalk/strip-ansi"])

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

    def test_declaration_filler_cannot_displace_reviewed_problem_terms_for_diversity(self):
        repo = repository()
        cap = repo["capabilities"][0]
        repo["capabilities"] = [dict(cap, claim_source="model", entrypoint="src/one.py:f", search_terms=[term])
                                for term in ("promise concurrency", "limited function wrapper", "async task queue")]
        repo["capabilities"] += [dict(cap, claim_source="structural", entrypoint="benchmark.js:taskWithDelay",
            summary="Declaration candidate taskWithDelay; JavaScript/TypeScript partial scan.",
            search_terms=["task", "delay", "declaration", "candidate", "java", "script", "type", "partial", "scan"])]
        repo["capabilities"] += [dict(cap, claim_source="structural", entrypoint="README.md:project",
            search_terms=["documentation metadata filler"])]
        queries = problem_queries(repo)
        self.assertEqual(len(queries), 3)
        self.assertTrue(all("declaration" not in q and "java script" not in q and "metadata filler" not in q for q in queries))
        repo["capabilities"] = repo["capabilities"][-2:-1]
        with self.assertRaisesRegex(ValueError, "No problem-oriented"):
            problem_queries(repo)

    def test_constructor_name_is_not_a_problem_phrase(self):
        repo = repository()
        repo["capabilities"][0]["search_terms"] = ["relativedelta constructor", "calendar interval difference"]
        self.assertTrue(problem_queries(repo)[0].startswith("calendar interval difference is:open"))
        repo["capabilities"][0]["search_terms"] = ["relativedelta constructor"]
        with self.assertRaisesRegex(ValueError, "No problem-oriented"):
            problem_queries(repo)

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

    def test_api_url_uses_public_html_url_and_qualifiers_are_not_title_terms(self):
        selected, count = select_candidates([[{"url": "https://api.github.com/repos/a/site/issues/1",
            "html_url": "https://github.com/a/site/issues/1", "title": "open title body repo"}]],
            ["shorten string is:open in:title,body -repo:example/words"], repository(), 1)
        self.assertEqual(count, 1)
        self.assertEqual(selected[0]["title_term_overlap"], 0)


class DiscoveryServiceTests(unittest.TestCase):
    setUp = fixtures.ServiceTests.setUp
    fake_sources = fixtures.ServiceTests.fake_sources

    def test_automatic_discovery_with_only_single_word_terms_reaches_search_without_ai(self):
        repo = repository()
        repo["capabilities"][0]["search_terms"] = ["pagination"]
        source = self.fake_sources()
        source.fetch_repository.return_value = repo
        with mock.patch("missing_link.service.PublicGitHub", return_value=source), \
             mock.patch("missing_link.service.extract_structure", return_value=repo["capabilities"]):
            result = self.service.start({"repo": "example/words"}, background=False)
        job = self.service.store.get("jobs", result["job_id"])
        self.assertEqual(job["status"], "completed")
        source.search_issues.assert_called_once_with("pagination is:open in:title,body -repo:example/words", max_pages=2, page_size=20)
        self.assertTrue(job["result"]["search"]["automatic_query"])
        self.assertEqual(job["ai_calls_used"], 0)

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


class QualificationTests(unittest.TestCase):
    def test_extension_groups_exclude_stale_or_unknown_demand_even_when_rejected(self):
        for updated in ("2017-04-07T13:24:36Z", "not-a-date", None,
                        "2027-01-01T00:00:00Z", "2026-09-29T12:00:00"):
            for partial in (True, False):
                with self.subTest(updated=updated, partial=partial):
                    matches = []
                    for number in (7, 8):
                        demand = issue()
                        demand.update(updated_at=updated, url=f"https://github.com/example/site/issues/{number}")
                        raw_match = fixtures.raw_match()
                        if not partial:
                            raw_match["checks"][0].update(status="undetermined", source_ids=[])
                        matches.append(self.evaluate(repository(), demand, fixtures.request_raw(), raw_match))
                    self.assertEqual({m["discovery_assessment"]["status"] for m in matches},
                                     {"partial_contribution" if partial else "not_a_fit"})
                    self.assertTrue(all(m["discovery_assessment"]["opportunity_review"]["qualification_blockers"]
                                        for m in matches))
                    self.assertEqual(extension_groups(matches), [])

    def test_extension_groups_still_include_independent_recent_conflicting_requests(self):
        matches = []
        for number in (7, 8):
            demand = issue()
            demand["url"] = f"https://github.com/example/site/issues/{number}"
            matches.append(self.evaluate(repository(), demand, fixtures.request_raw(), fixtures.raw_match()))
        groups = extension_groups(matches)
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["count"], 2)

    def test_old_request_and_unknown_or_future_activity_cannot_be_followup_ready(self):
        for updated in ("2017-04-07T13:24:36Z", "not-a-date", None, "2027-01-01T00:00:00Z",
                        "2026-09-29T12:00:00"):
            with self.subTest(updated=updated):
                repo, demand, raw_request, raw_match = self.case()
                demand["updated_at"] = updated
                assessment = self.evaluate(repo, demand, raw_request, raw_match)["discovery_assessment"]
                self.assertEqual(assessment["status"], "needs_review")
                self.assertFalse(assessment["eligible_for_followup"])
                self.assertTrue(assessment["opportunity_review"]["qualification_blockers"])
        repo, demand, raw_request, raw_match = self.case()
        demand.pop("fetched_at")
        self.assertFalse(self.evaluate(repo, demand, raw_request, raw_match)["discovery_assessment"]["eligible_for_followup"])

    def test_reference_only_body_does_not_turn_title_into_adoption_demand(self):
        repo, demand, raw_request, raw_match = self.case()
        demand["title"] = "Shorten text without splitting words"
        demand["body"] = "For ex:\n- https://github.com/another/cache\n"
        assessment = self.evaluate(repo, demand, raw_request, raw_match)["discovery_assessment"]
        self.assertEqual(assessment["status"], "reference_only")
        self.assertFalse(assessment["eligible_for_followup"])
        self.assertTrue(assessment["opportunity_review"]["reference_body_hint"])

    def test_markdown_and_html_link_labels_do_not_establish_adoption_demand(self):
        for body in (
            "[Example project](https://github.com/x/y)",
            "[Example project](<https://github.com/x/y>)",
            '[Example project](https://github.com/x/y "Project title")',
            "[Example [nested] project](https://example.org/wiki/Foo_(bar))",
            '<a href="https://github.com/x/y"><strong>Example project</strong></a>',
            '<p>For example: <a href="https://github.com/x/y">Useful project</a></p>',
            "![Project screenshot](https://example.org/image.png)",
            "[Example project][project]\n\n[project]: https://github.com/x/y",
            "[Project][]\n\n[Project]: https://github.com/x/y",
            "[Project]\n\n[Project]: https://github.com/x/y",
        ):
            with self.subTest(body=body):
                repo, demand, raw_request, raw_match = self.case()
                demand.update(title="Shorten text without splitting words", body=body)
                assessment = self.evaluate(repo, demand, raw_request, raw_match)["discovery_assessment"]
                self.assertEqual(assessment["status"], "reference_only")
                self.assertFalse(assessment["eligible_for_followup"])
                self.assertTrue(assessment["opportunity_review"]["reference_body_hint"])

    def test_link_normalization_preserves_real_request_prose(self):
        for body in (
            "I need plain text shortened without splitting words. [Example project](https://github.com/x/y)",
            '<p>I need plain text shortened without splitting words. <a href="https://github.com/x/y">Example project</a></p>',
            "I need plain text shortened without splitting words. [Project][p]\n\n[p]: https://github.com/x/y",
            "I need plain text shortened without splitting words. [An unfinished link](",
            "I need plain text shortened without splitting words. [Plain bracketed prose]",
            r"I need plain text shortened without splitting words. \[Literal label](https://github.com/x/y)",
        ):
            with self.subTest(body=body):
                repo, demand, raw_request, raw_match = self.case()
                demand["body"] = body
                assessment = self.evaluate(repo, demand, raw_request, raw_match)["discovery_assessment"]
                self.assertEqual(assessment["status"], "external_lead")
                self.assertTrue(assessment["eligible_for_followup"])
                self.assertFalse(assessment["opportunity_review"]["reference_body_hint"])

    def test_short_real_request_and_snapshot_relative_age_are_not_discarded(self):
        repo, demand, raw_request, raw_match = self.case()
        demand["body"] = "without splitting words"
        assessment = self.evaluate(repo, demand, raw_request, raw_match)["discovery_assessment"]
        self.assertEqual(assessment["status"], "external_lead")
        self.assertEqual(assessment["opportunity_review"]["activity_age_days"], 1)
        # Reassessing a saved snapshot does not age its observations using wall time.
        self.assertEqual(self.evaluate(repo, demand, raw_request, raw_match)["discovery_assessment"], assessment)

    def test_partial_support_survives_hard_conflict_without_becoming_a_lead(self):
        match = validate_matches([fixtures.raw_match()], repository(), issue(),
                                 validate_request(fixtures.request_raw(), issue()), "model")[0]
        assessment = match["discovery_assessment"]
        self.assertEqual(match["classification"], "rejected")
        self.assertEqual(assessment["status"], "partial_contribution")
        self.assertEqual(assessment["contribution"], "supported_with_conflicts")
        self.assertEqual(assessment["supported_requirement_ids"], ["r0"])
        self.assertEqual(assessment["conflicting_requirement_ids"], ["r1"])
        self.assertFalse(assessment["eligible_for_followup"])
        self.assertEqual(extension_groups([match, copy.deepcopy(match)]), [])
        self.assertEqual(export_handoff(match, repository())["match"]["discovery_assessment"], assessment)

    def case(self):
        demand = issue()
        demand["target_context"] = {"id": 101, "full_name": "example/site", "revision": "b" * 40,
            "public": True, "reference_only": True,
            "files": [{"path": "package.json", "text": '{"name":"consumer"}',
                "url": "https://github.com/example/site/blob/" + "b" * 40 + "/package.json"}], "fingerprint": "target-fixture"}
        demand["body"] = "I need plain text shortened without splitting words."
        demand["comments"] = []
        raw_request = fixtures.request_raw()
        raw_request["requirements"] = raw_request["requirements"][:1]
        raw_match = fixtures.raw_match()
        raw_match["checks"] = raw_match["checks"][:1]
        return repository(), demand, raw_request, raw_match

    def evaluate(self, repo, demand, raw_request, raw_match):
        request = validate_request(raw_request, demand)
        return validate_matches([raw_match], repo, demand, request, "coding_agent_import")[0]

    def test_supported_external_lead_does_not_claim_verified_novelty(self):
        match = self.evaluate(*self.case())
        self.assertEqual(match["classification"], "direct")
        self.assertEqual(match["discovery_assessment"]["status"], "external_lead")
        self.assertTrue(match["discovery_assessment"]["eligible_for_followup"])
        self.assertEqual(match["discovery_assessment"]["novelty"], "unverified")
        self.assertEqual(match["bridge"]["verification"]["status"], "not_executed")

    def test_same_project_uses_canonical_url_and_immutable_repo_id_after_rename(self):
        for fields in ({"url": "https://github.com/EXAMPLE/WORDS/issues/9", "repo": "untrusted/other"},
                       {"url": "https://github.com/renamed/project/issues/9", "repo_id": 42}):
            repo, demand, raw_request, raw_match = self.case()
            demand.update(fields)
            match = self.evaluate(repo, demand, raw_request, raw_match)
            self.assertEqual(match["classification"], "direct")
            self.assertEqual(match["discovery_assessment"]["status"], "same_project")
            self.assertFalse(match["discovery_assessment"]["eligible_for_followup"])

    def test_known_repository_reference_keeps_technical_fit_but_not_new_discovery(self):
        repo, demand, raw_request, raw_match = self.case()
        demand["comments"] = [{"url": demand["url"] + "#issuecomment-8",
                               "body": "Already discussed https://github.com/example/words#readme"}]
        match = self.evaluate(repo, demand, raw_request, raw_match)
        self.assertEqual(match["classification"], "direct")
        assessment = match["discovery_assessment"]
        self.assertEqual(assessment["status"], "known_reference")
        ref = assessment["references"][0]
        self.assertEqual(ref["source_id"], "q1")
        self.assertIn(ref["quote"], demand["comments"][0]["body"])
        self.assertFalse(assessment["eligible_for_followup"])

    def test_name_reference_is_only_a_hint_and_never_assumes_endorsement(self):
        for name, mention in (("p-limit", "We tried p-limit but rejected it."),
                              ("click", "The existing `click` package did not suit us."),
                              ("dateutil", "from dateutil import parser")):
            repo, demand, raw_request, raw_match = self.case()
            repo["full_name"] = "source/" + name
            demand["body"] += " " + mention
            assessment = self.evaluate(repo, demand, raw_request, raw_match)["discovery_assessment"]
            self.assertEqual(assessment["status"], "reference_review")
            self.assertFalse(assessment["eligible_for_followup"])
            self.assertTrue(any("not adoption or endorsement" in reason for reason in assessment["reasons"]))

    def test_ordinary_click_and_similar_repo_link_are_not_source_references(self):
        repo, demand, raw_request, raw_match = self.case()
        repo["full_name"] = "pallets/click"
        demand["body"] += " When I click a button: https://github.com/pallets/click-extra ."
        assessment = self.evaluate(repo, demand, raw_request, raw_match)["discovery_assessment"]
        self.assertEqual(assessment["relationship"], "external")
        self.assertEqual(assessment["references"], [])

    def test_terminal_sentence_and_markdown_punctuation_keep_exact_repository_reference(self):
        for suffix in (".", ". Next sentence", ".\nNext line", "...", '"', "'", "`", "**",
                       ".)", '."', ".`", ";", "!", ":", "}", ".git.", '.git"'):
            with self.subTest(suffix=suffix):
                repo, demand, raw_request, raw_match = self.case()
                demand["body"] += " See https://github.com/example/words" + suffix
                assessment = self.evaluate(repo, demand, raw_request, raw_match)["discovery_assessment"]
                self.assertEqual(assessment["status"], "known_reference")
                self.assertEqual(assessment["relationship"], "already_referenced")
                self.assertFalse(assessment["eligible_for_followup"])
                self.assertEqual(assessment["reference_count"], 1)
                self.assertEqual(assessment["references"][0]["kind"], "repository_link")
                self.assertIn(assessment["references"][0]["quote"], demand["title"] + "\n" + demand["body"])

    def test_repository_name_suffixes_are_not_terminal_punctuation(self):
        for suffix in (".extra", ".extra.", ".git.extra", ".git-extra", ".git2", "-extra", "_extra", "2", "...extra", "._extra"):
            with self.subTest(suffix=suffix):
                repo, demand, raw_request, raw_match = self.case()
                demand["body"] += " See https://github.com/example/words" + suffix
                assessment = self.evaluate(repo, demand, raw_request, raw_match)["discovery_assessment"]
                self.assertEqual(assessment["relationship"], "external")
                self.assertEqual(assessment["reference_count"], 0)
                self.assertEqual(assessment["references"], [])

    def test_punctuated_existing_reference_cannot_enter_external_extension_groups(self):
        matches = []
        for number in (7, 8):
            demand = issue()
            demand["url"] = f"https://github.com/example/site/issues/{number}"
            demand["body"] += " Previously considered https://github.com/example/words."
            matches += validate_matches([fixtures.raw_match()], repository(), demand,
                validate_request(fixtures.request_raw(), demand), "model")
        self.assertTrue(all(m["classification"] == "rejected" for m in matches))
        self.assertTrue(all(m["discovery_assessment"]["status"] == "known_reference" for m in matches))
        self.assertEqual(extension_groups(matches), [])

    def test_all_undetermined_checks_and_forged_discovery_claim_are_not_a_lead(self):
        repo, demand, raw_request, raw_match = self.case()
        raw_match["checks"] = []
        raw_match["discovery_assessment"] = {"status": "external_lead", "novelty": "verified", "eligible_for_followup": True}
        match = self.evaluate(repo, demand, raw_request, raw_match)
        self.assertEqual(match["discovery_assessment"]["status"], "similarity_only")
        self.assertEqual(match["discovery_assessment"]["contribution"], "not_demonstrated")
        self.assertFalse(match["discovery_assessment"]["eligible_for_followup"])

    def test_inferred_mandatory_demand_needs_confirmation_even_with_supported_code(self):
        repo, demand, raw_request, raw_match = self.case()
        raw_request["requirements"][0]["explicit"] = False
        raw_request["requirements"][0]["inference"] = "Fixture inference requiring author confirmation."
        match = self.evaluate(repo, demand, raw_request, raw_match)
        self.assertEqual(match["classification"], "direct")
        self.assertEqual(match["discovery_assessment"]["status"], "needs_review")
        self.assertFalse(match["discovery_assessment"]["eligible_for_followup"])

    def test_empty_reference_notes_and_incomplete_or_resolved_demand_not_new(self):
        repo, demand, raw_request, raw_match = self.case()
        demand["title"] += " without splitting words"
        demand["body"] = ""
        self.assertEqual(self.evaluate(repo, demand, raw_request, raw_match)["discovery_assessment"]["status"], "reference_only")
        for update, expected in (({"context_complete": False}, "needs_review"),
                                 ({"repo_archived": True}, "not_actionable"),
                                 ({"bot": True}, "not_actionable")):
            repo, demand, raw_request, raw_match = self.case()
            demand.update(update)
            self.assertEqual(self.evaluate(repo, demand, raw_request, raw_match)["discovery_assessment"]["status"], expected)
        repo, demand, raw_request, raw_match = self.case()
        raw_request["status"] = "resolved"
        self.assertEqual(self.evaluate(repo, demand, raw_request, raw_match)["discovery_assessment"]["status"], "not_actionable")

    def test_bounded_reference_ledger_preserves_exact_original_quotes(self):
        repo, demand, raw_request, raw_match = self.case()
        demand["comments"] = [{"url": demand["url"] + f"#issuecomment-{i}",
                               "body": f"Reference {i}: https://github.com/example/words/"} for i in range(20)]
        assessment = self.evaluate(repo, demand, raw_request, raw_match)["discovery_assessment"]
        self.assertEqual(assessment["reference_count"], 20)
        self.assertEqual(len(assessment["references"]), 8)
        self.assertFalse(assessment["reference_coverage_complete"])
        for ref in assessment["references"]:
            index = int(ref["source_id"][1:]) - 1
            self.assertIn(ref["quote"], demand["comments"][index]["body"])

    def test_late_repository_link_overrides_full_hint_ledger_and_survives_exports(self):
        repo, demand, raw_request, raw_match = self.case()
        demand["body"] += " " + "`words` " * 8
        link_comment = {"url": demand["url"] + "#issuecomment-9",
                        "body": "Previously tried https://github.com/example/words#readme", "author": "fixture-author"}
        demand["comments"] = [link_comment]
        match = self.evaluate(repo, demand, raw_request, raw_match)
        assessment = match["discovery_assessment"]
        self.assertEqual(assessment["status"], "known_reference")
        self.assertEqual(assessment["relationship"], "already_referenced")
        self.assertEqual(assessment["reference_count"], 9)
        self.assertEqual(len(assessment["references"]), 8)
        self.assertFalse(assessment["reference_coverage_complete"])
        self.assertFalse(assessment["eligible_for_followup"])
        strongest = assessment["references"][0]
        self.assertEqual(strongest["kind"], "repository_link")
        self.assertEqual(strongest["source_id"], "q1")
        self.assertEqual(strongest["url"], link_comment["url"])
        self.assertIn(strongest["quote"], link_comment["body"])
        self.assertEqual(export_handoff(match, repo)["match"]["discovery_assessment"], assessment)
        with zipfile.ZipFile(io.BytesIO(build_package(match, repo))) as archive:
            self.assertEqual(json.loads(archive.read("handoff.json"))["match"]["discovery_assessment"], assessment)

    def test_links_keep_precedence_and_stable_order_even_after_both_kinds_exceed_cap(self):
        repo, demand, raw_request, raw_match = self.case()
        demand["body"] += " " + "`words` " * 12
        demand["comments"] = [{"url": demand["url"] + f"#issuecomment-{i}",
            "body": f"Exact reference {i}: https://github.com/example/words/"} for i in range(12)]
        assessment = self.evaluate(repo, demand, raw_request, raw_match)["discovery_assessment"]
        self.assertEqual(assessment["status"], "known_reference")
        self.assertEqual(assessment["reference_count"], 24)
        self.assertEqual([ref["source_id"] for ref in assessment["references"]], [f"q{i}" for i in range(1, 9)])
        self.assertTrue(all(ref["kind"] == "repository_link" for ref in assessment["references"]))
        self.assertFalse(assessment["reference_coverage_complete"])

    def test_more_than_eight_name_hints_alone_still_require_reference_review(self):
        repo, demand, raw_request, raw_match = self.case()
        demand["body"] += " " + "`words` " * 12
        assessment = self.evaluate(repo, demand, raw_request, raw_match)["discovery_assessment"]
        self.assertEqual(assessment["status"], "reference_review")
        self.assertEqual(assessment["reference_count"], 12)
        self.assertEqual(len(assessment["references"]), 8)
        self.assertTrue(all(ref["kind"] == "package_name_hint" for ref in assessment["references"]))

    def test_known_and_internal_work_do_not_inflate_external_extension_groups(self):
        match = validate_matches([fixtures.raw_match()], repository(), issue(),
                                  validate_request(fixtures.request_raw(), issue()), "model")[0]
        other = copy.deepcopy(match)
        other["id"] = "other"
        other["request"]["url"] += "1"
        self.assertEqual(extension_groups([match, other])[0]["count"], 2)
        for relationship in ("same_project", "already_referenced", "reference_hint", "unknown"):
            other["discovery_assessment"]["relationship"] = relationship
            self.assertEqual(extension_groups([match, other]), [])
