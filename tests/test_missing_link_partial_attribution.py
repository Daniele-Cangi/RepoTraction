"""Attribution/relevance reviews are auditable assertions, never execution proof."""
import copy
import unittest
from unittest import mock

from missing_link.analysis import analysis_contract, validate_matches
from missing_link.contracts import schema_for, validate_shape
from missing_link.provider import Provider, CandidateValidationError
import test_missing_link_partial_support as partial_fixtures


class PartialAttributionTests(unittest.TestCase):
    def case(self):
        return partial_fixtures.PartialSupportTests().case()

    def result(self, raw, repo, issue, request):
        return validate_matches([raw], repo, issue, request, "model")[0]

    def test_target_tooling_cannot_borrow_an_unrelated_candidate_citation(self):
        repo, issue, request, raw = self.case()
        raw["checks"][0]["reason"] = "Jest/ESLint configuration belongs to the target; candidate global config does not implement it."
        raw["checks"][0]["source_ids"].append("target:package.json")
        raw["partial_support"][0].update(basis="target_context", operation="Target-side tooling configuration",
            requirement_part="Configure Jest and ESLint", remaining_work="Candidate contributes no tooling behavior",
            source_ids=["target:package.json"])
        match = self.result(raw, repo, issue, request)
        self.assertEqual(match["checks"][0]["contribution"], "not_demonstrated")
        self.assertEqual(match["checks"][0]["partial_support"]["basis"], "target_context")
        self.assertEqual(match["discovery_assessment"]["partial_requirement_ids"], [])
        self.assertFalse(match["discovery_assessment"]["eligible_for_followup"])

    def test_runtime_cache_analogy_is_not_static_analyzer_implementation(self):
        repo, issue, request, raw = self.case()
        raw["partial_support"][0].update(basis="analogy", operation="Runtime cached-method key construction",
            requirement_part="Static B019 checking", remaining_work="AST recognition and diagnostics are new work")
        match = self.result(raw, repo, issue, request)
        self.assertEqual(match["checks"][0]["contribution"], "not_demonstrated")
        self.assertEqual(match["discovery_assessment"]["partial_requirement_ids"], [])

    def test_invalid_option_does_not_establish_invalid_size_or_project_tests(self):
        repo, issue, request, raw = self.case()
        raw["partial_support"][0].update(basis="not_established", operation="Reject unknown incomplete option",
            requirement_part="Reject invalid size and add size-validation tests",
            remaining_work="Size validation and project tests are not established")
        self.assertEqual(self.result(raw, repo, issue, request)["checks"][0]["contribution"], "not_demonstrated")

    def test_candidate_basis_still_requires_check_bound_implementation_anchors(self):
        for refs in ([], ["q0"], ["target:package.json"], ["file:words.py", "target:package.json"]):
            with self.subTest(refs=refs):
                repo, issue, request, raw = self.case()
                raw["partial_support"][0]["source_ids"] = refs
                raw["checks"][0]["source_ids"] = list(dict.fromkeys(raw["checks"][0]["source_ids"] + refs))
                self.assertEqual(self.result(raw, repo, issue, request)["checks"][0]["contribution"], "not_demonstrated")
        repo, issue, request, raw = self.case()
        raw["partial_support"][0]["source_ids"] = ["file:words.py#L1-L1"]
        self.assertEqual(self.result(raw, repo, issue, request)["checks"][0]["contribution"], "not_demonstrated")

    def test_missing_legacy_review_or_empty_relevance_cannot_create_partial_credit(self):
        for key in (None, "operation", "requirement_part", "remaining_work"):
            with self.subTest(key=key):
                repo, issue, request, raw = self.case()
                if key is None:
                    del raw["partial_support"]
                else:
                    raw["partial_support"][0][key] = "  "
                self.assertEqual(self.result(raw, repo, issue, request)["checks"][0]["contribution"], "not_demonstrated")

    def test_explicit_candidate_primitive_remains_undetermined_and_auditable(self):
        repo, issue, request, raw = self.case()
        original = copy.deepcopy((repo, issue, request, raw))
        match = self.result(raw, repo, issue, request)
        self.assertEqual(match["checks"][0]["contribution"], "partial_behavior")
        self.assertEqual(match["checks"][0]["status"], "undetermined")
        self.assertEqual(match["checks"][0]["partial_support"], raw["partial_support"][0])
        self.assertFalse(match["discovery_assessment"]["eligible_for_followup"])
        self.assertEqual((repo, issue, request, raw), original)

    def test_bad_review_shape_unknown_duplicate_and_unknown_citation_are_rejected(self):
        for change in ("duplicate", "unknown_requirement", "unknown_source", "unknown_basis", "extra", "oversize"):
            with self.subTest(change=change):
                repo, issue, request, raw = self.case()
                review = raw["partial_support"][0]
                if change == "duplicate":
                    raw["partial_support"].append(copy.deepcopy(review))
                elif change == "unknown_requirement":
                    review["requirement_id"] = "r99"
                elif change == "unknown_source":
                    review["source_ids"] = ["file:invented.py"]
                elif change == "unknown_basis":
                    review["basis"] = "proven"
                elif change == "extra":
                    review["execute"] = True
                else:
                    review["operation"] = "x" * 6001
                with self.assertRaises(ValueError):
                    self.result(raw, repo, issue, request)

    def test_wire_scope_and_prompt_separate_reuse_from_target_and_analogy(self):
        repo, issue, request, raw = self.case()
        validate_shape({"matches": analysis_contract()["matches"]}, schema_for("matches"))
        provider = Provider({"REPOTRACTION_AI_URL": "http://localhost/v1", "REPOTRACTION_AI_MODEL": "fixture"})
        raw.setdefault("obstacles", [])
        with mock.patch.object(provider, "complete", return_value={"matches": [raw]}) as complete:
            provider.evaluate(repo, issue, request, mock.Mock())
        instruction, data = complete.call_args.args[:2]
        self.assertIn("Runtime caching as an analogy", instruction)
        self.assertIn("Rejecting an invalid option", instruction)
        self.assertIn("not semantic relevance", instruction)
        review = data["schema"]["properties"]["matches"]["items"]["properties"]["partial_support"]["items"]
        self.assertEqual(set(review["properties"]["source_ids"]["items"]["enum"]), set(data["sources"]))
        raw["partial_support"][0]["source_ids"] = ["file:words.py#L1-L99"]
        with mock.patch.object(provider, "complete", return_value={"matches": [raw]}), self.assertRaises(CandidateValidationError):
            provider.evaluate(repo, issue, request, mock.Mock())


if __name__ == "__main__":
    unittest.main()
