"""Authored protocol fixtures, not model-quality evidence or acquired-code execution."""
import copy
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from github_cli import ActiveAccountChangedError
from missing_link.behavior_contracts import VERSION, INSTRUCTION, proposal_schema, resolve_proposal
from missing_link.provider import Provider, CandidateValidationError
from missing_link.service import Budget, Cancelled, Paused, Service
from test_missing_link import repository, issue


def demand():
    result = issue()
    result.update(title="Distinct readings", body="In Python, keep the first occurrence of each reading in order. "
        "[3, 1, 3] must become [3, 1]; an empty list must remain empty.",
        comments=[{"id": 8, "url": issue()["url"] + "#issuecomment-8",
                   "body": "The order matters; sorting the readings would be wrong."}])
    return result


def proposal(data):
    ref = next(key for key, value in data["demand_spans"].items() if value["source_id"] == "q0")
    return {"status": "proposed", "reason": "The requested suboperation has exampleable inputs and outputs.",
        "unknowns": ["Performance requirements are unspecified."], "contracts": [{
        "operation": "Retain first occurrences in input order", "citation_ids": [ref],
        "input_kind": "arguments", "runtime": "python", "runtime_citation_ids": [ref],
        "preconditions": ["JSON-compatible scalar readings"], "assumptions": [],
        "uncovered_requirements": ["Integration and performance"],
        "examples": [{"args_json": "[[3, 1, 3]]", "expected_json": "[3, 1]",
                      "citation_ids": [ref], "basis": "explicit_example"}],
        "checks": [{"args_json": "[[]]", "expected_json": "[]",
                    "citation_ids": [ref], "basis": "explicit_example"}]}]}


