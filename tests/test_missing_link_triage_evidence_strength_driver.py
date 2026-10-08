"""Reuse authored safety controls with the new prompt, never a live ledger."""
import ast
import importlib
import inspect
import unittest
from unittest.mock import patch

import test_missing_link_triage_prospective_driver as controls
from scripts import missing_link_triage_prospective_driver as predecessor
from scripts import missing_link_triage_evidence_strength_driver as task
from scripts import missing_link_triage_evidence_strength_prompt as wording


class FreshDriverTests(controls.ProspectiveDriverTests):
    def setUp(self):
        # Older import-safety tests can reload modules; rebind this facade first.
        importlib.reload(task)
        binding = patch.object(controls, "task", task)
        binding.start()
        self.addCleanup(binding.stop)


class FreshBindingTests(unittest.TestCase):
    def setUp(self):
        importlib.reload(task)

    def test_only_prompt_binding_changes_existing_request_and_execution_logic(self):
        for name in ("verify_requests", "execute_cases"):
            self.assertEqual(ast.dump(ast.parse(inspect.getsource(getattr(task, name)))),
                             ast.dump(ast.parse(inspect.getsource(getattr(predecessor, name)))))
        self.assertIs(task.verify_increment, predecessor.verify_increment)
        self.assertIs(task.schema_for_context, wording.schema_for_context)
        self.assertIs(task.normalize_prediction, wording.normalize_prediction)
        self.assertEqual(task.PROMPT, wording.PROMPT)
        self.assertNotEqual(task.PROMPT, predecessor.PROMPT)

    def test_predecessor_requests_cannot_pass_fresh_prompt_freeze(self):
        provider, frozen = controls.setup()
        with self.assertRaisesRegex(ValueError, "frozen request changed"):
            task.verify_requests(provider, **frozen)

    def test_fresh_requests_cannot_pass_predecessor_prompt_freeze(self):
        with patch.object(controls, "task", task):
            provider, frozen = controls.setup()
        with self.assertRaisesRegex(ValueError, "frozen request changed"):
            predecessor.verify_requests(provider, **frozen)


if __name__ == "__main__":
    unittest.main()
