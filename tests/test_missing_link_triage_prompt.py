"""Experimental prompt/context fixtures, not live Luna predictions or accuracy."""
import copy
import json
import unittest
from unittest.mock import patch

from missing_link.provider import Provider
from missing_link.service import Budget
from scripts.missing_link_triage_contract import FACETS
from scripts.missing_link_triage_prompt import (
    PROMPT, MAX_SPANS, demand_catalog, build_context, schema_for_context, normalize_prediction)


def context(sources=None):
    return build_context({"repository": "fixture/source", "revision": "pinned",
        "selected_entrypoint": "module.py:operation", "demand_sources": sources or {"q0": "Explicit original demand"},
        "operation_evidence": {"e0": {"path": "module.py", "line": 1, "end_line": 1, "quote": "return value"}},
        "acquisition_complete": False, "acquisition_limitations": ["Acceptance context missing"]})


def unknown():
    return {"demand_complete": False, "facets": {name: {"relation": "unknown", "reason": "Not established",
        "demand_span_id": "", "operation_id": "", "requested_part": "", "existing_behavior": "",
        "remaining_work": ""} for name in FACETS}}


class PromptTests(unittest.TestCase):
    def normalize(self, raw, data=None, sources=None, spans=None):
        sources = sources or {"q0": "Explicit original demand"}
        return normalize_prediction(raw, data or context(sources), demand_sources=sources,
            operation_body="return value", operation_spans=spans or {"e0": {"start": 0, "end": 12, "quote": "return value"}})

    def known(self, relation="slice", facet="outcome", data=None):
        raw = unknown()
        item = raw["facets"][facet]
        item.update(relation=relation, demand_span_id=next(iter((data or context())["demand_spans"])), operation_id="e0")
        if relation == "slice":
            item.update(requested_part="Explicit requested suboperation", existing_behavior="Selected body behavior",
                        remaining_work="Project wiring, tests and other requirements")
        return raw

    def test_complete_catalog_roundtrip_preserves_unicode_and_whitespace(self):
        sources = {"q0": "α\n `original`\r\n" * 100, "q1": "Trailing spaces  \n", "q2": ""}
        catalog = demand_catalog(sources)
        for ref, text in sources.items():
            entries = [span for span in catalog.values() if span["source_id"] == ref]
            self.assertEqual("".join(span["quote"] for span in entries), text)
            last = 0
            for entry in entries:
                self.assertEqual(entry["start"], last)
                self.assertEqual(text[entry["start"]:entry["end"]], entry["quote"])
                last = entry["end"]
            self.assertEqual(last, len(text))

    def test_duplicate_text_has_distinct_offset_identifiers(self):
        catalog = demand_catalog({"q0": "x" * 1000})
        self.assertEqual(len(catalog), 2)
        self.assertEqual(len(set(catalog)), 2)
        self.assertEqual([s["start"] for s in catalog.values()], [0, 500])

    def test_id_stability_and_changed_source_changes_id(self):
        first = demand_catalog({"q0": "Original", "q1": "Comment"})
        self.assertEqual(first, demand_catalog({"q0": "Original", "q1": "Comment"}))
        self.assertNotEqual(set(first), set(demand_catalog({"q0": "original", "q1": "Comment"})))

    def test_over_bound_catalog_is_rejected_without_truncation(self):
        with self.assertRaises(ValueError):
            demand_catalog({"q0": "x" * ((MAX_SPANS + 1) * 500)})
        with self.assertRaises(ValueError):
            demand_catalog({"q0": "é" * 100000})

    def test_empty_source_and_invalid_sources(self):
        self.assertEqual(demand_catalog({"q0": ""}), {})
        for sources in ({}, {"q0": 1}, {1: "text"}):
            with self.assertRaises(ValueError):
                demand_catalog(sources)

    def test_no_reference_annotations_or_duplicate_body_are_sent(self):
        data = context()
        self.assertNotIn("demand_sources", data)
        self.assertNotIn("annotation", data)
        self.assertNotIn("matches", data)
        self.assertTrue(data["context_coverage"]["all_original_source_characters"])

    def test_schema_scopes_ids_and_runtime_cannot_be_slice(self):
        schema = schema_for_context(context())
        runtime = schema["properties"]["facets"]["properties"]["runtime"]["properties"]
        self.assertNotIn("slice", runtime["relation"]["enum"])
        self.assertEqual(runtime["operation_id"]["enum"], ["", "e0"])
        self.assertNotIn("demand_quote", runtime)
        with self.assertRaises(ValueError):
            self.normalize(self.known(facet="runtime"))

    def test_api_wide_enum_limit_is_checked_before_transport(self):
        data = context({"q0": "x" * (MAX_SPANS * 500)})
        data["operation_evidence"] = {f"e{i}": {} for i in range(40)}
        with self.assertRaises(ValueError):
            schema_for_context(data)

    def test_unknown_stays_unknown(self):
        checked = self.normalize(unknown())
        self.assertEqual(checked["summary"]["status"], "context_required")
        self.assertIsNone(checked["slice_description"])
        self.assertFalse(checked["slice_semantics_independently_verified"])

    def test_unknown_must_not_have_reference_or_slice_fields(self):
        for field, value in (("demand_span_id", next(iter(context()["demand_spans"]))),
                             ("operation_id", "e0"), ("remaining_work", "unreviewed")):
            raw = unknown()
            raw["facets"]["outcome"][field] = value
            with self.assertRaises(ValueError):
                self.normalize(raw)

    def test_slice_requires_all_three_descriptions(self):
        for field in ("requested_part", "existing_behavior", "remaining_work"):
            for value in ("", " ", "x" * 801):
                raw = self.known()
                raw["facets"]["outcome"][field] = value
                with self.assertRaises(ValueError):
                    self.normalize(raw)

    def test_non_slice_cannot_claim_slice_credit(self):
        raw = self.known(relation="different")
        raw["facets"]["outcome"]["existing_behavior"] = "Unreviewed credit"
        with self.assertRaises(ValueError):
            self.normalize(raw)

    def test_known_relation_requires_nonempty_supplied_ids(self):
        for field, value in (("demand_span_id", ""), ("demand_span_id", "invented"),
                             ("operation_id", ""), ("operation_id", "sibling")):
            raw = self.known()
            raw["facets"]["outcome"][field] = value
            with self.assertRaises(ValueError):
                self.normalize(raw)

    def test_tampered_catalog_and_selected_body_are_rejected(self):
        data = context()
        data["demand_spans"][next(iter(data["demand_spans"]))]["quote"] = "Paraphrase"
        with self.assertRaises(ValueError):
            self.normalize(self.known(), data)
        with self.assertRaises(ValueError):
            self.normalize(self.known(), spans={"e0": {"start": 0, "end": 7, "quote": "sibling"}})

    def test_bad_operation_offsets_cannot_launder_exact_quote(self):
        with self.assertRaises(ValueError):
            self.normalize(self.known(), spans={"e0": {"start": 1, "end": 13, "quote": "return value"}})

    def test_catalog_does_not_establish_complete_requirements(self):
        raw = unknown()
        raw["demand_complete"] = True
        with self.assertRaisesRegex(ValueError, "invented_completeness"):
            self.normalize(raw)

    def test_reason_is_bounded(self):
        for reason in (" ", "x" * 801):
            raw = unknown()
            raw["facets"]["input"]["reason"] = reason
            with self.assertRaises(ValueError):
                self.normalize(raw)

    def test_id_resolution_uses_original_comment_character_offsets(self):
        sources = {"q0": "é body", "q1": "comment"}
        data = context(sources)
        raw = self.known(data=data)
        raw["facets"]["outcome"]["demand_span_id"] = list(data["demand_spans"])[1]
        checked = self.normalize(raw, data, sources)
        self.assertEqual(checked["annotation"]["facets"]["outcome"]["demand"],
                         {"start": 8, "end": 15, "quote": "comment"})

    def test_raw_context_and_source_inputs_are_preserved(self):
        raw, data, sources = self.known(), context(), {"q0": "Explicit original demand"}
        before = copy.deepcopy((raw, data, sources))
        checked = self.normalize(raw, data, sources)
        self.assertEqual((raw, data, sources), before)
        self.assertEqual(checked["origin"], "model_prediction")
        self.assertFalse(checked["summary"]["changes_qualification"])
        self.assertFalse(checked["slice_semantics_independently_verified"])

    def test_real_provider_path_with_simulated_stream_and_scoped_schema(self):
        provider = Provider({"REPOTRACTION_AI_URL": "http://127.0.0.1:1", "REPOTRACTION_AI_MODEL": "fixture",
            "REPOTRACTION_AI_API_KIND": "responses", "REPOTRACTION_AI_STREAMING": "1",
            "REPOTRACTION_AI_RESPONSE_FORMAT": "json_schema"})
        raw, data = self.known(), context()
        terminal = {"type": "response.completed", "response": {"id": "fixture", "status": "completed",
            "output": [{"type": "message", "content": [{"type": "output_text", "text": json.dumps(raw)}]}]}}
        class Stream:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def readline(self, limit):
                if getattr(self, "sent", False): return b""
                self.sent = True
                return ("data: " + json.dumps(terminal) + "\n").encode()
        job = {"id": "fixture", "ai_calls_used": 0, "cost_reserved_usd": 0, "checkpoint": {}}
        budget = Budget(job, lambda: None, lambda: False, lambda: None)
        with patch("missing_link.provider.urllib.request.build_opener") as opener:
            opener.return_value.open.return_value = Stream()
            result = provider.complete(PROMPT, data, budget, schema=schema_for_context(data))
        self.assertEqual(result, raw)
        self.assertEqual(len(job["ai_trace"]), 1)
        self.assertEqual(job["checkpoint"]["ai_outputs"][0]["output"], raw)
        self.assertFalse(self.normalize(result)["slice_semantics_independently_verified"])
