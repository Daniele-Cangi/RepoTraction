"""Offline preflight of the case bindings. Never contacts a paid provider."""
import importlib.util
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("cycle_bindings", Path(__file__).with_name("execution_bindings.py"))
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


class BindingsPreflight(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = patch.object(b, "DATA", Path(self.temp.name))
        self.root.start()
        self.addCleanup(self.root.stop)
        self.identity = patch.object(b, "verify_cli_account", return_value=b.ACCOUNT)
        self.identity.start()
        self.addCleanup(self.identity.stop)

    def test_clock_cannot_restart_and_expiry_blocks_helper(self):
        b.initialize("A")
        with self.assertRaises(ValueError):
            b.initialize("A")
        with self.assertRaises(b.Paused):
            b.verify("A", time.monotonic() - 1)

    def test_six_calls_and_aggregate_reservation_are_shared(self):
        b.initialize("A")
        for _ in range(6):
            model, budget = b.helper_budget("A")
            budget.reserve_ai(.0242048, model.max_calls, model.max_cost)
        model, budget = b.helper_budget("A")
        self.assertEqual(budget.job["ai_calls_used"], 6)
        self.assertAlmostEqual(b.store("A").ai_reserved(model.budget_id), .1452288)
        with self.assertRaises(b.Paused):
            budget.reserve_ai(.000001, model.max_calls, model.max_cost)
        with self.assertRaises(ValueError):
            b.store("A").reserve_ai_allowance(model.budget_id, "extra", .01, .15)

    def test_github_calls_share_the_original_120_cap(self):
        b.initialize("A")
        _, budget = b.helper_budget("A")
        budget.job["requests_used"] = 120
        budget.save()
        with patch.object(b, "fetch_get") as remote:
            with self.assertRaises(b.Paused):
                b.github("A", {"endpoint": "repos/networkx/networkx"})
            remote.assert_not_called()

    def test_expired_identity_and_public_endpoint_checks_fail_closed(self):
        b.initialize("A")
        with self.assertRaises(ValueError):
            b.github("A", {"endpoint": "repos/networkx/networkx/../../private"})
        with patch.object(b, "verify_cli_account", side_effect=RuntimeError("identity unverified")):
            with self.assertRaises(RuntimeError):
                b.note("A", {"instruction": "technical note", "data": {}})

    def test_standard_processing_and_symmetric_provider_bounds(self):
        for arm in ("A", "B"):
            b.initialize(arm)
            model = b.provider(arm)
            _, payload, body = model._encode_prompt("note", {}, None, "analysis")
            self.assertEqual(payload["service_tier"], "default")
            self.assertEqual(json.loads(body), payload)
            self.assertEqual((model.max_calls, model.max_bytes, model.max_tokens, model.max_cost),
                             (6, 180000, 12000, .15))
        self.assertNotEqual(b.provider("A").budget_id, b.provider("B").budget_id)

    def test_frozen_discussion_and_target_are_unchanged(self):
        frozen = json.loads((b.FROZEN / "frozen-inputs.json").read_text(encoding="utf-8"))
        self.assertEqual(b.digest(frozen), b.FINGERPRINT)
        self.assertEqual(frozen["target"]["revision"], b.PIN)
        service = object.__new__(b.FrozenService)
        service.frozen = frozen
        with patch.object(b.Service, "_prepare_request_discovery", side_effect=lambda job, source, *args: source) as native:
            source = service._prepare_request_discovery({}, object(), None, None, None)
            self.assertEqual(source.fetch_issue(frozen["issue"]["url"]), frozen["issue"])
            self.assertEqual(source.fetch_reference_context(frozen["issue"]), frozen["target"])
            with self.assertRaises(ValueError):
                source.fetch_issue("https://github.com/other/project/issues/1")
            native.assert_called_once()

    def packet_fixture(self):
        repo = {"public": True, "id": 1, "revision": "a" * 40, "coverage": {},
            "files": [{"path": "README.md", "text": "A documented operation.\nSecond line.\n",
                       "sha": "b" * 40, "url": "https://github.com/example/fixture/blob/" + "a" * 40 + "/README.md"}]}
        issue = {"url": "https://github.com/networkx/networkx/issues/8128"}
        evidence = b.resolve_evidence("file:README.md", b.evidence_catalog(repo, issue))
        evidence.update(source_id="file:README.md", sha="b" * 40)
        item = {"repo": "example/fixture", "repo_id": 1, "revision": "a" * 40,
            "title": "Fixture", "mechanism": "Hypothetical operation", "relevance": "pertinent",
            "reason": "Fixture only", "requirement_ids": ["r0"], "evidence": [evidence],
            "adaptation": [], "assumptions": [], "limitations": [], "direct_alternative": "unknown",
            "expected_advantage": "untested", "verification": {"status": "not_executed"},
            "benefit_status": "not_tested"}
        return {"status": "completed", "result": {"strategies": {"0": {"items": [item]}}},
                "checkpoint": {"repository": repo, "discussions": {"0": issue}}}

    def test_packet_preserves_whole_file_final_newline_and_native_ranges(self):
        job = self.packet_fixture()
        result = json.loads(b.packet(job))
        self.assertTrue(result["evidence"][0]["quote"].endswith("\n"))
        item = job["result"]["strategies"]["0"]["items"][0]
        evidence = b.resolve_evidence("file:README.md#L2", b.evidence_catalog(
            job["checkpoint"]["repository"], job["checkpoint"]["discussions"]["0"]))
        evidence.update(source_id="file:README.md#L2", sha="b" * 40)
        item["evidence"] = [evidence]
        self.assertEqual(json.loads(b.packet(job))["evidence"][0]["quote"], "Second line.")

    def test_packet_does_not_substitute_later_item_or_trim_evidence(self):
        job = self.packet_fixture()
        items = job["result"]["strategies"]["0"]["items"]
        items.insert(0, dict(items[0], relevance="undetermined"))
        self.assertIsNone(b.packet(job))
        items.pop(0)
        items[0]["evidence"][0]["quote"] = "Different text"
        with self.assertRaises(ValueError):
            b.packet(job)

    def test_note_context_is_not_given_a_smaller_32k_limit(self):
        b.initialize("A")
        with patch.object(b.RecordedProvider, "complete", return_value={"notes": "fixture"}) as call:
            b.note("A", {"instruction": "note", "data": {"public": "word " * 8000}})
            call.assert_called_once()


if __name__ == "__main__":
    unittest.main(verbosity=2)
