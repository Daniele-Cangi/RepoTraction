"""Authored no-spend controls, not live model responses or quality measures."""
import copy
import json
import unittest
from unittest.mock import patch

from missing_link.provider import Provider
from missing_link.service import Budget
from scripts import missing_link_triage_explicit_scope as task
from scripts import missing_link_triage_prompt as original
from scripts.missing_link_triage_contract import FACETS
from scripts.missing_link_triage_evidence import audit_reviewed_prediction


SOURCES = {"q0": "Compute the arithmetic mean from numeric values."}
BODY = "function mean(values) { return sum(values) / values.length; }"
SPANS = {"e0": {"start": 0, "end": len(BODY), "quote": BODY}}


def context(sources=None):
    return original.build_context({"repository": "fixture/stats", "revision": "pinned",
        "selected_entrypoint": "stats.js:mean", "demand_sources": sources or SOURCES,
        "operation_evidence": {"e0": {"path": "stats.js", "line": 1, "end_line": 1, "quote": BODY}},
        "acquisition_complete": False, "acquisition_limitations": ["Acceptance not established"]})


def unknown():
    return {"demand_complete": False, "facets": {name: {
        "axis": task.AXES[name], "comparison_scope": "", "operation_layer": "",
        "demand_property": "", "operation_property": "", "relation": "unknown",
        "reason": "Not established", "demand_span_id": "", "operation_id": "",
        "requested_part": "", "existing_behavior": "", "remaining_work": ""} for name in FACETS}}


def known(facet="outcome", relation="slice", data=None, layer="selected_entrypoint"):
    raw = unknown()
    raw["facets"][facet].update(comparison_scope="requested_operation", operation_layer=layer,
        demand_property="Compute arithmetic mean", operation_property="Sum values and divide by count",
        relation=relation, demand_span_id=next(iter((data or context())["demand_spans"])), operation_id="e0")
    if relation == "slice":
        raw["facets"][facet].update(requested_part="Arithmetic mean for profiling",
            existing_behavior="Return sum divided by count", remaining_work="Other statistics and integration")
    return raw


def reviews(facet, basis):
    result = {name: {"basis": "not_established", "reason": "Independent authored review",
        "requested_part": None, "existing_behavior": None, "remaining_work": None} for name in FACETS}
    result[facet]["basis"] = basis
    return result