def response(request, **_kwargs):
    payload = json.loads(request.data)
    data = json.loads(payload["messages"][1]["content"].split("\nUNTRUSTED_DATA_JSON:\n")[-1])
    return io.BytesIO(json.dumps({"choices": [{"message": {"content": json.dumps(proposal(data))}}],
        "usage": {"prompt_tokens": 100, "completion_tokens": 200}}).encode())


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.provider = Provider({"REPOTRACTION_AI_URL": "http://localhost/v1", "REPOTRACTION_AI_MODEL": "fixture"})
        self.data, self.report = self.provider._bounded_context(None, demand(), "request", INSTRUCTION)
        self.raw = proposal(self.data)

    def resolve(self, raw=None):
        return resolve_proposal(raw or self.raw, self.data, self.report, demand(), self.provider.identity())

    def test_citations_and_examples_are_decoded_without_certifying_semantics(self):
        result = self.resolve()
        contract = result["contracts"][0]
        self.assertEqual(contract["examples"], [{"args": [[3, 1, 3]], "expected": [3, 1]}])
        self.assertEqual(contract["evidence"]["url"], demand()["url"])
        self.assertIn(contract["evidence"]["quote"], contract["evidence"]["body"])
        self.assertEqual(contract["check_origin"], "same_model_response_not_independent_oracle")
        self.assertFalse(contract["qualified"])
        self.assertEqual(result["execution_status"], "not_requested")
        self.assertEqual(result["provider_identity"], self.provider.identity())

    def test_unknown_runtime_and_incomplete_context_remain_unknown(self):
        self.raw["contracts"][0].update(runtime="unknown", runtime_citation_ids=[])
        self.report["discussion_complete"] = False
        result = self.resolve()
        self.assertEqual(result["contracts"][0]["runtime"], "unknown")
        self.assertIn("incomplete", result["unknowns"][-1])

    def test_undetermined_is_valid_and_cannot_carry_contracts(self):
        empty = dict(self.raw, status="undetermined", contracts=[])
        self.assertEqual(self.resolve(empty)["contracts"], [])
        with self.assertRaises(ValueError):
            self.resolve(dict(self.raw, status="undetermined"))
        with self.assertRaises(ValueError):
            self.resolve(dict(self.raw, contracts=[]))

    def test_unknown_or_duplicate_citations_rejected_in_every_scope(self):
        for scope in ("citation_ids", "runtime_citation_ids", "examples", "checks"):
            for refs in (["file:candidate.py"], [next(iter(self.data["demand_spans"]))] * 2):
                with self.subTest(scope=scope, refs=refs):
                    raw = copy.deepcopy(self.raw)
                    contract = raw["contracts"][0]
                    if scope in {"examples", "checks"}:
                        contract[scope][0]["citation_ids"] = refs
                    else:
                        contract[scope] = refs
                    with self.assertRaises(ValueError):
                        self.resolve(raw)

    def test_declared_runtime_needs_evidence(self):
        self.raw["contracts"][0]["runtime_citation_ids"] = []
        with self.assertRaises(ValueError):
            self.resolve()

    def test_json_is_data_only_and_rejects_ambiguous_or_nonfinite_values(self):
        for value in ('__import__("os")', '{"x":1,"x":2}', 'NaN', 'Infinity', '1e999'):
            with self.subTest(value=value):
                raw = copy.deepcopy(self.raw)
                raw["contracts"][0]["checks"][0]["expected_json"] = value
                with self.assertRaises(ValueError):
                    self.resolve(raw)

    def test_checks_cannot_repeat_example_inputs_and_masks_are_strict(self):
        self.raw["contracts"][0]["checks"][0]["args_json"] = "[ [3,1,3] ]"
        with self.assertRaises(ValueError):
            self.resolve()
        self.raw = proposal(self.data)
        self.raw["contracts"][0]["input_kind"] = "boolean_mask"
        with self.assertRaises(ValueError):
            self.resolve()

    def test_bounds_unknown_fields_and_sensitive_model_text_rejected(self):
        variants = [dict(self.raw, qualified=True), dict(self.raw, contracts=self.raw["contracts"] * 4),
                    dict(self.raw, reason="x" * 50000), dict(self.raw, reason="ghp_" + "A" * 36)]
        for raw in variants:
            with self.subTest(reason=raw["reason"][:20]):
                with self.assertRaises(ValueError):
                    self.resolve(raw)

    def test_provider_wire_is_source_blind_and_uses_existing_call_accounting(self):
        budget = mock.Mock()
        target = demand()
        target["target_context"] = repository()
        target["target_context"]["files"][0]["text"] = "SECRET_CANDIDATE_IMPLEMENTATION"
        with mock.patch("urllib.request.build_opener") as opener:
            opener.return_value.open.side_effect = response
            result = self.provider.propose_behavior_contracts(target, budget)
        request = opener.return_value.open.call_args.args[0]
        wire = request.data.decode()
        self.assertNotIn("SECRET_CANDIDATE_IMPLEMENTATION", wire)
        self.assertNotIn('"file:words.py"', wire)
        self.assertIn("sorting the readings would be wrong", wire)
        self.assertIn(VERSION, wire)
        budget.reserve_ai.assert_called_once()
        budget.record_output.assert_called_once()
        self.assertEqual(budget.record_call.call_args.args[0]["phase"], "request")
        self.assertEqual(budget.record_call.call_args.args[0]["context_coverage"]["interpretation_contract"], VERSION)
        self.assertEqual(result["status"], "proposed")

    def test_escaped_sensitive_example_cannot_change_when_persisted(self):
        self.raw["contracts"][0]["checks"][0]["expected_json"] = '"\\u0067hp_' + "A" * 36 + '"'
        with self.assertRaisesRegex(ValueError, "redaction"):
            self.resolve()

    def test_budget_cancel_identity_and_prompt_limits_stop_before_transport(self):
        for error in (Paused("budget"), Cancelled("cancel"), ActiveAccountChangedError("account")):
            budget = mock.Mock()
            budget.reserve_ai.side_effect = error
            with mock.patch("urllib.request.build_opener") as opener, self.assertRaises(type(error)):
                self.provider.propose_behavior_contracts(demand(), budget)
            opener.assert_not_called()
        self.provider.max_bytes = 500
        budget = mock.Mock()
        with mock.patch("urllib.request.build_opener") as opener, self.assertRaises(ValueError):
            self.provider.propose_behavior_contracts(demand(), budget)
        budget.reserve_ai.assert_not_called()
        opener.assert_not_called()

    def test_invalid_semantics_have_fixed_public_diagnostic(self):
        self.raw["contracts"][0]["checks"][0]["expected_json"] = "private-invalid-content"
        with mock.patch.object(self.provider, "complete", return_value=self.raw):
            with self.assertRaises(CandidateValidationError) as error:
                self.provider.propose_behavior_contracts(demand(), mock.Mock())
        self.assertNotIn("private-invalid-content", str(error.exception))

    def test_atomic_allowance_rejection_prevents_dispatch_and_call_increment(self):
        job = {"ai_calls_used": 0, "cost_reserved_usd": 0}
        reserve_total = mock.Mock(side_effect=Paused("allowance exhausted"))
        budget = Budget(job, mock.Mock(), lambda: False, lambda: None, reserve_total)
        with mock.patch("urllib.request.build_opener") as opener, self.assertRaises(Paused):
            self.provider.propose_behavior_contracts(demand(), budget)
        opener.assert_not_called()
        reserve_total.assert_called_once()
        self.assertEqual(job["ai_calls_used"], 0)


class DiscoverProposalTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.account = "alice"
        self.provider = Provider({"REPOTRACTION_AI_URL": "http://localhost/v1", "REPOTRACTION_AI_MODEL": "fixture"})
        self.service = Service(Path(temp.name) / "test.sqlite3", "alice", mock.Mock(), lambda: self.account, self.provider)
        source = mock.Mock()
        source.fetch_repository.return_value = repository()
        source.fetch_issue.return_value = demand()
        source.fetch_reference_context.return_value = {"id": 101, "full_name": "example/site",
            "revision": "b" * 40, "public": True, "reference_only": True, "files": [], "fingerprint": "target-fixture"}
        for patcher in (mock.patch("missing_link.service.PublicGitHub", return_value=source),
                mock.patch("missing_link.service.extract_structure", return_value=repository()["capabilities"]),
                mock.patch.object(self.provider, "interpret_capabilities", return_value=repository()["capabilities"]),
                mock.patch.object(self.provider, "interpret_request", return_value={"status": "unresolved"})):
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = mock.patch.object(self.provider, "evaluate", return_value=[])
        self.evaluate = patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch("urllib.request.build_opener")
        self.opener = patcher.start()
        self.opener.return_value.open.side_effect = response
        self.addCleanup(patcher.stop)

    def run_job(self, enabled=True):
        result = self.service.start({"repo": "example/words", "issue_url": demand()["url"],
            "use_ai": True, "behavioral_examples": enabled}, background=False)
        return self.service.store.get("jobs", result["job_id"])

    def test_opt_in_persists_proposal_and_prepares_without_running_code(self):
        job = self.run_job()
        self.assertEqual(job["status"], "completed", job.get("error"))
        self.assertEqual(job["ai_calls_used"], 1)
        saved = job["checkpoint"]["behavioral_proposals"]["0"]
        self.assertEqual(self.service.context(job["id"])["behavioral_proposals"]["0"], saved)
        with mock.patch("missing_link.wasi_runner.WasiRunner.run") as run:
            prepared = self.service.behavioral_plan(job["id"], 0)
        run.assert_not_called()
        self.assertEqual(prepared["status"], "prepared")
        self.assertEqual(prepared["plan"]["contracts"], saved["contracts"])
        self.assertEqual(prepared["plan"]["revision"], repository()["revision"])
        self.assertFalse(job["result"]["behavioral_proposals"]["0"]["qualified"])
        self.assertEqual(job["result"]["match_ids"], [])
        self.opener.return_value.open.assert_called_once()

    def test_default_discover_adds_no_call_or_proposal(self):
        job = self.run_job(False)
        self.assertEqual(job["status"], "completed")
        self.assertNotIn("behavioral_proposals", job["checkpoint"])
        self.assertNotIn("behavioral_proposals", self.service.context(job["id"]))
        self.opener.assert_not_called()

    def test_undetermined_proposal_has_no_executable_plan(self):
        def unavailable(request, **kwargs):
            return io.BytesIO(json.dumps({"choices": [{"message": {"content": json.dumps({
                "status": "undetermined", "reason": "Missing input/output semantics.",
                "contracts": [], "unknowns": ["Ordering is unspecified."]})}}]}).encode())
        self.opener.return_value.open.side_effect = unavailable
        job = self.run_job()
        self.assertEqual(job["status"], "completed")
        self.assertEqual(self.service.behavioral_plan(job["id"], 0)["plan"], None)
        self.assertEqual(job["ai_calls_used"], 1)
        self.evaluate.assert_called_once()

    def test_added_stage_respects_job_call_cap_before_dispatch(self):
        def consume_existing_call(repo, budget):
            budget.reserve_ai(0, 1, None)
            return repository()["capabilities"]
        self.provider.max_calls = 1
        self.provider.interpret_capabilities.side_effect = consume_existing_call
        job = self.run_job()
        self.assertEqual(job["status"], "paused")
        self.assertEqual(job["ai_calls_used"], 1)
        self.opener.assert_not_called()
        self.evaluate.assert_not_called()

    def test_flag_requires_ai_discover_and_boolean(self):
        for override in ({"use_ai": False}, {"action": "analyze"}, {"behavioral_examples": "true"}):
            data = {"repo": "example/words", "use_ai": True, "behavioral_examples": True, **override}
            with self.subTest(override=override), self.assertRaisesRegex(ValueError, "behavioral_examples"):
                self.service.start(data, background=False)
        self.opener.assert_not_called()

    def test_resume_reuses_persisted_proposal_without_extra_model_call(self):
        self.evaluate.side_effect = Paused("Controlled downstream pause")
        job = self.run_job()
        self.assertEqual(job["status"], "paused")
        self.evaluate.side_effect = None
        self.service.resume({"job_id": job["id"]}, background=False)
        resumed = self.service.store.get("jobs", job["id"])
        self.assertEqual(resumed["status"], "completed", resumed.get("error"))
        self.assertEqual(resumed["checkpoint"]["behavioral_proposals"], job["checkpoint"]["behavioral_proposals"])
        self.opener.return_value.open.assert_called_once()

    def test_invalid_proposal_is_candidate_local_without_implicit_retry(self):
        with mock.patch.object(self.provider, "propose_behavior_contracts", side_effect=CandidateValidationError("Invalid proposal")) as propose:
            job = self.run_job()
        self.assertEqual(job["status"], "completed")
        self.assertTrue(job["result"]["partial"])
        self.assertEqual(job["result"]["candidate_errors"][0]["stage"], "behavioral-examples")
        self.evaluate.assert_not_called()
        propose.assert_called_once()

    def test_read_only_plan_rejects_wrong_account_and_changed_discussion(self):
        job = self.run_job()
        self.account = "bob"
        with self.assertRaises(ActiveAccountChangedError):
            self.service.behavioral_plan(job["id"], 0)
        self.account = "alice"
        job["checkpoint"]["discussions"]["0"]["fingerprint"] = "changed"
        self.service.store.put("jobs", job["id"], job)
        with self.assertRaisesRegex(ValueError, "snapshot"):
            self.service.behavioral_plan(job["id"], 0)


if __name__ == "__main__":
    unittest.main()
