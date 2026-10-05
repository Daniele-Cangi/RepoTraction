"""One-request authored probe controls; mocked IO only, no real ledger/provider."""
import copy
import importlib
import json
import unittest
import urllib.error
from unittest.mock import patch

from missing_link.provider import Provider, ResponseError, CandidateValidationError
from scripts import missing_link_triage_native_probe as task
from scripts import missing_link_triage_declaration_schema as schema_task
from scripts.missing_link_triage_receipts import ReceiptPersistenceError
import test_missing_link_triage_properties as fixtures
from test_missing_link_triage_property_execution import Stream, event


class NativeProbeTests(unittest.TestCase):
    def simulate(self, terminal, *, identity_failure=False, reservation_failure=False,
                 receipt_failure=False, opener_failure=None):
        provider = Provider({"REPOTRACTION_AI_URL": "http://127.0.0.1:1", "REPOTRACTION_AI_MODEL": "gpt-6-luna",
            "REPOTRACTION_AI_API_KIND": "responses", "REPOTRACTION_AI_STREAMING": "1",
            "REPOTRACTION_AI_RESPONSE_FORMAT": "json_schema", "REPOTRACTION_AI_MAX_CALLS": "1",
            "REPOTRACTION_AI_MAX_OUTPUT_TOKENS": "6000", "REPOTRACTION_AI_INPUT_USD_PER_MILLION": ".1",
            "REPOTRACTION_AI_OUTPUT_USD_PER_MILLION": ".5"})
        self.reservations, self.jobs, self.receipts, self.results, self.identities, self.order = [], [], [], [], [], []
        def identity(*, force=False):
            self.identities.append(force)
            if identity_failure:
                raise RuntimeError("Account mismatch")
        def reserve(job, cost):
            if reservation_failure:
                raise ValueError("Original allowance cap")
            self.reservations.append((job, cost))
        def persist(job):
            self.jobs.append(copy.deepcopy(job))
        def retain(value):
            self.order.append("terminal")
            if receipt_failure:
                raise OSError("Private storage failure")
            self.receipts.append(copy.deepcopy(value))
        def record(result):
            self.order.append("result")
            self.results.append(copy.deepcopy(result))
        with patch("scripts.missing_link_triage_receipts.urllib.request.build_opener") as opener, \
             patch("os.getenv", side_effect=AssertionError("credentials")), \
             patch("sqlite3.connect", side_effect=AssertionError("real ledger")), \
             patch("socket.socket", side_effect=AssertionError("network")):
            opener.return_value.open.return_value = Stream(terminal)
            if opener_failure:
                opener.return_value.open.side_effect = opener_failure
            try:
                return task.execute_probe(provider, identity=identity, reserve=reserve, persist=persist,
                    retain_terminal=retain, record=record)
            finally:
                self.calls = opener.return_value.open.call_count
                if self.calls:
                    request = opener.return_value.open.call_args.args[0]
                    case = task.build_case()
                    _, _, encoded = provider._encode_prompt(task.PROMPT, case["data"],
                        task.schema_for_context(case["data"]), "analysis")
                    self.assertEqual(request.data, encoded)
                    self.assertEqual(json.loads(encoded)["text"]["format"]["schema"], schema_task.schema_for_context(case["data"]))
                    self.assertEqual(len(self.reservations), 1)
                    self.assertAlmostEqual(self.reservations[0][1], ((len(encoded) + 2048) * .1 + 6000 * .5) / 1e6)

    def slice_card(self):
        case = task.build_case()
        raw = fixtures.unknown()
        raw["facets"]["outcome"].update(relation="slice", comparison_scope="requested_operation",
            operation_layer="selected_entrypoint", demand_property="Compute sum of numeric values",
            operation_property="Return the supplied values' sum", demand_span_id=next(iter(case["data"]["demand_spans"])),
            operation_id="e0", requested_part="Sum", existing_behavior="Sum supplied values",
            remaining_work="Count, numeric edge cases and integration", reason="Authored sum suboperation only")
        return raw

    def test_one_exact_call_all_unknown_is_not_forced_into_a_known_label(self):
        terminal = event(fixtures.unknown())
        result = self.simulate(terminal)
        self.assertEqual(self.calls, 1)
        self.assertEqual(sum(self.identities), 1)
        self.assertEqual(self.receipts, [terminal])
        self.assertEqual(result["parsed"], fixtures.unknown())
        self.assertEqual(result["checked"]["summary"]["unknown_facets"], ["runtime", "input", "output", "outcome"])
        self.assertLess(self.order.index("terminal"), self.order.index("result"))
        self.assertEqual(self.jobs[-1]["ai_calls_used"], 1)
        self.assertEqual(self.jobs[-1]["checkpoint"]["ai_outputs"][0]["output"], fixtures.unknown())

    def test_valid_slice_stays_unverified_and_cannot_change_selection(self):
        raw = self.slice_card()
        checked = self.simulate(event(raw))["checked"]
        self.assertTrue(checked["summary"]["partial_outcome_hint"])
        self.assertFalse(checked["comparison_semantics_independently_verified"])
        self.assertFalse(checked["slice_semantics_independently_verified"])
        self.assertFalse(checked["summary"]["changes_selection"])
        self.assertFalse(checked["summary"]["changes_qualification"])

    def test_empty_property_survives_receipt_then_rejects_without_retry(self):
        raw = self.slice_card()
        raw["facets"]["outcome"]["demand_property"] = ""
        before = copy.deepcopy(raw)
        result = self.simulate(event(raw))
        self.assertEqual(result["parsed"], before)
        self.assertIn("nonempty", result["checked"]["validation_error"])
        self.assertEqual(self.calls, 1)
        self.assertEqual(self.receipts, [event(before)])
        self.assertEqual(len(self.results), 1)

    def test_unknown_nonempty_declaration_is_not_cleared_or_repaired(self):
        raw = fixtures.unknown()
        raw["facets"]["runtime"]["operation_property"] = "Invented"
        result = self.simulate(event(raw))
        self.assertIn("validation_error", result["checked"])
        self.assertEqual(result["parsed"], raw)
        self.assertEqual(self.calls, 1)

    def test_identity_and_atomic_allowance_failure_prevent_network(self):
        for flag, error in (("identity_failure", RuntimeError), ("reservation_failure", ValueError)):
            with self.subTest(flag=flag), self.assertRaises(error):
                self.simulate(event(fixtures.unknown()), **{flag: True})
            self.assertEqual(self.calls, 0)
            self.assertEqual(self.results, [])
            self.assertEqual(self.reservations, [])

    def test_receipt_storage_failure_stops_before_acceptance(self):
        with self.assertRaises(ReceiptPersistenceError):
            self.simulate(event(fixtures.unknown()), receipt_failure=True)
        self.assertEqual(self.calls, 1)
        self.assertEqual(len(self.reservations), 1)
        self.assertEqual(self.results, [])
        self.assertNotIn("reported_usage", self.jobs[-1])

    def test_http_schema_rejection_stops_without_terminal_or_retry(self):
        failure = urllib.error.HTTPError("http://127.0.0.1:1/responses", 400, "Invalid schema", {}, None)
        with self.assertRaises(ResponseError) as captured:
            self.simulate(None, opener_failure=failure)
        self.assertEqual(captured.exception.http_status, 400)
        self.assertEqual(self.calls, 1)
        self.assertEqual(len(self.reservations), 1)
        self.assertEqual(self.receipts, [])
        self.assertEqual(self.results, [])
        self.assertNotIn("reported_usage", self.jobs[-1])

    def test_incomplete_refused_missing_terminal_and_wrong_shape_are_not_success(self):
        refused = event(fixtures.unknown())
        refused["response"]["output"][0]["content"] = [{"type": "refusal", "refusal": "No"}]
        wrong = fixtures.unknown() | {"extra": True}
        for terminal in (event(fixtures.unknown(), "incomplete"), refused, event(wrong), None):
            with self.subTest(terminal=terminal is None), self.assertRaises((CandidateValidationError, ResponseError)):
                self.simulate(terminal)
            self.assertEqual(self.calls, 1)
            self.assertEqual(self.results, [])
            self.assertEqual(len(self.receipts), 0 if terminal is None else 1)

    def test_fixture_has_full_source_and_fresh_owned_dicts_without_labels(self):
        first = task.build_case()
        second = task.build_case()
        before = copy.deepcopy(second)
        self.assertEqual(first, second)
        self.assertEqual(first["operation_body"], task.BODY)
        self.assertEqual(first["demand_sources"], {"q0": task.DEMAND})
        self.assertFalse(first["data"]["acquisition_complete"])
        self.assertEqual("".join(item["quote"] for item in first["data"]["demand_spans"].values()), task.DEMAND)
        self.assertNotIn("facets", first["data"])
        first["data"]["operation_evidence"]["e0"]["quote"] = "changed"
        self.assertEqual(second, before)
        self.assertEqual(task.build_case(), before)

    def test_import_starts_no_provider_job_io_or_execution(self):
        with patch("builtins.open", side_effect=AssertionError("file IO")), \
             patch("os.getenv", side_effect=AssertionError("environment")), \
             patch("socket.socket", side_effect=AssertionError("network")), \
             patch("sqlite3.connect", side_effect=AssertionError("database")), \
             patch("subprocess.run", side_effect=AssertionError("process")), \
             patch("threading.Thread.start", side_effect=AssertionError("thread")), \
             patch.object(Provider, "__init__", side_effect=AssertionError("provider")), \
             patch.object(task, "complete_with_receipt", side_effect=AssertionError("call")):
            importlib.reload(task)
            task.build_case()


if __name__ == "__main__":
    unittest.main()
