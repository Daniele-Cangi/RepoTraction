"""Authored comparison controls, not sampled model predictions or a classifier.

Evidence may support a local property contrast without proving implementation or
adoption. Both a bounded contrast and abstention remain syntactically permissible;
independent fixture reviews do not turn abstention into a scored false negative.
No prompt/schema, historical artifact, production gate or provider is changed.
"""
import copy
import unittest

from scripts import missing_link_triage_explicit_scope as task
from scripts.missing_link_triage_contract import FACETS
from scripts.missing_link_triage_evidence import audit_reviewed_prediction
from scripts.missing_link_triage_prompt import build_context


def unknown():
    return {"demand_complete": False, "facets": {name: {
        "axis": task.AXES[name], "comparison_scope": "", "operation_layer": "",
        "demand_property": "", "operation_property": "", "relation": "unknown",
        "reason": "Authored abstention; implementation/adoption not established",
        "demand_span_id": "", "operation_id": "", "requested_part": "",
        "existing_behavior": "", "remaining_work": ""} for name in FACETS}}


def fixture(demand, body, facet, demand_property, operation_property, *,
            relation="different", layer="selected_entrypoint", path="sample.js"):
    sources = {"q0": demand}
    data = build_context({"repository": "fixture/comparison", "revision": "pinned",
        "selected_entrypoint": f"{path}:operation", "demand_sources": sources,
        "operation_evidence": {"e0": {"path": path, "line": 1, "end_line": len(body.splitlines()),
                                      "quote": body}},
        "acquisition_complete": False, "acquisition_limitations": ["Acceptance and adoption not established"]})
    spans = {"e0": {"start": 0, "end": len(body), "quote": body}}
    raw = unknown()
    raw["facets"][facet].update(relation=relation, reason="Authored local property comparison, not adoption proof",
        comparison_scope="requested_operation", operation_layer=layer,
        demand_property=demand_property, operation_property=operation_property,
        demand_span_id=next(iter(data["demand_spans"])), operation_id="e0")
    return raw, data, sources, body, spans


def normalize(value):
    raw, data, sources, body, spans = value
    return task.normalize_prediction(raw, data, demand_sources=sources, operation_body=body, operation_spans=spans)


def reviews(facet, basis):
    result = {name: {"basis": "not_established", "reason": "Independent authored fixture reading",
        "requested_part": None, "existing_behavior": None, "remaining_work": None} for name in FACETS}
    result[facet]["basis"] = basis
    return result


def audit(value, review):
    return audit_reviewed_prediction(normalize(value)["annotation"], review,
        demand_body="\n\n".join(value[2].values()), operation_body=value[3])


