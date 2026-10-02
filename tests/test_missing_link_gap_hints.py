"""Observed gaps do not erase explicit or ambiguous negative constraints."""
import copy
import unittest

from missing_link.analysis import validate_matches, validate_request
from missing_link.context import build_context
from missing_link.discussion import constraint_hints, MAX_CONSTRAINT_HINTS
from missing_link.gap_hints import current_gap_hint
import test_missing_link as fixtures


class GapHintTests(unittest.TestCase):
    def demand(self, body):
        issue = fixtures.issue()
        issue.update(title="Add a transformation", body=body + "\nAdd a text transformation.", comments=[])
        raw = fixtures.request_raw()
        raw["requirements"] = [dict(raw["requirements"][0], text="Add a text transformation",
                                    quote="Add a text transformation.")]
        return issue, raw

    def test_observed_chunking_and_sanitizer_gaps_do_not_invent_dependency_bans(self):
        for text in ("There is no built-in chunking step.",
                     "Today the iterable surface has operators, but there is no built-in chunking step.",
                     "The companion script does not strip ANSI escape sequences before parsing JSONL lines.",
                     "Because the logging path does not neutralize ANSI/CSI control sequences before printing, logs are unsafe.",
                     "The shared sink does not sanitize terminal control sequences before printing:"):
            with self.subTest(text=text):
                self.assertTrue(current_gap_hint(text))
                issue, raw = self.demand(text)
                original = copy.deepcopy(issue)
                request = validate_request(raw, issue)
                self.assertEqual(request["constraint_review"]["qualification_blockers"], [])
                self.assertEqual(request["constraint_review"]["items"][0]["kind"], "current_gap")
                self.assertFalse(request["constraint_review"]["items"][0]["needs_review"])
                self.assertEqual(issue, original)

    def test_real_negative_functional_and_dependency_constraints_remain_reviewable(self):
        for text in ("Must not use Python.", "No p-limit or Axios.", "Do not split words.",
                     "The parser should not sanitize text.", "The parser does not accept external dependencies.",
                     "There is no built-in chunking step; avoid new dependencies.",
                     "The current parser does not sanitize text and must remain unchanged.",
                     "The logging path does not neutralize ANSI; do not add libraries.",
                     "There is no built-in chunking step and no Node.js.",
                     "The shared sink does not sanitize text and does not allow dependencies.",
                     "Ensure the shared sink does not sanitize the raw input.",
                     "Expected: the current parser does not strip terminal codes.",
                     "Keep the logging path as-is; it does not neutralize ANSI."):
            with self.subTest(text=text):
                self.assertFalse(current_gap_hint(text))
                issue, raw = self.demand(text)
                request = validate_request(raw, issue)
                self.assertTrue(request["constraint_review"]["qualification_blockers"])
                self.assertTrue(any(h["kind"] == "potential_constraint" for h in request["constraint_review"]["items"]))

    def test_gap_plus_separate_prohibition_keeps_prohibition_blocker(self):
        issue, raw = self.demand("There is no built-in chunking step. Must not use Python.")
        request = validate_request(raw, issue)
        hints = request["constraint_review"]["items"]
        self.assertEqual([h["kind"] for h in hints], ["current_gap", "potential_constraint"])
        self.assertTrue(hints[1]["needs_review"])
        raw_match = fixtures.raw_match()
        raw_match["checks"] = raw_match["checks"][:1]
        match = validate_matches([raw_match], fixtures.repository(), issue, request, "model")[0]
        self.assertFalse(match["discovery_assessment"]["eligible_for_followup"])

    def test_many_gaps_cannot_displace_a_later_real_constraint_or_fake_incomplete_constraints(self):
        body = "\n".join("There is no built-in operation." for _ in range(40))
        issue, raw = self.demand(body)
        hints = constraint_hints(issue)
        self.assertTrue(hints["complete"])
        self.assertFalse(hints["gap_hints_complete"])
        self.assertEqual(hints["constraint_markers_found"], 0)
        self.assertEqual(len(hints["items"]), MAX_CONSTRAINT_HINTS)
        self.assertEqual(validate_request(raw, issue)["constraint_review"]["qualification_blockers"], [])
        issue["body"] += "\nMust not use Python."
        hints = constraint_hints(issue)
        self.assertIn("Must not use Python.", [h["quote"] for h in hints["items"]])
        self.assertEqual(hints["constraint_markers_found"], 1)
        self.assertTrue(validate_request(raw, issue)["constraint_review"]["qualification_blockers"])

    def test_unknown_comment_authority_remains_a_blocker_for_real_constraints(self):
        issue, raw = self.demand("There is no built-in chunking step.")
        issue["comments"] = [{"url": issue["url"] + "#issuecomment-9", "body": "Must not use Python.",
                              "author": "outsider", "author_association": "NONE"}]
        request = validate_request(raw, issue)
        self.assertTrue(request["constraint_review"]["items"][-1]["needs_review"])
        self.assertEqual(request["constraint_review"]["items"][-1]["authority"], "not_established")

    def test_hint_kind_survives_context_but_never_certifies_complete_discussion(self):
        issue, _ = self.demand("There is no built-in chunking step.")
        issue["context_complete"] = False
        data, report = build_context(None, issue, "request", 180000)
        self.assertEqual(data["potential_constraints"]["items"][0]["kind"], "current_gap")
        self.assertFalse(report["discussion_complete"])
