"""Reuse the reviewed receipt controls with the new experimental instruction."""
import importlib
from pathlib import Path
import unittest
from unittest.mock import patch

from scripts import missing_link_triage_branch_execution as task
from scripts import missing_link_triage_property_execution as previous
import test_missing_link_triage_property_execution as controls


class BranchExecutionControls(controls.PropertyExecutionTests):
    def simulate(self, *args, **kwargs):
        # Swap only this test helper's executor, not production or the predecessor.
        with patch.object(controls, "task", task):
            return super().simulate(*args, **kwargs)


class BranchExecutionTests(unittest.TestCase):
    def test_only_prompt_import_differs_from_reviewed_executor(self):
        frozen = Path(previous.__file__).read_text(encoding="utf-8")
        old = "from scripts.missing_link_triage_property_prompt import"
        self.assertEqual(frozen.count(old), 1)
        self.assertEqual(Path(task.__file__).read_text(encoding="utf-8"),
            frozen.replace(old, "from scripts.missing_link_triage_branch_prompt import", 1))
        self.assertEqual(task.PROMPT, task.execute_cases.__globals__["PROMPT"])
        self.assertNotEqual(task.PROMPT, previous.PROMPT)
        self.assertIs(task.schema_for_context, previous.schema_for_context)
        self.assertIs(task.normalize_prediction, previous.normalize_prediction)
        self.assertIs(task.complete_with_receipt, previous.complete_with_receipt)

    def test_reloading_executor_has_no_application_io(self):
        with patch("builtins.open", side_effect=AssertionError("file IO")), \
            patch("pathlib.Path.read_text", side_effect=AssertionError("file IO")), \
            patch("os.getenv", side_effect=AssertionError("environment lookup")), \
            patch("socket.socket", side_effect=AssertionError("network IO")), \
            patch("sqlite3.connect", side_effect=AssertionError("database IO")), \
            patch("subprocess.run", side_effect=AssertionError("process IO")):
            importlib.reload(task)
        self.assertIs(task.complete_with_receipt, previous.complete_with_receipt)
