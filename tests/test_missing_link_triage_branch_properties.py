"""Authored offline controls for branch returns and local property comparison.

The two Python functions below are our synthetic fixtures, not acquired code.
Their small executable witnesses inform explicit reviewer labels; the existing
audit does NOT infer those labels or grade Luna. Production and old cards stay
unchanged. No network, provider configuration or model call is involved.
"""
import copy
import inspect
import unittest

from scripts import missing_link_triage_property_prompt as task
from scripts.missing_link_triage_contract import FACETS
from scripts.missing_link_triage_evidence import audit_reviewed_prediction
import test_missing_link_triage_properties as fixtures


def encode_or_pass_through(value: str | bytes, encoding: str = "utf-8", errors: str = "strict") -> bytes:
    if isinstance(value, str):
        value = value.encode(encoding, errors)
    return value


def filename_predicate(path: str, pattern: str) -> bool:
    if path == pattern:
        return True
    return False


def value_for(demand, facet, demanded, offered, *, operation=encode_or_pass_through, relation="different"):
    # The cited source and executed authored fixture cannot silently diverge.
    body = inspect.getsource(operation)
    value = fixtures.fixture(demand, body, facet, demanded, offered, relation=relation, path="authored.py")
    value[1]["selected_entrypoint"] = f"authored.py:{operation.__name__}"
    return value


