"""Owned evaluator mechanics with authored data, no model or source execution."""
import copy
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import Mock, patch

from missing_link.lease import WorkerLease
from missing_link.provider import CandidateValidationError, Provider
from missing_link.service import Budget, Service
from missing_link.store import Store
from scripts.missing_link_repository_only_evaluator import (
    EvaluationStopped, PinnedSource, ReceiptProvider, ReservationBinding, execute_slots, verify_prefix)
from scripts.missing_link_repository_only_run import CEILING, frozen, knobs, run, save, sha, snapshot
from scripts.missing_link_repository_only_evaluator import configuration
from test_missing_link import repository, issue, request_raw, wire_request


class Stream:
    def __init__(self, event):
        self.lines = iter([("data: " + json.dumps(event) + "\n").encode(), b""])
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def readline(self, limit): return next(self.lines, b"")


def terminal(raw=None, status="completed", refusal=False):
    return {"type": "response." + status, "response": {"id": "authored", "status": status,
        "usage": {"input_tokens": 50, "output_tokens": 25, "input_tokens_details": {"cached_tokens": 7},
                  "output_tokens_details": {"reasoning_tokens": 5}},
        "output": [{"type": "message", "content": [{"type": "refusal", "refusal": "authored"} if refusal else
            {"type": "output_text", "text": json.dumps(raw)}]}]}}


class EvaluatorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.original = Store(Path(self.temp.name) / "original.sqlite3", "alice")
        self.private = Path(self.temp.name) / "evaluation.sqlite3"
        self.gate, self.receipts, self.journal = Mock(), [], []
        self.binding = ReservationBinding(self.original, allowance="missing-link-verification-2026-09-30",
            ceiling=.04, verify=lambda: None, persist=lambda n, row: self.journal.append(row))
        self.provider = ReceiptProvider(dict(knobs(), REPOTRACTION_AI_KEY="authored"), gate=self.gate,
            binding=self.binding, retain=lambda kind, attempt, value: self.receipts.append((kind, copy.deepcopy(value))))

    def budget(self):
        job = {"id": "authored-job", "ai_calls_used": 0, "cost_reserved_usd": 0, "checkpoint": {}}
        return Budget(job, lambda: None, lambda: False, lambda: None,
            lambda cost: self.binding(self.provider.budget_id, job["id"], cost, 10))

    def service(self):
        service = Service(self.private, "alice", Mock(), lambda: "alice", self.provider)
        service.store.reserve_ai_allowance = self.binding
        return service

    def source(self):
        source = Mock()
        source.fetch_repository.return_value = repository()
        demands = [dict(issue(), comments=[], id=n, url=f"https://github.com/example/site/issues/{n}") for n in (7, 9)]
        source.search_issues.return_value = {"items": [{"url": demand["url"]} for demand in demands]}
        source.fetch_issue.side_effect = demands
        source.fetch_reference_context.return_value = {"id": 101, "full_name": "example/site",
            "revision": "b" * 40, "public": True, "reference_only": True, "files": [], "fingerprint": "authored-target"}
        return source

    def test_exact_production_body_and_native_details_survive_before_parse(self):
        expected = Provider(dict(knobs(), REPOTRACTION_AI_KEY="authored"))._encode_prompt("Authored", {}, None, "request")[2]
        event = terminal({"value": "authored"})
        with patch("urllib.request.build_opener") as opener:
            opener.return_value.open.return_value = Stream(event)
            parsed = self.provider.complete("Authored", {}, self.budget(), phase="request")
        self.assertEqual(opener.return_value.open.call_args.args[0].data, expected)
        self.assertEqual(parsed, {"value": "authored"})
        self.assertEqual(self.receipts[1], ("terminal", event))
        self.assertEqual(self.receipts[0][0], "request")
        self.assertEqual(len(self.journal), 1)
        self.assertGreater(self.original.ai_reserved(self.provider.budget_id), 0)

    def test_fatal_native_shapes_latch_and_never_call_again(self):
        cases = [terminal({}, "incomplete"), terminal({}, "failed"), terminal({}, refusal=True), terminal([]), terminal({"wrong": 1})]
        malformed = terminal({})
        malformed["response"]["output"][0]["content"][0]["text"] = "{"
        cases.append(malformed)
        schema = {"type": "object", "properties": {"value": {"type": "string"}}, "required": ["value"], "additionalProperties": False}
        for event in cases:
            with self.subTest(event=event["response"]["status"]):
                self.setUp()
                with patch("urllib.request.build_opener") as opener:
                    opener.return_value.open.return_value = Stream(event)
                    budget = self.budget()
                    with self.assertRaises(EvaluationStopped):
                        self.provider.complete("Authored", {}, budget, schema, "request")
                    with self.assertRaises(EvaluationStopped):
                        self.provider.complete("Authored", {}, budget, schema, "request")
                    self.assertEqual(opener.return_value.open.call_count, 1)
                self.assertEqual(len(self.journal), 1)
                self.assertEqual(self.receipts[1][1], event)

    def test_transport_or_receipt_storage_failure_stops_without_second_attempt(self):
        for storage in (False, True):
            with self.subTest(storage=storage):
                self.setUp()
                if storage:
                    def retain(kind, attempt, value):
                        if kind == "terminal": raise OSError("authored disk failure")
                    self.provider.retain = retain
                with patch("urllib.request.build_opener") as opener:
                    if storage: opener.return_value.open.return_value = Stream(terminal({}))
                    else: opener.return_value.open.side_effect = TimeoutError()
                    budget = self.budget()
                    for _ in range(2):
                        with self.assertRaises(EvaluationStopped): self.provider.complete("Authored", {}, budget)
                    self.assertEqual(opener.return_value.open.call_count, 1)
                self.assertEqual(len(self.journal), 1)

    def test_failed_preflight_or_request_persistence_never_reserves(self):
        for location in ("gate", "request"):
            with self.subTest(location=location):
                self.setUp()
                if location == "gate": self.gate.side_effect = EvaluationStopped("authored identity/code failure")
                else: self.provider.retain = Mock(side_effect=OSError("authored failure"))
                with patch("urllib.request.build_opener") as opener, self.assertRaises(EvaluationStopped):
                    self.provider.complete("Authored", {}, self.budget())
                opener.assert_not_called()
                self.assertEqual(self.journal, [])
                self.assertEqual(self.original.ai_reserved(self.provider.budget_id), 0)

    def test_atomic_original_cap_not_private_or_provider_total(self):
        self.binding.ceiling = .002
        service = self.service()
        with patch("urllib.request.build_opener") as opener, self.assertRaises(EvaluationStopped):
            self.provider.complete("Authored", {}, self.budget())
        opener.assert_not_called()
        self.assertEqual(self.original.ai_reserved(self.provider.budget_id), 0)
        self.assertEqual(service.store.ai_reserved(self.provider.budget_id), 0)
        self.binding.pending = None
        self.binding.ceiling = .04
        with patch("urllib.request.build_opener") as opener:
            opener.return_value.open.return_value = Stream(terminal({}))
            self.provider.fatal = None
            self.provider.complete("Authored", {}, self.budget())
        self.assertGreater(self.original.ai_reserved(self.provider.budget_id), 0)
        self.assertEqual(service.store.ai_reserved(self.provider.budget_id), 0)

    def test_journal_failure_leaves_charge_retained_and_latches(self):
        self.binding.persist = Mock(side_effect=OSError("authored disk failure"))
        with patch("urllib.request.build_opener") as opener, self.assertRaises(EvaluationStopped):
            self.provider.complete("Authored", {}, self.budget())
        opener.assert_not_called()
        self.assertGreater(self.original.ai_reserved(self.provider.budget_id), 0)
        self.assertEqual(len(self.binding.rows), 1)

    def test_actual_service_stops_same_job_and_next_slot_on_refusal(self):
        service, source = self.service(), self.source()
        # Structural interpretation is bypassed only in this authored candidate
        # harness so the fatal is exercised *inside* Service's broad candidate catch.
        self.provider.interpret_capabilities = lambda repo, budget: repo["capabilities"]
        slots = [{"input": "example/words", "order": n} for n in (1, 2)]
        with patch("missing_link.service.PublicGitHub", return_value=source), \
             patch("missing_link.service.extract_structure", return_value=repository()["capabilities"]), \
             patch("urllib.request.build_opener") as opener:
            opener.return_value.open.return_value = Stream(terminal({}, refusal=True))
            result = execute_slots(service, self.provider, slots, set_slot=lambda s: None,
                                   persist=lambda slot, job: None, verify=lambda: None)
        self.assertEqual(opener.return_value.open.call_count, 1)
        self.assertEqual(source.fetch_issue.call_count, 1)
        self.assertEqual(result["stopped_order"], 1)
        self.assertEqual(result["unattempted"], ["example/words"])
        job = service.store.get("jobs", result["slots"][0]["job_id"])
        self.assertEqual(job["status"], "failed")
        self.assertNotIn("candidate_errors", job["result"])

    def test_production_local_semantic_failure_remains_charged_and_continues(self):
        service, source = self.service(), self.source()
        self.provider.interpret_capabilities = lambda repo, budget: repo["capabilities"]
        self.provider.evaluate = lambda *args: []
        # Schema-valid zero-requirement unresolved request violates the unchanged
        # cross-field rule: zero is permitted only for a non-demand disposition.
        actual_count = 0
        def stream(request, **kwargs):
            nonlocal actual_count
            actual_count += 1
            data = json.loads(json.loads(request.data)["input"][1]["content"].split("UNTRUSTED_DATA_JSON:\n")[1])
            raw = wire_request(data)
            if actual_count == 1: raw["requirements"] = []
            return Stream(terminal(raw))
        with patch("missing_link.service.PublicGitHub", return_value=source), \
             patch("missing_link.service.extract_structure", return_value=repository()["capabilities"]), \
             patch("urllib.request.build_opener") as opener:
            opener.return_value.open.side_effect = stream
            result = service.start({"repo": "example/words", "use_ai": True, "max_candidates": 3}, background=False)
        job = service.store.get("jobs", result["job_id"])
        self.assertEqual(job["status"], "completed")
        self.assertEqual(job["ai_calls_used"], 2)
        self.assertEqual(len(self.journal), 2)
        self.assertIn("0", job["checkpoint"]["candidate_failures"])
        self.assertEqual(job["checkpoint"]["evaluated"], ["1"])
        self.assertIsNone(self.provider.fatal)

    def test_original_and_private_leases_prevent_overlap_and_release(self):
        original, competing = WorkerLease(self.original.path), WorkerLease(self.original.path)
        self.assertTrue(original.acquire())
        try:
            self.assertFalse(competing.acquire())
            service = self.service()
            other = WorkerLease(self.private)
            self.assertTrue(other.acquire())
            try:
                with self.assertRaises(ValueError): service.start({"repo": "example/words"}, background=False)
            finally: other.release()
        finally: original.release()
        self.assertTrue(competing.acquire())
        competing.release()

    def test_four_initial_service_jobs_keep_all_three_production_phases_and_empty_inputs(self):
        service = self.service()
        self.binding.ceiling = .8
        persisted = []
        slots = [{"input": "example/words", "order": n} for n in range(1, 5)]
        phases = []
        def stream(request, **kwargs):
            payload = json.loads(request.data)
            phase = payload["text"]["format"]["name"].removeprefix("missing_link_")
            data = json.loads(payload["input"][1]["content"].split("UNTRUSTED_DATA_JSON:\n")[1])
            phases.append(phase)
            raw = {"capabilities": []} if phase == "capabilities" else wire_request(data) if phase == "request" else {"matches": []}
            return Stream(terminal(raw))
        # Public acquisition is authored. Provider interpretation, automatic query
        # generation, selection, extraction, comparisons and budgets are real.
        sources = [self.source() for _ in slots]
        with patch("missing_link.service.PublicGitHub", side_effect=sources), \
             patch("missing_link.service.extract_structure", return_value=repository()["capabilities"]), \
             patch("urllib.request.build_opener") as opener:
            opener.return_value.open.side_effect = stream
            result = execute_slots(service, self.provider, slots, set_slot=lambda s: None,
                persist=lambda slot, job: persisted.append(job), verify=lambda: None)
        self.assertIsNone(result["stopped_order"])
        self.assertEqual(len({job["id"] for job in persisted}), 4)
        self.assertEqual(phases, ["capabilities", "request", "matches", "request", "matches"] * 4)
        self.assertEqual(len(self.journal), 20)
        for job in persisted:
            self.assertEqual(job["input"]["issue_url"], "")
            self.assertEqual(job["input"]["query"], "")
            self.assertTrue(job["result"]["search"]["automatic_query"])
            self.assertEqual(job["ai_calls_used"], 5)
        self.assertEqual(service.store.ai_reserved(self.provider.budget_id), 0)


