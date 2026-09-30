"""Passive API preservation is not a discovered reusable mechanism."""
import copy
import unittest

from missing_link.analysis import validate_request, validate_matches, passive_api_constraint
from missing_link.contracts import schema_for, validate_shape
import test_missing_link as fixtures


class ContributionTests(unittest.TestCase):
    def case(self, include_behavior=False, conflict=False):
        repo, issue = fixtures.repository(), fixtures.issue()
        issue.update(body="The capture APIs require no changes. Offload blocking file preparation.", comments=[])
        issue["target_context"] = {"public": True, "revision": "b" * 40,
            "files": [{"path": "pyproject.toml", "text": '[project]\nname="target"', "url": issue["url"]}]}
        raw_request = fixtures.request_raw()
        raw_request["requirements"] = [{"text": "Keep capture APIs unchanged", "mandatory": True,
            "explicit": True, "source_id": "q0", "quote": "The capture APIs require no changes.", "inference": ""}]
        raw = fixtures.raw_match()
        raw["checks"] = [{"requirement_id": "r0", "status": "satisfied", "contribution": "existing_behavior",
            "reason": "The helper does not modify capture APIs", "source_ids": ["file:words.py"]}]
        if include_behavior or conflict:
            raw_request["requirements"].append({"text": "Offload blocking file preparation", "mandatory": True,
                "explicit": True, "source_id": "q0", "quote": "Offload blocking file preparation.", "inference": ""})
            raw["checks"].append({"requirement_id": "r1", "status": "incompatible" if conflict else "satisfied",
                "contribution": "not_demonstrated" if conflict else "existing_behavior",
                "reason": "Fixture behavior evidence", "source_ids": ["file:words.py"]})
        return validate_matches([raw], repo, issue, validate_request(raw_request, issue), "model")[0]

    def test_passive_preservation_cannot_be_a_lead_even_if_model_claims_behavior(self):
        match = self.case()
        self.assertEqual(match["classification"], "investigate")
        self.assertEqual(match["checks"][0]["status"], "satisfied")
        self.assertEqual(match["checks"][0]["contribution"], "scope_compatible")
        assessment = match["discovery_assessment"]
        self.assertEqual(assessment["supported_requirement_ids"], [])
        self.assertEqual(assessment["scope_compatible_requirement_ids"], ["r0"])
        self.assertEqual(assessment["status"], "similarity_only")
        self.assertFalse(assessment["eligible_for_followup"])

    def test_passive_scope_with_a_conflict_is_not_partial_contribution(self):
        match = self.case(conflict=True)
        self.assertEqual(match["classification"], "rejected")
        self.assertEqual(match["discovery_assessment"]["status"], "not_a_fit")
        self.assertEqual(match["discovery_assessment"]["supported_requirement_ids"], [])

    def test_real_behavior_and_passive_boundary_are_counted_separately(self):
        match = self.case(include_behavior=True)
        self.assertEqual(match["classification"], "direct")
        self.assertEqual(match["discovery_assessment"]["supported_requirement_ids"], ["r1"])
        self.assertEqual(match["discovery_assessment"]["scope_compatible_requirement_ids"], ["r0"])

    def test_supported_behavior_does_not_erase_hard_conflict(self):
        match = validate_matches([fixtures.raw_match()], fixtures.repository(), fixtures.issue(),
            validate_request(fixtures.request_raw(), fixtures.issue()), "model")[0]
        self.assertEqual(match["classification"], "rejected")
        self.assertEqual(match["discovery_assessment"]["status"], "partial_contribution")

    def test_old_import_without_contribution_is_unknown_not_a_positive_default(self):
        raw = fixtures.raw_match()
        del raw["checks"][0]["contribution"]
        match = validate_matches([raw], fixtures.repository(), fixtures.issue(),
            validate_request(fixtures.request_raw(), fixtures.issue()), "coding_agent_import")[0]
        self.assertEqual(match["checks"][0]["status"], "undetermined")
        self.assertEqual(match["discovery_assessment"]["supported_requirement_ids"], [])

    def test_scope_guard_does_not_confuse_functional_negative_requirement(self):
        for value in ("Do not split words", "Reject unsafe Python tags", "Use async APIs to offload work"):
            self.assertFalse(passive_api_constraint({"text": value}))
        self.assertTrue(passive_api_constraint({"text": "It should not be necessary to make changes to capture_xxx APIs"}))

    def test_provider_schema_requires_an_explicit_bounded_contribution_kind(self):
        schema = schema_for("matches")["properties"]["matches"]["items"]["properties"]["checks"]["items"]
        check = fixtures.raw_match()["checks"][0]
        validate_shape(check, schema)
        for value in (None, "invented", "<script>"):
            invalid = copy.deepcopy(check)
            if value is None:
                del invalid["contribution"]
            else:
                invalid["contribution"] = value
            with self.assertRaises(ValueError):
                validate_shape(invalid, schema)