class BranchPropertyTests(unittest.TestCase):
    def compare(self, value):
        before = copy.deepcopy(value)
        raw, data, sources, body, spans = value
        checked = task.normalize_prediction(raw, data, demand_sources=sources,
            operation_body=body, operation_spans=spans)
        self.assertEqual(value, before)
        self.assertEqual(checked, fixtures.normalize(value))
        self.assertEqual(checked["summary"]["status"], "context_required")
        self.assertFalse(checked["summary"]["demand_complete"])
        self.assertFalse(checked["summary"]["changes_selection"])
        self.assertFalse(checked["summary"]["changes_qualification"])
        self.assertFalse(checked["comparison_semantics_independently_verified"])
        self.assertFalse(checked["slice_semantics_independently_verified"])
        self.assertEqual(checked["annotation"]["facets"]["runtime"]["relation"], "unknown")
        return checked

    def review(self, value, facet, basis, reason):
        before = copy.deepcopy(value)
        reviewed = fixtures.reviews(facet, basis)
        reviewed[facet]["reason"] = reason
        result = audit_reviewed_prediction(self.compare(value)["annotation"], reviewed,
            demand_body="\n\n".join(value[2].values()), operation_body=value[3])
        self.assertEqual(value, before)
        self.assertEqual(result["review_origin"], "independent_review_not_automatically_inferred")
        self.assertFalse(result["changes_selection"])
        self.assertFalse(result["changes_qualification"])
        return result

    def assert_supported(self, value, facet, reason, basis="observed_difference"):
        result = self.review(value, facet, basis, reason)
        self.assertTrue(result["semantic_consistent_with_review"])
        self.assertEqual(result["issues"], [])
        return self.compare(value)

    def assert_unestablished(self, value, facet, reason):
        # Mechanical acceptance is intentionally not semantic certification.
        self.assertEqual(self.compare(value)["annotation"]["facets"][facet]["relation"], "different")
        result = self.review(value, facet, "not_established", reason)
        self.assertFalse(result["semantic_consistent_with_review"])
        self.assertEqual(result["issues"], [{"facet": facet, "kind": "relation_not_established_by_review"}])

    def test_declared_scalar_input_contrast_does_not_reject_runtime_collections(self):
        mixed = ["text", b"bytes"]
        self.assertIs(encode_or_pass_through(mixed), mixed)
        value = value_for("The requested callback declares a mixed-collection input.", "input",
            "Declared mixed-collection input", "Declared scalar str or bytes input; runtime acceptance not asserted")
        self.assert_supported(value, "input", "The annotation declares scalar str or bytes, not a collection; the body does not reject collections.")

    def test_declared_bytes_output_contrast_does_not_claim_all_actual_returns(self):
        value = value_for("The requested callback declares an object-array result.", "output",
            "Declared object-array result", "Declared bytes return annotation; actual branch returns not asserted")
        self.assertIn("-> bytes", value[3])
        self.assert_supported(value, "output", "This contrasts two declared contracts only, not actual returns for arbitrary values.")

    def test_explicit_string_branch_has_bytes_output_without_whole_task_parity(self):
        self.assertEqual(encode_or_pass_through("caf\u00e9"), b"caf\xc3\xa9")
        value = value_for("For a string input the requested callback returns UTF-8 bytes.", "output",
            "For string input return UTF-8 bytes", "For str input encode to UTF-8 bytes", relation="aligned")
        checked = self.assert_supported(value, "output", "The supplied branch encodes strings using the default UTF-8 encoding.", "observed_alignment")
        self.assertFalse(checked["summary"]["partial_outcome_hint"])
        self.assertEqual(checked["annotation"]["facets"]["outcome"]["relation"], "unknown")

    def test_bytes_input_takes_identity_return_branch(self):
        value = b"already encoded"
        self.assertIs(encode_or_pass_through(value), value)
        self.assertIs(encode_or_pass_through(value, encoding="not-a-codec"), value)
        # Only the string branch invokes the encoding; no claim about NumPy dtype behavior.

    def test_non_string_witnesses_disprove_unconditional_bytes_return(self):
        mixed = ["text", b"bytes", 3]
        original = copy.deepcopy(mixed)
        for value in (mixed, {"key": "value"}, object(), 42, None):
            with self.subTest(kind=type(value).__name__):
                returned = encode_or_pass_through(value)
                self.assertIs(returned, value)
                self.assertNotIsInstance(returned, bytes)
        self.assertEqual(mixed, original)

    def test_unqualified_bytes_output_claim_needs_review_despite_valid_citation(self):
        mixed = ["text", b"bytes"]
        self.assertIs(encode_or_pass_through(mixed), mixed)
        value = value_for("Return an object array preserving mixed values.", "output",
            "Object-array output", "The body always returns bytes rather than a collection")
        self.assert_unestablished(value, "output", "A non-string list returns unchanged. The annotation cannot prove the asserted unconditional bytes result or object-array incompatibility.")

    def test_unqualified_bytes_behavior_claim_cannot_borrow_string_branch(self):
        value = value_for("Detect mixed types and preserve the collection when mixed.", "outcome",
            "Detect mixture and preserve mixed collection", "Always encode input into bytes instead of preserving a mixed collection")
        self.assertIs(encode_or_pass_through(None), None)
        self.assert_unestablished(value, "outcome", "Only strings are encoded; non-string inputs return unchanged. That branch cannot establish the stated universal behavior contrast or the complete requested dtype policy.")

    def test_runtime_collection_rejection_is_not_established_by_annotation(self):
        value = value_for("The requested callback accepts mixed collections at runtime.", "input",
            "Accept mixed collections at runtime", "Reject all collections at runtime because str or bytes is annotated")
        mixed = ["text", b"bytes"]
        self.assertIs(encode_or_pass_through(mixed), mixed)
        self.assert_unestablished(value, "input", "The authored function accepts this non-string collection unchanged. A declared scalar type is not an enforced rejection policy.")

    def test_string_encoding_is_not_a_mixed_collection_detection_slice(self):
        value = value_for("Detect mixtures within and between collections, preserving mixed values.", "outcome",
            "Mixed-collection detection", "Encode a string or pass through a non-string", relation="slice")
        value[0]["facets"]["outcome"].update(requested_part="Detect mixed types",
            existing_behavior="Encode a string", remaining_work="Collection integration")
        self.assertEqual(self.compare(value)["annotation"]["facets"]["outcome"]["relation"], "slice")
        reviewed = fixtures.reviews("outcome", "not_established")
        reviewed["outcome"]["reason"] = "No mixture detector is present; passing through a collection does not establish its requested dtype policy."
        result = fixtures.audit(value, reviewed)
        self.assertEqual(result["issues"], [{"facet": "outcome", "kind": "relation_not_established_by_review"}])

    def test_grep_command_output_contrast_needs_no_prior_implementation_identity(self):
        value = value_for("The requested callback returns command text such as grep -P -A 2 -B 1 -C 3 -e first -e second.",
            "output", "Return a grep command string", "Return a filename-matching boolean", operation=filename_predicate)
        self.assertIs(filename_predicate("example.txt", "example.txt"), True)
        self.assertIs(filename_predicate("example.md", "example.txt"), False)
        checked = self.assert_supported(value, "output", "The demand specifies textual command output; both visible predicate branches return literal booleans, not a command string.")
        self.assertEqual(checked["summary"]["different_facets"], ["output"])
        self.assertNotIn("implementation_verified", value[0])
        self.assertNotIn("implementation_verified", value[1])

    def test_grep_construction_vs_filename_matching_is_behavior_not_runtime(self):
        value = value_for("The requested callback constructs grep commands with context flags and multiple -e patterns.",
            "outcome", "Construct grep commands and their options", "Match a filename against a pattern and return a boolean", operation=filename_predicate)
        self.assert_supported(value, "outcome", "The visible operation is filename matching, not construction of the explicitly requested command text; this proves no execution-environment ban.")

    def test_grep_abstention_remains_abstention_not_repaired_or_scored(self):
        value = value_for("The requested callback returns a grep command string.", "output",
            "Command string", "Boolean", operation=filename_predicate)
        value[0]["facets"]["output"] = fixtures.unknown()["facets"]["output"]
        value[0]["facets"]["output"]["reason"] = "Prior implementation relationship not established"
        before = copy.deepcopy(value)
        for basis in ("observed_difference", "not_established"):
            result = self.review(value, "output", basis, "A supported local contrast is available but this raw card abstains; no error or quality score is assigned.")
            self.assertEqual(result["issues"], [])
            self.assertEqual(result["syntactic_summary"]["unknown_facets"], list(FACETS))
            for key in ("accuracy", "correct_rejection", "false_negative", "quality_score"):
                self.assertNotIn(key, result)
        self.assertEqual(value, before)

    def test_filename_matching_cannot_be_certified_as_grep_command_slice(self):
        value = value_for("Generate grep commands with -P and context flags.", "outcome",
            "Generate grep command options", "Match a filename pattern", operation=filename_predicate, relation="slice")
        value[0]["facets"]["outcome"].update(requested_part="Generate command options",
            existing_behavior="Match filename pattern", remaining_work="Integrate command generator")
        result = self.review(value, "outcome", "analogy", "Pattern vocabulary alone does not implement an explicitly requested command-generation suboperation.")
        self.assertEqual(result["issues"], [{"facet": "outcome", "kind": "analogy_is_not_suboperation"}])

    def test_real_delegate_gap_and_mean_slice_survive_the_control_cases(self):
        delegated = fixtures.fixture("Return nested keys.", "function operation(values) { return unseen(values); }",
            "output", "Nested keys", "Alleged flat list")
        delegated[0]["facets"]["output"] = fixtures.unknown()["facets"]["output"]
        checked = self.compare(delegated)
        self.assertEqual(checked["summary"]["unknown_facets"], list(FACETS))
        self.assertFalse(checked["summary"]["partial_outcome_hint"])

        mean = fixtures.fixture("Profile rows, including their average and other statistics.",
            "function operation(rows) { let sum = 0; for (const x of rows) sum += x; return sum / rows.length; }",
            "outcome", "Average of rows", "Sum divided by count", relation="slice")
        mean[0]["facets"]["outcome"].update(requested_part="Arithmetic mean",
            existing_behavior="Sum divided by count", remaining_work="Other statistics and adoption")
        self.assertTrue(self.compare(mean)["summary"]["partial_outcome_hint"])
