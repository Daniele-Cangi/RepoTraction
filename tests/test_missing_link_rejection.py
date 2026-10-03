"""An explicit non-fit verdict is not an invitation to investigate a solution.

Unknown requirements remain unknown; rejection never bypasses citation validation.
All evidence is fictional and every provider response is mocked.
"""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from missing_link.analysis import validate_matches
from missing_link.provider import Provider
from missing_link.service import Service
from missing_link.store import Store
import test_missing_link_partial_support as fixtures


class ExplicitRejectionTests(unittest.TestCase):
    def case(self):
        repo, issue, request, raw = fixtures.PartialSupportTests().case(
            contribution="not_demonstrated")
        raw.update(classification="rejected", partial_support=[], obstacles=[])
        raw["checks"][0].update(source_ids=["q0"], reason="An unrelated implementation does not solve this demand.")
        return repo, issue, request, raw

    def results(self, case):
        repo, issue, request, raw = case
        original = copy.deepcopy(case)
        results = [validate_matches([raw], repo, issue, request, source)[0]
                   for source in ("model", "coding_agent_import")]
        provider = Provider({"REPOTRACTION_AI_URL": "http://localhost/v1", "REPOTRACTION_AI_MODEL": "fixture"})
        budget = mock.Mock()
        with mock.patch.object(provider, "complete", return_value={"matches": [copy.deepcopy(raw)]}), \
             mock.patch("urllib.request.build_opener", side_effect=AssertionError("No live provider calls")) as network:
            results.append(provider.evaluate(repo, issue, request, budget)[0])
        network.assert_not_called()
        budget.reserve_ai.assert_not_called()
        self.assertEqual(case, original)
        return results

    def assert_rejected(self, case, qualification="not_a_fit"):
        for match in self.results(case):
            self.assertEqual(match["classification"], "rejected")
            self.assertEqual(match["discovery_assessment"]["status"], qualification)
            self.assertFalse(match["discovery_assessment"]["eligible_for_followup"])
            self.assertEqual(match["bridge"]["verification"]["status"], "not_executed")

    def test_explicit_rejection_survives_unknown_mandatory_checks_without_invented_conflicts(self):
        for match in self.results(self.case()):
            self.assertEqual(match["classification"], "rejected")
            self.assertEqual(match["checks"][0]["status"], "undetermined")
            self.assertEqual(match["checks"][0]["contribution"], "not_demonstrated")
            self.assertEqual(match["discovery_assessment"]["conflicting_requirement_ids"], [])
            self.assertEqual(match["discovery_assessment"]["status"], "not_a_fit")
            self.assertFalse(match["discovery_assessment"]["eligible_for_followup"])

    def test_omitted_checks_do_not_revive_explicit_rejection(self):
        case = self.case()
        case[3]["checks"] = []
        self.assert_rejected(case)

    def test_unclear_demand_incomplete_context_and_constraint_blockers_do_not_revive_rejection(self):
        for reason in ("unclear", "incomplete", "blocker"):
            with self.subTest(reason=reason):
                case = self.case()
                if reason == "unclear":
                    case[2]["status"] = "unclear"
                elif reason == "incomplete":
                    case[2]["context_complete"] = False
                else:
                    # Acquired demand has an omitted explicit hard constraint.
                    case[1]["body"] += " Must run offline without network access."
                self.assert_rejected(case)
                if reason == "blocker":
                    match = self.results(case)[0]
                    self.assertTrue(match["request"]["constraint_review"]["qualification_blockers"])

    def test_optional_only_checks_do_not_revive_rejection(self):
        case = self.case()
        case[2]["requirements"][0]["mandatory"] = False
        self.assert_rejected(case)
        case[3]["classification"] = "direct"
        for match in self.results(case):
            self.assertEqual(match["classification"], "investigate")

    def test_passive_scope_alone_does_not_revive_rejection_or_grant_implementation_credit(self):
        case = self.case()
        case[2]["requirements"][0]["text"] = "Keep the public API unchanged"
        case[3]["checks"][0].update(status="satisfied", contribution="scope_compatible", source_ids=["file:words.py"])
        self.assert_rejected(case)
        for match in self.results(case):
            self.assertEqual(match["checks"][0]["contribution"], "scope_compatible")
            self.assertEqual(match["discovery_assessment"]["supported_requirement_ids"], [])
        case[3]["classification"] = "direct"
        for match in self.results(case):
            self.assertEqual(match["classification"], "investigate")

    def test_rejected_full_request_can_retain_valid_partial_mechanism_but_never_eligibility(self):
        case = fixtures.PartialSupportTests().case()
        case[3].update(classification="rejected", obstacles=[])
        self.assert_rejected(case, "partial_contribution")
        for match in self.results(case):
            self.assertEqual(match["checks"][0]["status"], "undetermined")
            self.assertEqual(match["checks"][0]["contribution"], "partial_behavior")
            self.assertEqual(match["discovery_assessment"]["partial_requirement_ids"], ["r0"])
            self.assertEqual(match["discovery_assessment"]["conflicting_requirement_ids"], [])

    def test_existing_supported_part_does_not_override_explicit_full_rejection(self):
        case = fixtures.PartialSupportTests().case(status="satisfied", contribution="existing_behavior")
        case[3].update(classification="rejected", partial_support=[], obstacles=[])
        self.assert_rejected(case, "partial_contribution")
        self.assertEqual(self.results(case)[0]["discovery_assessment"]["supported_requirement_ids"], ["r0"])

    def test_unknown_checks_still_downgrade_positive_verdicts(self):
        for classification in ("direct", "adapter", "extraction", "investigate"):
            with self.subTest(classification=classification):
                case = self.case()
                case[3]["classification"] = classification
                for match in self.results(case):
                    self.assertEqual(match["classification"], "investigate")
                    self.assertFalse(match["discovery_assessment"]["eligible_for_followup"])

    def test_hard_conflicts_still_reject_positive_verdicts(self):
        case = self.case()
        case[3]["classification"] = "direct"
        case[3]["checks"][0].update(status="incompatible", source_ids=["file:words.py"])
        self.assert_rejected(case)
        self.assertEqual(self.results(case)[0]["discovery_assessment"]["conflicting_requirement_ids"], ["r0"])

    def test_missing_verdict_is_not_inferred_as_rejection(self):
        case = self.case()
        del case[3]["classification"]
        # Imports/defaulted analyses may omit classification; schema-conforming
        # model output still requires it. Test the shared validator directly.
        for source in ("model", "coding_agent_import"):
            match = validate_matches([case[3]], *case[:3], source)[0]
            self.assertEqual(match["classification"], "investigate")

    def test_rejection_does_not_bypass_invalid_citations_or_candidate_ids(self):
        for invalid in ("source", "capability", "classification"):
            case = self.case()
            if invalid == "source":
                case[3]["checks"][0]["source_ids"] = ["file:invented.py"]
            elif invalid == "capability":
                case[3]["capability_id"] = "invented"
            else:
                case[3]["classification"] = "invalid"
            for source in ("model", "coding_agent_import"):
                with self.subTest(invalid=invalid, source=source), self.assertRaises(ValueError):
                    validate_matches([case[3]], *case[:3], source)

    def test_rejection_survives_storage_state_export_and_blocks_execution(self):
        repo, issue, request, raw = self.case()
        match = validate_matches([raw], repo, issue, request, "model")[0]
        with tempfile.TemporaryDirectory() as directory:
            store = Store(Path(directory) / "fixture.sqlite3", "fixture")
            store.put("repositories", repo["id"], repo)
            store.save_matches([match], repo)
            service = Service(store.path, "fixture", mock.Mock(side_effect=AssertionError("No GitHub calls")),
                              lambda: "fixture", Provider({}))
            state = service.state()["matches"][0]
            self.assertFalse(state["stale"])
            self.assertEqual(state["classification"], "rejected")
            exported = service.export(match["id"])["match"]
            self.assertEqual(exported["classification"], "rejected")
            self.assertEqual(exported["discovery_assessment"]["status"], "not_a_fit")
            with self.assertRaisesRegex(ValueError, "non-rejected"):
                service.execute_example({"match_id": match["id"], "approved": True})
            self.assertEqual(store.get("matches", match["id"]), match)
            self.assertEqual(store.ai_reserved("fixture"), 0)


if __name__ == "__main__":
    unittest.main()
