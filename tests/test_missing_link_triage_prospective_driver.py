"""Authored cohort safety/transport/accounting controls, no real provider or ledger."""
import copy
import hashlib
import importlib
import json
import tempfile
from pathlib import Path
import unittest
import urllib.error
from unittest.mock import Mock, patch

from missing_link.provider import Provider, CandidateValidationError, ResponseError
from scripts import missing_link_triage_prospective_driver as task
from scripts.missing_link_triage_native_driver import run_once
from scripts.missing_link_triage_receipts import ReceiptPersistenceError
from scripts.missing_link_triage_prospective_sources import documented_case
from test_missing_link_triage_prospective_sources import source
from test_missing_link_triage_property_execution import Stream, event
from test_missing_link_triage_properties import unknown

SEGMENT, ALLOWANCE = "authored-prospective", "original"


def setup():
    provider = Provider({"REPOTRACTION_AI_URL": "http://127.0.0.1:1", "REPOTRACTION_AI_MODEL": "gpt-6-luna",
        "REPOTRACTION_AI_API_KIND": "responses", "REPOTRACTION_AI_RESPONSE_FORMAT": "json_schema",
        "REPOTRACTION_AI_STREAMING": "1", "REPOTRACTION_AI_MAX_CALLS": "1",
        "REPOTRACTION_AI_MAX_COST_USD": ".02", "REPOTRACTION_AI_MAX_OUTPUT_TOKENS": "6000",
        "REPOTRACTION_AI_INPUT_USD_PER_MILLION": ".1", "REPOTRACTION_AI_OUTPUT_USD_PER_MILLION": ".5"})
    cases = [documented_case(number, source(), "chosen", demand_record=source(), demand_function="chosen") for number in range(1, 7)]
    payloads, metadata = [], []
    for case in cases:
        schema = task.schema_for_context(case["data"])
        _, payload, body = provider._encode_prompt(task.PROMPT, case["data"], schema, "analysis")
        payloads.append(payload)
        metadata.append({"case": case["case"], "job_id": f"{SEGMENT}-{case['case']:02}",
            "request_bytes": len(body), "request_sha256": hashlib.sha256(body).hexdigest(),
            "schema_sha256": hashlib.sha256(json.dumps(schema, sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
            "reservation_usd": ((len(body) + 2048) * .1 + 6000 * .5) / 1e6})
    return provider, {"cases": cases, "payloads": payloads, "metadata": metadata,
        "config": task.configuration(provider), "segment": SEGMENT}


def snapshot():
    return {"artifacts": {"old": "hash"}, "active_jobs": [],
        "tables": {"ml_ai_allowances": "a", "ml_ai_reservations": "r", "ml_jobs": "j"},
        "reservation_rows": [[1, ALLOWANCE, "old-job", 7.6197550, "old-time"]],
        "allowance_rows": [[ALLOWANCE, 7.6197550], ["other", 2.0]],
        "reservations": 1, "reserved_usd": 7.6197550}


def incremented(metadata, count):
    after = snapshot()
    for index, item in enumerate(metadata[:count], 2):
        after["reservation_rows"].append([index, ALLOWANCE, item["job_id"], item["reservation_usd"], "new-time"])
        after["allowance_rows"][0][1] += item["reservation_usd"]
        after["reserved_usd"] += item["reservation_usd"]
        after["reservations"] += 1
    if count:
        after["tables"].update(ml_ai_allowances="new-a", ml_ai_reservations="new-r")
    return after


class ProspectiveDriverTests(unittest.TestCase):
    def verify(self, after, metadata, minimum=0, maximum=6, ceiling=7.7197550):
        before = snapshot()
        saved = copy.deepcopy((before, after, metadata))
        try:
            task.verify_increment(before, after, allowance=ALLOWANCE, requests=metadata, ceiling=ceiling,
                min_added=minimum, max_added=maximum)
        finally:
            self.assertEqual((before, after, metadata), saved)

    def test_every_exact_ordered_prefix_reproduces_without_mutation(self):
        _, frozen = setup()
        for count in range(7):
            with self.subTest(count=count):
                self.verify(incremented(frozen["metadata"], count), frozen["metadata"], count, count)

    def test_missing_future_reordered_duplicate_foreign_and_wrong_cost_rows_reject(self):
        _, frozen = setup()
        metadata = frozen["metadata"]
        for kind in ("missing", "future", "order", "duplicate", "foreign", "allowance", "cost", "nan", "bool", "short", "prior"):
            after = incremented(metadata, 2)
            if kind == "missing": after = incremented(metadata, 1)
            elif kind == "future": after = incremented(metadata, 3)
            elif kind == "order": after["reservation_rows"][1:] = list(reversed(after["reservation_rows"][1:]))
            elif kind == "duplicate": after["reservation_rows"][-1][2] = metadata[0]["job_id"]
            elif kind == "foreign": after["reservation_rows"][-1][2] = "foreign"
            elif kind == "allowance": after["reservation_rows"][-1][1] = "other"
            elif kind == "cost": after["reservation_rows"][-1][3] += .001
            elif kind == "nan": after["reservation_rows"][-1][3] = float("nan")
            elif kind == "bool": after["reservation_rows"][-1][3] = True
            elif kind == "short": after["reservation_rows"][-1] = [3]
            else: after["reservation_rows"][0][-1] = "changed"
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                self.verify(after, metadata, 2, 2)

    def test_artifacts_tables_workers_counts_and_allowances_stay_exact(self):
        _, frozen = setup()
        for kind in ("artifact", "table", "table_set", "active", "count", "total", "other", "tiny_other", "allowance_set", "duplicate_allowance"):
            after = incremented(frozen["metadata"], 6)
            if kind == "artifact": after["artifacts"]["old"] = "changed"
            elif kind == "table": after["tables"]["ml_jobs"] = "changed"
            elif kind == "table_set": after["tables"]["new"] = "hash"
            elif kind == "active": after["active_jobs"] = ["active"]
            elif kind == "count": after["reservations"] += 1
            elif kind == "total": after["reserved_usd"] += .001
            elif kind == "other": after["allowance_rows"][1][1] += .001
            elif kind == "tiny_other": after["allowance_rows"][1][1] += 5e-9
            elif kind == "allowance_set": after["allowance_rows"].append(["new", 0])
            else: after["allowance_rows"].append(copy.deepcopy(after["allowance_rows"][0]))
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                self.verify(after, frozen["metadata"])

    def test_zero_rows_cannot_change_accounting_and_ceiling_remains_enforced(self):
        _, frozen = setup()
        for name in task.ACCOUNTING_TABLES:
            after = snapshot()
            after["tables"][name] = "changed"
            with self.subTest(name=name), self.assertRaises(ValueError): self.verify(after, frozen["metadata"])
        with self.assertRaisesRegex(ValueError, "cumulative"):
            self.verify(incremented(frozen["metadata"], 1), frozen["metadata"], ceiling=7.6197550)

    def test_prefix_bounds_existing_or_duplicate_job_ids_reject(self):
        _, frozen = setup()
        for low, high in ((-1, 6), (0, 7), (2, 1), (True, 6), (0, 6.0)):
            with self.subTest(low=low, high=high), self.assertRaises(ValueError):
                self.verify(snapshot(), frozen["metadata"], low, high)
        metadata = copy.deepcopy(frozen["metadata"])
        metadata[-1]["job_id"] = metadata[0]["job_id"]
        with self.assertRaises(ValueError): self.verify(snapshot(), metadata)
        metadata = copy.deepcopy(frozen["metadata"])
        metadata[0]["job_id"] = "old-job"
        with self.assertRaises(ValueError): self.verify(snapshot(), metadata)

    def test_frozen_request_drift_and_case_order_reject_without_network(self):
        for kind in ("case_order", "case_bool", "source", "payload", "metadata", "config", "provider", "count"):
            provider, frozen = setup()
            if kind == "case_order": frozen["cases"].reverse()
            elif kind == "case_bool": frozen["cases"][0]["case"] = True
            elif kind == "source": frozen["cases"][0]["data"]["operation_evidence"]["e0"]["quote"] += "changed"
            elif kind == "payload": frozen["payloads"][0]["store"] = True
            elif kind == "metadata": frozen["metadata"][0]["request_sha256"] = "changed"
            elif kind == "config": frozen["config"]["model"] = "other"
            elif kind == "provider": provider.output_price = .6
            else: frozen["cases"].pop()
            with self.subTest(kind=kind), patch("socket.socket", side_effect=AssertionError("network")), self.assertRaises(ValueError):
                task.verify_requests(provider, **frozen)

    def test_readiness_blocks_marker_and_does_not_encode_or_echo_diagnostics(self):
        provider, frozen = setup()
        provider.error = "private sentinel"
        with tempfile.TemporaryDirectory() as temporary, patch.object(provider, "_encode_prompt", side_effect=AssertionError("encode")):
            marker = Path(temporary) / "started.json"
            lease, execute = Mock(), Mock()
            with self.assertRaisesRegex(ValueError, "^Prospective provider is not ready$"):
                run_once(preflight=lambda: task.verify_requests(provider, **frozen), merged=lambda: True,
                    lease=lease, identity=Mock(), marker=marker, marker_metadata={}, execute=execute, verify_after=Mock())
            self.assertFalse(marker.exists())
            lease.acquire.assert_not_called()
            execute.assert_not_called()

    def test_verified_requests_leave_inputs_and_credentials_out_of_public_config(self):
        provider, frozen = setup()
        saved = copy.deepcopy(frozen)
        provider.key = "not-a-real-secret"
        with patch("socket.socket", side_effect=AssertionError("network")), patch("os.getenv", side_effect=AssertionError("environment")):
            self.assertEqual(task.verify_requests(provider, **frozen), sum(item["reservation_usd"] for item in frozen["metadata"]))
        self.assertEqual(frozen, saved)
        self.assertNotIn(provider.key, json.dumps(task.configuration(provider)))

    def simulate(self, terminals=None, fail=None):
        provider, frozen = setup()
        self.trace, self.reservations, self.jobs, self.receipts, self.results = [], [], [], [], []
        terminals = terminals or [event(unknown()) for _ in range(6)]
        def before(number):
            self.trace.append(("before", number))
            if fail == "preflight": raise ValueError("drift")
            if fail == "between" and number == 2: raise ValueError("drift")
        def identity(**kw):
            if kw.get("force"): self.trace.append(("identity", True))
            if fail == "identity": raise RuntimeError("account")
        def reserve(job, cost):
            if fail == "reserve": raise ValueError("atomic cap")
            self.reservations.append((job, cost))
        def terminal(number, receipt):
            if fail == "receipt": raise OSError("storage")
            self.trace.append(("terminal", number))
            self.receipts.append((number, copy.deepcopy(receipt)))
        def record(result):
            if fail == "record": raise OSError("storage")
            self.trace.append(("result", result["case"]))
            self.results.append(copy.deepcopy(result))
        with patch("scripts.missing_link_triage_receipts.urllib.request.build_opener") as opener, \
             patch("socket.socket", side_effect=AssertionError("network")), patch("sqlite3.connect", side_effect=AssertionError("ledger")):
            opener.return_value.open.side_effect = [Stream(value) for value in terminals]
            if fail == "http": opener.return_value.open.side_effect = urllib.error.HTTPError("http://127.0.0.1:1", 503, "Unavailable", {}, None)
            try:
                return task.execute_cases(provider, frozen["cases"], segment=SEGMENT, identity=identity,
                    before_case=before, after_case=lambda number: self.trace.append(("after", number)), reserve=reserve,
                    persist=lambda number, job: self.jobs.append((number, job)), retain_terminal=terminal, record=record)
            finally:
                self.calls = opener.return_value.open.call_count
                for number, call in enumerate(opener.return_value.open.call_args_list):
                    self.assertEqual(json.loads(call.args[0].data), frozen["payloads"][number])
                self.assertLessEqual(self.calls, 6)

    def test_six_exact_requests_use_declaration_schema_keep_raw_and_do_not_force_labels(self):
        results = self.simulate()
        self.assertEqual(self.calls, 6)
        self.assertEqual(len(self.reservations), 6)
        for number, result in enumerate(results, 1):
            self.assertEqual(result["case"], number)
            self.assertEqual(result["parsed"], unknown())
            self.assertIn("source_url", result)
            self.assertNotIn("issue", result)
            self.assertEqual(result["checked"]["summary"]["status"], "context_required")
            self.assertFalse(result["checked"]["comparison_semantics_independently_verified"])
            self.assertFalse(result["checked"]["summary"]["changes_selection"])
            self.assertLess(self.trace.index(("terminal", number)), self.trace.index(("result", number)))
        self.assertEqual(sum(item == ("identity", True) for item in self.trace), 6)
        self.assertEqual(sum(item[0] == "before" for item in self.trace), 12)
        self.assertTrue(all(job["ai_calls_used"] == 1 for _, job in self.jobs))

    def test_final_branch_rejection_is_preserved_then_next_case_runs_once(self):
        raw = unknown()
        raw["facets"]["input"]["operation_property"] = "Forbidden for unknown"
        terminals = [event(unknown()), event(raw)] + [event(unknown()) for _ in range(4)]
        results = self.simulate(terminals)
        self.assertEqual(self.calls, 6)
        self.assertEqual(results[1]["parsed"], raw)
        self.assertIn("validation_error", results[1]["checked"])
        self.assertEqual(self.receipts[1][1], terminals[1])
        self.assertEqual(self.jobs[-1][1]["checkpoint"]["ai_outputs"][0]["output"], unknown())

    def test_account_reservation_and_between_case_integrity_failures_stop_without_retry(self):
        for flag in ("preflight", "identity", "reserve", "between"):
            with self.subTest(flag=flag), self.assertRaises((ValueError, RuntimeError)):
                self.simulate(fail=flag)
            self.assertEqual(self.calls, 1 if flag == "between" else 0)
            self.assertEqual(len(self.results), 1 if flag == "between" else 0)

    def test_transport_and_persistence_failure_stop_before_next_case(self):
        for flag, error in (("http", ResponseError), ("receipt", ReceiptPersistenceError), ("record", OSError)):
            with self.subTest(flag=flag), self.assertRaises(error): self.simulate(fail=flag)
            self.assertEqual(self.calls, 1)
            self.assertEqual(len(self.reservations), 1)
            self.assertEqual(self.results, [])

    def test_refusal_incomplete_missing_terminal_and_generic_shape_failure_stop(self):
        refused = event(unknown())
        refused["response"]["output"][0]["content"] = [{"type": "refusal", "refusal": "No"}]
        for terminal in (refused, event(unknown(), "incomplete"), None, event(unknown() | {"extra": True})):
            with self.subTest(missing=terminal is None), self.assertRaises((CandidateValidationError, ResponseError)):
                self.simulate([terminal] + [event(unknown()) for _ in range(5)])
            self.assertEqual(self.calls, 1)
            self.assertEqual(self.results, [])

    def test_execution_rejects_reordered_or_incomplete_cases_before_any_callback(self):
        provider, frozen = setup()
        for cases in (frozen["cases"][:-1], list(reversed(frozen["cases"]))):
            callbacks = {name: Mock() for name in ("identity", "before_case", "after_case", "reserve", "persist", "retain_terminal", "record")}
            with self.assertRaises(ValueError): task.execute_cases(provider, cases, segment=SEGMENT, **callbacks)
            for callback in callbacks.values(): callback.assert_not_called()

    def test_import_performs_no_io_thread_provider_or_credential_lookup(self):
        with patch("builtins.open", side_effect=AssertionError("file")), patch("os.getenv", side_effect=AssertionError("environment")), \
             patch("socket.socket", side_effect=AssertionError("network")), patch("sqlite3.connect", side_effect=AssertionError("ledger")), \
             patch("subprocess.run", side_effect=AssertionError("process")), patch("threading.Thread.start", side_effect=AssertionError("thread")), \
             patch.object(Provider, "__init__", side_effect=AssertionError("provider")):
            importlib.reload(task)
