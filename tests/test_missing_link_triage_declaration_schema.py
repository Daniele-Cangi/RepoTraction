"""Authored offline generation/reader controls, not a model-quality benchmark."""
import copy
import importlib
import json
import unittest
from unittest.mock import Mock, patch

from missing_link.contracts import validate_shape
from missing_link.provider import Provider
from scripts import missing_link_triage_declaration_schema as task
from scripts import missing_link_triage_layer_prompt as frozen
from scripts.missing_link_triage_contract import FACETS
from scripts.missing_link_triage_explicit_scope import _enum_values
from scripts.missing_link_triage_receipts import complete_with_receipt
import test_missing_link_triage_properties as fixtures
from test_missing_link_triage_layer_result_controls import mean_slice
from test_missing_link_triage_property_execution import Stream, event


class DeclarationSchemaTests(unittest.TestCase):
    def normalize(self, value):
        before = copy.deepcopy(value)
        raw, context, sources, body, spans = value
        try:
            return task.normalize_prediction(raw, context, demand_sources=sources,
                operation_body=body, operation_spans=spans)
        finally:
            self.assertEqual(value, before)

    def test_prompt_is_frozen_and_valid_slice_normalizes_identically(self):
        self.assertIs(task.PROMPT, frozen.PROMPT)
        value = mean_slice()
        checked = self.normalize(value)
        self.assertEqual(checked, frozen.normalize_prediction(value[0], value[1],
            demand_sources=value[2], operation_body=value[3], operation_spans=value[4]))
        self.assertTrue(checked["summary"]["partial_outcome_hint"])
        self.assertEqual(checked["summary"]["status"], "context_required")
        self.assertFalse(checked["comparison_semantics_independently_verified"])
        self.assertFalse(checked["slice_semantics_independently_verified"])
        self.assertFalse(checked["summary"]["changes_selection"])
        self.assertFalse(checked["summary"]["changes_qualification"])

    def test_known_empty_properties_fail_new_shape_without_repair(self):
        for relation in ("aligned", "different", "slice"):
            for field in ("demand_property", "operation_property"):
                value = mean_slice()
                facet = value[0]["facets"]["outcome"]
                facet["relation"] = relation
                if relation != "slice":
                    facet.update({key: "" for key in task.SLICE_FIELDS})
                facet[field] = ""
                # Both generic readers ignore new keywords. This is not acceptance.
                validate_shape(value[0], frozen.schema_for_context(value[1]))
                validate_shape(value[0], task.schema_for_context(value[1]))
                with self.subTest(relation=relation, field=field), self.assertRaisesRegex(ValueError, "nonempty"):
                    self.normalize(value)

    def test_all_facets_and_known_relations_require_properties(self):
        for name in FACETS:
            for relation in ("aligned", "different"):
                value = fixtures.fixture("Return a number.", "def operation():\n    return 1\n",
                    name, "Number", "Integer one", relation=relation)
                self.normalize(value)
                for field in ("demand_property", "operation_property"):
                    changed = copy.deepcopy(value)
                    changed[0]["facets"][name][field] = ""
                    with self.subTest(facet=name, relation=relation, field=field), self.assertRaises(ValueError):
                        self.normalize(changed)

    def test_unknown_keeps_axis_and_empty_declarations(self):
        value = mean_slice()
        value[0]["facets"]["outcome"] = fixtures.unknown()["facets"]["outcome"]
        checked = self.normalize(value)
        self.assertEqual(checked["summary"]["unknown_facets"], list(FACETS))
        self.assertIsNone(checked["slice_description"])
        for name in FACETS:
            for field in ("comparison_scope", "operation_layer", "demand_property", "operation_property",
                          "demand_span_id", "operation_id", *task.SLICE_FIELDS):
                changed = copy.deepcopy(value)
                changed[0]["facets"][name][field] = "Forbidden declaration"
                with self.subTest(facet=name, field=field), self.assertRaises(ValueError):
                    self.normalize(changed)

    def test_whitespace_and_length_still_require_unchanged_local_guards(self):
        for field in ("demand_property", "operation_property"):
            for text in ("\t\n", "\u2003", "x" * 401):
                value = mean_slice()
                value[0]["facets"]["outcome"][field] = text
                task.validate_prediction_shape(value[0], value[1])
                with self.subTest(field=field, text_length=len(text)), self.assertRaisesRegex(
                    ValueError, "bounded concrete property declarations"):
                    self.normalize(value)
            value[0]["facets"]["outcome"][field] = "x" * 400
            self.assertFalse(self.normalize(value)["comparison_semantics_independently_verified"])

    def test_slice_descriptions_are_nonempty_only_in_slice_branch(self):
        for field in task.SLICE_FIELDS:
            value = mean_slice()
            value[0]["facets"]["outcome"][field] = ""
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "nonempty"):
                self.normalize(value)
            value[0]["facets"]["outcome"][field] = "\u2003"
            task.validate_prediction_shape(value[0], value[1])
            with self.assertRaisesRegex(ValueError, "bounded suboperation"):
                self.normalize(value)
        for relation in ("aligned", "different"):
            value = mean_slice()
            value[0]["facets"]["outcome"]["relation"] = relation
            with self.subTest(relation=relation), self.assertRaises(ValueError):
                self.normalize(value)

    def test_axis_layer_scope_relation_and_scoped_ids_are_not_bypassed(self):
        for field, invalid in (("axis", "input_values"), ("operation_layer", ""),
                               ("comparison_scope", "project_deliverable"), ("relation", "invented"),
                               ("demand_span_id", ""), ("operation_id", ""),
                               ("demand_span_id", "unseen"), ("operation_id", "unseen")):
            value = mean_slice()
            value[0]["facets"]["outcome"][field] = invalid
            with self.subTest(field=field, invalid=invalid), self.assertRaises(ValueError):
                self.normalize(value)
        value = mean_slice()
        value[0]["facets"]["input"].update(value[0]["facets"]["outcome"], axis="input_values")
        with self.assertRaises(ValueError):
            self.normalize(value)

    def test_missing_extra_wrong_type_keys_reject_whole_card_immutably(self):
        for field in ("demand_property", "operation_property", "requested_part"):
            for mutation in ("missing", "extra", "wrong_type"):
                value = mean_slice()
                facet = value[0]["facets"]["outcome"]
                if mutation == "missing":
                    del facet[field]
                elif mutation == "extra":
                    facet["implementation_verified"] = True
                else:
                    facet[field] = None
                with self.subTest(field=field, mutation=mutation), self.assertRaises(ValueError):
                    self.normalize(value)

    def test_old_completeness_and_exact_provenance_guards_still_run(self):
        value = mean_slice()
        value[0]["demand_complete"] = True
        with self.assertRaisesRegex(ValueError, "invented_completeness"):
            self.normalize(value)
        value = mean_slice()
        value[2]["q0"] += " changed source"
        with self.assertRaisesRegex(ValueError, "original source text"):
            self.normalize(value)
        value = mean_slice()
        value[4]["e0"]["quote"] = "changed code"
        with self.assertRaisesRegex(ValueError, "selected body evidence"):
            self.normalize(value)

    def test_reason_pattern_does_not_claim_explanation_truth(self):
        value = mean_slice()
        value[0]["facets"]["runtime"]["reason"] = "All delegates always return bytes."
        self.assertEqual(self.normalize(value)["annotation"]["facets"]["runtime"]["reason"],
            "All delegates always return bytes.")
        value[0]["facets"]["runtime"]["reason"] = ""
        with self.assertRaisesRegex(ValueError, "nonempty"):
            self.normalize(value)
        for text in (" ", "x" * 801):
            value[0]["facets"]["runtime"]["reason"] = text
            task.validate_prediction_shape(value[0], value[1])
            with self.assertRaisesRegex(ValueError, "bounded facet reason"):
                self.normalize(value)

    def test_objects_are_closed_required_and_union_is_nested(self):
        schema = task.schema_for_context(mean_slice()[1])
        self.assertNotIn("anyOf", schema)
        def walk(node):
            if isinstance(node, dict):
                self.assertLessEqual(set(node), {"type", "properties", "required", "additionalProperties",
                    "$defs", "$ref", "enum", "pattern", "anyOf"})
                if node.get("type") == "object":
                    self.assertIs(node["additionalProperties"], False)
                    self.assertEqual(node["required"], list(node["properties"]))
                if "$ref" in node:
                    self.assertEqual(node, {"$ref": node["$ref"]})
                    self.assertIn(node["$ref"].split("/")[-1], schema["$defs"])
                if "enum" in node:
                    self.assertTrue(node["enum"])
                for key, child in node.items():
                    if key in ("properties", "$defs"):
                        for value in child.values():
                            walk(value)
                    elif key == "anyOf":
                        for value in child:
                            walk(value)
        walk(schema)
        self.assertEqual([len(schema["properties"]["facets"]["properties"][name]["anyOf"])
            for name in FACETS], [2, 2, 2, 3])

    def test_catalogs_are_shared_without_truncation_at_old_context_limit(self):
        value = mean_slice()
        context = copy.deepcopy(value[1])
        context["demand_spans"] = {f"d{index}": {} for index in range(220)}
        schema = task.schema_for_context(context)
        self.assertEqual(schema["$defs"]["demand_id"]["enum"], list(context["demand_spans"]))
        self.assertEqual(schema["$defs"]["operation_id"]["enum"], ["e0"])
        self.assertLess(_enum_values(schema), 1000)
        self.assertEqual(len(context["demand_spans"]), 220)
        context["demand_spans"]["d221"] = {}
        with self.assertRaises(ValueError):
            task.schema_for_context(context)

    def test_missing_catalog_emits_only_abstention_without_empty_enum(self):
        for field in ("demand_spans", "operation_evidence"):
            value = mean_slice()
            value[1][field] = {}
            schema = task.schema_for_context(value[1])
            self.assertTrue(all(len(item["anyOf"]) == 1
                for item in schema["properties"]["facets"]["properties"].values()))
            with self.assertRaisesRegex(ValueError, "supplied citation catalogs"):
                task.validate_prediction_shape(value[0], value[1])
            task.validate_prediction_shape(fixtures.unknown(), value[1])

    def test_generation_and_validation_do_not_mutate_or_alias_context(self):
        value = mean_slice()
        before = copy.deepcopy(value)
        schema = task.schema_for_context(value[1])
        schema["$defs"]["demand_id"]["enum"].append("invented")
        self.assertEqual(value, before)
        self.assertNotIn("invented", task.schema_for_context(value[1])["$defs"]["demand_id"]["enum"])
        self.normalize(value)

    def test_responses_encoding_retains_exact_schema_without_network_or_credentials(self):
        value = mean_slice()
        before = copy.deepcopy(value)
        with patch("os.getenv", side_effect=AssertionError("credential lookup")), \
             patch("urllib.request.build_opener", side_effect=AssertionError("network")), \
             patch("socket.socket", side_effect=AssertionError("network")), \
             patch("sqlite3.connect", side_effect=AssertionError("ledger")):
            # Explicit dummy local config; no real provider or allowance loaded.
            provider = Provider({"REPOTRACTION_AI_URL": "http://127.0.0.1:1", "REPOTRACTION_AI_MODEL": "gpt-6-luna",
                "REPOTRACTION_AI_API_KIND": "responses", "REPOTRACTION_AI_RESPONSE_FORMAT": "json_schema",
                "REPOTRACTION_AI_STREAMING": "1"})
            schema = task.schema_for_context(value[1])
            endpoint, payload, body = provider._encode_prompt(task.PROMPT, value[1], schema, "triage_declaration")
        self.assertEqual(endpoint, "/responses")
        self.assertEqual(json.loads(body), payload)
        self.assertEqual(payload["text"]["format"]["schema"], schema)
        self.assertTrue(payload["text"]["format"]["strict"])
        self.assertTrue(payload["stream"])
        self.assertFalse(payload["store"])
        self.assertEqual(value, before)

    def test_import_has_no_application_io(self):
        with patch("builtins.open", side_effect=AssertionError("file IO")), \
             patch("os.getenv", side_effect=AssertionError("environment")), \
             patch("socket.socket", side_effect=AssertionError("network")), \
             patch("sqlite3.connect", side_effect=AssertionError("database")), \
             patch("subprocess.run", side_effect=AssertionError("process")), \
             patch("threading.Thread.start", side_effect=AssertionError("thread")), \
             patch.object(Provider, "__init__", side_effect=AssertionError("provider")):
            importlib.reload(task)
            self.normalize(mean_slice())

    def test_mocked_receipt_reader_preserves_raw_before_required_branch_validation(self):
        for invalid in (False, True):
            value = mean_slice()
            if invalid:
                value[0]["facets"]["outcome"]["demand_property"] = ""
            before = copy.deepcopy(value)
            terminal, order = event(value[0]), []
            budget = Mock()
            receipts = []
            def retain(receipt):
                order.append("terminal")
                receipts.append(copy.deepcopy(receipt))
            budget.record_output.side_effect = lambda *args: order.append("parsed")
            provider = Provider({"REPOTRACTION_AI_URL": "http://127.0.0.1:1", "REPOTRACTION_AI_MODEL": "gpt-6-luna",
                "REPOTRACTION_AI_API_KIND": "responses", "REPOTRACTION_AI_RESPONSE_FORMAT": "json_schema",
                "REPOTRACTION_AI_STREAMING": "1"})
            with patch("scripts.missing_link_triage_receipts.urllib.request.build_opener") as opener, \
                 patch("socket.socket", side_effect=AssertionError("network")), \
                 patch("sqlite3.connect", side_effect=AssertionError("ledger")):
                opener.return_value.open.return_value = Stream(terminal)
                parsed = complete_with_receipt(provider, task.PROMPT, value[1], budget,
                    schema=task.schema_for_context(value[1]), retain_terminal=retain)
            self.assertEqual(receipts, [terminal])
            self.assertEqual(parsed, value[0])
            self.assertLess(order.index("terminal"), order.index("parsed"))
            self.assertEqual(opener.return_value.open.call_count, 1)
            budget.record_output.assert_called_once_with("analysis", parsed)
            if invalid:
                # The compatible generic reader is deliberately not the final guard.
                with self.assertRaisesRegex(ValueError, "nonempty"):
                    self.normalize(value)
            else:
                self.normalize(value)
            self.assertEqual(value, before)


if __name__ == "__main__":
    unittest.main()
