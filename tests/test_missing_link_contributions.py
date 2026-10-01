"""Passive API preservation is not a discovered reusable mechanism."""
import copy
import unittest

from missing_link.analysis import validate_request, validate_matches, passive_api_constraint, extension_groups
from missing_link.contracts import schema_for, validate_shape
import test_missing_link as fixtures


class ContributionTests(unittest.TestCase):
    def case(self, include_behavior=False, conflict=False):
        repo, issue = fixtures.repository(), fixtures.issue()
        issue.update(body="The capture APIs require no changes. Offload blocking file preparation.", comments=[])
        issue["target_context"] = {"public": True, "revision": "b" * 40,
            "files": [{"path": "package.json", "text": '{"name":"target"}', "url": issue["url"]}]}
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

    def test_repeated_passive_scope_does_not_create_an_extension_opportunity(self):
        match = self.case(conflict=True)
        other = copy.deepcopy(match)
        other["id"] = "independent-request"
        other["request"]["url"] += "1"
        self.assertEqual(extension_groups([match, other]), [])

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

    def test_auxiliary_evidence_cannot_substantiate_behavior_even_with_implementation_elsewhere(self):
        for path in ("benchmark.js", "fixture.ts", "parser.bench.ts", "data.fixture.js", "src/trim.ts"):
            repo, issue = fixtures.repository(), fixtures.issue()
            implementation = copy.deepcopy(repo["files"][0])
            url = implementation["url"].rsplit("/", 1)[0] + "/" + path
            repo["files"][0].update(path=path, url=url, text="export function trim(value) { return value; }")
            repo["files"].append(implementation)
            repo["capabilities"][0]["evidence"][0].update(path=path, url=url, line=1, end_line=1,
                                                       quote="function trim(value)")
            issue.update(body="I need plain text shortened without splitting words.", comments=[])
            raw_request = fixtures.request_raw()
            raw_request["requirements"] = raw_request["requirements"][:1]
            request = validate_request(raw_request, issue)
            for reference in ("c0:0", "file:" + path):
                with self.subTest(path=path, reference=reference):
                    raw = fixtures.raw_match()
                    raw["checks"] = [dict(raw["checks"][0], source_ids=[reference])]
                    match = validate_matches([raw], repo, issue, request, "model")[0]
                    is_implementation = path == "src/trim.ts"
                    self.assertEqual(match["checks"][0]["status"], "satisfied" if is_implementation else "undetermined")
                    self.assertEqual(match["checks"][0]["contribution"],
                                     "existing_behavior" if is_implementation else "not_demonstrated")
                    self.assertEqual(match["classification"], "direct" if is_implementation else "investigate")

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

    def test_compound_functional_requirement_keeps_existing_behavior_and_fit(self):
        for text in ("Shorten text without changing the public API.",
                     "Keep the public API unchanged while shortening text.",
                     "Shorten text and keep the public API unchanged.",
                     "Format byte counts without modifying existing interfaces."):
            with self.subTest(text=text):
                repo, issue, raw_request, raw = fixtures.repository(), fixtures.issue(), fixtures.request_raw(), fixtures.raw_match()
                issue.update(title="Compound functional requirement", body=text, comments=[])
                issue["target_context"] = {"public": True, "revision": "b" * 40, "files": [
                    {"path": "package.json", "text": '{"name":"consumer"}', "url": issue["url"]}]}
                raw_request["requirements"] = [dict(raw_request["requirements"][0], text=text, quote=text)]
                raw["checks"] = raw["checks"][:1]
                match = validate_matches([raw], repo, issue, validate_request(raw_request, issue), "model")[0]
                self.assertFalse(passive_api_constraint(match["request"]["requirements"][0]))
                self.assertEqual(match["checks"][0]["contribution"], "existing_behavior")
                self.assertEqual(match["classification"], "direct")
                self.assertEqual(match["discovery_assessment"]["supported_requirement_ids"], ["r0"])
                self.assertEqual(match["discovery_assessment"]["scope_compatible_requirement_ids"], [])

    def test_quote_preservation_clause_cannot_override_functional_extracted_text(self):
        self.assertFalse(passive_api_constraint({"text": "Format byte counts without changing the public API",
            "source": {"quote": "Keep the public API unchanged."}}))
        self.assertFalse(passive_api_constraint({"text": "Format byte counts",
            "source": {"quote": "Format byte counts. The public API requires no changes."}}))

    def test_pure_preservation_variants_remain_scope_only(self):
        for text in ("Keep capture APIs unchanged", "The capture APIs require no changes.",
                     "Public interfaces must remain unchanged", "No changes are needed to the public API",
                     "Do not modify the public API", "Without changing the API", "API unchanged",
                     "It should not be necessary to make changes to Sentry's capture_xxx APIs"):
            with self.subTest(text=text):
                self.assertTrue(passive_api_constraint({"text": text}))

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

    def test_no_toml_parser_or_bad_manifest_blocks_followup_not_core_import(self):
        from unittest import mock
        from missing_link import qualification
        repo, issue = fixtures.repository(), fixtures.issue()
        issue.update(body="without splitting words", comments=[])
        raw, demand = fixtures.raw_match(), fixtures.request_raw()
        raw["checks"] = raw["checks"][:1]
        demand["requirements"] = demand["requirements"][:1]
        for path, value, truncated in (("pyproject.toml", '[project]\nname="target"', False),
                                        ("package.json", '{"dependencies":[]}', False),
                                        ("package.json", '{"name":"target"}', True)):
            with self.subTest(path=path, value=value, truncated=truncated), mock.patch.object(qualification, "tomllib", None):
                issue["target_context"] = {"public": True, "revision": "b" * 40, "files": [
                    {"path": path, "text": value, "url": issue["url"], "reference_truncated": truncated}]}
                match = validate_matches([raw], repo, issue, validate_request(demand, issue), "model")[0]
                self.assertEqual(match["discovery_assessment"]["status"], "needs_review")
                self.assertTrue(match["discovery_assessment"]["manifest_review_blockers"])
                self.assertFalse(match["discovery_assessment"]["eligible_for_followup"])
