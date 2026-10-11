"""Authored control-flow fixtures, not evidence of autonomous model quality."""
import copy
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from github_cli import ActiveAccountChangedError
from missing_link.analysis import validate_request
from missing_link.discovery_decisions import (VERSION, plan_input, resolve_plan,
    resolve_selection, search_terms)
from missing_link.provider import Provider, CandidateValidationError
from missing_link.service import Service, Budget, Paused, Cancelled
from missing_link.sources import PublicGitHub
from test_missing_link import issue, repository, request_raw, raw_match, wire_request


def decision(kind="search"):
    return {"decision": kind, "reason": "Authored fixture decision, not a real model judgment.",
        "direct_alternative": {"description": "Use the target's native CSS overflow behavior.",
            "adequacy": "likely_sufficient" if kind == "use_direct" else "unknown",
            "limitations": ["Word-boundary behavior needs a target test."]},
        "benefit_hypothesis": "Avoid splitting words with a native implementation.",
        "benefit_test": "Compare actual target rendering at word boundaries against native overflow.",
        "operations": [{"operation": "Preserve complete words in bounded text", "input": "Text and width",
            "output": "Whole words within width", "requirement_ids": ["r0", "r1"],
            "rationale": "Native runtime is a required constraint.",
            "search_terms": "word boundary CSS overflow"}] if kind == "search" else [], "unknowns": []}


def selection(kind="inspect"):
    return {"decision": kind, "candidate_id": "source1" if kind == "inspect" else "",
        "operation_ids": ["op0"] if kind == "inspect" else [],
        "reason": "A mechanism hypothesis, not the top-ranked catalogue.",
        "source_check": "Check runtime and actual word-boundary implementation.", "risks": ["May require Python"]}


def candidates():
    return [{"id": "source0", "full_name": "example/catalogue", "description": "A list of related articles"},
            {"id": "source1", "full_name": "example/words", "description": "Text shortening implementation"}]


