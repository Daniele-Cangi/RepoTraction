"""Offline instructions/transport checks, not evidence of model compliance."""
import copy
import hashlib
import importlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from scripts import missing_link_triage_evidence_strength_prompt as revised
from scripts import missing_link_triage_declaration_schema as previous
import test_missing_link_triage_evidence_strength_controls as controls
import test_missing_link_triage_properties as fixtures


class EvidenceStrengthPromptCases(controls.EvidenceStrengthControls):
    """Replay all 18 authored controls with the exact native-schema delegates."""

    def normalize(self, value):
        expected = super().normalize(value)
        before = copy.deepcopy(value)
        checked = revised.normalize_prediction(value[0], value[1], demand_sources=value[2],
            operation_body=value[3], operation_spans=value[4])
        self.assertEqual(checked, expected)
        self.assertEqual(value, before)
        return checked


class EvidenceStrengthPromptTests(unittest.TestCase):
    def setUp(self):
        # Other discovery tests reload the predecessor to check import safety.
        # Bind this facade to its current function objects, not stale pre-reload
        # aliases. Do not change the predecessor or production for test isolation.
        importlib.reload(revised)

    def value(self):
        return controls.value_for(controls.documented_empty, 'For None, return text "x".',
            "output", "Actual text x", "Unseen constructor's actual result")

    def test_predecessor_prompt_stays_frozen(self):
        self.assertEqual(hashlib.sha256(previous.PROMPT.encode()).hexdigest(),
            "cdc7ecc5c86a84512027ba803b95d5fe44efa887d7fb7b80176e8b901d96e6a0")
        self.assertEqual(revised.PROMPT, revised._revise_prompt(previous.PROMPT))
        self.assertNotEqual(revised.PROMPT, previous.PROMPT)

    def test_only_two_insertions_change_prompt(self):
        restored = revised.PROMPT
        self.assertEqual(len(revised._INSERTIONS), 2)
        for anchor, addition in revised._INSERTIONS:
            self.assertEqual(restored.count(anchor + addition), 1)
            restored = restored.replace(anchor + addition, anchor, 1)
        self.assertEqual(restored, previous.PROMPT)

    def test_missing_or_duplicate_anchors_fail(self):
        for anchor, _ in revised._INSERTIONS:
            for prompt in (previous.PROMPT.replace(anchor, ""), previous.PROMPT + anchor):
                with self.subTest(anchor=anchor), self.assertRaisesRegex(ValueError, "missing or duplicated"):
                    revised._revise_prompt(prompt)

    def test_declaration_guidance_preserves_scope_and_unseen_gaps(self):
        for phrase in ("textual declaration", "unseen\ndelegate's actual result",
            "not independent implementation evidence", "do not satisfy it by comparing declarations",
            "requested property itself concerns a declared contract", "without certifying\nruntime enforcement",
            "separately visible local composition", "Do not force a known relation or slice"):
            self.assertIn(phrase, revised._DECLARATION_GUIDANCE)

    def test_difference_guidance_requires_positive_scope_without_blanket_abstention(self):
        for phrase in ("conditional possibility is not an established counterexample",
            "positively supported differing property", "may preserve or change a result",
            "Missing proof of\nalignment is not proof of difference",
            "Runtime execution is not required", "explicit literal behavior",
            "one default branch to all\nbranches", "requested validation suboperation",
            "does not certify\nthe producer's results", "Do not manufacture a slice"):
            self.assertIn(phrase, revised._DIFFERENCE_GUIDANCE)

    def test_native_schema_and_normalizer_are_exact_predecessor_objects(self):
        self.assertIs(revised.schema_for_context, previous.schema_for_context)
        self.assertIs(revised.normalize_prediction, previous.normalize_prediction)
        value = self.value()
        schema = revised.schema_for_context(value[1])
        self.assertEqual(schema, previous.schema_for_context(value[1]))
        self.assertIn("anyOf", schema["properties"]["facets"]["properties"]["output"])
        self.assertEqual(revised.normalize_prediction(value[0], value[1], demand_sources=value[2],
            operation_body=value[3], operation_spans=value[4]),
            previous.normalize_prediction(value[0], value[1], demand_sources=value[2],
                operation_body=value[3], operation_spans=value[4]))

    def test_existing_branch_provenance_and_completeness_guards_still_reject(self):
        value = self.value()
        invalid_fields = (("operation_id", "unseen"), ("demand_span_id", "unseen"),
            ("axis", ""), ("operation_layer", "invented"), ("comparison_scope", "project_deliverable"),
            ("demand_property", ""), ("operation_property", " "), ("requested_part", "invented slice"))
        for field, invalid in invalid_fields:
            raw = copy.deepcopy(value[0])
            raw["facets"]["output"][field] = invalid
            before = copy.deepcopy(raw)
            with self.subTest(field=field), self.assertRaises(ValueError):
                revised.normalize_prediction(raw, value[1], demand_sources=value[2],
                    operation_body=value[3], operation_spans=value[4])
            self.assertEqual(raw, before)
        raw = copy.deepcopy(value[0])
        raw["demand_complete"] = True
        with self.assertRaisesRegex(ValueError, "invented_completeness"):
            revised.normalize_prediction(raw, value[1], demand_sources=value[2],
                operation_body=value[3], operation_spans=value[4])

    def test_unknown_keeps_axis_and_empty_declarations_without_repair(self):
        value = self.value()
        value[0].clear()
        value[0].update(fixtures.unknown())
        before = copy.deepcopy(value)
        checked = revised.normalize_prediction(value[0], value[1], demand_sources=value[2],
            operation_body=value[3], operation_spans=value[4])
        for name, facet in value[0]["facets"].items():
            self.assertEqual(checked["comparison_declarations"][name]["axis"], facet["axis"])
            self.assertEqual(checked["annotation"]["facets"][name]["relation"], "unknown")
            self.assertTrue(all(not item for key, item in checked["comparison_declarations"][name].items()
                if key != "axis"))
        self.assertFalse(checked["summary"]["partial_outcome_hint"])
        self.assertEqual(value, before)

    def test_reload_has_no_application_io_or_configuration_lookup(self):
        with patch("builtins.open", side_effect=AssertionError("file IO")), \
            patch("pathlib.Path.read_text", side_effect=AssertionError("file IO")), \
            patch("os.getenv", side_effect=AssertionError("environment lookup")), \
            patch("socket.socket", side_effect=AssertionError("network IO")), \
            patch("sqlite3.connect", side_effect=AssertionError("database IO")), \
            patch("subprocess.run", side_effect=AssertionError("process IO")):
            importlib.reload(revised)
        self.assertIs(revised.normalize_prediction, previous.normalize_prediction)

    def test_offline_transport_changes_only_instruction_for_both_api_kinds(self):
        from missing_link.provider import Provider
        value = self.value()
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

    def test_frozen_driver_and_production_do_not_use_the_new_prompt(self):
        from scripts import missing_link_triage_prospective_driver as driver
        self.assertEqual(driver.PROMPT, previous.PROMPT)
        self.assertNotEqual(driver.PROMPT, revised.PROMPT)
        root = Path(__file__).resolve().parents[1]
        files = [root / "app.py", root / "github_cli.py"]
        for folder in ("missing_link", "analytics", "storage"):
            files.extend((root / folder).rglob("*.py"))
        for path in files:
            self.assertNotIn("missing_link_triage_evidence_strength_prompt", path.read_text(encoding="utf-8"))
