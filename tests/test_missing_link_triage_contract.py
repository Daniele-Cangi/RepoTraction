"""Synthetic contract checks, not AI outputs or measurements of relevance."""
import copy
import unittest

from scripts.missing_link_triage_contract import FACETS, MAX_BODY_BYTES, summarize_review


def span(body, quote):
    start = body.index(quote)
    return {"start": start, "end": start + len(quote), "quote": quote}


def review(demand, operation, *, complete=True):
    # Human-authored fixture labels; the contract never infers these from text.
    return {"demand_complete": complete, "facets": {
        name: {"relation": "aligned", "reason": "Synthetic reviewed alignment",
               "demand": span(demand, demand), "operation": span(operation, operation)} for name in FACETS}}


class TriageContractTests(unittest.TestCase):
    def evaluate(self, relations=None, complete=True):
        demand, operation = "Original demand body", "Selected operation body"
        value = review(demand, operation, complete=complete)
        for name, relation in (relations or {}).items():
            value["facets"][name]["relation"] = relation
            if relation == "unknown":
                value["facets"][name].update(demand=None, operation=None)
        return summarize_review(value, demand_body=demand, operation_body=operation)

    def test_complete_alignment_is_review_candidate_not_eligibility(self):
        result = self.evaluate()
        self.assertEqual(result["status"], "candidate_for_review")
        self.assertFalse(result["changes_qualification"])
        self.assertFalse(result["changes_selection"])
        self.assertNotIn("eligible", result)

    def test_incomplete_alignment_stays_unknown(self):
        self.assertEqual(self.evaluate(complete=False)["status"], "context_required")

    def test_unknown_each_facet_prevents_positive(self):
        for name in FACETS:
            with self.subTest(name=name):
                self.assertEqual(self.evaluate({name: "unknown"})["status"], "context_required")

    def test_complete_difference_is_hint_not_rejection(self):
        for name in FACETS:
            with self.subTest(name=name):
                result = self.evaluate({name: "different"})
                self.assertEqual(result["status"], "mismatch_hint")
                self.assertEqual(result["different_facets"], [name])
                self.assertFalse(result["changes_selection"])

    def test_incomplete_demand_keeps_difference_without_rejecting(self):
        result = self.evaluate({"outcome": "different"}, complete=False)
        self.assertEqual(result["status"], "context_required")
        self.assertEqual(result["different_facets"], ["outcome"])

    def test_slice_does_not_certify_whole_request(self):
        self.assertEqual(self.evaluate({"outcome": "slice"})["status"], "partial_candidate")
        result = self.evaluate({"outcome": "slice", "runtime": "unknown"})
        self.assertEqual(result["status"], "context_required")
        self.assertTrue(result["partial_outcome_hint"])

    def test_slice_cannot_mask_other_difference(self):
        self.assertEqual(self.evaluate({"outcome": "slice", "input": "different"})["status"], "mismatch_hint")

    def test_runtime_slice_invalid(self):
        with self.assertRaises(ValueError):
            self.evaluate({"runtime": "slice"})

    def test_missing_facet_and_non_boolean_completeness_invalid(self):
        for mutate in (lambda value: value["facets"].pop("runtime"),
                       lambda value: value.update(demand_complete="true")):
            value = review("demand", "operation")
            mutate(value)
            with self.assertRaises(ValueError):
                summarize_review(value, demand_body="demand", operation_body="operation")

    def test_forged_title_quote_wrong_offsets_and_blank_evidence_invalid(self):
        for evidence in ({"start": 0, "end": 5, "quote": "title"},
                         {"start": -1, "end": 5, "quote": "demand"},
                         {"start": True, "end": 6, "quote": "demand"},
                         {"start": 0, "end": 1, "quote": " "}):
            value = review("demand", "operation")
            value["facets"]["outcome"]["demand"] = evidence
            with self.assertRaises(ValueError):
                summarize_review(value, demand_body="demand", operation_body="operation")

    def test_unknown_cannot_smuggle_established_evidence(self):
        value = review("demand", "operation")
        value["facets"]["runtime"]["relation"] = "unknown"
        with self.assertRaises(ValueError):
            summarize_review(value, demand_body="demand", operation_body="operation")

    def test_over_bound_unicode_body_rejected_without_truncation(self):
        with self.assertRaises(ValueError):
            summarize_review(review("demand", "operation"), demand_body="é" * (MAX_BODY_BYTES // 2 + 1), operation_body="operation")

    def test_original_inputs_unchanged(self):
        value = review("demand", "operation")
        before = copy.deepcopy(value)
        summarize_review(value, demand_body="demand", operation_body="operation")
        self.assertEqual(value, before)

    def test_near_wording_has_different_reviewed_outcomes(self):
        # Paired controls mirror known error types without using real issue text.
        pairs = (("search", "sorted numeric array position", "hosted manual text search"),
                 ("bytes", "encode one string", "detect mixed array dtypes"),
                 ("group", "group collection values", "emit typed schema members"),
                 ("copy", "skip newer destination", "publish atomically after failure"),
                 ("token", "compress serialized bytes", "measure full model token savings"))
        for shared, mechanism, different in pairs:
            with self.subTest(shared=shared):
                operation = f"{shared}: {mechanism}"
                for outcome, relation, expected in ((mechanism, "aligned", "candidate_for_review"),
                                                    (different, "different", "mismatch_hint")):
                    demand = f"{shared}: {outcome}"
                    value = review(demand, operation)
                    value["facets"]["outcome"].update(relation=relation, reason="Human-reviewed synthetic control")
                    self.assertEqual(summarize_review(value, demand_body=demand, operation_body=operation)["status"], expected)
