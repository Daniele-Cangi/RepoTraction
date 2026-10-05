"""Authored source-reading controls, not a parser or model-quality measurement.

Execute only these Python fixtures with our own inert callbacks. Their witnesses
inform explicit independent reviewer labels; the audit does not infer labels or
inspect unknown-reason truth. No prompt, schema, normalizer or production change.
"""
import copy
import inspect
import unittest

from scripts import missing_link_triage_branch_prompt as task
from scripts.missing_link_triage_contract import FACETS
from scripts.missing_link_triage_evidence import audit_reviewed_prediction
import test_missing_link_triage_properties as fixtures


def make_copy_guard(copy_func):
    def wrapper(src, dst, *, newer=False):
        if newer:
            return dst
        return copy_func(src, dst)
    return wrapper


def assemble_envelope(value, get_timestamp, get_signature):
    timestamp = str(get_timestamp())
    payload = value + "|" + timestamp
    return payload + "|" + get_signature(payload)


def forward_proof(value, proof_func):
    return proof_func(value)


MECHANISM_DEMAND = (
    "The requested entrypoint directly invokes an external-proof command on the "
    "tag hash and publishes the resulting proof file."
)


def value_for(operation, demand, facet, demanded, offered, *,
              relation="different", layer="selected_entrypoint"):
    body = inspect.getsource(operation)
    value = fixtures.fixture(demand, body, facet, demanded, offered,
        relation=relation, layer=layer, path="authored_layers.py")
    value[1]["selected_entrypoint"] = f"authored_layers.py:{operation.__name__}"
    return value


