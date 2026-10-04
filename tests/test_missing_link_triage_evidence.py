"""Synthetic controls; no AI, network, database writes or acquired code execution."""
import copy
import unittest

from scripts.missing_link_triage_contract import FACETS, MAX_BODY_BYTES
from scripts.missing_link_triage_evidence import resolve_demand_quote, audit_reviewed_prediction


def span(body):
    return {"start": 0, "end": len(body), "quote": body}


def prediction(demand, operation, facet="outcome", relation="slice"):
    result = {"demand_complete": False, "facets": {name: {"relation": "unknown",
        "reason": "Synthetic context not established", "demand": None, "operation": None} for name in FACETS}}
    result["facets"][facet] = {"relation": relation, "reason": "Synthetic proposed relation",
        "demand": span(demand), "operation": span(operation)}
    return result


def reviews(facet="outcome", basis="analogy"):
    result = {name: {"basis": "not_established", "reason": "Independent synthetic review",
        "requested_part": None, "existing_behavior": None, "remaining_work": None} for name in FACETS}
    result[facet]["basis"] = basis
    return result


class DemandQuotationTests(unittest.TestCase):
    def test_exact_original_characters_and_comment_offsets(self):
        sources = {"q0": "Original body é", "q1": "α\n  exact `quote`\r\nω"}
        quote = "\n  exact `quote`\r\n"
        before = copy.deepcopy(sources)
        result = resolve_demand_quote(sources, "q1", quote)
        body = "\n\n".join(sources.values())
        self.assertEqual(body[result["start"]:result["end"]], quote)
        self.assertEqual(result["start"], len(sources["q0"]) + 3)
        self.assertEqual(sources, before)

    def test_paraphrase_rejected(self):
        with self.assertRaises(ValueError):
            resolve_demand_quote({"q0": "Keep the previous file if the copy fails."}, "q0",
                                 "The proposed fix replaces the file after copying succeeds.")

    def test_markdown_and_whitespace_are_not_repaired(self):
        for quote in ("cargo install (stable)", "Use  grep", "Use\r\ngrep"):
            with self.subTest(quote=quote), self.assertRaises(ValueError):
                resolve_demand_quote({"q0": "`cargo install` and Use\ngrep"}, "q0", quote)

    def test_exact_inner_markdown_text_is_legal(self):
        self.assertEqual(resolve_demand_quote({"q0": "`cargo install`"}, "q0", "cargo install")["quote"], "cargo install")

    def test_duplicate_and_overlapping_quotations_rejected(self):
        for text, quote in (("again again", "again"), ("aaa", "aa")):
            with self.subTest(text=text), self.assertRaises(ValueError):
                resolve_demand_quote({"q0": text}, "q0", quote)

    def test_declared_source_not_elsewhere(self):
        with self.assertRaises(ValueError):
            resolve_demand_quote({"q0": "Wrong source", "q1": "Exact demand"}, "q0", "Exact demand")

    def test_no_cross_source_quote(self):
        with self.assertRaises(ValueError):
            resolve_demand_quote({"q0": "start", "q1": "end"}, "q0", "start\n\nend")

    def test_unknown_source_and_invalid_shapes(self):
        for sources, source, quote in (({}, "q0", "text"), ({"q0": 1}, "q0", "text"),
                ({"q0": "text"}, [], "text"), ({"q0": "text"}, "q1", "text"),
                ({"q0": "text"}, "q0", None), ({"q0": "text"}, "q0", " ")):
            with self.subTest(source=source), self.assertRaises(ValueError):
                resolve_demand_quote(sources, source, quote)

    def test_quote_and_body_bounds_do_not_truncate(self):
        with self.assertRaises(ValueError):
            resolve_demand_quote({"q0": "x" * 501}, "q0", "x" * 501)
        with self.assertRaises(ValueError):
            resolve_demand_quote({"q0": "é" * (MAX_BODY_BYTES // 2 + 1)}, "q0", "é")


class ReviewedSemanticTests(unittest.TestCase):
    def audit(self, demand, operation, *, facet="outcome", relation="slice", basis="analogy"):
        return audit_reviewed_prediction(prediction(demand, operation, facet, relation), reviews(facet, basis),
            demand_body=demand, operation_body=operation)

    def test_local_timestamp_is_not_external_anchor(self):
        result = self.audit("An independently controlled external timestamp anchor",
                            "Attach a local timestamp and signature")
        self.assertEqual(result["issues"], [{"facet": "outcome", "kind": "analogy_is_not_suboperation"}])
        self.assertFalse(result["semantic_consistent_with_review"])
        self.assertFalse(result["changes_qualification"])

    def test_array_position_is_not_unestablished_help_search_support(self):
        result = self.audit("Search the hosted manual's TOC tree", "Find insertion position in a sorted array")
        self.assertFalse(result["semantic_consistent_with_review"])

    def test_same_primitive_can_be_requested_suboperation(self):
        demand, operation = "Find sorted-array boundaries for the index", "Find insertion position in a sorted array"
        value = prediction(demand, operation)
        review = reviews(basis="requested_suboperation")
        review["outcome"].update(requested_part="Find ordered index boundaries",
            existing_behavior="Binary-search insertion positions", remaining_work="Index construction and viewer integration")
        result = audit_reviewed_prediction(value, review, demand_body=demand, operation_body=operation)
        self.assertTrue(result["semantic_consistent_with_review"])
        self.assertEqual(result["syntactic_summary"]["status"], "context_required")
        self.assertFalse(result["changes_selection"])

    def test_mean_preserves_narrow_partial_value(self):
        demand, operation = "Profile count, nulls, average and quantiles", "Compute sum / count"
        review = reviews(basis="requested_suboperation")
        review["outcome"].update(requested_part="Average metric", existing_behavior="Arithmetic mean",
            remaining_work="Other metrics, ingestion, tests and project wiring")
        result = audit_reviewed_prediction(prediction(demand, operation), review,
            demand_body=demand, operation_body=operation)
        self.assertTrue(result["semantic_consistent_with_review"])
        self.assertNotIn("eligible", result)

    def test_missing_ci_integration_is_not_runtime_conflict(self):
        result = self.audit("A main-only CI step", "A Python method", facet="runtime",
                            relation="different", basis="missing_integration")
        self.assertEqual(result["issues"][0]["kind"], "missing_integration_is_not_difference")

    def test_observed_runtime_difference_is_hint_not_rejection(self):
        result = self.audit("An in-process JVM callable", "A Python callable", facet="runtime",
                            relation="different", basis="observed_difference")
        self.assertTrue(result["semantic_consistent_with_review"])
        self.assertEqual(result["syntactic_summary"]["status"], "context_required")

    def test_unknown_is_not_error_for_reference_disagreement(self):
        value = prediction("demand", "operation", relation="unknown")
        value["facets"]["outcome"].update(demand=None, operation=None)
        result = audit_reviewed_prediction(value, reviews(basis="observed_difference"),
            demand_body="demand", operation_body="operation")
        self.assertTrue(result["semantic_consistent_with_review"])
        self.assertFalse(result["syntactic_summary"]["partial_outcome_hint"])

    def test_semantic_review_cannot_launder_invalid_span(self):
        value = prediction("demand", "operation")
        value["facets"]["outcome"]["demand"]["quote"] = "paraphrase"
        with self.assertRaises(ValueError):
            audit_reviewed_prediction(value, reviews(), demand_body="demand", operation_body="operation")

    def test_missing_review_and_forged_basis_rejected(self):
        for change in (lambda r: r.pop("input"), lambda r: r["outcome"].update(basis="self_certified"),
                       lambda r: r["outcome"].update(reason=" ")):
            review = reviews()
            change(review)
            with self.assertRaises(ValueError):
                audit_reviewed_prediction(prediction("demand", "operation"), review,
                    demand_body="demand", operation_body="operation")

    def test_slice_needs_requested_part_behavior_and_remaining_work(self):
        for missing in ("requested_part", "existing_behavior", "remaining_work"):
            review = reviews(basis="requested_suboperation")
            review["outcome"].update(requested_part="part", existing_behavior="behavior", remaining_work="work")
            review["outcome"][missing] = None
            with self.assertRaises(ValueError):
                audit_reviewed_prediction(prediction("demand", "operation"), review,
                    demand_body="demand", operation_body="operation")

    def test_no_prediction_or_review_rewriting(self):
        value, review = prediction("demand", "operation"), reviews()
        before = copy.deepcopy((value, review))
        audit_reviewed_prediction(value, review, demand_body="demand", operation_body="operation")
        self.assertEqual((value, review), before)
