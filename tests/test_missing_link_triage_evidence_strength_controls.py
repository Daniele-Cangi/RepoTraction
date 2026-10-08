"""Authored no-spend controls for two prospective source-reading failures.

Execute only these synthetic functions and inert supplied callbacks, never
acquired code. Reviewer bases are explicit fixture judgments, not automatically
inferred gold labels. Native cards, prompts, schemas and production stay frozen.
"""
import copy
import inspect
import unittest

from scripts import missing_link_triage_declaration_schema as task
from scripts.missing_link_triage_contract import FACETS
from scripts.missing_link_triage_evidence import audit_reviewed_prediction
import test_missing_link_triage_properties as fixtures


def documented_empty(value, constructor):
    """For None, return an empty string."""
    if value is None:
        return constructor()
    return value


def documented_chunks(values, producer):
    """Return a sequence of list-valued chunks."""
    return producer(values)


def conditional_separator(text, use_default, separator):
    if use_default:
        return text.replace(",", ",")
    return text.replace(",", separator())


def literal_separator(text):
    return text.replace(",", ";")


def checked_chunks(values, size, strict, producer):
    for chunk in producer(values, size):
        if strict and len(chunk) != size:
            raise ValueError("Incomplete chunk")
        yield chunk


def value_for(operation, demand, facet, demanded, offered, *, relation="aligned"):
    # Only the selected wrapper is cited. Test callbacks are NOT supplied evidence.
    body = inspect.getsource(operation)
    value = fixtures.fixture(demand, body, facet, demanded, offered,
        relation=relation, path="authored_evidence_strength.py")
    value[1]["selected_entrypoint"] = f"authored_evidence_strength.py:{operation.__name__}"
    return value


