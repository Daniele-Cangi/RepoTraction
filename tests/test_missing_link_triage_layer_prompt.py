"""Offline instruction/delegate checks, not AI explanation-quality tests."""
import copy
import hashlib
import importlib
import json
import unittest
from unittest.mock import patch

from scripts import missing_link_triage_layer_prompt as revised
from scripts import missing_link_triage_branch_prompt as previous
import test_missing_link_triage_layer_mechanisms as layers
import test_missing_link_triage_properties as fixtures


class LayerPromptCases(layers.LayerMechanismTests):
    """Reuse 16 authored controls with exactly the predecessor's delegates."""

    def compare(self, value):
        expected = super().compare(value)
        before = copy.deepcopy(value)
        raw, data, sources, body, spans = value
        checked = revised.normalize_prediction(raw, data, demand_sources=sources,
            operation_body=body, operation_spans=spans)
        self.assertEqual(checked, expected)
        self.assertEqual(value, before)
        return checked


class LayerPromptTests(unittest.TestCase):
    def test_predecessor_prompt_stays_frozen(self):
        self.assertEqual(hashlib.sha256(previous.PROMPT.encode()).hexdigest(),
            "dde418f150a00fd90b30e8a8c5725ceb91f262a60e82942f8d7737252ceaa1d7")
        self.assertEqual(revised.PROMPT, revised._revise_prompt(previous.PROMPT))
        self.assertNotEqual(revised.PROMPT, previous.PROMPT)

    def test_only_one_instruction_insertion_changes_prompt(self):
        self.assertEqual(len(revised._INSERTIONS), 1)
        anchor, addition = revised._INSERTIONS[0]
        self.assertEqual(revised.PROMPT.count(anchor + addition), 1)
        self.assertEqual(revised.PROMPT.replace(anchor + addition, anchor, 1), previous.PROMPT)

    def test_missing_or_duplicate_anchor_fails(self):
        anchor = revised._LAYER_ANCHOR
        for prompt in (previous.PROMPT.replace(anchor, ""), previous.PROMPT + anchor):
            with self.subTest(duplicated=prompt.endswith(anchor)):
                with self.assertRaisesRegex(ValueError, "missing or duplicated"):
                    revised._revise_prompt(prompt)

    def test_guidance_covers_unknown_reasons_without_forced_labels(self):
        for phrase in ("accurate in reason even for unknown", "structured declarations and IDs empty",
            "own layer", "specific evidence gap without guessing", "clock policy",
            "Do not impose a direct-call mechanism unless the demand requires",
            "force a known relation merely because a composition is visible",
            "Unknown\nremains appropriate", "a bytes annotation does not prove"):
            self.assertIn(phrase, revised.PROMPT)
        # Presence is not evidence that a model follows these instructions.

    def test_schema_normalizer_and_existing_guards_are_identical(self):
        self.assertIs(revised.schema_for_context, previous.schema_for_context)
        self.assertIs(revised.normalize_prediction, previous.normalize_prediction)
        value = layers.value_for(layers.make_copy_guard, "Return a path.", "output", "Path", "Callable")
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

    def test_factory_and_returned_method_layers_remain_distinct(self):
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
        value = layers.value_for(layers.make_copy_guard, 'Return text "x".', "output", "Text", "Callable")
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