class PropertyComparisonTests(unittest.TestCase):
    def assert_pair(self, value, facet, basis="observed_difference"):
        before = copy.deepcopy(value)
        checked = normalize(value)
        reviewed = audit(value, reviews(facet, basis))
        self.assertEqual(checked["annotation"]["facets"][facet]["relation"], value[0]["facets"][facet]["relation"])
        self.assertNotIn(facet, checked["summary"]["unknown_facets"])
        self.assertTrue(reviewed["semantic_consistent_with_review"])
        self.assertEqual(reviewed["issues"], [])
        self.assertEqual(checked["summary"]["status"], "context_required")
        self.assertFalse(checked["summary"]["changes_selection"])
        self.assertFalse(checked["summary"]["changes_qualification"])
        self.assertFalse(checked["comparison_semantics_independently_verified"])
        self.assertEqual(value, before)

        # This equally valid abstention is preserved, not repaired to the authored label.
        abstention = copy.deepcopy(value)
        abstention[0]["facets"][facet] = unknown()["facets"][facet]
        abstention_before = copy.deepcopy(abstention)
        abstained = normalize(abstention)
        abstained_review = audit(abstention, reviews(facet, basis))
        self.assertEqual(abstained["summary"]["unknown_facets"], list(FACETS))
        self.assertEqual(abstained["summary"]["different_facets"], [])
        self.assertFalse(abstained["summary"]["partial_outcome_hint"])
        self.assertEqual(abstained_review["issues"], [])
        # Label consistency is not usefulness: the same no-issues result is NOT a quality score.
        self.assertTrue(abstained_review["semantic_consistent_with_review"])
        self.assertEqual(abstention, abstention_before)
        return checked

    def test_output_contrast_does_not_require_an_implementation_link(self):
        value = fixture("The requested callback must return command text.",
            "function operation(path) { return path === 'document.txt'; }", "output",
            "Return command text", "Return a boolean predicate result")
        checked = self.assert_pair(value, "output")
        self.assertEqual(checked["summary"]["different_facets"], ["output"])
        self.assertNotIn("implementation_verified", value[1])

    def test_input_contrast_stays_a_declared_interface_not_adoption(self):
        value = fixture("The requested callback accepts an array of mixed text and byte values.",
            "def operation(value: str | bytes) -> bytes:\n    if isinstance(value, str):\n        return value.encode()\n    return value",
            "input", "Declared mixed-collection input", "Declared scalar str or bytes input", path="sample.py")
        checked = self.assert_pair(value, "input")
        self.assertEqual(checked["summary"]["different_facets"], ["input"])

    def test_direct_behavior_contrast_is_not_a_runtime_judgment(self):
        value = fixture("The requested operation computes the arithmetic mean of numeric rows.",
            "function operation(rows) { return false; }", "outcome",
            "Compute arithmetic mean", "Always return false without arithmetic")
        checked = self.assert_pair(value, "outcome")
        self.assertEqual(checked["summary"]["different_facets"], ["outcome"])
        self.assertIn("runtime", checked["summary"]["unknown_facets"])

    def test_unfetched_acceptance_does_not_erase_a_local_output_contrast(self):
        value = fixture("Return a numeric scalar from the requested callback.",
            "function operation() { return true; }", "output", "Numeric scalar", "Boolean true")
        checked = self.assert_pair(value, "output")
        self.assertFalse(value[1]["acquisition_complete"])
        self.assertFalse(checked["summary"]["demand_complete"])

    def test_factory_result_is_compared_at_its_own_layer(self):
        value = fixture("The requested entrypoint directly returns a numeric scalar.",
            "function operation() { return {read: () => true}; }", "output",
            "Numeric result directly from entrypoint", "Object of methods directly from entrypoint")
        checked = self.assert_pair(value, "output")
        self.assertEqual(checked["comparison_declarations"]["output"]["operation_layer"], "selected_entrypoint")

    def test_returned_method_result_can_be_compared_without_factory_conflation(self):
        value = fixture("The returned read method must return a numeric scalar.",
            "function operation() { return {read: () => true}; }", "output",
            "Numeric scalar from returned read method", "Boolean true from returned read method",
            layer="returned_method")
        checked = self.assert_pair(value, "output")
        self.assertEqual(checked["comparison_declarations"]["output"]["operation_layer"], "returned_method")

    def test_output_alignment_is_not_implementation_or_slice_proof(self):
        value = fixture("An averaging callback must return a numeric scalar.",
            "function operation() { return 42; }", "output", "Numeric scalar", "Numeric literal 42",
            relation="aligned")
        checked = self.assert_pair(value, "output", "observed_alignment")
        self.assertFalse(checked["summary"]["partial_outcome_hint"])
        self.assertEqual(checked["annotation"]["facets"]["outcome"]["relation"], "unknown")

    def test_explicit_average_slice_survives_without_complete_project_context(self):
        value = fixture("Profile numeric rows, including their average and other statistics.",
            "function operation(rows) { let sum = 0; for (const x of rows) sum += x; return sum / rows.length; }",
            "outcome", "Compute the average of numeric rows", "Sum rows and divide by count", relation="slice")
        descriptions = {"requested_part": "Arithmetic mean for profiling",
            "existing_behavior": "Sum rows and divide by count",
            "remaining_work": "Other statistics, numeric edge cases and project integration"}
        value[0]["facets"]["outcome"].update(descriptions)
        review = reviews("outcome", "requested_suboperation")
        review["outcome"].update(descriptions)
        checked = normalize(value)
        self.assertEqual(audit(value, review)["issues"], [])
        self.assertTrue(checked["summary"]["partial_outcome_hint"])
        self.assertEqual(checked["summary"]["status"], "context_required")
        self.assertFalse(checked["slice_semantics_independently_verified"])

    def test_unseen_delegate_still_cannot_establish_output_difference(self):
        value = fixture("Return a nested dictionary of keys.",
            "function operation(values) { return unseen(values); }", "output",
            "Nested dictionary", "Flat list alleged without seeing the delegate")
        result = audit(value, reviews("output", "unseen_delegate"))
        self.assertEqual(result["issues"], [{"facet": "output", "kind": "delegate_contract_not_established"}])
        self.assertFalse(result["changes_qualification"])

    def test_generic_input_does_not_prove_specific_values_are_excluded(self):
        value = fixture("Supply flat schema keys to the requested grouping operation.",
            "function operation(values) { return unseen(values); }", "input",
            "Flat schema keys", "Claimed exclusion inferred from generic values parameter")
        self.assertFalse(audit(value, reviews("input", "unseen_delegate"))["semantic_consistent_with_review"])

    def test_missing_wiring_alone_is_not_a_property_difference(self):
        value = fixture("Integrate a numeric callback in the application.",
            "function operation() { return 42; }", "output",
            "Numeric callback output", "Claimed different output because not integrated")
        result = audit(value, reviews("output", "missing_integration"))
        self.assertEqual(result["issues"], [{"facet": "output", "kind": "missing_integration_is_not_difference"}])

    def test_product_report_cannot_be_laundered_as_primitive_output(self):
        value = fixture("Compute a numeric statistic, then export the final study report.",
            "function operation() { return 42; }", "output", "Whole study report", "Numeric primitive result")
        # False same-operation labels may pass mechanically; comparison permission is not proof.
        self.assertFalse(audit(value, reviews("output", "broader_scope"))["semantic_consistent_with_review"])
        value[0]["facets"]["output"]["comparison_scope"] = "project_deliverable"
        with self.assertRaises(ValueError): normalize(value)

    def test_declared_scalar_contract_does_not_prove_runtime_collection_rejection(self):
        value = fixture("Accept mixed collections.",
            "def operation(value: str | bytes):\n    if isinstance(value, str):\n        return value.encode()\n    return value",
            "input", "Mixed collections", "Runtime rejection of all collections, alleged from the annotation",
            path="sample.py")
        result = audit(value, reviews("input", "not_established"))
        self.assertEqual(result["issues"], [{"facet": "input", "kind": "relation_not_established_by_review"}])

    def test_direct_contrast_permission_does_not_fix_wrong_chunk_relevance(self):
        demand = "The requested callback must return command text."
        value = fixture(demand + " " * (500 - len(demand)) + "Unrelated build history.",
            "function operation() { return false; }", "output", "Command text", "Boolean false")
        value[0]["facets"]["output"]["demand_span_id"] = list(value[1]["demand_spans"])[1]
        result = audit(value, reviews("output", "irrelevant_citation"))
        self.assertEqual(result["issues"], [{"facet": "output", "kind": "citation_does_not_support_claim"}])

    def test_abstention_cannot_gain_a_score_or_rejection_from_reviewer_label(self):
        value = fixture("Return a numeric scalar.", "function operation() { return false; }",
            "output", "Numeric scalar", "Boolean false")
        value[0].clear()
        value[0].update(unknown())
        before = copy.deepcopy(value)
        for basis in ("observed_difference", "observed_alignment", "not_established", "unseen_delegate"):
            reviewed = audit(value, reviews("output", basis))
            self.assertEqual(reviewed["issues"], [])
            self.assertEqual(reviewed["syntactic_summary"]["different_facets"], [])
            self.assertEqual(reviewed["syntactic_summary"]["unknown_facets"], list(FACETS))
            self.assertNotIn("accuracy", reviewed)
            self.assertNotIn("correct_rejection", reviewed)
        self.assertEqual(value, before)

    def test_comparison_neither_requires_nor_accepts_self_certified_implementation(self):
        value = fixture("Return a numeric scalar.", "function operation() { return false; }",
            "output", "Numeric scalar", "Boolean false")
        self.assert_pair(value, "output")
        value[0]["implementation_verified"] = True
        with self.assertRaises(ValueError): normalize(value)
