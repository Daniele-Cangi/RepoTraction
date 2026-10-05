"""Authored safety gates, synthetic accounting and exclusive temporary markers."""
import copy
import importlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from missing_link.provider import Provider
from scripts import missing_link_triage_native_driver as task
from scripts import missing_link_triage_native_probe as probe

ALLOWANCE, JOB, COST, CEILING = "original", probe.SEGMENT + "-01", .0053961, 7.6343589


def snapshot():
    return {"artifacts": {"old": "hash"}, "active_jobs": [],
        "tables": {"ml_ai_allowances": "a", "ml_ai_reservations": "r", "ml_jobs": "j"},
        "reservation_rows": [[1, ALLOWANCE, "old-job", 7.6143589, "old-time"]],
        "allowance_rows": [[ALLOWANCE, 7.6143589], ["other", 2.0]],
        "reservations": 1, "reserved_usd": 7.6143589}


def incremented():
    after = snapshot()
    after["reservation_rows"].append([2, ALLOWANCE, JOB, COST, "new-time"])
    after["allowance_rows"][0][1] += COST
    after["reservations"] += 1
    after["reserved_usd"] += COST
    after["tables"].update(ml_ai_allowances="new-a", ml_ai_reservations="new-r")
    return after


class NativeDriverTests(unittest.TestCase):
    def verify(self, after):
        before = snapshot()
        saved = copy.deepcopy((before, after))
        try:
            task.verify_increment(before, after, allowance=ALLOWANCE, job_id=JOB, reservation=COST, ceiling=CEILING)
        finally:
            self.assertEqual((before, after), saved)

    def test_zero_and_one_exact_owned_reservation_are_permitted_without_mutation(self):
        self.verify(snapshot())
        self.verify(incremented())

    def test_prior_rows_foreign_jobs_allowances_and_wrong_cost_are_rejected(self):
        for mutation in ("prior", "foreign_job", "foreign_allowance", "cost", "nan", "bool", "short", "duplicate"):
            after = incremented()
            if mutation == "prior":
                after["reservation_rows"][0][-1] = "rewritten"
            elif mutation == "foreign_job":
                after["reservation_rows"][-1][2] = "foreign"
            elif mutation == "foreign_allowance":
                after["reservation_rows"][-1][1] = "other"
            elif mutation == "cost":
                after["reservation_rows"][-1][3] += .001
            elif mutation == "nan":
                after["reservation_rows"][-1][3] = float("nan")
            elif mutation == "bool":
                after["reservation_rows"][-1][3] = True
            elif mutation == "short":
                after["reservation_rows"][-1] = [2]
            else:
                after["reservation_rows"].append(copy.deepcopy(after["reservation_rows"][-1]))
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                self.verify(after)

    def test_artifact_tables_workers_counts_and_balances_cannot_change(self):
        for mutation in ("artifact", "table", "table_set", "active", "count", "total", "other_balance", "other_allowance", "duplicate_allowance"):
            after = incremented()
            if mutation == "artifact":
                after["artifacts"]["old"] = "changed"
            elif mutation == "table":
                after["tables"]["ml_jobs"] = "changed"
            elif mutation == "table_set":
                after["tables"]["new"] = "hash"
            elif mutation == "active":
                after["active_jobs"] = ["active"]
            elif mutation == "count":
                after["reservations"] += 1
            elif mutation == "total":
                after["reserved_usd"] += .001
            elif mutation == "other_balance":
                after["allowance_rows"][1][1] += .001
            elif mutation == "other_allowance":
                after["allowance_rows"].append(["new", 0])
            else:
                after["allowance_rows"].append(copy.deepcopy(after["allowance_rows"][0]))
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                self.verify(after)

    def test_without_an_owned_increment_even_accounting_hashes_must_match(self):
        for table in task.ACCOUNTING_TABLES:
            after = snapshot()
            after["tables"][table] = "changed"
            with self.subTest(table=table), self.assertRaises(ValueError):
                self.verify(after)

    def test_unrelated_allowance_rejects_even_sub_tolerance_mutation(self):
        for delta in (5e-9, -5e-9):
            after = incremented()
            after["allowance_rows"][1][1] += delta
            with self.subTest(delta=delta), self.assertRaisesRegex(ValueError, "allowance balance"):
                self.verify(after)

    def test_already_reserved_job_and_segment_ceiling_are_rejected(self):
        before = snapshot()
        before["reservation_rows"][0][2] = JOB
        with self.assertRaisesRegex(ValueError, "already reserved"):
            task.verify_increment(before, copy.deepcopy(before), allowance=ALLOWANCE, job_id=JOB,
                reservation=COST, ceiling=CEILING)
        with self.assertRaisesRegex(ValueError, "cumulative"):
            task.verify_increment(snapshot(), incremented(), allowance=ALLOWANCE, job_id=JOB,
                reservation=COST, ceiling=7.615)

    def gate(self, root, *, merged=True, busy=False, fail_stage=None):
        self.trace = []
        lease = Mock()
        def stage(name):
            self.trace.append(name)
            if fail_stage == name:
                raise RuntimeError(name)
        def acquire():
            stage("acquire")
            return not busy
        lease.acquire.side_effect = acquire
        lease.release.side_effect = lambda: stage("release")
        return task.run_once(preflight=lambda: stage("preflight"), merged=lambda: merged, lease=lease,
            identity=lambda **kw: stage("identity"), marker=root / "started.json", marker_metadata={"one_shot": True},
            execute=lambda: stage("execute") or "result", verify_after=lambda: stage("verify_after"))

    def test_marker_is_exclusive_and_prevents_another_execution(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.assertEqual(self.gate(root), "result")
            self.assertEqual(self.trace, ["preflight", "acquire", "preflight", "identity", "execute", "release", "verify_after"])
            before = (root / "started.json").read_bytes()
            with self.assertRaises(FileExistsError):
                self.gate(root)
            self.assertNotIn("execute", self.trace)
            self.assertEqual((root / "started.json").read_bytes(), before)

    def test_main_preflight_and_busy_lease_block_before_marker_or_request(self):
        for kwargs in ({"merged": False}, {"busy": True}, {"fail_stage": "preflight"}):
            with self.subTest(kwargs=kwargs), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                with self.assertRaises(RuntimeError):
                    self.gate(root, **kwargs)
                self.assertFalse((root / "started.json").exists())
                self.assertNotIn("execute", self.trace)
                self.assertNotIn("release", self.trace)

    def test_failed_account_check_releases_lease_without_consuming_marker(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaises(RuntimeError):
                self.gate(root, fail_stage="identity")
            self.assertFalse((root / "started.json").exists())
            self.assertEqual(self.trace[-2:], ["release", "verify_after"])
            self.assertNotIn("execute", self.trace)

    def test_execution_failure_keeps_marker_and_checks_integrity_after_release(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaises(RuntimeError):
                self.gate(root, fail_stage="execute")
            self.assertEqual(json.loads((root / "started.json").read_text()), {"one_shot": True})
            self.assertEqual(self.trace[-3:], ["execute", "release", "verify_after"])
            with self.assertRaises(FileExistsError):
                self.gate(root)
            self.assertNotIn("execute", self.trace)

    def test_release_failure_does_not_skip_integrity_check(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(RuntimeError):
                self.gate(Path(temporary), fail_stage="release")
            self.assertEqual(self.trace[-2:], ["release", "verify_after"])

    def frozen_request(self, overrides=None):
        env = {"REPOTRACTION_AI_URL": "http://127.0.0.1:1", "REPOTRACTION_AI_MODEL": "gpt-6-luna",
            "REPOTRACTION_AI_API_KIND": "responses", "REPOTRACTION_AI_RESPONSE_FORMAT": "json_schema",
            "REPOTRACTION_AI_STREAMING": "1", "REPOTRACTION_AI_MAX_CALLS": "1", "REPOTRACTION_AI_MAX_COST_USD": ".02",
            "REPOTRACTION_AI_MAX_OUTPUT_TOKENS": "6000", "REPOTRACTION_AI_INPUT_USD_PER_MILLION": ".1",
            "REPOTRACTION_AI_OUTPUT_USD_PER_MILLION": ".5"}
        env.update(overrides or {})
        provider = Provider(env)
        case = probe.build_case()
        schema = probe.schema_for_context(case["data"])
        endpoint, payload, body = provider._encode_prompt(probe.PROMPT, case["data"], schema, "analysis")
        import hashlib
        metadata = {"endpoint": endpoint, "request_bytes": len(body), "request_sha256": hashlib.sha256(body).hexdigest(),
            "prompt_characters": len(probe.PROMPT), "prompt_sha256": hashlib.sha256(probe.PROMPT.encode()).hexdigest(),
            "schema_sha256": hashlib.sha256(json.dumps(schema, sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
            "reservation_usd": ((len(body) + 2048) * .1 + 6000 * .5) / 1e6}
        return provider, {"case": case, "payload": payload, "metadata": metadata, "config": task.configuration(provider)}

    def test_missing_remote_authorization_cannot_consume_marker_or_attempt(self):
        remote = {"REPOTRACTION_AI_URL": "https://api.openai.com/v1",
            "REPOTRACTION_AI_KEY": "dummy-test-value", "REPOTRACTION_AI_ALLOW_REMOTE": "1",
            "REPOTRACTION_AI_TOTAL_BUDGET_USD": "10", "REPOTRACTION_AI_BUDGET_ID": ALLOWANCE}
        ready, frozen = self.frozen_request(remote)
        unauthorized = {key: value for key, value in remote.items() if key != "REPOTRACTION_AI_ALLOW_REMOTE"}
        invalid, invalid_frozen = self.frozen_request(unauthorized)
        self.assertTrue(ready.describe()["configured"])
        self.assertFalse(invalid.describe()["configured"])
        self.assertEqual(invalid_frozen, frozen)
        with tempfile.TemporaryDirectory() as temporary, \
             patch("socket.socket", side_effect=AssertionError("network")), \
             patch("os.getenv", side_effect=AssertionError("environment")), \
             patch("sqlite3.connect", side_effect=AssertionError("ledger")):
            marker = Path(temporary) / "started.json"
            lease, identity, execute, verify_after = Mock(), Mock(), Mock(), Mock()
            with self.assertRaisesRegex(ValueError, "not ready"):
                task.run_once(preflight=lambda: task.verify_request(invalid, **frozen),
                    merged=lambda: True, lease=lease, identity=identity, marker=marker,
                    marker_metadata={}, execute=execute, verify_after=verify_after)
            self.assertFalse(marker.exists())
            lease.acquire.assert_not_called()
            identity.assert_not_called()
            execute.assert_not_called()
            verify_after.assert_not_called()
            self.assertEqual(task.verify_request(ready, **frozen), COST)

    def test_provider_readiness_rejection_does_not_encode_or_echo_error(self):
        provider, frozen = self.frozen_request()
        provider.error = "private diagnostic sentinel"
        with patch.object(provider, "_encode_prompt", side_effect=AssertionError("encode")):
            with self.assertRaisesRegex(ValueError, "^Native probe provider is not ready$"):
                task.verify_request(provider, **frozen)

    def test_exact_frozen_request_and_configuration_exclude_credentials(self):
        provider, frozen = self.frozen_request()
        provider.key = "dummy-value-not-a-real-secret"
        before = copy.deepcopy(frozen)
        with patch("socket.socket", side_effect=AssertionError("network")), \
             patch("os.getenv", side_effect=AssertionError("credentials")), \
             patch("sqlite3.connect", side_effect=AssertionError("ledger")):
            self.assertEqual(task.verify_request(provider, **frozen), frozen["metadata"]["reservation_usd"])
        self.assertNotIn(provider.key, json.dumps(task.configuration(provider)))
        self.assertEqual(frozen, before)

    def test_source_payload_bytes_hash_configuration_and_cost_drift_reject(self):
        for kind in ("case", "payload", "metadata", "config", "provider"):
            provider, frozen = self.frozen_request()
            if kind == "case":
                frozen[kind]["operation_body"] += "changed"
            elif kind == "payload":
                frozen[kind]["store"] = True
            elif kind == "metadata":
                frozen[kind]["request_sha256"] = "changed"
            elif kind == "config":
                frozen[kind]["model"] = "wrong"
            else:
                provider.output_price = .6
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                task.verify_request(provider, **frozen)

    def test_import_starts_no_file_job_network_or_provider(self):
        with patch("builtins.open", side_effect=AssertionError("file IO")), \
             patch("os.getenv", side_effect=AssertionError("environment")), \
             patch("socket.socket", side_effect=AssertionError("network")), \
             patch("sqlite3.connect", side_effect=AssertionError("database")), \
             patch("subprocess.run", side_effect=AssertionError("process")), \
             patch("threading.Thread.start", side_effect=AssertionError("thread")), \
             patch.object(Provider, "__init__", side_effect=AssertionError("provider")):
            importlib.reload(task)


if __name__ == "__main__":
    unittest.main()
