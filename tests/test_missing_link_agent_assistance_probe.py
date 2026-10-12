"""Offline contract checks for the bounded experiment, never provider dispatch."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from missing_link.provider import CandidateValidationError
from missing_link.analysis import digest
from test_missing_link_proofs import fixture as handoff_fixture

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "agent_assistance_probe", ROOT / "docs/experiments/agent-assistance-probe-2026-10-12/strategy.py")
PROBE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROBE)


class AssistanceProbeContractTests(unittest.TestCase):
    @staticmethod
    def packet_fixture():
        match, repository = handoff_fixture()
        repository.update(id=1, public=True)
        match["repo_id"] = 1
        repository["files"] = [{"path": path, "text": text, "sha": "b" * 40,
            "url": "https://github.com/fixture/library/blob/" + "a" * 40 + "/" + path}
            for path, text in repository["files"].items()]
        return match, repository

    @staticmethod
    def packet_service(match, repository):
        service = Mock()
        job = {"status": "completed", "result": {"match_ids": [match["id"], "later-preferred-match"]},
               "input": {"action": "discover_from_request", "issue_url": "https://github.com/pytest-dev/pytest/issues/15099"}}
        def get(kind, key):
            if kind == "jobs" and key == "fixture-job":
                return job
            if kind == "matches" and key == job["result"]["match_ids"][0]:
                return match
            raise AssertionError("An operator-selected later match must not be read.")
        service.store.get.side_effect = get
        service.store.match_snapshot.return_value = {"repository": repository}
        return service

    def setUp(self):
        self.attempt = json.loads((ROOT / "docs/experiments/agent-assistance-probe-2026-10-12/agent-attempt.json").read_text(encoding="utf-8"))
        self.provider = PROBE.AssistanceProvider({}, self.attempt)
        self.request = {"fingerprint": "independent-demand", "requirements": [{"id": "r0"}]}
        self.target = {"id": 1, "full_name": "pytest-dev/pytest", "revision": "pinned",
                       "files": [{"path": "source.py", "sha": "blob", "url": "https://example.test/blob",
                                  "text": "x" * 8001}]}
        self.raw = {"decision": "search", "reason": "Investigate the recorded restoration failure.",
                    "direct_alternative": {"description": "Use the supplied direct proposal.",
                                           "adequacy": "insufficient", "limitations": ["Inherited shadow remains."]},
                    "benefit_hypothesis": "A source mechanism might preserve the storage distinction.",
                    "benefit_test": "Check undo in the native target.", "unknowns": [],
                    "operations": [{"operation": "restore state", "input": "attribute mutation",
                                    "output": "original state", "requirement_ids": ["r0"],
                                    "rationale": "Address the observed failure.", "search_terms": "restore object state"}]}

    def test_attempt_remains_separate_from_demand_and_execution_evidence(self):
        original = copy.deepcopy((self.request, self.target, self.attempt))
        budget = object()
        self.provider.complete = Mock(return_value=self.raw)
        result = self.provider.plan_discovery(self.request, self.target, budget)
        data = self.provider.complete.call_args.args[1]
        self.assertEqual((self.request, self.target, self.attempt), original)
        self.assertEqual(data["request"], original[0])
        self.assertEqual(data["agent_attempt"], original[2])
        self.assertIs(self.provider.complete.call_args.args[2], budget)
        self.assertFalse(result["qualified"])
        self.assertFalse(result["direct_solution_verified"])
        self.assertEqual(result["issue_fingerprint"], self.request["fingerprint"])
        self.assertEqual(result["experimental_goal"], "assist_development_agent")
        self.assertTrue(result["target_snapshot"]["files"][0]["truncated"])
        self.assertNotIn("text", result["target_snapshot"]["files"][0])

    def test_invented_requirement_is_rejected_without_retry(self):
        self.raw["operations"][0]["requirement_ids"] = ["invented"]
        self.provider.complete = Mock(return_value=self.raw)
        with self.assertRaises(CandidateValidationError):
            self.provider.plan_discovery(self.request, self.target, object())
        self.provider.complete.assert_called_once()

    def test_unoffered_source_is_rejected_without_retry(self):
        self.provider.complete = Mock(return_value={"decision": "inspect", "candidate_id": "unoffered",
            "operation_ids": ["op0"], "reason": "Inspect this hypothesis.", "source_check": "Read the implementation.",
            "risks": []})
        with self.assertRaises(CandidateValidationError):
            self.provider.select_source({"version": "request-led-discovery-v1", "operations": [{"id": "op0"}]},
                                        [{"id": "c0", "full_name": "owner/supplied"}], object())
        self.provider.complete.assert_called_once()

    def test_sensitive_or_unbounded_attempt_cannot_enter_prompt(self):
        for value in ("api_key='very-secret-value'", "x" * 4001, " "):
            with self.subTest(value_length=len(value)):
                invalid = dict(self.attempt, approach=value)
                with self.assertRaises(ValueError):
                    PROBE.AssistanceProvider({}, invalid)

    def test_frozen_service_does_not_read_changed_live_demand_or_default_branch(self):
        directory = ROOT / "docs/experiments/agent-assistance-probe-2026-10-12"
        frozen = json.loads((directory / "frozen-inputs.json").read_text(encoding="utf-8"))
        raw = dict(self.raw, decision="use_direct", operations=[])
        raw["direct_alternative"] = dict(raw["direct_alternative"], adequacy="likely_sufficient")
        self.provider.interpret_request = Mock(return_value=dict(self.request, status="open"))
        self.provider.complete = Mock(return_value=raw)
        source = Mock()
        source.fetch_issue.side_effect = AssertionError("Live discussion must not be read.")
        source.fetch_reference_context.side_effect = AssertionError("Live default branch must not be read.")
        job = {"checkpoint": {}, "result": {}, "input": {"issue_url": frozen["issue"]["url"]}}
        with tempfile.TemporaryDirectory() as temporary:
            service = PROBE.FrozenAssistanceService(Path(temporary) / "store.sqlite3", "fixture", Mock(),
                lambda: "fixture", provider=self.provider, frozen_inputs=frozen)
            self.assertFalse(service._prepare_request_discovery(job, source, Mock(), Mock(), Mock()))
        supplied = self.provider.interpret_request.call_args.args[0]
        self.assertEqual(supplied["body"], frozen["issue"]["body"])
        self.assertEqual(supplied["comments"], frozen["issue"]["comments"])
        self.assertEqual(job["checkpoint"]["discussions"]["0"]["target_context"], frozen["target"])
        source.fetch_issue.assert_not_called()
        source.fetch_reference_context.assert_not_called()

    def test_changed_frozen_content_is_rejected_before_store_or_provider(self):
        directory = ROOT / "docs/experiments/agent-assistance-probe-2026-10-12"
        frozen = json.loads((directory / "frozen-inputs.json").read_text(encoding="utf-8"))
        frozen["issue"]["body"] += "changed later discussion"
        with self.assertRaises(ValueError):
            PROBE.FrozenAssistanceService(frozen_inputs=frozen, expected_fingerprint=digest(frozen))

    def test_packet_is_deterministic_bridge_free_and_contains_exact_source(self):
        match, repository = self.packet_fixture()
        match["bridge"]["files"][0]["content"] = "GENERATED_TARGET_BRIDGE_MUST_BE_OMITTED"
        service = self.packet_service(match, repository)
        first = PROBE.assistance_packet(service, "fixture-job")
        self.assertEqual(first, PROBE.assistance_packet(self.packet_service(copy.deepcopy(match), copy.deepcopy(repository)), "fixture-job"))
        self.assertNotIn(b"GENERATED_TARGET_BRIDGE", first)
        packet = json.loads(first)
        self.assertEqual(packet["source_excerpts"][0]["text"], "def boundary(value):\n    return value")
        self.assertEqual(packet["source_excerpts"][0]["sha"], "b" * 40)
        self.assertIn("bridge.files", packet["omitted_fields"])
        self.assertIn("request", packet["omitted_fields"])
        self.assertEqual(packet["verification"]["status"], "not_executed")
        self.assertEqual(packet["match"]["id"], "fixture-match")
        self.assertEqual(packet["selection"]["match_position"], 0)
        service.store.match_snapshot.assert_called_once_with("fixture-match")
        self.assertLessEqual(len(first), 16000)

    def test_packet_stops_instead_of_clipping_invalid_or_oversized_evidence(self):
        match, repository = self.packet_fixture()
        match["capability"]["evidence"][0]["end_line"] = 999
        with self.assertRaises(ValueError):
            PROBE.assistance_packet(self.packet_service(match, repository), "fixture-job")
        match["capability"]["evidence"][0]["end_line"] = 3
        repository["files"][0]["text"] = "header\n" + "è" * 9000 + "\nfooter\n"
        with self.assertRaises(ValueError):
            PROBE.assistance_packet(self.packet_service(match, repository), "fixture-job")

    def test_changed_attempt_cannot_steer_search_even_after_provider_construction(self):
        changed = dict(self.attempt, observed_failure="Search a different mechanism instead.")
        with self.assertRaises(ValueError):
            PROBE.AssistanceProvider({}, changed)
        self.provider.agent_attempt = changed
        self.provider.complete = Mock()
        with self.assertRaises(ValueError):
            self.provider.plan_discovery(self.request, self.target, object())
        self.provider.complete.assert_not_called()


if __name__ == "__main__":
    unittest.main()