class EvidenceStrengthControls(unittest.TestCase):
    def normalize(self, value):
        before = copy.deepcopy(value)
        raw, data, sources, body, spans = value
        result = task.normalize_prediction(raw, data, demand_sources=sources,
            operation_body=body, operation_spans=spans)
        self.assertEqual(value, before)
        for name in FACETS:
            for field in ("relation", "reason"):
                self.assertEqual(result["annotation"]["facets"][name][field], raw["facets"][name][field])
            for field, declaration in result["comparison_declarations"][name].items():
                self.assertEqual(declaration, raw["facets"][name][field])
        self.assertEqual(result["summary"]["status"], "context_required")
        for flag in ("demand_complete", "changes_selection", "changes_qualification"):
            self.assertFalse(result["summary"][flag])
        self.assertFalse(result["comparison_semantics_independently_verified"])
        self.assertFalse(result["slice_semantics_independently_verified"])
        return result

    def review(self, value, facet, basis, reason, *, descriptions=None):
        before = copy.deepcopy(value)
        labels = fixtures.reviews(facet, basis)
        labels[facet]["reason"] = reason
        if descriptions:
            labels[facet].update(descriptions)
        result = audit_reviewed_prediction(self.normalize(value)["annotation"], labels,
            demand_body="\n\n".join(value[2].values()), operation_body=value[3])
        self.assertEqual(value, before)
        self.assertEqual(result["review_origin"], "independent_review_not_automatically_inferred")
        self.assertFalse(result["changes_selection"])
        self.assertFalse(result["changes_qualification"])
        for key in ("accuracy", "quality_score", "correct_rejection", "false_negative"):
            self.assertNotIn(key, result)
        return result

    def abstain(self, value, facet, reason):
        result = copy.deepcopy(value)
        result[0]["facets"][facet] = fixtures.unknown()["facets"][facet]
        result[0]["facets"][facet]["reason"] = reason
        return result

    def test_same_documented_constructor_can_return_empty_or_nonempty(self):
        self.assertEqual(documented_empty(None, lambda: ""), "")
        self.assertEqual(documented_empty(None, lambda: "not empty"), "not empty")
        marker = object()
        self.assertIs(documented_empty(None, lambda: marker), marker)

    def test_docstring_is_preserved_but_not_actual_empty_result_proof(self):
        for facet in ("output", "outcome"):
            value = value_for(documented_empty, "For None, return an empty string.", facet,
                "Actual empty string for None", "None branch produces an empty string")
            self.assertIn('"""For None, return an empty string."""', value[3])
            result = self.review(value, facet, "unseen_delegate",
                "The branch calls an unseen constructor; repeating its docstring does not demonstrate empty contents.")
            self.assertEqual(result["issues"], [{"facet": facet, "kind": "delegate_contract_not_established"}])

    def test_explicit_declared_contract_alignment_remains_permissible(self):
        value = value_for(documented_empty, "The documented contract declares an empty string for None.",
            "output", "Declared empty-string contract for None",
            "Docstring declares an empty string for None; actual constructor result not certified")
        result = self.review(value, "output", "observed_alignment",
            "Only two explicitly declared contracts are compared, not demonstrated constructor behavior.")
        self.assertEqual(result["issues"], [])
        self.assertFalse(self.normalize(value)["summary"]["partial_outcome_hint"])

    def test_visible_none_dispatch_is_not_lost_with_unseen_constructor(self):
        calls = []
        def constructor():
            calls.append("called")
            return "result"
        marker = object()
        self.assertIs(documented_empty(marker, constructor), marker)
        self.assertEqual(calls, [])
        self.assertEqual(documented_empty(None, constructor), "result")
        self.assertEqual(calls, ["called"])
        value = value_for(documented_empty, "Dispatch None to the constructor.", "outcome",
            "Dispatch None to constructor", "Explicit None branch calls constructor")
        self.assertEqual(self.review(value, "outcome", "observed_alignment",
            "The supplied branch establishes dispatch only, not the constructor's returned contents.")["issues"], [])

    def test_constructor_gap_abstention_is_preserved_without_repair(self):
        value = value_for(documented_empty, "For None, return an empty string.", "output", "", "")
        value = self.abstain(value, "output", "Constructor contents are not in the selected body.")
        checked = self.normalize(value)
        self.assertEqual(checked["summary"]["unknown_facets"], list(FACETS))
        self.assertFalse(checked["summary"]["partial_outcome_hint"])
        self.assertIsNone(checked["slice_description"])
        self.assertEqual(self.review(value, "output", "unseen_delegate",
            "Keep the missing result contract unknown.")["issues"], [])

    def test_same_documented_chunk_wrapper_allows_list_or_tuple_results(self):
        values = [1, 2]
        self.assertEqual(documented_chunks(values, lambda items: [list(items)]), [[1, 2]])
        self.assertEqual(documented_chunks(values, lambda items: [tuple(items)]), [(1, 2)])

    def test_list_chunk_claim_needs_delegate_contract_not_repeated_docs(self):
        value = value_for(documented_chunks, "Return list-valued chunks.", "output",
            "Observed list-valued chunks", "List-valued chunks because the docstring says so")
        result = self.review(value, "output", "unseen_delegate",
            "The supplied wrapper only forwards to a producer; its list-valued return contract is unseen.")
        self.assertEqual(result["issues"], [{"facet": "output", "kind": "delegate_contract_not_established"}])

    def test_missing_chunk_type_proof_is_not_proof_of_tuple_output(self):
        value = value_for(documented_chunks, "Return list-valued chunks.", "output",
            "List-valued chunks", "Different tuple output inferred from missing list proof", relation="different")
        self.assertEqual(self.review(value, "output", "unseen_delegate",
            "Both list and tuple producers are possible; absence of list proof establishes neither actual type.")["issues"],
            [{"facet": "output", "kind": "delegate_contract_not_established"}])

    def test_conditional_delegate_can_preserve_comma_or_change_separator(self):
        self.assertEqual(conditional_separator("1,234", False, lambda: ","), "1,234")
        self.assertEqual(conditional_separator("1,234", False, lambda: ";"), "1;234")
        self.assertEqual(conditional_separator("1234", False, lambda: ";"), "1234")

    def test_possible_separator_difference_is_not_established_difference(self):
        for facet in ("output", "outcome"):
            value = value_for(conditional_separator, "Keep comma separators in formatted text.", facet,
                "Preserve comma separators", "Different separator because a conditional helper can supply one",
                relation="different")
            result = self.review(value, facet, "not_established",
                "A reachable translation path with unknown helper values can preserve or change commas; no actual differing result is established.")
            self.assertEqual(result["issues"], [{"facet": facet, "kind": "relation_not_established_by_review"}])

    def test_possible_preservation_is_not_universal_alignment(self):
        value = value_for(conditional_separator, "Keep comma separators for all supported calls.", "output",
            "Always preserve comma separators", "All branches preserve commas because the default branch does")
        self.assertEqual(self.review(value, "output", "not_established",
            "The helper branch has no supplied result contract; default-path preservation cannot certify all calls.")["issues"],
            [{"facet": "output", "kind": "relation_not_established_by_review"}])

    def test_explicit_default_branch_alignment_does_not_certify_helper_branch(self):
        def unused():
            raise AssertionError("Default branch must not call helper")
        self.assertEqual(conditional_separator("1,234", True, unused), "1,234")
        value = value_for(conditional_separator, "On the default branch, preserve commas.", "output",
            "Preserve commas when use_default is true", "Visible default branch replaces comma by comma")
        self.assertEqual(self.review(value, "output", "observed_alignment",
            "Only the explicit default branch is compared; other calls remain outside this property.")["issues"], [])
        self.assertFalse(self.normalize(value)["summary"]["partial_outcome_hint"])

    def test_unseen_helper_branch_abstention_stays_unknown(self):
        value = value_for(conditional_separator, "Keep comma separators for all calls.", "outcome", "", "")
        value = self.abstain(value, "outcome", "Helper values are unseen; the conditional branch may preserve or change commas.")
        self.assertEqual(self.review(value, "outcome", "not_established",
            "Unknown retains the evidence gap rather than asserting a counterexample.")["issues"], [])
        self.assertFalse(self.normalize(value)["summary"]["partial_outcome_hint"])

    def test_literal_counterexample_supports_bounded_difference(self):
        self.assertEqual(literal_separator("1,234"), "1;234")
        value = value_for(literal_separator, "For the input 1,234, preserve the comma.", "output",
            "Return 1,234 for the specified input", "Visible literal translation returns 1;234 for that input",
            relation="different")
        self.assertEqual(self.review(value, "output", "observed_difference",
            "A literal semicolon replacement establishes this specific differing result, not a runtime ban.")["issues"], [])

    def test_literal_translation_does_not_imply_every_input_changes(self):
        self.assertEqual(literal_separator("1234"), "1234")
        value = value_for(literal_separator, "Preserve formatted text.", "outcome",
            "Preserve text", "Every input necessarily changes", relation="different")
        self.assertEqual(self.review(value, "outcome", "not_established",
            "Inputs without commas remain unchanged; the literal branch does not justify the asserted universal difference.")["issues"],
            [{"facet": "outcome", "kind": "relation_not_established_by_review"}])

    def test_strict_length_check_is_visible_despite_unseen_chunk_producer(self):
        with self.assertRaisesRegex(ValueError, "Incomplete chunk"):
            list(checked_chunks([1], 2, True, lambda values, size: [values]))
        self.assertEqual(list(checked_chunks([1], 2, False, lambda values, size: [values])), [[1]])
        self.assertEqual(list(checked_chunks([1, 2], 2, True, lambda values, size: [values])), [[1, 2]])
        value = value_for(checked_chunks, "Reject incomplete chunks in strict mode and provide list-valued grouping.",
            "outcome", "Reject a yielded chunk shorter than the requested size in strict mode",
            "Visible strict length check raises on a mismatching yielded chunk", relation="slice")
        descriptions = {"requested_part": "Strict length validation of yielded chunks",
            "existing_behavior": "Raise for strict and mismatching chunk length",
            "remaining_work": "Producer result type, grouping semantics and adoption remain unestablished"}
        value[0]["facets"]["outcome"].update(descriptions)
        self.assertEqual(self.review(value, "outcome", "requested_suboperation",
            "The visible check supports only the requested validation suboperation, not unseen producer behavior.",
            descriptions=descriptions)["issues"], [])
        self.assertTrue(self.normalize(value)["summary"]["partial_outcome_hint"])

    def test_partial_check_cannot_certify_complete_grouping(self):
        value = value_for(checked_chunks, "Provide list-valued groups of size two.", "outcome",
            "Complete list-valued grouping", "Strict length check proves complete list-valued grouping")
        self.assertEqual(self.review(value, "outcome", "unseen_delegate",
            "Checking supplied lengths does not implement grouping or establish the producer's chunk type.")["issues"],
            [{"facet": "outcome", "kind": "delegate_contract_not_established"}])

    def test_abstention_never_becomes_a_scored_error_or_forced_slice(self):
        value = value_for(literal_separator, "For 1,234 preserve commas.", "output", "", "")
        value = self.abstain(value, "output", "Authored abstention, not a model-quality measurement.")
        self.assertEqual(self.review(value, "output", "observed_difference",
            "This fixture has a visible contrast; the raw abstention remains unchanged, not repaired or scored.")["issues"], [])
        self.assertEqual(self.normalize(value)["summary"]["unknown_facets"], list(FACETS))
