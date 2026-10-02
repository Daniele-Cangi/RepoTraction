"""Source-bound partial primitives never certify full target integration."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from missing_link.analysis import ANALYSIS_CONTRACT_VERSION, extension_groups, validate_matches, validate_request
from missing_link.contracts import schema_for, validate_shape
from missing_link.provider import Provider
from missing_link.store import Store
import test_missing_link as fixtures


class PartialSupportTests(unittest.TestCase):
    def case(self, *, contribution="partial_behavior", status="undetermined", reason="The string operation is implemented; logger wiring remains new work.", reference="file:words.py"):
        repo, issue = fixtures.repository(), fixtures.issue()
        issue.update(title="Clean logger text", body="Sanitize text before logging at both application entry points.", comments=[])
        issue["target_context"] = {"public": True, "revision": "b" * 40, "files": [
            {"path": "package.json", "text": '{"name":"consumer"}', "url": issue["url"]}]}
        demand = fixtures.request_raw()
        demand["requirements"] = [dict(demand["requirements"][0], text=issue["body"], quote=issue["body"])]
        raw = fixtures.raw_match()
        raw["checks"] = [dict(raw["checks"][0], status=status, contribution=contribution,
                              reason=reason, source_ids=[reference])]
        raw["partial_support"] = [{"requirement_id": "r0", "basis": "candidate_implementation",
            "operation": "String operation", "requirement_part": "Sanitize logger text",
            "remaining_work": "Wire both logger entry points", "source_ids": [reference]}]
        request = validate_request(demand, issue)
        return repo, issue, request, raw

    def result(self, **kwargs):
        repo, issue, request, raw = self.case(**kwargs)
        return validate_matches([raw], repo, issue, request, "model")[0]

    def test_tinyagi_shaped_primitive_is_retained_without_certifying_remediation(self):
        match = self.result()
        self.assertEqual(match["classification"], "investigate")
        self.assertEqual(match["checks"][0]["status"], "undetermined")
        self.assertEqual(match["checks"][0]["contribution"], "partial_behavior")
        assessment = match["discovery_assessment"]
        self.assertEqual(assessment["status"], "partial_contribution")
        self.assertEqual(assessment["supported_requirement_ids"], [])
        self.assertEqual(assessment["partial_requirement_ids"], ["r0"])
        self.assertEqual(assessment["undetermined_requirement_ids"], ["r0"])
        self.assertFalse(assessment["eligible_for_followup"])
        self.assertEqual(match["bridge"]["verification"]["status"], "not_executed")
        self.assertEqual(match["analysis_contract_version"], ANALYSIS_CONTRACT_VERSION)

    def test_satisfied_partial_claim_is_downgraded_not_promoted(self):
        match = self.result(status="satisfied")
        self.assertEqual(match["checks"][0]["status"], "undetermined")
        self.assertFalse(match["discovery_assessment"]["eligible_for_followup"])

    def test_legacy_ambiguous_behavior_is_not_automatically_promoted_to_partial(self):
        match = self.result(contribution="existing_behavior")
        self.assertEqual(match["checks"][0]["contribution"], "not_demonstrated")
        self.assertEqual(match["discovery_assessment"]["partial_requirement_ids"], [])

    def test_partial_claim_requires_explicit_nonempty_reason_and_source_implementation(self):
        for reference in ("q0", "target:package.json"):
            self.assertEqual(self.result(reference=reference)["checks"][0]["contribution"], "not_demonstrated")
        for reason in ("", "   "):
            self.assertEqual(self.result(reason=reason)["checks"][0]["contribution"], "not_demonstrated")
        repo, issue, request, raw = self.case()
        del raw["checks"][0]["reason"]
        self.assertEqual(validate_matches([raw], repo, issue, request, "model")[0]["checks"][0]["contribution"], "not_demonstrated")

    def test_docs_tests_types_and_neighboring_tools_are_not_implementation_support(self):
        for path in ("README.md", "tests/check.py", "src/trim.d.ts", "scripts/trim.py", "fixture.ts", "parser.bench.ts"):
            with self.subTest(path=path):
                repo, issue, request, raw = self.case()
                repo["files"][0]["path"] = path
                raw["checks"][0]["source_ids"] = ["file:" + path]
                raw["partial_support"][0]["source_ids"] = ["file:" + path]
                result = validate_matches([raw], repo, issue, request, "model")[0]
                self.assertEqual(result["checks"][0]["contribution"], "not_demonstrated")

    def test_partial_support_does_not_erase_hard_conflict_or_create_extension_group(self):
        repo, issue, request, raw = self.case()
        issue["body"] += " Must not use Python."
        request = validate_request(dict(fixtures.request_raw(), requirements=[
            dict(fixtures.request_raw()["requirements"][0], quote="Sanitize text before logging at both application entry points."),
            dict(fixtures.request_raw()["requirements"][1], quote="Must not use Python.")]), issue)
        raw["checks"].append(dict(fixtures.raw_match()["checks"][1]))
        result = validate_matches([raw], repo, issue, request, "model")[0]
        self.assertEqual(result["classification"], "rejected")
        self.assertEqual(result["discovery_assessment"]["status"], "partial_contribution")
        self.assertEqual(result["discovery_assessment"]["conflicting_requirement_ids"], ["r1"])
        other = copy.deepcopy(result)
        other["request"]["url"] += "1"
        self.assertEqual(extension_groups([result, other]), [])

    def test_partial_cannot_credit_passive_preservation_or_conflicting_behavior(self):
        self.assertEqual(self.result(status="incompatible")["checks"][0]["contribution"], "not_demonstrated")
        repo, issue, request, raw = self.case()
        request["requirements"][0]["text"] = "Keep the public API unchanged"
        self.assertEqual(validate_matches([raw], repo, issue, request, "model")[0]["checks"][0]["contribution"], "not_demonstrated")

    def test_completed_requirement_is_still_supported_independently(self):
        match = self.result(status="satisfied", contribution="existing_behavior")
        self.assertEqual(match["discovery_assessment"]["supported_requirement_ids"], ["r0"])
        self.assertEqual(match["discovery_assessment"]["partial_requirement_ids"], [])
        self.assertEqual(match["discovery_assessment"]["status"], "external_lead")

    def test_partial_survives_storage_without_mutating_original_analysis(self):
        repo, issue, request, raw = self.case()
        original = copy.deepcopy((repo, issue, request, raw))
        match = validate_matches([raw], repo, issue, request, "coding_agent_import")[0]
        self.assertEqual((repo, issue, request, raw), original)
        with tempfile.TemporaryDirectory() as directory:
            store = Store(Path(directory) / "fixture.sqlite3", "fixture")
            store.put("matches", match["id"], match)
            self.assertEqual(Store(store.path, "fixture").get("matches", match["id"]), match)

    def test_wire_contract_and_provider_prompt_distinguish_partial_from_complete(self):
        repo, issue, request, raw = self.case()
        provider = Provider({"REPOTRACTION_AI_URL": "http://localhost/v1", "REPOTRACTION_AI_MODEL": "fixture"})
        raw.setdefault("obstacles", [])
        schema = schema_for("matches")["properties"]["matches"]["items"]["properties"]["checks"]["items"]
        validate_shape(raw["checks"][0], schema)
        with mock.patch.object(provider, "complete", return_value={"matches": [raw]}) as complete:
            result = provider.evaluate(repo, issue, request, mock.Mock())
        self.assertEqual(result[0]["checks"][0]["contribution"], "partial_behavior")
        self.assertIn("partial_behavior", complete.call_args.args[0])
        self.assertIn("Missing project-specific documentation", complete.call_args.args[0])
        self.assertIn("not by itself an incompatible runtime", complete.call_args.args[0])