class ExplicitScopeTests(unittest.TestCase):
    def normalize(self, raw, data=None, sources=None, spans=None):
        return task.normalize_prediction(raw, data or context(sources), demand_sources=sources or SOURCES,
            operation_body=BODY, operation_spans=spans if spans is not None else SPANS)

    def test_strict_schema_requires_all_declarations_and_no_extras(self):
        schema = task.schema_for_context(context())
        for name in FACETS:
            facet = schema["properties"]["facets"]["properties"][name]
            self.assertFalse(facet["additionalProperties"])
            self.assertEqual(set(facet["required"]), set(facet["properties"]))
            self.assertTrue(set(task.DECLARATIONS) <= set(facet["required"]))
            self.assertEqual(facet["properties"]["axis"]["enum"], [task.AXES[name]])
        for field in task.DECLARATIONS:
            raw = unknown()
            del raw["facets"]["input"][field]
            with self.assertRaises(ValueError): self.normalize(raw)
        raw = unknown()
        raw["facets"]["input"]["self_verified"] = True
        with self.assertRaises(ValueError): self.normalize(raw)

    def test_axis_cannot_change_the_question(self):
        raw = unknown()
        raw["facets"]["runtime"]["axis"] = "requested_behavior"
        with self.assertRaises(ValueError): self.normalize(raw)

    def test_unknown_requires_empty_comparison_declarations(self):
        for field in task.DECLARATIONS[1:]:
            raw = unknown()
            raw["facets"]["input"][field] = {"comparison_scope": "requested_operation",
                "operation_layer": "selected_entrypoint"}.get(field, "Unproved property")
            with self.subTest(field=field), self.assertRaises(ValueError): self.normalize(raw)

    def test_unknown_remains_abstention_with_fixed_axes(self):
        checked = self.normalize(unknown())
        self.assertEqual(checked["summary"]["unknown_facets"], list(FACETS))
        self.assertEqual(checked["summary"]["status"], "context_required")
        self.assertFalse(checked["comparison_semantics_independently_verified"])
        self.assertFalse(checked["summary"]["changes_qualification"])

    def test_known_project_scope_is_rejected_without_repair(self):
        for scope in ("", "project_deliverable"):
            raw = known()
            raw["facets"]["outcome"]["comparison_scope"] = scope
            before = copy.deepcopy(raw)
            with self.assertRaises(ValueError): self.normalize(raw)
            self.assertEqual(raw, before)

    def test_known_needs_explicit_bounded_properties(self):
        for field in ("demand_property", "operation_property"):
            for value in ("", " ", "x" * 401, None, 17):
                raw = known()
                raw["facets"]["outcome"][field] = value
                with self.subTest(field=field, value=value), self.assertRaises(ValueError): self.normalize(raw)
        raw = known()
        raw["facets"]["outcome"]["demand_property"] = "x" * 400
        self.normalize(raw)

    def test_layers_are_explicit_but_not_automatically_proven(self):
        for layer in task.LAYERS[1:]:
            checked = self.normalize(known(layer=layer))
            self.assertEqual(checked["comparison_declarations"]["outcome"]["operation_layer"], layer)
            self.assertFalse(checked["comparison_semantics_independently_verified"])
        for layer in ("", "unseen_helper", "returned_callable_then_method"):
            with self.assertRaises(ValueError): self.normalize(known(layer=layer))

    def test_runtime_slice_is_not_added(self):
        with self.assertRaises(ValueError): self.normalize(known("runtime"))

    def test_slice_still_needs_three_bounded_descriptions(self):
        for field in ("requested_part", "existing_behavior", "remaining_work"):
            for value in ("", " ", "x" * 801):
                raw = known()
                raw["facets"]["outcome"][field] = value
                with self.assertRaises(ValueError): self.normalize(raw)

    def test_non_slice_cannot_claim_partial_credit(self):
        raw = known(relation="different")
        raw["facets"]["outcome"]["existing_behavior"] = "Unreviewed credit"
        with self.assertRaises(ValueError): self.normalize(raw)

    def test_unknown_references_cannot_be_laundered(self):
        for field, value in (("demand_span_id", next(iter(context()["demand_spans"]))), ("operation_id", "e0")):
            raw = unknown()
            raw["facets"]["input"][field] = value
            with self.assertRaises(ValueError): self.normalize(raw)

    def test_known_needs_original_scoped_ids(self):
        for field, value in (("demand_span_id", ""), ("demand_span_id", "invented"),
                             ("operation_id", ""), ("operation_id", "sibling")):
            raw = known()
            raw["facets"]["outcome"][field] = value
            with self.assertRaises(ValueError): self.normalize(raw)

    def test_catalog_tampering_is_still_rejected(self):
        data = context()
        data["demand_spans"][next(iter(data["demand_spans"]))]["quote"] = "Paraphrase"
        with self.assertRaises(ValueError): self.normalize(known(), data)

    def test_operation_scope_quote_and_offsets_are_still_checked(self):
        for spans in ({}, {"sibling": SPANS["e0"]},
                      {"e0": {"start": 0, "end": 7, "quote": "sibling"}},
                      {"e0": {"start": 1, "end": len(BODY) + 1, "quote": BODY}}):
            with self.assertRaises(ValueError): self.normalize(known(), spans=spans)

    def test_completeness_cannot_be_invented(self):
        raw = unknown()
        raw["demand_complete"] = True
        with self.assertRaisesRegex(ValueError, "invented_completeness"): self.normalize(raw)

    def test_reason_bound_is_preserved(self):
        for value in (" ", "x" * 801):
            raw = unknown()
            raw["facets"]["input"]["reason"] = value
            with self.assertRaises(ValueError): self.normalize(raw)

    def test_projection_preserves_raw_context_and_old_contract(self):
        raw, data = known(), context()
        before = copy.deepcopy((raw, data, SOURCES, SPANS))
        checked = self.normalize(raw, data)
        projection = copy.deepcopy(raw)
        for facet in projection["facets"].values():
            for field in task.DECLARATIONS: del facet[field]
        old_checked = original.normalize_prediction(projection, data, demand_sources=SOURCES,
            operation_body=BODY, operation_spans=SPANS)
        self.assertEqual({key: checked[key] for key in old_checked}, old_checked)
        self.assertEqual((raw, data, SOURCES, SPANS), before)
        checked["comparison_declarations"]["outcome"]["demand_property"] = "Changed result"
        self.assertEqual((raw, data, SOURCES, SPANS), before)

    def test_fixed_runtime_axis_cannot_certify_semantics(self):
        raw = known("runtime", "different")
        checked = self.normalize(raw)
        audit = audit_reviewed_prediction(checked["annotation"], reviews("runtime", "facet_mismatch"),
            demand_body=SOURCES["q0"], operation_body=BODY)
        self.assertEqual(audit["issues"], [{"facet": "runtime", "kind": "reviewed_property_is_not_requested_facet"}])
        self.assertFalse(checked["comparison_semantics_independently_verified"])

    def test_false_layer_declaration_requires_independent_review(self):
        checked = self.normalize(known("input", "aligned", layer="returned_callable"))
        audit = audit_reviewed_prediction(checked["annotation"], reviews("input", "unresolved_interface_layer"),
            demand_body=SOURCES["q0"], operation_body=BODY)
        self.assertFalse(audit["semantic_consistent_with_review"])
        self.assertFalse(audit["changes_selection"])

    def test_wrong_valid_chunk_still_requires_review_and_preserves_mean_slice(self):
        sources = {"q0": SOURCES["q0"] + " " * (500 - len(SOURCES["q0"])) + "Unrelated browser history."}
        data = context(sources)
        raw = known(data=data)
        raw["facets"]["output"] = known("output", "aligned", data)["facets"]["output"]
        raw["facets"]["output"].update(demand_property="Return numeric scalar",
            operation_property="Return numeric scalar", demand_span_id=list(data["demand_spans"])[1])
        checked = self.normalize(raw, data, sources)
        review = reviews("output", "irrelevant_citation")
        review["outcome"].update(basis="requested_suboperation", requested_part="Arithmetic mean",
            existing_behavior="Return sum divided by count", remaining_work="Other statistics and integration")
        audit = audit_reviewed_prediction(checked["annotation"], review, demand_body=sources["q0"], operation_body=BODY)
        self.assertEqual(audit["issues"], [{"facet": "output", "kind": "citation_does_not_support_claim"}])
        self.assertTrue(audit["syntactic_summary"]["partial_outcome_hint"])
        self.assertFalse(checked["slice_semantics_independently_verified"])

    def test_all_new_enums_count_toward_api_limit(self):
        data = context({"q0": "x" * 110000})
        evidence = data["operation_evidence"]["e0"]
        data["operation_evidence"] = {f"e{i}": evidence for i in range(16)}
        schema = task.schema_for_context(data)
        self.assertEqual(task._enum_values(schema), 997)
        data["operation_evidence"]["e16"] = evidence
        original.schema_for_context(data)  # Old schema fits; the new schema must not borrow its old cap.
        with self.assertRaisesRegex(ValueError, "enum bound"): task.schema_for_context(data)

    def test_original_character_coverage_and_offsets_are_unchanged(self):
        sources = {"q0": "é\n" * 300, "q1": "comment\r\n  ", "q2": ""}
        data = context(sources)
        raw = known(data=data)
        raw["facets"]["outcome"]["demand_span_id"] = list(data["demand_spans"])[2]
        checked = self.normalize(raw, data, sources)
        self.assertEqual(checked["annotation"]["facets"]["outcome"]["demand"],
            {"start": 602, "end": 613, "quote": sources["q1"]})
        self.assertEqual(data, context(sources))

    def test_real_provider_contract_with_simulated_stream_never_calls_network(self):
        provider = Provider({"REPOTRACTION_AI_URL": "http://127.0.0.1:1", "REPOTRACTION_AI_MODEL": "fixture",
            "REPOTRACTION_AI_API_KIND": "responses", "REPOTRACTION_AI_STREAMING": "1",
            "REPOTRACTION_AI_RESPONSE_FORMAT": "json_schema"})
        raw, data = known(), context()
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
            result = provider.complete(task.PROMPT, data, budget, schema=task.schema_for_context(data))
            opener.return_value.open.assert_called_once()
        self.assertEqual(result, raw)
        self.assertEqual(job["checkpoint"]["ai_outputs"][0]["output"], raw)
        self.assertEqual(len(job["ai_trace"]), 1)
        self.assertFalse(self.normalize(result)["comparison_semantics_independently_verified"])
