"""Regression fixtures for constraint loss; no provider or repository code execution."""
import unittest
from unittest import mock

from missing_link.analysis import validate_request, validate_matches
from missing_link.context import build_context
from missing_link.discussion import constraint_hints, MAX_CONSTRAINT_HINTS
from missing_link.provider import Provider
from test_missing_link import issue, repository, request_raw, raw_match, request_completion


class DiscussionReviewTests(unittest.TestCase):
    def positive(self, demand, raw=None):
        request = validate_request(raw or request_raw(), demand)
        match = raw_match()
        match["checks"] = [{"requirement_id": r["id"], "status": "satisfied", "contribution": "existing_behavior", "reason": "Fixture citation only",
                            "source_ids": ["c0:0"]} for r in request["requirements"]]
        return validate_matches([match], repository(), demand, request, "model")[0]

    def comment(self, body, association="OWNER", author="maintainer"):
        return {"url": issue()["url"] + "#issuecomment-later", "body": body, "author": author,
                "author_type": "User", "author_association": association}

    def title_constraint(self):
        demand = issue()
        demand.update(title="Must not use Python", body="I need plain text shortened without splitting words.",
                      comments=[])
        raw = request_raw()
        raw["requirements"] = raw["requirements"][:1]
        return demand, raw

    def test_omitted_title_constraint_blocks_positive(self):
        demand, raw = self.title_constraint()
        match = self.positive(demand, raw)
        self.assertEqual(match["classification"], "investigate")
        hint = match["request"]["constraint_review"]["items"][0]
        self.assertEqual(hint["quote"], demand["title"])
        self.assertEqual(hint["source_id"], "q0")
        self.assertEqual(hint["authority"], "request_author")
        self.assertEqual(hint["represented_by"], [])
        self.assertTrue(hint["needs_review"])

    def test_extracted_title_constraint_is_grounded_and_conflict_rejected(self):
        demand, raw = self.title_constraint()
        raw["requirements"].append({"text": "No Python runtime", "mandatory": True, "explicit": True,
                                    "source_id": "q0", "quote": demand["title"], "inference": ""})
        request = validate_request(raw, demand)
        self.assertEqual(request["constraint_review"]["qualification_blockers"], [])
        self.assertEqual(request["constraint_review"]["items"][0]["represented_by"], ["r1"])
        self.assertEqual(self.positive(demand, raw)["classification"], "direct")
        self.assertEqual(validate_matches([raw_match()], repository(), demand, request, "model")[0]
                         ["classification"], "rejected")

    def test_constraint_sentence_citation_does_not_require_following_explanation(self):
        body = "Must preserve the API. This keeps clients working."
        demand = dict(issue(), body=body, comments=[])
        raw = request_raw()
        raw["requirements"] = [dict(raw["requirements"][0], text="Preserve the API",
                                    quote="Must preserve the API.")]
        provider = Provider({"REPOTRACTION_AI_URL": "http://localhost/v1", "REPOTRACTION_AI_MODEL": "fixture"})
        with mock.patch.object(provider, "complete", side_effect=request_completion(raw)) as complete:
            request = provider.interpret_request(demand, mock.Mock())
        complete.assert_called_once()
        self.assertEqual(request["requirements"][0]["source"]["quote"], "Must preserve the API.")
        hint = request["constraint_review"]["items"][0]
        self.assertEqual(hint["quote"], "Must preserve the API.")
        self.assertEqual(hint["represented_by"], ["r0"])
        self.assertFalse(request["constraint_review"]["qualification_blockers"])
        self.assertEqual(self.positive(demand, raw)["classification"], "direct")
        # Broader legacy/manual exact citations keep their existing contract.
        raw["requirements"][0]["quote"] = body
        self.assertFalse(validate_request(raw, demand)["constraint_review"]["qualification_blockers"])

    def test_separate_constraint_sentences_on_one_line_cannot_hide_an_omission(self):
        demand = dict(issue(), body="Must preserve the API. This keeps clients working. No Node.js dependencies.",
                      comments=[])
        raw = request_raw()
        raw["requirements"] = [dict(raw["requirements"][0], text="Preserve the API", quote="Must preserve the API."),
            dict(raw["requirements"][0], text="No Node.js dependencies", quote="No Node.js dependencies.")]
        provider = Provider({"REPOTRACTION_AI_URL": "http://localhost/v1", "REPOTRACTION_AI_MODEL": "fixture"})
        with mock.patch.object(provider, "complete", side_effect=request_completion(raw)):
            request = provider.interpret_request(demand, mock.Mock())
        hints = request["constraint_review"]["items"]
        self.assertEqual([hint["quote"] for hint in hints], ["Must preserve the API.", "No Node.js dependencies."])
        self.assertEqual(len({hint["id"] for hint in hints}), 2)
        self.assertEqual([hint["represented_by"] for hint in hints], [["r0"], ["r1"]])
        self.assertFalse(request["constraint_review"]["qualification_blockers"])
        self.assertEqual(self.positive(demand, raw)["classification"], "direct")
        raw["requirements"].pop()
        match = self.positive(demand, raw)
        self.assertEqual(match["classification"], "investigate")
        self.assertTrue(match["request"]["constraint_review"]["items"][1]["needs_review"])

    def test_sentence_constraints_keep_source_mandatory_and_explicit_guards(self):
        demand = dict(issue(), body="Must preserve the API. This keeps clients working.",
                      comments=[self.comment("Must preserve the API.")])
        base = dict(request_raw()["requirements"][0], text="Preserve the API", quote="Must preserve the API.")
        for override in ({"quote": "This keeps clients working."}, {"source_id": "q1"},
                         {"mandatory": False}, {"explicit": False}):
            with self.subTest(override=override):
                raw = dict(request_raw(), requirements=[dict(base, **override)])
                hint = validate_request(raw, demand)["constraint_review"]["items"][0]
                self.assertEqual(hint["represented_by"], [])
                self.assertTrue(hint["needs_review"])

    def test_later_constraint_sentence_keeps_authority_review(self):
        for body, association, needs_review in (
                ("No Node.js dependencies. This keeps installation small.", "OWNER", False),
                ("No Node.js dependencies. This keeps installation small.", "NONE", True),
                ("[automation] No Node.js dependencies. This keeps installation small.", "OWNER", True)):
            with self.subTest(body=body, association=association):
                demand = dict(issue(), body="Shorten plain text.", comments=[self.comment(body, association)])
                raw = request_raw()
                raw["requirements"] = [dict(raw["requirements"][0], text="No Node.js dependencies",
                                            source_id="q1", quote="No Node.js dependencies.")]
                provider = Provider({"REPOTRACTION_AI_URL": "http://localhost/v1", "REPOTRACTION_AI_MODEL": "fixture"})
                with mock.patch.object(provider, "complete", side_effect=request_completion(raw)):
                    request = provider.interpret_request(demand, mock.Mock())
                hint = request["constraint_review"]["items"][0]
                self.assertEqual(hint["represented_by"], ["r0"])
                self.assertEqual(hint["needs_review"], needs_review)

    def test_same_line_constraint_scan_stays_bounded_and_prioritizes_dependencies(self):
        body = " ".join(f"Must preserve rule {index}." for index in range(20)) + " No Node.js dependencies."
        hints = constraint_hints(dict(issue(), body=body, comments=[]))
        self.assertEqual(len(hints["items"]), MAX_CONSTRAINT_HINTS)
        self.assertEqual(hints["markers_found"], 21)
        self.assertFalse(hints["complete"])
        self.assertEqual(len({hint["id"] for hint in hints["items"]}), MAX_CONSTRAINT_HINTS)
        self.assertEqual(hints["items"][-1]["quote"], "No Node.js dependencies.")

    def test_short_citation_cannot_clear_truncated_or_compound_constraint(self):
        for body in ("Must preserve " + "boundary " * 100, "Must preserve the API and must not use Node.js."):
            with self.subTest(body=body):
                demand = dict(issue(), body=body, comments=[])
                raw = dict(request_raw(), requirements=[dict(request_raw()["requirements"][0],
                    text="Preserve boundary", quote=body[:20])])
                request = validate_request(raw, demand)
                self.assertTrue(request["constraint_review"]["qualification_blockers"])

    def test_title_constraint_reaches_provider_context_but_comment_titles_are_not_evidence(self):
        demand, _ = self.title_constraint()
        demand["comments"] = [dict(self.comment("Additional context."), title="Must not use Node.js")]
        data, report = build_context(None, demand, "request", 60000)
        hints = data["potential_constraints"]["items"]
        self.assertEqual(len(hints), 1)
        self.assertEqual(hints[0]["quote"], demand["title"])
        self.assertIn(hints[0]["quote"], data["sources"]["q0"]["quote"])
        self.assertEqual(report["omitted_constraint_ids"], [])

    def test_middle_dependency_constraint_survives_shortening_and_keeps_authority(self):
        demand = issue()
        demand["comments"] = [self.comment("prefix\n" * 2000 + "No `p-limit` or Axios.\n" + "suffix\n" * 2000)]
        data, report = build_context(None, demand, "request", 60000)
        self.assertIn("No `p-limit` or Axios.", data["sources"]["q1"]["quote"])
        self.assertIn("[SELECTED CONSTRAINT EXCERPT]", data["sources"]["q1"]["quote"])
        self.assertEqual(data["sources"]["q1"]["author_association"], "OWNER")
        self.assertEqual(data["sources"]["q1"]["authority"], "repository_member")
        self.assertFalse(report["discussion_complete"])
        self.assertEqual(report["omitted_constraint_ids"], [])
        self.assertLess(len(str(data).encode()), 44000)

    def test_omitted_later_prohibition_blocks_positive_even_if_context_is_complete(self):
        demand = issue()
        demand["comments"] = [self.comment("No `p-limit` or Axios.")]
        match = self.positive(demand)
        self.assertEqual(match["classification"], "investigate")
        hint = match["request"]["constraint_review"]["items"][-1]
        self.assertEqual(hint["source_id"], "q1")
        self.assertEqual(hint["represented_by"], [])
        self.assertTrue(hint["needs_review"])
        self.assertTrue(any("constraint" in x.lower() for x in match["obstacles"]))

    def test_extracted_authoritative_conflict_is_rejected_not_hidden(self):
        demand = issue()
        demand["comments"] = [self.comment("No `p-limit` or Axios.")]
        raw = request_raw()
        raw["requirements"].append({"text": "No external p-limit or Axios dependency", "mandatory": True,
                                    "explicit": True, "source_id": "q1", "quote": "No `p-limit` or Axios.", "inference": ""})
        request = validate_request(raw, demand)
        self.assertEqual(request["constraint_review"]["qualification_blockers"], [])
        match = raw_match()
        match["checks"].append({"requirement_id": "r2", "status": "incompatible",
                                "reason": "Fixture external dependency", "source_ids": ["c0:0"]})
        self.assertEqual(validate_matches([match], repository(), demand, request, "model")[0]["classification"], "rejected")

    def test_generated_plan_is_visible_but_not_automatically_maintainer_authority(self):
        demand = issue()
        demand["comments"] = [self.comment("[Orquestrador TDD] Generated plan.\nNo `p-limit` or Axios.")]
        raw = request_raw()
        raw["requirements"].append({"text": "No dependency", "mandatory": True, "explicit": True,
                                    "source_id": "q1", "quote": "No `p-limit` or Axios.", "inference": ""})
        match = self.positive(demand, raw)
        hint = match["request"]["constraint_review"]["items"][-1]
        self.assertEqual(hint["represented_by"], ["r2"])
        self.assertTrue(hint["generated_hint"])
        self.assertTrue(hint["needs_review"])
        self.assertEqual(match["classification"], "investigate")

    def test_reference_notes_without_body_are_not_qualified_demand(self):
        demand = issue()
        demand["body"] = ""
        demand["comments"] = [self.comment("Already using the package; personal notes.")]
        raw = request_raw()
        raw["requirements"] = [dict(raw["requirements"][0], quote=demand["title"])]
        match = self.positive(demand, raw)
        self.assertEqual(match["classification"], "investigate")
        self.assertTrue(any("reference notes" in x for x in match["obstacles"]))

    def test_imported_request_cannot_bypass_derived_constraint_review(self):
        demand = issue()
        demand["comments"] = [self.comment("Must not use external packages.", association="NONE")]
        request = validate_request(request_raw(), demand)
        request["constraint_review"] = {"qualification_blockers": []}
        match = raw_match()
        for check in match["checks"]:
            check["status"] = "satisfied"
        result = validate_matches([match], repository(), demand, request, "coding_agent_import")[0]
        self.assertEqual(result["classification"], "investigate")
        self.assertEqual(result["request"]["constraint_review"]["items"][-1]["authority"], "not_established")

    def test_constraint_limits_are_visible_and_block_qualification(self):
        demand = issue()
        demand["body"] += "\n" + "\n".join(f"Must preserve constraint {index}." for index in range(20))
        hints = constraint_hints(demand)
        self.assertEqual(len(hints["items"]), MAX_CONSTRAINT_HINTS)
        self.assertFalse(hints["complete"])
        match = self.positive(demand)
        self.assertEqual(match["classification"], "investigate")
        self.assertIn("Constraint hint scan is bounded/incomplete.", match["obstacles"])

    def test_late_prohibition_is_prioritized_over_long_must_checklists(self):
        demand = issue()
        demand["body"] += "\n" + "\n".join(f"Must preserve original rule {i}." for i in range(30))
        demand["comments"] = [self.comment("\n".join(f"Must check generated rule {i}." for i in range(30))
                                          + "\nNo `p-limit` or Axios.")]
        hints = constraint_hints(demand)
        self.assertFalse(hints["complete"])
        self.assertTrue(any(h["source_id"] == "q1" and "No `p-limit`" in h["quote"] for h in hints["items"]))

    def test_archived_target_and_bot_request_cannot_be_qualified(self):
        for field in ("repo_archived", "bot"):
            demand = issue()
            demand[field] = True
            match = self.positive(demand)
            self.assertEqual(match["classification"], "rejected" if field == "bot" else "investigate")

    def test_no_missing_constraint_does_not_prevent_well_grounded_positive(self):
        self.assertEqual(self.positive(issue())["classification"], "direct")

    def test_provider_gets_dependency_hint_without_candidate_repository(self):
        demand = issue()
        demand["comments"] = [self.comment("No p-limit or Axios.")]
        provider = Provider({"REPOTRACTION_AI_URL": "http://localhost/v1", "REPOTRACTION_AI_MODEL": "fixture"})
        from test_missing_link import request_completion
        with mock.patch.object(provider, "complete", side_effect=request_completion()) as complete:
            request = provider.interpret_request(demand, mock.Mock())
        data = complete.call_args.args[1]
        self.assertNotIn("repository", data)
        self.assertIn("No p-limit or Axios.", [h["quote"] for h in data["potential_constraints"]["items"]])
        self.assertTrue(request["constraint_review"]["qualification_blockers"])


if __name__ == "__main__":
    unittest.main()