class PinAndHistoryTests(unittest.TestCase):
    def slot(self):
        return {"canonical_name": "sample/project", "default_branch": "feature/main", "revision": "a" * 40,
                "commit_tree_sha": "b" * 40}

    def test_pin_routes_only_source_commit_and_checks_full_tree(self):
        metadata = {"full_name": "sample/project", "default_branch": "feature/main", "private": False,
                    "visibility": "public", "archived": False, "disabled": False, "has_issues": True}
        read = Mock(side_effect=[metadata, {"sha": "a" * 40, "commit": {"tree": {"sha": "b" * 40}}}, {"sha": "live"}, {"sha": "live-same-repo"}])
        pin = PinnedSource(read, self.slot())
        pin("repos/sample/project")
        pin("repos/sample/project/commits/feature%2Fmain")
        pin("repos/target/site/commits/main")
        pin("repos/sample/project/commits/feature%2Fmain")
        self.assertEqual(read.call_args_list[1].args[0], "repos/sample/project/commits/" + "a" * 40)
        self.assertEqual(read.call_args_list[2].args[0], "repos/target/site/commits/main")
        self.assertEqual(read.call_args_list[3].args[0], "repos/sample/project/commits/feature%2Fmain")
        pin.verify({"checkpoint": {"repository": {"public": True, "full_name": "sample/project", "revision": "a" * 40}}})

    def test_source_drift_or_missing_pin_blocks_payment(self):
        for result in ({"full_name": "different"}, {"sha": "a" * 40, "commit": {"tree": {"sha": "c" * 40}}}):
            pin = PinnedSource(Mock(return_value=result), self.slot())
            with self.assertRaises(EvaluationStopped):
                pin("repos/sample/project" if "full_name" in result else "repos/sample/project/commits/" + "a" * 40)
        with self.assertRaises(EvaluationStopped): PinnedSource(Mock(), self.slot()).verify({})

    def test_readonly_snapshot_prefix_rejects_foreign_writes_and_preserves_history(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "original.sqlite3"
            store = Store(path, "alice")
            allowance = "missing-link-verification-2026-09-30"
            store.reserve_ai_allowance(allowance, "prior", .01, 10)
            store.put("jobs", "old", {"id": "old", "status": "completed", "retained": "authored"})
            with patch("scripts.missing_link_repository_only_run.DB", path):
                before = snapshot({"artifacts": {}})
                store.reserve_ai_allowance(allowance, "owned", .02, .04)
                after = snapshot(before)
                rows = [{"job_id": "owned", "cost": .02}]
                verify_prefix(before, after, rows, allowance=allowance, ceiling=.04)
                for mutation in ("foreign", "cost", "old", "history", "balance"):
                    changed = copy.deepcopy(after)
                    if mutation == "foreign": changed["reservation_rows"][-1][2] = "foreign"
                    if mutation == "cost": changed["reservation_rows"][-1][3] += .001
                    if mutation == "old": changed["reservation_rows"][0][3] += .001
                    if mutation == "history": changed["tables"]["ml_jobs"] = "changed"
                    if mutation == "balance": changed["allowance_rows"][0][1] += .001
                    with self.subTest(mutation=mutation), self.assertRaises(EvaluationStopped):
                        verify_prefix(before, changed, rows, allowance=allowance, ceiling=.04)
                with closing(sqlite3.connect(path)) as db:
                    self.assertEqual(db.execute("SELECT COUNT(*) FROM ml_ai_reservations").fetchone()[0], 2)


class RuntimeGatesTests(unittest.TestCase):
    def test_consumed_cohort_rejects_before_configuration_lookup(self):
        for marker in ("started.json", "summary.json", "evaluation.sqlite3"):
            with self.subTest(marker=marker), tempfile.TemporaryDirectory() as temp:
                out = Path(temp)
                (out / marker).write_text("authored", encoding="utf-8")
                with patch("scripts.missing_link_repository_only_run.frozen", return_value={}), \
                     patch("scripts.missing_link_repository_only_run.provider_environment") as env, \
                     self.assertRaises(EvaluationStopped):
                    run(out)
                env.assert_not_called()

    def test_fingerprints_provider_readiness_and_main_ancestry_block_before_payment(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            out, prep = root / "owned", root / "prep"
            out.mkdir()
            prep.mkdir()
            (root / "authored.py").write_text("# data only\n", encoding="utf-8")
            save(out, "baseline.json", {})
            save(prep, "prepared.json", {})
            save(prep, "cohort.json", {"records": []})
            provider = Provider(dict(knobs(), REPOTRACTION_AI_KEY="authored"))
            manifest = {"baseline_sha256": sha(out / "baseline.json"),
                "code_sha256_canonical_lf": {"authored.py": sha(root / "authored.py", canonical=True)},
                "preparation_sha256": sha(prep / "prepared.json"), "cohort_sha256": sha(prep / "cohort.json"),
                "slots": [], "ceiling": CEILING, "segment_usd": .80, "configured_total_usd": 10,
                "config_without_key": configuration(provider), "required_main": "a" * 40}
            save(out, "prepared.json", manifest)
            with patch("scripts.missing_link_repository_only_run.ROOT", root), \
                 patch("scripts.missing_link_repository_only_run.PREP", prep), \
                 patch("scripts.missing_link_repository_only_run.git", return_value="") as git:
                frozen(out, provider, fetch=True)
                git.assert_any_call("fetch", "origin", "main")
                git.assert_any_call("merge-base", "--is-ancestor", "a" * 40, "origin/main")
                provider.error = "Authored provider unavailable"
                with self.assertRaises(EvaluationStopped): frozen(out, provider)
                provider.error = ""
                provider.max_tokens += 1
                with self.assertRaises(EvaluationStopped): frozen(out, provider)
                provider.max_tokens -= 1
                (root / "authored.py").write_text("# changed\n", encoding="utf-8")
                with self.assertRaises(EvaluationStopped): frozen(out, provider)


if __name__ == "__main__":
    unittest.main()
