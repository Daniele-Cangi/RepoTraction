"""Authored no-spend witnesses for declaration failures and explanation limits.

No retained model card is edited or used as a gold label. Execute only our own
fixtures and inert callbacks. Normalization proves shape/provenance, not the
truth of a reason. In particular, the existing review audit does not classify
unknown reasons. Prompt, schema, normalizer and production gates stay unchanged.
"""
import copy
import inspect
import unittest

from missing_link.contracts import validate_shape
from scripts import missing_link_triage_layer_prompt as task
from scripts.missing_link_triage_contract import FACETS
from scripts.missing_link_triage_evidence import audit_reviewed_prediction
import test_missing_link_triage_properties as fixtures
from test_missing_link_triage_branch_properties import encode_or_pass_through


def average_numbers(values):
    return sum(values) / len(values) if values else None


def forward_encoding(value, serialize, encode) -> bytes:
    intermediate = serialize(value)
    return encode(intermediate)


def value_for(operation, demand, facet, demanded, offered, *, relation="different"):
    body = inspect.getsource(operation)
    value = fixtures.fixture(demand, body, facet, demanded, offered,
        relation=relation, path="authored_result_controls.py")
    value[1]["selected_entrypoint"] = f"authored_result_controls.py:{operation.__name__}"
    return value


def mean_slice():
    value = value_for(average_numbers, "Profile numeric rows, including an arithmetic average and other statistics.",
        "outcome", "Compute an arithmetic average of numeric rows",
        "For nonempty numeric rows return sum divided by length", relation="slice")
    value[0]["facets"]["outcome"].update(requested_part="Arithmetic average",
        existing_behavior="Sum divided by length for nonempty numeric rows",
        remaining_work="Numeric edge cases, other statistics and integration")
    return value


