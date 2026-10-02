"""Original optional-field citations across packing cuts; no live AI calls."""
import copy
import unittest
from unittest import mock

from missing_link.analysis import evidence_catalog, validate_request
from missing_link.context import build_context, size
from missing_link.demand import optional_field_hints, supplied_optional_field_hints
from missing_link.provider import Provider
from test_missing_link import issue, request_raw, request_completion


class OptionalContextTests(unittest.TestCase):
    def demand(self, body):
        return dict(issue(), author="requester", comments=[], body=body)

    def raw(self):
        raw = request_raw()
        raw["requirements"] = [dict(raw["requirements"][0], text="Add pagination", quote="Please add pagination.")]
        return raw

    def cut_body(self, position):
        declaration = "For context, an unrelated interface has telemetry?: boolean. " + "not requested. " * 30
        if position == "head":
            prefix = "Please add pagination.\n" + "filler\n" * 1100
            return prefix + "x" * (7899 - len(prefix)) + "\n" + declaration + "\n" + "filler\n" * 1800
        # The tail begins inside this original line, before the declaration.
        return "Please add pagination.\n" + "filler\n" * 1600 + "Context: " * 30 + declaration + "\n" + "x" * 7450

    def assert_canonical(self, data, demand):
        canonical = {item["id"]: item for item in optional_field_hints(evidence_catalog({}, demand))["items"]}
        for item in data["potential_subrequirements"]["items"]:
            self.assertEqual(item["quote"], canonical[item["id"]]["quote"])
            for ref in item["source_ids"]:
                self.assertIn(ref, canonical[item["id"]]["source_ids"])
                self.assertIn(item["quote"], data["sources"][ref]["quote"])

    def test_clipped_head_and_tail_lines_cannot_offer_noncanonical_field_ids(self):
        for position in ("head", "tail"):
            for location in ("root", "comment"):
                with self.subTest(position=position, location=location):
                    demand = self.demand(self.cut_body(position))
                    if location == "comment":
                        demand.update(body="Please add pagination.", comments=[{
                            "body": demand["body"], "author": "requester", "url": demand["url"] + "#issuecomment-1"}])
                    original = copy.deepcopy(demand)
                    data, report = build_context(None, demand, "request", 180000)
                    ref = "q0" if location == "root" else "q1"
                    self.assertEqual(report["shortened_discussion_ids"], [ref])
                    self.assertTrue("telemetry?: boolean" in data["sources"][ref]["quote"])
                    self.assertEqual(data["potential_subrequirements"]["items"], [])
                    self.assertFalse(report["optional_field_hint_scan_complete"])
                    self.assertFalse(report["discussion_complete"])
                    self.assert_canonical(data, demand)
                    self.assertEqual(demand, original)

    def test_provider_accepts_offered_decisions_but_keeps_cut_discussion_unqualified(self):
        declaration = "For context, an unrelated interface has debug?: boolean.\n"
        demand = self.demand(self.cut_body("head") + declaration)
        provider = Provider({"REPOTRACTION_AI_URL": "http://localhost/v1", "REPOTRACTION_AI_MODEL": "fixture"})
        budget = mock.Mock()

        def completion(instruction, data, budget, schema, phase):
            self.assert_canonical(data, demand)
            hints = data["potential_subrequirements"]["items"]
            self.assertEqual([item["field"] for item in hints], ["debug"])
            raw = self.raw()
            raw["optional_field_dispositions"] = [{"hint_id": item["id"], "disposition": "not_requested",
                "reason": "The original declaration describes unrelated context."} for item in hints]
            return request_completion(raw)(instruction, data, budget, schema, phase)

        with mock.patch.object(provider, "complete", side_effect=completion) as complete:
            request = provider.interpret_request(demand, budget)
        complete.assert_called_once()
        budget.reserve_ai.assert_not_called()
        self.assertEqual(request["status"], "unclear")
        fields = {item["field"]: item for item in request["constraint_review"]["optional_field_review"]["items"]}
        self.assertTrue(fields["telemetry"]["needs_review"])
        self.assertEqual(fields["debug"]["disposition"], "not_requested")
        self.assertTrue(request["constraint_review"]["qualification_blockers"])

    def test_whole_trusted_repetition_retains_canonical_id_without_leaking_cut_reference(self):
        demand = self.demand(self.cut_body("head"))
        line = next(line for line in demand["body"].splitlines() if "telemetry?" in line)
        demand["comments"] = [{"body": line, "author": "requester", "url": demand["url"] + "#issuecomment-1"}]
        data, report = build_context(None, demand, "request", 180000)
        self.assert_canonical(data, demand)
        item = data["potential_subrequirements"]["items"][0]
        self.assertEqual(item["source_id"], "q1")
        self.assertEqual(item["source_ids"], ["q1"])
        self.assertFalse(report["discussion_complete"])
        raw = self.raw()
        raw["optional_field_dispositions"] = [{"hint_id": item["id"], "disposition": "not_requested", "reason": "Unrelated example."}]
        request = validate_request(raw, demand)
        self.assertEqual(request["constraint_review"]["optional_field_review"]["items"][0]["source_ids"], ["q0", "q1"])

    def test_clipping_does_not_turn_overlong_original_line_into_reviewable_hint(self):
        demand = self.demand(self.cut_body("head").replace("not requested. " * 30, "x" * 2000))
        data, report = build_context(None, demand, "request", 180000)
        self.assertIn("telemetry?: boolean", data["sources"]["q0"]["quote"])
        self.assertEqual(data["potential_subrequirements"]["items"], [])
        self.assertGreater(data["potential_subrequirements"]["omitted_fields"], 0)
        self.assertFalse(report["optional_field_hint_scan_complete"])

    def test_reverse_comment_packing_cannot_offer_fields_outside_canonical_scan_cap(self):
        demand = self.demand("Please add pagination.")
        demand["comments"] = [{"body": f"For context only, field_{index}?: boolean.", "author": "requester",
            "url": demand["url"] + f"#issuecomment-{index}"} for index in range(31)]
        data, report = build_context(None, demand, "request", 180000)
        self.assert_canonical(data, demand)
        hints = data["potential_subrequirements"]["items"]
        self.assertEqual(len(hints), 30)
        self.assertNotIn("field_30", [item["field"] for item in hints])
        self.assertFalse(report["optional_field_hint_scan_complete"])
        self.assertLessEqual(size(data), 164000)
        raw = self.raw()
        raw["optional_field_dispositions"] = [{"hint_id": item["id"], "disposition": "not_requested", "reason": "Unrelated example."} for item in hints]
        self.assertTrue(validate_request(raw, demand)["constraint_review"]["qualification_blockers"])

    def test_unsupplied_original_hints_do_not_leak_text_or_mutate_canonical_review(self):
        demand = self.demand("Please add pagination.\nFor context, private_example?: boolean.")
        review = optional_field_hints(evidence_catalog({}, demand))
        original = copy.deepcopy(review)
        sources = {"q0": {"quote": "Please add pagination."}}
        supplied = supplied_optional_field_hints(review, sources)
        self.assertEqual(supplied["items"], [])
        self.assertFalse(supplied["complete"])
        self.assertEqual(supplied["omitted_fields"], 1)
        self.assertNotIn("private_example", str(supplied))
        self.assertEqual(review, original)


if __name__ == "__main__":
    unittest.main()
