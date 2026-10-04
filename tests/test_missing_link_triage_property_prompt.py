"""Offline wording/contract controls, not live-model prompt quality evaluation."""
import copy
import hashlib
import importlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from scripts import missing_link_triage_explicit_scope as previous
from scripts import missing_link_triage_property_prompt as revised
from scripts.missing_link_triage_contract import FACETS
from scripts.missing_link_triage_evidence import audit_reviewed_prediction
import test_missing_link_triage_properties as fixtures


class PropertyPromptTests(unittest.TestCase):
    def compare(self, value):
        before = copy.deepcopy(value)
        raw, data, sources, body, spans = value
        result = revised.normalize_prediction(raw, data, demand_sources=sources,
            operation_body=body, operation_spans=spans)
        self.assertEqual(result, fixtures.normalize(value))
        self.assertEqual(value, before)
        self.assertFalse(result["comparison_semantics_independently_verified"])
        self.assertFalse(result["summary"]["changes_selection"])
        self.assertFalse(result["summary"]["changes_qualification"])
        return result

    def test_predecessor_source_stays_frozen_with_canonical_newlines(self):
        path = Path(previous.__file__)
        self.assertEqual(hashlib.sha256(path.read_text(encoding="utf-8").encode()).hexdigest(),
            "649f7b8f48c64334dcb04af115900e5b7a6ec3f67cf672c9851d93aac3daa0f2")

    def test_only_comparison_paragraph_changes(self):
        self.assertNotEqual(revised.PROMPT, previous.PROMPT)
        self.assertEqual(revised.PROMPT.replace(revised._PROPERTY_COMPARISON, revised._PREVIOUS_COMPARISON, 1),
                         previous.PROMPT)
        self.assertEqual(revised.PROMPT.count(revised._PROPERTY_COMPARISON), 1)

    def test_predecessor_drift_fails_instead_of_dropping_safeguards(self):
        for prompt in (previous.PROMPT.replace(revised._PREVIOUS_COMPARISON, ""),
                       previous.PROMPT + revised._PREVIOUS_COMPARISON):
            with self.assertRaisesRegex(ValueError, "missing or duplicated"):
                revised._revise_prompt(prompt)

    def test_wording_distinguishes_comparison_from_implementation(self):
        for phrase in ("property comparison, not an implementation or adoption assessment",
                       "you do not need proof that the candidate",
                       "does not assert that the candidate implements that demand",
                       "it alone does not erase an evidenced local comparison",
                       "Property alignment is not proof of the requested behavior"):
            self.assertIn(phrase, revised.PROMPT)
        # Wording assertions do not establish that a model follows these instructions.

    def test_wording_keeps_real_evidence_gaps_and_declared_interfaces_distinct(self):
        for phrase in ("Type\nannotations can support a declared interface contrast, not runtime rejection",
                       "unseen delegate's return\ncontract is unknown",
                       "Do not invent a requested property",
                       "force a relation when comparable evidence is missing"):
            self.assertIn(phrase, revised.PROMPT)

    def test_schema_and_normalizer_are_unchanged_delegates(self):
        self.assertIs(revised.schema_for_context, previous.schema_for_context)
        self.assertIs(revised.normalize_prediction, previous.normalize_prediction)
        value = fixtures.fixture("Return text.", "function operation() { return false; }",
                                 "output", "Text", "Boolean false")
        before = copy.deepcopy(value[1])
        self.assertEqual(revised.schema_for_context(value[1]), previous.schema_for_context(value[1]))
        self.assertEqual(value[1], before)

    def test_supported_contrasts_still_survive_without_implementation_proof(self):
        cases = (
            ("Return text.", "function operation() { return false; }", "output", "Text", "Boolean false", "sample.js"),
            ("Accept mixed collections.", "def operation(value: str | bytes):\n    return value",
             "input", "Declared mixed collection", "Declared scalar str or bytes", "sample.py"),
            ("Compute arithmetic mean.", "function operation() { return false; }",
             "outcome", "Arithmetic mean", "Always return false", "sample.js"))
        for demand, body, facet, dp, op, path in cases:
            with self.subTest(facet=facet):
                value = fixtures.fixture(demand, body, facet, dp, op, path=path)
                checked = self.compare(value)
                self.assertEqual(checked["summary"]["different_facets"], [facet])
                self.assertEqual(checked["summary"]["status"], "context_required")

    def test_unchanged_unknown_is_not_repaired_or_scored(self):
        value = fixtures.fixture("Return text.", "function operation() { return false; }",
                                 "output", "Text", "Boolean false")
        value[0].clear()
        value[0].update(fixtures.unknown())
        checked = self.compare(value)
        self.assertEqual(checked["summary"]["unknown_facets"], list(FACETS))
        review = audit_reviewed_prediction(checked["annotation"], fixtures.reviews("output", "observed_difference"),
            demand_body=value[2]["q0"], operation_body=value[3])
        self.assertTrue(review["semantic_consistent_with_review"])
        self.assertEqual(review["issues"], [])
        self.assertNotIn("accuracy", review)  # No-issues abstention is not a usefulness measurement.

    def test_unseen_delegate_still_needs_an_independent_review(self):
        value = fixtures.fixture("Return nested keys.", "function operation(values) { return unseen(values); }",
                                 "output", "Nested keys", "Alleged flat list")
        checked = self.compare(value)
        review = audit_reviewed_prediction(checked["annotation"], fixtures.reviews("output", "unseen_delegate"),
            demand_body=value[2]["q0"], operation_body=value[3])
        self.assertEqual(review["issues"], [{"facet": "output", "kind": "delegate_contract_not_established"}])

    def test_factory_and_returned_method_layers_remain_explicit(self):
        for layer, operation_property in (("selected_entrypoint", "Object of methods"),
                                          ("returned_method", "Boolean true from read method")):
            value = fixtures.fixture("Return a numeric scalar.", "function operation() { return {read: () => true}; }",
                "output", "Numeric scalar", operation_property, layer=layer)
            self.assertEqual(self.compare(value)["comparison_declarations"]["output"]["operation_layer"], layer)
            # Layer validity is mechanical, not independent semantic verification.

    def test_mean_slice_and_missing_completeness_are_preserved(self):
        value = fixtures.fixture("Profile rows, including their average and other statistics.",
            "function operation(rows) { let sum = 0; for (const x of rows) sum += x; return sum / rows.length; }",
            "outcome", "Average of rows", "Sum divided by count", relation="slice")
        value[0]["facets"]["outcome"].update(requested_part="Arithmetic mean",
            existing_behavior="Sum divided by count", remaining_work="Other statistics and adoption")
        checked = self.compare(value)
        self.assertTrue(checked["summary"]["partial_outcome_hint"])
        self.assertFalse(checked["summary"]["demand_complete"])
        self.assertFalse(checked["slice_semantics_independently_verified"])

    def test_exact_provenance_and_completeness_guards_are_not_weakened(self):
        for field, invalid in (("operation_id", "sibling"), ("demand_span_id", "invented")):
            value = fixtures.fixture("Return text.", "function operation() { return false; }",
                                     "output", "Text", "Boolean false")
            value[0]["facets"]["output"][field] = invalid
            with self.assertRaises(ValueError): self.compare(value)
        value = fixtures.fixture("Return text.", "function operation() { return false; }",
                                 "output", "Text", "Boolean false")
        value[0]["demand_complete"] = True
        with self.assertRaisesRegex(ValueError, "invented_completeness"): self.compare(value)

    def test_reloading_revision_has_no_application_io(self):
        # The frozen dependency is already loaded; this checks the revision itself.
        with patch("builtins.open", side_effect=AssertionError("file IO")), \
             patch("pathlib.Path.read_text", side_effect=AssertionError("file IO")), \
             patch("os.getenv", side_effect=AssertionError("environment lookup")), \
             patch("socket.socket", side_effect=AssertionError("network IO")), \
             patch("sqlite3.connect", side_effect=AssertionError("database IO")), \
             patch("subprocess.run", side_effect=AssertionError("process IO")):
            importlib.reload(revised)
        self.assertIs(revised.normalize_prediction, previous.normalize_prediction)

    def test_offline_provider_encoding_uses_new_prompt_and_identical_context_schema(self):
        from missing_link.provider import Provider
        value = fixtures.fixture("Return text.", "function operation() { return false; }",
                                 "output", "Text", "Boolean false")
        data = value[1]
        before = copy.deepcopy(data)
        schema = revised.schema_for_context(data)
        for api_kind, field in (("responses", "input"), ("chat", "messages")):
            with self.subTest(api_kind=api_kind):
                provider = Provider({"REPOTRACTION_AI_URL": "http://127.0.0.1:1", "REPOTRACTION_AI_MODEL": "fixture",
                    "REPOTRACTION_AI_API_KIND": api_kind, "REPOTRACTION_AI_RESPONSE_FORMAT": "json_schema"})
                self.assertEqual(provider.error, "")
                endpoint, old, _ = provider._encode_prompt(previous.PROMPT, data, schema, "analysis")
                new_endpoint, new, body = provider._encode_prompt(revised.PROMPT, data, schema, "analysis")
                self.assertEqual(endpoint, new_endpoint)
                self.assertEqual(old[field][1]["content"], previous.PROMPT + "\nUNTRUSTED_DATA_JSON:\n" + json.dumps(data, ensure_ascii=False))
                old[field][1]["content"] = revised.PROMPT + "\nUNTRUSTED_DATA_JSON:\n" + json.dumps(data, ensure_ascii=False)
                self.assertEqual(new, old)
                self.assertEqual(json.loads(body), new)
        self.assertEqual(data, before)