class LayerResultControls(unittest.TestCase):
    def normalize(self, value):
        before = copy.deepcopy(value)
        raw, data, sources, body, spans = value
        try:
            checked = task.normalize_prediction(raw, data, demand_sources=sources,
                operation_body=body, operation_spans=spans)
        finally:
            self.assertEqual(value, before)
        self.assertEqual(checked["summary"]["status"], "context_required")
        self.assertFalse(checked["summary"]["changes_selection"])
        self.assertFalse(checked["summary"]["changes_qualification"])
        self.assertFalse(checked["comparison_semantics_independently_verified"])
        self.assertFalse(checked["slice_semantics_independently_verified"])
        return checked

    def review(self, value, facet, basis, reason):
        before = copy.deepcopy(value)
        labels = fixtures.reviews(facet, basis)
        labels[facet]["reason"] = reason
        result = audit_reviewed_prediction(self.normalize(value)["annotation"], labels,
            demand_body="\n\n".join(value[2].values()), operation_body=value[3])
        self.assertEqual(value, before)
        self.assertEqual(result["review_origin"], "independent_review_not_automatically_inferred")
        self.assertFalse(result["changes_selection"])
        self.assertFalse(result["changes_qualification"])
        for key in ("accuracy", "correct_rejection", "false_negative", "quality_score"):
            self.assertNotIn(key, result)
        return result

    def abstention(self, value, facet, reason):
        value = copy.deepcopy(value)
        value[0]["facets"][facet] = fixtures.unknown()["facets"][facet]
        value[0]["facets"][facet]["reason"] = reason
        return value

    def test_fully_declared_mean_slice_remains_only_a_partial_hint(self):
        value = mean_slice()
        self.assertEqual(average_numbers([2, 4]), 3)
        self.assertIsNone(average_numbers([]))
        checked = self.normalize(value)
        self.assertTrue(checked["summary"]["partial_outcome_hint"])
        self.assertEqual(checked["annotation"]["facets"]["outcome"]["relation"], "slice")
        self.assertEqual(checked["comparison_declarations"]["outcome"]["demand_property"],
            value[0]["facets"]["outcome"]["demand_property"])

    def test_slice_descriptions_cannot_replace_either_or_both_empty_properties(self):
        for fields in (("demand_property",), ("operation_property",), ("demand_property", "operation_property")):
            value = mean_slice()
            for field in fields:
                value[0]["facets"]["outcome"][field] = ""
            with self.subTest(fields=fields):
                # The existing provider shape allows empty strings; local guards do not.
                validate_shape(value[0], task.schema_for_context(value[1]))
                with self.assertRaisesRegex(ValueError, "bounded concrete property declarations"):
                    self.normalize(value)
                self.assertTrue(all(value[0]["facets"]["outcome"][field]
                    for field in ("requested_part", "existing_behavior", "remaining_work")))

    def test_whitespace_property_is_not_repaired_from_reason_or_slice_text(self):
        for field in ("demand_property", "operation_property"):
            for blank in (" ", "\t\r\n", "\u2003"):
                value = mean_slice()
                value[0]["facets"]["outcome"][field] = blank
                with self.subTest(field=field, blank=repr(blank)), self.assertRaisesRegex(
                    ValueError, "bounded concrete property declarations"):
                    self.normalize(value)

    def test_property_character_boundary_applies_to_both_slice_properties(self):
        for field in ("demand_property", "operation_property"):
            value = mean_slice()
            value[0]["facets"]["outcome"][field] = "x" * 400
            self.assertTrue(self.normalize(value)["summary"]["partial_outcome_hint"])
            # Arbitrary accepted text is not independently verified source meaning.
            value[0]["facets"]["outcome"][field] += "x"
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "bounded concrete property declarations"):
                self.normalize(value)

    def test_omitted_property_key_is_not_equivalent_to_empty_unknown_declaration(self):
        for field in ("demand_property", "operation_property"):
            value = mean_slice()
            del value[0]["facets"]["outcome"][field]
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.normalize(value)

    def test_aligned_and_different_relations_also_require_both_properties(self):
        for facet in FACETS:
            for relation in ("aligned", "different"):
                for field in ("demand_property", "operation_property"):
                    value = value_for(average_numbers, "Compute an average of numeric values.", facet,
                        "Authored demand declaration", "Authored candidate declaration", relation=relation)
                    value[0]["facets"][facet][field] = ""
                    with self.subTest(facet=facet, relation=relation, field=field), self.assertRaisesRegex(
                        ValueError, "bounded concrete property declarations"):
                        self.normalize(value)

    def test_unknown_preserves_axis_and_requires_empty_properties_without_slice_credit(self):
        value = self.abstention(mean_slice(), "outcome", "The bounded comparison is not established.")
        checked = self.normalize(value)
        self.assertEqual(checked["summary"]["unknown_facets"], list(FACETS))
        self.assertFalse(checked["summary"]["partial_outcome_hint"])
        self.assertIsNone(checked["slice_description"])
        self.assertEqual(value[0]["facets"]["outcome"]["axis"], "requested_behavior")
        for field in ("demand_property", "operation_property"):
            changed = copy.deepcopy(value)
            changed[0]["facets"]["outcome"][field] = "Alleged property"
            with self.assertRaisesRegex(ValueError, "Unknown scope declarations must be empty"):
                self.normalize(changed)

    def test_invalid_slice_rejects_the_whole_card_without_salvaging_another_facet(self):
        value = mean_slice()
        value[0]["facets"]["input"] = value_for(average_numbers, value[2]["q0"], "input",
            "Numeric rows", "Numeric rows", relation="aligned")[0]["facets"]["input"]
        value[0]["facets"]["outcome"].update(demand_property="", operation_property="")
        before = copy.deepcopy(value)
        with self.assertRaisesRegex(ValueError, "bounded concrete property declarations"):
            self.normalize(value)
        self.assertEqual(value, before)
        self.assertEqual(value[0]["facets"]["input"]["relation"], "aligned")

    def test_unknown_branch_reason_pair_documents_no_automatic_truth_detection(self):
        value = value_for(encode_or_pass_through, "Detect mixed text/bytes inputs and preserve their original values.",
            "output", "", "")
        mixed = ["text", b"bytes"]
        before = copy.deepcopy(mixed)
        self.assertIs(encode_or_pass_through(mixed), mixed)
        self.assertEqual(mixed, before)
        for reason in ("The body always returns bytes; the requested output is unknown.",
                       "Only strings are encoded; non-strings pass through unchanged. The requested mixed-input policy is unseen."):
            pair = self.abstention(value, "output", reason)
            checked = self.normalize(pair)
            self.assertEqual(checked["annotation"]["facets"]["output"]["reason"], reason)
            reviewed = self.review(pair, "output", "not_established",
                "Our list witness disproves the first universal claim. The audit does not examine unknown-reason truth.")
            self.assertEqual(reviewed["issues"], [])
            self.assertEqual(reviewed["syntactic_summary"]["unknown_facets"], list(FACETS))

    def test_explicit_string_branch_can_support_a_bounded_output_alignment(self):
        self.assertEqual(encode_or_pass_through("text"), b"text")
        value = value_for(encode_or_pass_through, "For a string input, return UTF-8 encoded bytes.", "output",
            "For a string input return UTF-8 bytes", "For a string input encode using default UTF-8", relation="aligned")
        value[0]["facets"]["output"]["reason"] = "Both compared outputs are explicitly bounded to the string-input branch."
        reviewed = self.review(value, "output", "observed_alignment", "Our authored string branch and witness support only this bounded comparison.")
        self.assertEqual(reviewed["issues"], [])
        self.assertFalse(self.normalize(value)["summary"]["partial_outcome_hint"])

    def test_universal_bytes_claim_can_pass_shape_but_fail_explicit_source_review(self):
        value = value_for(encode_or_pass_through, "For mixed inputs preserve a collection.", "output",
            "Preserve mixed collection", "Always return bytes for every input")
        self.assertIsNone(encode_or_pass_through(None))
        reviewed = self.review(value, "output", "not_established", "The non-string branch returns None or a supplied collection unchanged; the bytes annotation is not enforcement.")
        self.assertEqual(reviewed["issues"], [{"facet": "output", "kind": "relation_not_established_by_review"}])

    def test_same_forwarder_body_does_not_fix_callback_result_type(self):
        calls = []
        def serializer(value):
            calls.append(("serialize", value))
            return ("intermediate", value)
        def encoder(value):
            calls.append(("encode", value))
            return "text-not-bytes"
        self.assertEqual(forward_encoding("input", serializer, encoder), "text-not-bytes")
        self.assertEqual(calls, [("serialize", "input"), ("encode", ("intermediate", "input"))])
        marker = ["unchanged callback result"]
        self.assertIs(forward_encoding("input", lambda value: value, lambda value: marker), marker)

    def test_unknown_delegate_reason_pair_is_retained_not_graded_or_repaired(self):
        value = value_for(forward_encoding, "Return a reversible encoding with a known decoder.", "output", "", "")
        for reason in ("The serialize and encode names prove serialization and a bytes output; reversibility is unknown.",
                       "The body forwards through two unseen callbacks; their observed output and decoder contracts remain unknown."):
            pair = self.abstention(value, "output", reason)
            checked = self.normalize(pair)
            self.assertEqual(checked["annotation"]["facets"]["output"]["reason"], reason)
            reviewed = self.review(pair, "output", "unseen_delegate", "Callback names and the bytes annotation do not establish actual output; this audit does not grade unknown explanations.")
            self.assertEqual(reviewed["issues"], [])
            self.assertFalse(checked["summary"]["partial_outcome_hint"])

    def test_declared_delegate_return_annotation_can_be_compared_without_certifying_actual_return(self):
        value = value_for(forward_encoding, "The requested entrypoint declares a bytes return type.", "output",
            "Declared bytes return type", "Declared bytes return annotation; callback results not certified", relation="aligned")
        value[0]["facets"]["output"]["reason"] = "This compares only the declared return annotation, not its runtime enforcement."
        self.assertIn("-> bytes", value[3])
        reviewed = self.review(value, "output", "observed_alignment", "Both sides explicitly name the declared contract; unseen callback behavior stays open.")
        self.assertEqual(reviewed["issues"], [])

    def test_observed_bytes_claim_from_delegate_names_requires_independent_review(self):
        value = value_for(forward_encoding, "Return bytes from the requested entrypoint.", "output",
            "Observed bytes result", "Callbacks always produce bytes because they are named serialize and encode", relation="aligned")
        reviewed = self.review(value, "output", "unseen_delegate", "Their implementations are not in the cited body; our inert alternate callbacks witness different possible results.")
        self.assertEqual(reviewed["issues"], [{"facet": "output", "kind": "delegate_contract_not_established"}])
