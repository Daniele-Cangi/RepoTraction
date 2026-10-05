"""Offline experimental-prompt checks; no model behavior or quality is measured."""
import copy
import hashlib
import importlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from scripts import missing_link_triage_branch_prompt as revised
from scripts import missing_link_triage_property_prompt as previous
import test_missing_link_triage_branch_properties as branch
import test_missing_link_triage_properties as fixtures


class BranchPromptCases(branch.BranchPropertyTests):
    """Reuse all 14 authored branch controls with the new, unchanged delegates."""

    def compare(self, value):
        expected = super().compare(value)
        before = copy.deepcopy(value)
        raw, data, sources, body, spans = value
        checked = revised.normalize_prediction(raw, data, demand_sources=sources,
            operation_body=body, operation_spans=spans)
        self.assertEqual(checked, expected)
        self.assertEqual(value, before)
        return checked


class BranchPromptTests(unittest.TestCase):
    def test_predecessor_prompt_and_module_stay_frozen(self):
        self.assertEqual(hashlib.sha256(previous.PROMPT.encode()).hexdigest(),
            "7697f92e260a315042b64ad92234a805e3629118b6aa660676fc8dcfc825c882")
        self.assertEqual(revised.PROMPT, revised._revise_prompt(previous.PROMPT))
        self.assertNotEqual(revised.PROMPT, previous.PROMPT)
        self.assertEqual(Path(previous.__file__).name, "missing_link_triage_property_prompt.py")

    def test_only_two_instruction_insertions_change_the_prompt(self):
        restored = revised.PROMPT
        for anchor, addition in revised._INSERTIONS:
            self.assertEqual(restored.count(anchor + addition), 1)
            restored = restored.replace(anchor + addition, anchor, 1)
        self.assertEqual(restored, previous.PROMPT)
        self.assertEqual(len(revised._INSERTIONS), 2)

    def test_missing_or_duplicate_anchor_fails_without_silent_drift(self):
        for anchor, _ in revised._INSERTIONS:
            for prompt in (previous.PROMPT.replace(anchor, ""), previous.PROMPT + anchor):
                with self.subTest(anchor=anchor, duplicated=prompt.endswith(anchor)):
                    with self.assertRaisesRegex(ValueError, "missing or duplicated"):
                        revised._revise_prompt(prompt)

    def test_guidance_bounds_returns_and_permits_only_evidenced_comparisons(self):
        for phrase in ("check the supplied return paths and",
            "Separate a declared return type from the actual behavior visible",
            "a bytes annotation does not prove\nan unconditional bytes result",
            "A single branch cannot certify all inputs",
            "Do not silently restate an observed-return claim as a declared-type comparison",
            "Passing through a collection does not establish",
            "Separate comparability of properties from identity of implementations",
            "Keep unknown when either comparable property is missing",
            "do not force a contrast merely because the operations have different names"):
            self.assertIn(phrase, revised.PROMPT)
        # Text presence verifies instructions, never a model's compliance with them.

    def test_schema_normalizer_and_existing_guards_remain_identical(self):
        self.assertIs(revised.schema_for_context, previous.schema_for_context)
        self.assertIs(revised.normalize_prediction, previous.normalize_prediction)
        value = branch.value_for("The requested callback returns text.", "output", "Text", "Declared bytes")
        self.assertEqual(revised.schema_for_context(value[1]), previous.schema_for_context(value[1]))
        for field, invalid in (("operation_id", "unseen"), ("demand_span_id", "unseen"),
            ("operation_layer", "invented_layer"), ("comparison_scope", "project_deliverable")):
            raw = copy.deepcopy(value[0])
            raw["facets"]["output"][field] = invalid
            with self.subTest(field=field), self.assertRaises(ValueError):
                revised.normalize_prediction(raw, value[1], demand_sources=value[2],
                    operation_body=value[3], operation_spans=value[4])
        raw = copy.deepcopy(value[0])
        raw["demand_complete"] = True
        with self.assertRaisesRegex(ValueError, "invented_completeness"):
            revised.normalize_prediction(raw, value[1], demand_sources=value[2],
                operation_body=value[3], operation_spans=value[4])

    def test_factory_and_returned_method_layers_do_not_merge(self):
        for layer, offered in (("selected_entrypoint", "Object of methods"),
            ("returned_method", "Boolean from the supplied read method")):
            value = fixtures.fixture("The requested callback returns a number.",
                "function operation() { return {read: () => true}; }", "output", "Number", offered, layer=layer)
            raw, data, sources, body, spans = value
            checked = revised.normalize_prediction(raw, data, demand_sources=sources,
                operation_body=body, operation_spans=spans)
            self.assertEqual(checked, fixtures.normalize(value))
            self.assertEqual(checked["comparison_declarations"]["output"]["operation_layer"], layer)
            self.assertFalse(checked["comparison_semantics_independently_verified"])

    def test_reload_performs_no_application_io_or_environment_lookup(self):
        with patch("builtins.open", side_effect=AssertionError("file IO")), \
            patch("pathlib.Path.read_text", side_effect=AssertionError("file IO")), \
            patch("os.getenv", side_effect=AssertionError("environment lookup")), \
            patch("socket.socket", side_effect=AssertionError("network IO")), \
            patch("sqlite3.connect", side_effect=AssertionError("database IO")), \
            patch("subprocess.run", side_effect=AssertionError("process IO")):
            importlib.reload(revised)
        self.assertIs(revised.normalize_prediction, previous.normalize_prediction)

    def test_offline_encoding_changes_only_prompt_for_both_api_kinds(self):
        from missing_link.provider import Provider
        value = branch.value_for("The requested callback returns text with escaped quotes: \"x\".",
            "output", "Text", "Declared bytes")
        before = copy.deepcopy(value)
        schema = revised.schema_for_context(value[1])
        for api_kind, field in (("responses", "input"), ("chat", "messages")):
            with self.subTest(api_kind=api_kind):
                provider = Provider({"REPOTRACTION_AI_URL": "http://127.0.0.1:1",
                    "REPOTRACTION_AI_MODEL": "fixture", "REPOTRACTION_AI_API_KIND": api_kind,
                    "REPOTRACTION_AI_RESPONSE_FORMAT": "json_schema"})
                self.assertEqual(provider.error, "")
                old_endpoint, old, _ = provider._encode_prompt(previous.PROMPT, value[1], schema, "analysis")
                endpoint, payload, body = provider._encode_prompt(revised.PROMPT, value[1], schema, "analysis")
                expected = copy.deepcopy(old)
                expected[field][1]["content"] = revised.PROMPT + "\nUNTRUSTED_DATA_JSON:\n" + json.dumps(value[1], ensure_ascii=False)
                self.assertEqual(endpoint, old_endpoint)
                self.assertEqual(payload, expected)
                self.assertEqual(json.loads(body), payload)
                self.assertLessEqual(len(body), provider.max_bytes)
        self.assertEqual(value, before)
