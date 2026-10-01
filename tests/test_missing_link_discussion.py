"""Regression fixtures for constraint loss; no provider or repository code execution."""
import unittest
from unittest import mock

from missing_link.analysis import validate_request, validate_matches
from missing_link.context import build_context
from missing_link.discussion import constraint_hints, MAX_CONSTRAINT_HINTS
from missing_link.provider import Provider
from test_missing_link import issue, repository, request_raw, raw_match


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