class DecisionTests(unittest.TestCase):
    def setUp(self):
        self.request = validate_request(request_raw(), issue())
        self.plan = resolve_plan(decision(), self.request, "fixture-provider")

    def test_decisions_are_hypotheses_linked_to_independent_requirements(self):
        self.assertEqual(self.plan["operations"][0]["requirement_ids"], ["r0", "r1"])
        self.assertEqual(self.plan["issue_fingerprint"], issue()["fingerprint"])
        self.assertEqual(self.plan["provider_identity"], "fixture-provider")
        self.assertFalse(self.plan["qualified"])
        self.assertFalse(self.plan["direct_solution_verified"])
        for kind in ("use_direct", "defer"):
            self.assertEqual(resolve_plan(decision(kind), self.request, "fixture")["operations"], [])

    def test_invalid_plan_cannot_trigger_search(self):
        variants = [dict(decision(), operations=[]), dict(decision("defer"), operations=decision()["operations"]),
            dict(decision(), benefit_test=""), dict(decision(), qualified=True),
            dict(decision(), reason="ghp_" + "A" * 36), dict(decision(), reason="x" * 25000)]
        invalid_ref = decision()
        invalid_ref["operations"][0]["requirement_ids"] = ["invented"]
        variants.append(invalid_ref)
        direct = decision("use_direct")
        direct["direct_alternative"]["adequacy"] = "unknown"
        variants.append(direct)
        for raw in variants:
            with self.subTest(raw=str(raw)[:60]), self.assertRaises(ValueError):
                resolve_plan(raw, self.request, "fixture")

    def test_query_scope_cannot_be_changed_by_model(self):
        for terms in ("a repo:private/secret", "graph OR database", "https://example.com", "a; command", "x" * 121):
            with self.subTest(terms=terms), self.assertRaises(ValueError):
                search_terms(terms)
        self.assertEqual(search_terms(" dependency graph ordering "), "dependency graph ordering")

    def test_selection_can_reject_pool_but_not_invent_source_or_operation(self):
        result = resolve_selection(selection(), self.plan, candidates())
        self.assertEqual(result["repository"], "example/words")
        self.assertFalse(result["qualified"])
        self.assertIsNone(resolve_selection(selection("none"), self.plan, candidates())["repository"])
        for raw in (dict(selection(), candidate_id="source99"), dict(selection(), operation_ids=["unknown"]),
                    dict(selection(), decision="none"), dict(selection(), source_check="")):
            with self.assertRaises(ValueError):
                resolve_selection(raw, self.plan, candidates())

    def test_target_sample_preserves_limits_and_redaction_without_mutating_input(self):
        target = repository()
        target["files"][0].update(text="x" * 9000, redacted=True)
        target["files"] *= 5
        before = copy.deepcopy(target)
        data = plan_input(self.request, target)
        self.assertEqual(target, before)
        self.assertEqual(len(data["target"]["files"]), 4)
        self.assertEqual(len(data["target"]["files"][0]["text"]), 8000)
        self.assertTrue(data["target"]["files"][0]["truncated"])
        self.assertTrue(data["target"]["files"][0]["redacted"])
        self.assertEqual(data["context_coverage"]["target_files_omitted"], 1)
        self.assertFalse(data["context_coverage"]["all_target_source_available"])
        self.assertEqual(data["request"], self.request)

    def test_provider_checks_budget_identity_and_cancel_before_dispatch(self):
        provider = Provider({"REPOTRACTION_AI_URL": "http://localhost/v1", "REPOTRACTION_AI_MODEL": "fixture"})
        for error in (Paused("budget"), Cancelled("cancel"), ActiveAccountChangedError("identity")):
            for call in (lambda b: provider.plan_discovery(self.request, repository(), b),
                         lambda b: provider.select_source(self.plan, candidates(), b)):
                budget = mock.Mock()
                budget.reserve_ai.side_effect = error
                with mock.patch("urllib.request.build_opener") as opener, self.assertRaises(type(error)):
                    call(budget)
                opener.assert_not_called()
        with mock.patch.object(provider, "complete", return_value=dict(selection(), candidate_id="invented")):
            with self.assertRaises(CandidateValidationError):
                provider.select_source(self.plan, candidates(), mock.Mock())

    def test_atomic_allowance_rejection_does_not_count_or_dispatch_decision(self):
        provider = Provider({"REPOTRACTION_AI_URL": "http://localhost/v1", "REPOTRACTION_AI_MODEL": "fixture"})
        job = {"ai_calls_used": 0, "cost_reserved_usd": 0}
        reserve = mock.Mock(side_effect=Paused("allowance exhausted"))
        budget = Budget(job, mock.Mock(), lambda: False, lambda: None, reserve)
        with mock.patch("urllib.request.build_opener") as opener, self.assertRaises(Paused):
            provider.plan_discovery(self.request, repository(), budget)
        self.assertEqual(job["ai_calls_used"], 0)
        self.assertEqual(job["cost_reserved_usd"], 0)
        reserve.assert_called_once()
        opener.assert_not_called()


class SearchTests(unittest.TestCase):
    def test_one_page_public_scope_dedup_redaction_and_no_private_payload(self):
        item = {"full_name": "example/words", "private": False, "description": "ghp_" + "A" * 36}
        items = [item, dict(item, full_name="EXAMPLE/WORDS"), dict(item, full_name="example/private", private=True),
            dict(item, full_name="example/internal", visibility="internal"),
            dict(item, full_name="example/unknown", private=None), dict(item, full_name="example/fork", fork=True),
            dict(item, full_name="../bad"), dict(item, full_name="example/archived", archived=True)]
        read = mock.Mock(return_value={"items": items, "incomplete_results": True})
        result = PublicGitHub(read).search_repositories("word boundary CSS")
        self.assertEqual(len(result["items"]), 1)
        self.assertTrue(result["items"][0]["description_redacted"])
        self.assertNotIn("ghp_", json.dumps(result))
        self.assertFalse(result["complete"])
        self.assertEqual(read.call_count, 1)
        self.assertEqual(read.call_args.kwargs["params"], {"q": result["query"], "page": 1, "per_page": 20})
        self.assertIn("is:public archived:false fork:false", result["query"])

    def test_response_cannot_expand_page_or_public_text_bounds(self):
        items = [{"full_name": f"example/project{i}", "private": False, "description": "x" * 2000}
                 for i in range(30)]
        result = PublicGitHub(mock.Mock(return_value={"items": items})).search_repositories("behavior")
        self.assertEqual(len(result["items"]), 20)
        self.assertTrue(all(item["description_truncated"] for item in result["items"]))
        self.assertTrue(all(len(item["description"]) == 1000 for item in result["items"]))


class RequestDiscoveryTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.provider = Provider({"REPOTRACTION_AI_URL": "http://localhost/v1", "REPOTRACTION_AI_MODEL": "fixture"})
        self.account = "alice"
        self.service = Service(Path(temp.name) / "test.sqlite3", "alice", mock.Mock(), lambda: self.account,
            provider=self.provider)
        self.source = mock.Mock()
        self.source.fetch_issue.return_value = dict(issue(), comments=[])
        self.source.fetch_reference_context.return_value = {"id": 101, "full_name": "example/site",
            "revision": "b" * 40, "public": True, "reference_only": True,
            "files": [], "fingerprint": "target-fixture"}
        self.source.fetch_repository.return_value = repository()
        self.source.search_repositories.return_value = {"query": "fixture query", "items": candidates(), "complete": False}
        self.mode, self.pick = "search", "inspect"
        self.match_response = []
        self.request_response = request_raw()
        self.wires = []

    def response(self, req, **kwargs):
        payload = json.loads(req.data)
        data = json.loads(payload["messages"][1]["content"].split("\nUNTRUSTED_DATA_JSON:\n")[-1])
        self.wires.append(data)
        if "decision_version" in data:
            raw = decision(self.mode)
        elif "plan" in data:
            raw = selection(self.pick)
        elif "demand_spans" in data and "repository" not in data:
            raw = wire_request(data, self.request_response)
        elif "request" in data:
            raw = {"matches": self.match_response}
        else:
            raw = {"capabilities": []}
        return io.BytesIO(json.dumps({"choices": [{"message": {"content": json.dumps(raw)}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50}}).encode())

    def run_job(self, *, resume=None):
        with mock.patch("missing_link.service.PublicGitHub", return_value=self.source), \
                mock.patch("missing_link.service.extract_structure", return_value=repository()["capabilities"]), \
                mock.patch("urllib.request.build_opener") as opener:
            opener.return_value.open.side_effect = self.response
            result = (self.service.resume({"job_id": resume}, background=False) if resume else
                self.service.start({"action": "discover_from_request", "issue_url": issue()["url"], "use_ai": True}, background=False))
        return self.service.store.get("jobs", result["job_id"])

    def test_autonomous_selection_enters_existing_comparison_without_donor_input(self):
        job = self.run_job()
        self.assertEqual(job["status"], "completed", job.get("error"))
        self.assertEqual(job["input"]["repo"], "")
        self.assertEqual(job["ai_calls_used"], 5)
        self.assertEqual(len(job["checkpoint"]["ai_outputs"]), 5)
        self.assertEqual(job["checkpoint"]["evaluated"], ["0"])
        self.source.fetch_repository.assert_called_once_with("example/words")
        self.source.fetch_reference_context.assert_called_once()
        self.source.fetch_issue.assert_called_once()
        self.source.search_repositories.assert_called_once_with("word boundary CSS overflow")
        self.source.search_issues.assert_not_called()
        self.assertNotIn("example/words", json.dumps(self.wires[:2]))
        self.assertEqual(self.wires[2]["candidates"][1]["retrieved_for"], ["op0"])
        self.assertFalse(job["result"]["source_selection"]["qualified"])
        self.assertEqual(job["result"]["match_ids"], [])

    def test_direct_and_unknown_stop_before_search_or_source_analysis(self):
        for mode in ("use_direct", "defer"):
            with self.subTest(mode=mode):
                self.mode = mode
                job = self.run_job()
                self.assertEqual(job["status"], "completed", job.get("error"))
                self.assertEqual(job["ai_calls_used"], 2)
                self.assertEqual(job["result"]["discovery_decision"]["decision"], mode)
                self.assertEqual(job["result"]["match_ids"], [])
        self.source.search_repositories.assert_not_called()
        self.source.fetch_repository.assert_not_called()

    def test_no_source_is_a_valid_result_without_replacement_or_comparison(self):
        self.pick = "none"
        job = self.run_job()
        self.assertEqual(job["status"], "completed", job.get("error"))
        self.assertEqual(job["ai_calls_used"], 3)
        self.source.fetch_repository.assert_not_called()
        self.assertEqual(self.source.search_repositories.call_count, 1)

    def test_selected_source_still_fails_existing_hard_runtime_constraint(self):
        match = raw_match()
        match.update(obstacles=[], bridge={"kind": "investigation", "summary": "Check runtime conflict",
            "steps": [], "existing_contribution": "Python string shortening", "new_logic": "None",
            "assumptions": [], "dependencies": [], "runtime": "Python", "permissions": [],
            "coupling": "Unknown", "input": "Text", "expected_output": "Shorter text",
            "ablation": "Compare with native CSS", "files": []})
        for check in match["checks"]:
            check["source_ids"] = ["file:words.py#L1-L3"]
        self.match_response = [match]
        job = self.run_job()
        self.assertEqual(job["status"], "completed", job.get("error"))
        self.assertEqual(len(job["result"]["match_ids"]), 1, job["result"])
        match = self.service.store.get("matches", job["result"]["match_ids"][0])
        self.assertEqual(match["classification"], "rejected")
        self.assertEqual(match["bridge"]["verification"]["status"], "not_executed")

    def test_resolved_request_stops_before_target_context_and_search(self):
        self.request_response.update(status="resolved", status_source_ids=["q1"])
        self.source.fetch_issue.return_value = issue()
        job = self.run_job()
        self.assertEqual(job["status"], "completed", job.get("error"))
        self.assertEqual(job["ai_calls_used"], 1)
        self.assertEqual(job["result"]["discovery_decision"]["decision"], "no_unresolved_request")
        self.source.fetch_reference_context.assert_not_called()
        self.source.search_repositories.assert_not_called()
        self.source.fetch_repository.assert_not_called()

    def test_account_change_after_planning_stops_before_search(self):
        response = self.response
        def change_account(req, **kwargs):
            result = response(req, **kwargs)
            if len(self.wires) == 2:
                self.account = "bob"
            return result
        with mock.patch.object(self, "response", side_effect=change_account):
            job = self.run_job()
        self.assertNotEqual(job["status"], "completed")
        self.assertEqual(job["ai_calls_used"], 2)
        self.source.search_repositories.assert_not_called()
        self.source.fetch_repository.assert_not_called()

    def test_empty_pool_does_not_spend_selection_call(self):
        self.source.search_repositories.return_value["items"] = []
        job = self.run_job()
        self.assertEqual(job["status"], "completed", job.get("error"))
        self.assertEqual(job["ai_calls_used"], 2)
        self.assertEqual(job["result"]["source_selection"]["decision"], "none")
        self.source.fetch_repository.assert_not_called()

    def test_budget_resume_reuses_demand_plan_and_pool(self):
        self.provider.max_calls = 2
        first = self.run_job()
        self.assertEqual(first["status"], "paused", first.get("error"))
        self.assertEqual(first["ai_calls_used"], 2)
        self.provider.max_calls = 5
        job = self.run_job(resume=first["id"])
        self.assertEqual(job["status"], "completed", job.get("error"))
        self.assertEqual(job["ai_calls_used"], 5)
        self.source.fetch_issue.assert_called_once()
        self.source.fetch_reference_context.assert_called_once()
        self.source.search_repositories.assert_called_once()
        self.assertEqual(len(self.wires), 5)

    def test_operator_cannot_supply_source_query_or_expand_source_inspections(self):
        base = {"action": "discover_from_request", "issue_url": issue()["url"], "use_ai": True}
        for extra in ({"repo": "example/words"}, {"query": "words"}, {"max_candidates": 2}, {"use_ai": False},
                      {"issue_url": ""}, {"behavioral_examples": True}):
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                self.service.start(dict(base, **extra), background=False)
        self.assertEqual(self.service.store.list("jobs"), [])


if __name__ == "__main__":
    unittest.main()