class LayerMechanismTests(unittest.TestCase):
    def compare(self, value):
        before = copy.deepcopy(value)
        raw, data, sources, body, spans = value
        checked = task.normalize_prediction(raw, data, demand_sources=sources,
            operation_body=body, operation_spans=spans)
        self.assertEqual(checked, fixtures.normalize(value))
        self.assertEqual(value, before)
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
        labels = fixtures.reviews(facet, basis)
        labels[facet]["reason"] = reason
        result = audit_reviewed_prediction(self.compare(value)["annotation"], labels,
            demand_body="\n\n".join(value[2].values()), operation_body=value[3])
        self.assertEqual(value, before)
        self.assertEqual(result["review_origin"], "independent_review_not_automatically_inferred")
        self.assertFalse(result["changes_selection"])
        self.assertFalse(result["changes_qualification"])
        for key in ("accuracy", "correct_rejection", "false_negative", "quality_score"):
            self.assertNotIn(key, result)
        return result

    def supported(self, value, facet, reason, basis="observed_difference"):
        self.assertEqual(self.review(value, facet, basis, reason)["issues"], [])
        return self.compare(value)

    def unsupported(self, value, facet, basis, reason, kind):
        # Wrong semantic declarations can pass provenance checks unchanged.
        self.assertNotEqual(self.compare(value)["annotation"]["facets"][facet]["relation"], "unknown")
        result = self.review(value, facet, basis, reason)
        self.assertFalse(result["semantic_consistent_with_review"])
        self.assertEqual(result["issues"], [{"facet": facet, "kind": kind}])

    def test_factory_creation_returns_callable_without_invoking_copy(self):
        calls = []
        wrapper = make_copy_guard(lambda src, dst: calls.append((src, dst)))
        self.assertTrue(callable(wrapper))
        self.assertEqual(calls, [])
        self.assertEqual(list(inspect.signature(make_copy_guard).parameters), ["copy_func"])
        self.assertEqual(list(inspect.signature(wrapper).parameters), ["src", "dst", "newer"])

    def test_factory_callable_input_alignment_stays_at_entrypoint(self):
        value = value_for(make_copy_guard, "The factory accepts a copy callback.", "input",
            "Copy callback as factory input", "copy_func is the factory parameter", relation="aligned")
        checked = self.supported(value, "input", "The selected factory's signature takes copy_func, not src/dst.",
            "observed_alignment")
        self.assertEqual(checked["comparison_declarations"]["input"]["operation_layer"], "selected_entrypoint")

    def test_returned_callable_input_alignment_names_its_own_layer(self):
        value = value_for(make_copy_guard, "The returned callable accepts source and destination paths.", "input",
            "Source/destination parameters on returned callable", "src/dst on wrapper; newer is keyword-only",
            relation="aligned", layer="returned_callable")
        checked = self.supported(value, "input", "The nested wrapper visibly takes src/dst and is returned by the factory.",
            "observed_alignment")
        self.assertEqual(checked["comparison_declarations"]["input"]["operation_layer"], "returned_callable")

    def test_factory_result_is_callable_not_destination_path(self):
        value = value_for(make_copy_guard, "The requested entrypoint directly returns a destination path.", "output",
            "Destination path directly from entrypoint", "A wrapper callable directly from factory")
        self.supported(value, "output", "return wrapper is the selected factory result; the wrapper result is another layer.")

    def test_wrapper_arguments_cannot_be_claimed_as_factory_input(self):
        value = value_for(make_copy_guard, "The requested entrypoint accepts source and destination paths.", "input",
            "src/dst directly on entrypoint", "The selected factory accepts src/dst", relation="aligned")
        self.unsupported(value, "input", "unresolved_interface_layer",
            "Only the returned wrapper takes src/dst; the selected factory takes copy_func.",
            "interface_layer_not_established")

    def test_wrapper_result_cannot_be_claimed_as_factory_output(self):
        value = value_for(make_copy_guard, "The requested entrypoint directly returns the destination path.", "output",
            "Destination path directly from entrypoint", "The factory directly returns dst or the copy result",
            relation="aligned")
        self.unsupported(value, "output", "unresolved_interface_layer",
            "The selected factory returns a callable; dst/delegate returns occur in that callable.",
            "interface_layer_not_established")

    def test_wrapper_skip_branch_can_support_its_own_bounded_result(self):
        sentinel = object()
        calls = []
        wrapper = make_copy_guard(lambda src, dst: calls.append((src, dst)))
        self.assertIs(wrapper("source", sentinel, newer=True), sentinel)
        self.assertEqual(calls, [])
        value = value_for(make_copy_guard, "On its newer=True branch, the returned callable returns dst unchanged.",
            "output", "dst unchanged on wrapper's newer=True branch", "dst unchanged on wrapper's newer=True branch",
            relation="aligned", layer="returned_callable")
        self.supported(value, "output", "The explicitly bounded wrapper branch directly returns dst without calling the delegate.",
            "observed_alignment")

    def test_non_skip_wrapper_delegate_result_remains_unestablished(self):
        value = value_for(make_copy_guard, "The non-skip returned callable must return a proof dictionary.", "output",
            "Proof dictionary from returned callable", "Alleged flat text result of copy_func",
            layer="returned_callable")
        self.unsupported(value, "output", "unseen_delegate",
            "The non-skip wrapper returns copy_func's result; that delegate contract is unseen.",
            "delegate_contract_not_established")

    def test_unknown_explanation_defect_is_not_detected_or_repaired_by_relation_audit(self):
        value = value_for(make_copy_guard, "Atomically publish the copied file.", "input", "", "")
        value[0].clear()
        value[0].update(fixtures.unknown())
        value[0]["facets"]["input"]["reason"] = "The selected factory takes src and dst; their contract is unknown."
        before = copy.deepcopy(value)
        # Independent witness contradicts this explanation; do not pretend the
        # existing relation audit has an unknown-reason classifier.
        self.assertEqual(list(inspect.signature(make_copy_guard).parameters), ["copy_func"])
        result = self.review(value, "input", "unresolved_interface_layer",
            "The abstention reason confuses the factory with the returned wrapper.")
        self.assertEqual(result["issues"], [])
        self.assertEqual(result["syntactic_summary"]["unknown_facets"], list(FACETS))
        self.assertEqual(value, before)

    def test_visible_envelope_mechanism_contrast_does_not_resolve_delegates(self):
        value = value_for(assemble_envelope, MECHANISM_DEMAND, "outcome",
            "Direct proof-command invocation and proof publication in the requested entrypoint",
            "Visible entrypoint calls timestamp/signature callbacks and assembles delimited text; helper internals unknown")
        checked = self.supported(value, "outcome",
            "The cited request specifies direct entrypoint steps; the supplied body shows a different local composition. This does not rule out external work inside a callback or reject the full workflow.")
        self.assertFalse(checked["summary"]["partial_outcome_hint"])
        self.assertEqual(checked["annotation"]["facets"]["output"]["relation"], "unknown")

    def test_envelope_trace_witness_establishes_only_authored_composition(self):
        calls = []
        def timestamp():
            calls.append("timestamp")
            return 12
        def signature(payload):
            calls.append(("signature", payload))
            return "sig"
        self.assertEqual(assemble_envelope("value", timestamp, signature), "value|12|sig")
        self.assertEqual(calls, ["timestamp", ("signature", "value|12")])

    def test_same_visible_body_does_not_fix_callback_results(self):
        # Both callbacks are inert fixtures. Their different marker values are
        # witnesses of dependence, not tests of any actual external service.
        first = assemble_envelope("tag", lambda: "first-marker", lambda payload: "first-signature")
        other = assemble_envelope("tag", lambda: "other-marker", lambda payload: "other-signature")
        self.assertEqual(first, "tag|first-marker|first-signature")
        self.assertEqual(other, "tag|other-marker|other-signature")
        self.assertNotEqual(first, other)

    def test_timestamp_name_cannot_prove_local_clock_or_no_external_call(self):
        value = value_for(assemble_envelope, "Externally anchor the tag hash.", "outcome",
            "External anchoring", "Timestamp callback always uses a local clock and never contacts an external service")
        self.unsupported(value, "outcome", "unseen_delegate",
            "The callback implementations are unseen; their names establish no clock or network policy.",
            "delegate_contract_not_established")

    def test_envelope_assembly_is_not_certified_as_external_proof_slice(self):
        value = value_for(assemble_envelope, "Create an independently verifiable external proof for the tag hash.",
            "outcome", "Create external proof", "Assemble timestamp/signature callbacks into text", relation="slice")
        value[0]["facets"]["outcome"].update(requested_part="External proof",
            existing_behavior="Call timestamp/signature callbacks", remaining_work="Publish proof")
        self.unsupported(value, "outcome", "unseen_delegate",
            "Assembly alone does not establish the requested external proof; helper internals remain unseen.",
            "delegate_contract_not_established")

    def test_pure_proof_forwarder_does_not_establish_proof_result_contract(self):
        value = value_for(forward_proof, "Return an independently verifiable external proof.", "output",
            "External proof result", "Alleged external proof from the proof_func name", relation="aligned")
        self.unsupported(value, "output", "unseen_delegate",
            "The body forwards to proof_func; neither its result nor verification policy is supplied.",
            "delegate_contract_not_established")

    def test_supported_local_mechanism_can_still_abstain_without_score_or_forced_label(self):
        value = value_for(assemble_envelope, MECHANISM_DEMAND, "outcome", "", "")
        value[0].clear()
        value[0].update(fixtures.unknown())
        before = copy.deepcopy(value)
        for basis in ("observed_difference", "unseen_delegate", "not_established"):
            result = self.review(value, "outcome", basis,
                "A narrow visible composition can be described; full external behavior is unresolved. Preserve this raw abstention.")
            self.assertEqual(result["issues"], [])
            self.assertEqual(result["syntactic_summary"]["unknown_facets"], list(FACETS))
            self.assertFalse(result["syntactic_summary"]["partial_outcome_hint"])
        self.assertEqual(value, before)
