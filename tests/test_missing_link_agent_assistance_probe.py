"""Offline contract checks for the bounded experiment, never provider dispatch."""
import copy
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock

from missing_link.provider import CandidateValidationError

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "agent_assistance_probe", ROOT / "docs/experiments/agent-assistance-probe-2026-10-12/strategy.py")
PROBE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROBE)


class AssistanceProbeContractTests(unittest.TestCase):
    def setUp(self):
        self.attempt = {"approach": "Restore through the public object interface.",
                        "observed_failure": "An inherited value remains shadowed.",
                        "verification": "The native restoration assertion failed."}
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


if __name__ == "__main__":
    unittest.main()
