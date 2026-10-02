"""Explicit optional-field decisions: offline protocol fixtures, not AI results."""
import copy
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from missing_link.analysis import analysis_contract, evidence_catalog, validate_request, validate_matches
from missing_link.context import build_context
from missing_link.contracts import schema_for, validate_shape
from missing_link.demand import optional_field_hints
from missing_link.provider import Provider, CandidateValidationError
from missing_link.store import Store
from test_missing_link import issue, request_raw, request_completion, repository


class OptionalDispositionTests(unittest.TestCase):
    def demand(self):
        return dict(issue(), author="requester", comments=[],
            body="For context, an unrelated interface has telemetry?: boolean. Please add pagination.")

    def raw(self):
        raw = request_raw()
        raw["requirements"] = [dict(raw["requirements"][0], text="Add pagination", quote="Please add pagination.")]
        return raw

    def decision(self, demand, disposition="not_requested"):
        hint = optional_field_hints(evidence_catalog({}, demand))["items"][0]
        return {"hint_id": hint["id"], "disposition": disposition,
                "reason": "The quoted unrelated interface is context, not requested behavior."}

    def match(self):
        match = copy.deepcopy(analysis_contract()["matches"][0])
        match.update(capability_id="trim", classification="direct",
                     summary="Offline guard fixture, not a semantic model evaluation.")
        match["checks"] = [dict(requirement_id="r0", status="satisfied", contribution="existing_behavior",
            reason="Offline source-provenance fixture only.", source_ids=["file:words.py#L1-L3"])]
        return match

    def test_context_field_can_be_reviewed_without_fabricating_a_requirement(self):
        demand, raw = self.demand(), self.raw()
        unreviewed = validate_request(raw, demand)
        self.assertTrue(unreviewed["constraint_review"]["qualification_blockers"])
        self.assertEqual(validate_matches([self.match()], repository(), demand, unreviewed, "model")[0]["classification"], "investigate")
        raw["optional_field_dispositions"] = [self.decision(demand)]
        original = copy.deepcopy((raw, demand))
        request = validate_request(raw, demand)
        self.assertEqual([item["text"] for item in request["requirements"]], ["Add pagination"])
        self.assertFalse(request["constraint_review"]["qualification_blockers"])
        hint = request["constraint_review"]["optional_field_review"]["items"][0]
        self.assertEqual(hint["disposition"], "not_requested")
        self.assertEqual(hint["represented_by"], [])
        self.assertFalse(hint["needs_review"])
        self.assertIn(hint["quote"], demand["body"])
        self.assertEqual(validate_matches([self.match()], repository(), demand, request, "model")[0]["classification"], "direct")
        self.assertEqual((raw, demand), original)
        incomplete = dict(demand, context_complete=False)
        request = validate_request(raw, incomplete)
        self.assertEqual(request["status"], "unclear")
        self.assertEqual(validate_matches([self.match()], repository(), incomplete, request, "model")[0]["classification"], "investigate")

    def test_uncertain_decision_and_uncertain_authority_remain_blockers(self):
        demand, raw = self.demand(), self.raw()
        raw["optional_field_dispositions"] = [self.decision(demand, "needs_review")]
        self.assertTrue(validate_request(raw, demand)["constraint_review"]["qualification_blockers"])
        for metadata in ({"author": "guest"}, {"author": "requester", "author_type": "Bot"},
                         {"author": "requester", "body": "Generated plan\n" + self.demand()["body"]}):
            with self.subTest(metadata=metadata):
                demand = self.demand()
                demand.update(body="Please add pagination.", comments=[{
                    "url": demand["url"] + "#issuecomment-8", "body": self.demand()["body"], **metadata}])
                raw["optional_field_dispositions"] = [self.decision(demand)]
                request = validate_request(raw, demand)
                self.assertTrue(request["constraint_review"]["optional_field_review"]["items"][0]["needs_review"])
                self.assertTrue(request["constraint_review"]["qualification_blockers"])

    def test_optional_decision_does_not_dismiss_mandatory_constraints(self):
        demand = dict(self.demand(), body="Must support telemetry?: boolean. Please add pagination.")
        raw = self.raw()
        raw["optional_field_dispositions"] = [self.decision(demand)]
        request = validate_request(raw, demand)
        self.assertTrue(request["constraint_review"]["items"][0]["needs_review"])
        self.assertTrue(request["constraint_review"]["qualification_blockers"])
        self.assertEqual(validate_matches([self.match()], repository(), demand, request, "model")[0]["classification"], "investigate")

    def test_a_represented_field_cannot_also_be_dismissed(self):
        demand, raw = self.demand(), self.raw()
        raw["requirements"].append(dict(raw["requirements"][0], text="telemetry behavior", quote="telemetry?: boolean."))
        raw["optional_field_dispositions"] = [self.decision(demand)]
        with self.assertRaisesRegex(ValueError, "both a requirement"):
            validate_request(raw, demand)
        # A bundled requirement must not evade contradiction checking merely
        # because it fails the separate, atomic-field representation rule.
        demand["body"] += "\nThe unrelated interface also has debug?: boolean."
        raw["requirements"][-1].update(text="telemetry and debug behavior", quote=demand["body"])
        raw["optional_field_dispositions"] = [self.decision(demand)]
        with self.assertRaisesRegex(ValueError, "both a requirement"):
            validate_request(raw, demand)

    def test_malformed_unknown_duplicate_and_unexplained_decisions_are_rejected(self):
        demand = self.demand()
        decision = self.decision(demand)
        variants = (None, "not_requested", {}, [None], [dict(decision, hint_id="private-secret")],
                    [decision, decision], [dict(decision, reason=" ")], [dict(decision, reason="x" * 2001)],
                    [dict(decision, disposition="satisfied")], [dict(decision, extra=True)])
        for value in variants:
            with self.subTest(value=value):
                raw = dict(self.raw(), optional_field_dispositions=value)
                with self.assertRaises(ValueError) as raised:
                    validate_request(raw, demand)
                self.assertNotIn("private-secret", str(raised.exception))

    def test_review_ids_share_trusted_repetitions_but_bind_to_issue_and_text(self):
        demand = self.demand()
        demand["comments"] = [{"url": demand["url"] + "#issuecomment-8", "body": demand["body"], "author": "requester"}]
        catalog = evidence_catalog({}, demand)
        whole = optional_field_hints(catalog)["items"][0]
        packed = optional_field_hints({"q1": catalog["q1"]})["items"][0]
        self.assertEqual(whole["id"], packed["id"])
        self.assertEqual(whole["source_ids"], ["q0", "q1"])
        request = validate_request(dict(self.raw(), optional_field_dispositions=[self.decision(demand)]), demand)
        self.assertFalse(request["constraint_review"]["qualification_blockers"])
        for changed in (dict(demand, url=demand["url"] + "0", comments=[]),
                        dict(demand, body=demand["body"].replace("boolean", "string"), comments=[])):
            with self.subTest(changed=changed):
                raw = dict(self.raw(), optional_field_dispositions=[self.decision(demand)])
                with self.assertRaisesRegex(ValueError, "unknown or repeated"):
                    validate_request(raw, changed)

    def test_dismissals_do_not_clear_optional_scan_overflow(self):
        demand = dict(self.demand(), body="Please add pagination.\n" + "\n".join(
            f"For context, an unrelated interface has field_{index}?: boolean." for index in range(31)))
        hints = optional_field_hints(evidence_catalog({}, demand))
        raw = self.raw()
        raw["optional_field_dispositions"] = [{"hint_id": item["id"], "disposition": "not_requested", "reason": "Unrelated context."}
                                               for item in hints["items"]]
        request = validate_request(raw, demand)
        review = request["constraint_review"]["optional_field_review"]
        self.assertEqual(len(review["dispositions"]), 30)
        self.assertFalse(review["complete"])
        self.assertTrue(request["constraint_review"]["qualification_blockers"])
        raw["optional_field_dispositions"].append(raw["optional_field_dispositions"][0])
        with self.assertRaisesRegex(ValueError, "bounded list"):
            validate_request(raw, demand)

    def test_provider_wire_decision_survives_comparison_and_sqlite_restart(self):
        demand, raw = self.demand(), self.raw()
        raw["optional_field_dispositions"] = [self.decision(demand)]
        provider = Provider({"REPOTRACTION_AI_URL": "http://localhost/v1", "REPOTRACTION_AI_MODEL": "fixture"})
        budget = mock.Mock()

        def completion(instruction, data, budget, schema, phase):
            result = request_completion(raw)(instruction, data, budget, schema, phase) if phase == "request" else {"matches": [self.match()]}
            validate_shape(result, schema)
            return result

        with mock.patch.object(provider, "complete", side_effect=completion) as complete:
            request = provider.interpret_request(demand, budget)
            matches = provider.evaluate(repository(), demand, request, budget)
        self.assertEqual(complete.call_count, 2)
        offered = complete.call_args_list[0].args[1]["potential_subrequirements"]["items"]
        self.assertEqual(raw["optional_field_dispositions"][0]["hint_id"], offered[0]["id"])
        self.assertEqual(matches[0]["classification"], "direct")
        budget.reserve_ai.assert_not_called()
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "fixture.sqlite3"
            Store(path, "fixture").save_matches(matches, repository())
            restored = Store(path, "fixture").get("matches", matches[0]["id"])
        self.assertEqual(restored["request"]["optional_field_dispositions"], raw["optional_field_dispositions"])
        self.assertEqual(restored["request"]["constraint_review"]["optional_field_review"]["items"][0]["disposition"], "not_requested")
        self.assertEqual(validate_matches([self.match()], repository(), demand, restored["request"], "model")[0]["classification"], "direct")

    def test_provider_rejects_even_known_decisions_when_not_offered(self):
        demand, raw = self.demand(), self.raw()
        raw["optional_field_dispositions"] = [self.decision(demand)]
        data, report = build_context(None, demand, "request", 180000)
        data["potential_subrequirements"]["items"] = []
        provider = Provider({"REPOTRACTION_AI_URL": "http://localhost/v1", "REPOTRACTION_AI_MODEL": "fixture"})
        with mock.patch("missing_link.provider.build_context", return_value=(data, report)), \
             mock.patch.object(provider, "complete", side_effect=request_completion(raw)) as complete:
            with self.assertRaisesRegex(CandidateValidationError, "unavailable context"):
                provider.interpret_request(demand, mock.Mock())
        complete.assert_called_once()

    def test_optional_scope_stays_bounded_and_schema_remains_closed(self):
        ids = [f"o{index:016x}" for index in range(30)]
        schema = schema_for("request", source_ids=[f"q{i}" for i in range(400)],
                            citation_ids=[f"s{i}" for i in range(400)], optional_field_ids=ids)
        self.assertIn("optional_field_dispositions", schema["required"])
        self.assertEqual(schema["properties"]["optional_field_dispositions"]["items"]["properties"]["hint_id"]["enum"], ids)

        def enum_count(value):
            if isinstance(value, dict):
                return len(value.get("enum", [])) + sum(enum_count(child) for child in value.values())
            return sum(enum_count(child) for child in value) if isinstance(value, list) else 0

        self.assertLess(enum_count(schema), 1000)
        for values in (ids + ["extra"], [["invalid"]], [None], [""]):
            with self.subTest(values=values), self.assertRaises(ValueError):
                schema_for("request", optional_field_ids=values)


if __name__ == "__main__":
    unittest.main()
