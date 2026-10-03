"""Method guidance and evidence-gate explanations; no live provider or imports."""
import copy
import json
import unittest
from unittest import mock

from missing_link.analysis import validate_matches
from missing_link.provider import Provider
from missing_link.proofs import export_handoff
import test_missing_link_operation_evidence as fixtures


SOURCE = ('class LineNumbers:\n'
          '    """Coordinate utilities."""\n'
          '    def from_utf8_col(self, line, column):\n'
          '        adjusted = column + line\n'
          '        return adjusted\n')


class SupportDiagnosticTests(unittest.TestCase):
    def case(self, name="LineNumbers"):
        repo, issue, request, raw = fixtures.OperationEvidenceTests().case(SOURCE, name=name, path="core.py")
        raw["checks"][0]["source_ids"] = ["file:core.py#L3-L5"]
        raw["partial_support"][0]["source_ids"] = ["file:core.py#L3-L5"]
        return repo, issue, request, raw

    def result(self, case):
        repo, issue, request, raw = case
        return validate_matches([raw], repo, issue, request, "model")[0]

    def test_class_claim_cannot_borrow_method_and_explains_the_discard(self):
        case = self.case()
        original = copy.deepcopy(case)
        match = self.result(case)
        check = match["checks"][0]
        self.assertEqual(check["contribution"], "not_demonstrated")
        self.assertEqual(check["status"], "undetermined")
        diagnostic = check["support_normalization"]
        self.assertEqual(diagnostic["codes"], ["selected_operation_body_missing"])
        self.assertEqual(diagnostic["original_reason"], case[3]["checks"][0]["reason"])
        self.assertEqual(diagnostic["original_contribution"], "partial_behavior")
        self.assertIn("select an available method ID", check["reason"])
        self.assertFalse(match["discovery_assessment"]["eligible_for_followup"])
        self.assertEqual(case, original)
        handoff = export_handoff(match, case[0])
        self.assertEqual(handoff["match"]["checks"][0], check)
        self.assertEqual(json.loads(json.dumps(check))["support_normalization"], diagnostic)

    def test_supplied_method_body_keeps_partial_credit_without_a_downgrade(self):
        case = self.case("LineNumbers.from_utf8_col")
        match = self.result(case)
        check = match["checks"][0]
        self.assertEqual(check["contribution"], "partial_behavior")
        self.assertEqual(check["status"], "undetermined")
        self.assertNotIn("support_normalization", check)
        self.assertEqual(check["reason"], case[3]["checks"][0]["reason"])
        self.assertFalse(match["discovery_assessment"]["eligible_for_followup"])

    def test_method_signature_is_not_implementation_even_with_the_correct_id(self):
        case = self.case("LineNumbers.from_utf8_col")
        case[3]["checks"][0]["source_ids"] = ["file:core.py#L3-L3"]
        case[3]["partial_support"][0]["source_ids"] = ["file:core.py#L3-L3"]
        check = self.result(case)["checks"][0]
        self.assertEqual(check["contribution"], "not_demonstrated")
        self.assertIn("selected_operation_body_missing", check["support_normalization"]["codes"])

    def test_target_context_and_missing_reviews_are_not_method_success(self):
        for basis in ("target_context", "analogy", "not_established", None):
            with self.subTest(basis=basis):
                case = self.case("LineNumbers.from_utf8_col")
                if basis is None:
                    case[3].pop("partial_support")
                else:
                    case[3]["partial_support"][0]["basis"] = basis
                check = self.result(case)["checks"][0]
                self.assertEqual(check["contribution"], "not_demonstrated")
                self.assertEqual(check["support_normalization"]["codes"], ["partial_attribution_not_established"])

    def test_full_method_claim_without_body_becomes_unknown_with_original_claim_retained(self):
        case = self.case("LineNumbers.from_utf8_col")
        raw = case[3]
        raw["checks"][0].update(status="satisfied", contribution="existing_behavior", source_ids=["file:core.py#L3-L3"])
        check = self.result(case)["checks"][0]
        self.assertEqual(check["status"], "undetermined")
        self.assertEqual(check["contribution"], "not_demonstrated")
        self.assertEqual(check["support_normalization"]["original_status"], "satisfied")
        self.assertEqual(check["support_normalization"]["codes"], ["selected_operation_body_missing"])

    def test_both_provider_phases_guide_only_available_method_ids_without_http(self):
        repo, issue, request, _ = self.case()
        before = copy.deepcopy(repo)
        provider = Provider({"REPOTRACTION_AI_URL": "http://localhost/v1", "REPOTRACTION_AI_MODEL": "fixture"})
        with mock.patch.object(provider, "complete", side_effect=[{"capabilities": []}, {"matches": []}]) as complete, \
             mock.patch("urllib.request.build_opener", side_effect=AssertionError("No provider HTTP")):
            provider.interpret_capabilities(repo, mock.Mock())
            provider.evaluate(repo, issue, request, mock.Mock())
        method = next(cap for cap in repo["capabilities"] if cap["entrypoint"].endswith(":LineNumbers.from_utf8_col"))
        for call in complete.call_args_list:
            instruction, data = call.args[:2]
            self.assertIn("method capability ID", instruction)
            self.assertIn("enclosing class", instruction)
            self.assertIn("not supplied" if "matches" in data["schema"]["properties"] else "absent", instruction)
        self.assertIn(method["id"], complete.call_args_list[1].args[1]["schema"]["properties"]["matches"]["items"]["properties"]["capability_id"]["enum"])
        self.assertEqual(repo, before)


if __name__ == "__main__":
    unittest.main()
