"""Authored inquiry fixtures verify bounds and control flow, not model quality."""
import copy
import io
import json
import unittest
from unittest import mock

from missing_link.analysis import validate_request
from missing_link.discovery_decisions import resolve_inquiry
from missing_link.sources import PublicGitHub
from test_missing_link import issue, request_raw, repository
import test_missing_link_request_discovery as baseline
from test_missing_link_sources import GitHubFixture, REVISION, TREE


def proposal(kind="read_target"):
    return {"decision": kind, "reason": "Inspect the target operation before estimating direct adequacy.",
        "question": "Does the target already preserve word boundaries?",
        "expected_decision_change": "Existing support favors direct correction; an absent operation may justify search.",
        "requirement_ids": ["r0"], "file_ids": ["f0"] if kind == "read_target" else []}


class InquiryTests(unittest.TestCase):
    def setUp(self):
        baseline.RequestDiscoveryTests.setUp(self)
        self.mode = "defer"
        self.probe = proposal()
        self.target = self.source.fetch_reference_context.return_value
        self.target["file_catalog"] = {"entries": [{"id": "f0", "path": "src/format.py", "sha": "c" * 40,
                                                   "kind": "source"}], "complete": True}
        self.evidence = dict(self.target, files=[{"path": "src/format.py", "sha": "c" * 40,
            "url": "https://github.com/example/site/blob/" + "b" * 40 + "/src/format.py",
            "text": "target-code " * 1000, "kind": "source"}], coverage={"files_scanned": 1, "complete": False})
        self.source.fetch_repository.side_effect = lambda *a, **k: self.evidence if "selected_paths" in k else repository()

    def response(self, req, **kwargs):
        payload = json.loads(req.data)
        data = json.loads(payload["messages"][1]["content"].split("\nUNTRUSTED_DATA_JSON:\n")[-1])
        if "inquiry_version" not in data:
            return baseline.RequestDiscoveryTests.response(self, req, **kwargs)
        self.wires.append(data)
        return io.BytesIO(json.dumps({"choices": [{"message": {"content": json.dumps(self.probe)}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50}}).encode())

    def run_job(self, resume=None):
        with mock.patch("missing_link.service.PublicGitHub", return_value=self.source), \
                mock.patch("missing_link.service.extract_structure", return_value=self.structure), \
                mock.patch("urllib.request.build_opener") as opener:
            opener.return_value.open.side_effect = self.response
            ack = (self.service.resume({"job_id": resume}, background=False) if resume else
                self.service.start({"action": "discover_from_request", "issue_url": issue()["url"],
                    "use_ai": True, "targeted_inquiry": True}, background=False))
        return self.service.store.get("jobs", ack["job_id"])

    def test_exact_selected_evidence_reaches_final_decision_and_public_report_keeps_provenance(self):
        job = self.run_job()
        self.assertEqual(job["status"], "completed", job.get("error"))
        self.assertEqual(job["ai_calls_used"], 3)
        self.source.fetch_repository.assert_called_once_with("example/site", max_files=3,
            pinned_revision="b" * 40, selected_paths=["src/format.py"])
        wire = self.wires[-1]["target_inquiry"]
        self.assertEqual(len(wire["evidence"]["files"][0]["text"]), 8000)
        self.assertTrue(wire["evidence"]["files"][0]["truncated"])
        public = self.service.state()["jobs"][0]["result"]["target_inquiry"]
        self.assertNotIn("text", public["evidence"]["files"][0])
        self.assertEqual(public["file_catalog"], self.wires[1]["file_catalog"])
        self.assertEqual(public["evidence"]["revision"], "b" * 40)
        self.assertFalse(public["qualified"])
        self.source.search_repositories.assert_not_called()

    def test_inquiry_can_continue_into_existing_donor_comparison_with_six_calls(self):
        self.mode = "search"
        job = self.run_job()
        self.assertEqual(job["status"], "completed", job.get("error"))
        self.assertEqual(job["ai_calls_used"], 6)
        self.assertEqual(job["checkpoint"]["evaluated"], ["0"])
        self.assertEqual(self.source.fetch_repository.call_count, 2)

    def test_none_does_not_acquire_target_files_or_force_search(self):
        self.probe = proposal("none")
        job = self.run_job()
        self.assertEqual(job["status"], "completed", job.get("error"))
        self.assertEqual(job["ai_calls_used"], 3)
        self.source.fetch_repository.assert_not_called()
        self.source.search_repositories.assert_not_called()

    def test_invalid_inquiry_stops_before_selected_read(self):
        self.probe["file_ids"] = ["invented"]
        job = self.run_job()
        self.assertEqual(job["status"], "failed")
        self.assertEqual(job["ai_calls_used"], 2)
        self.source.fetch_repository.assert_not_called()

    def test_identity_change_and_wrong_blob_stop_before_final_decision(self):
        for change in ("id", "revision", "sha"):
            with self.subTest(change=change):
                original = copy.deepcopy(self.evidence)
                if change == "sha":
                    self.evidence["files"][0]["sha"] = "d" * 40
                else:
                    self.evidence[change] = 999 if change == "id" else "d" * 40
                job = self.run_job()
                self.assertEqual(job["status"], "failed")
                self.assertEqual(job["ai_calls_used"], 2)
                self.evidence = original

    def test_explicit_resume_reuses_inquiry_and_reads_after_call_budget_pause(self):
        self.provider.max_calls = 2
        first = self.run_job()
        self.assertEqual(first["status"], "paused", first.get("error"))
        self.provider.max_calls = 3
        job = self.run_job(first["id"])
        self.assertEqual(job["status"], "completed", job.get("error"))
        self.assertEqual(job["ai_calls_used"], 3)
        self.source.fetch_repository.assert_called_once()
        self.assertEqual(sum("inquiry_version" in w for w in self.wires), 1)

    def test_missing_selected_file_stops_before_final_decision_without_replacement(self):
        self.evidence["files"] = []
        self.evidence["coverage"]["excluded"] = {"credential_looking_content": 1}
        job = self.run_job()
        self.assertEqual(job["status"], "failed", job.get("error"))
        self.assertEqual(job["ai_calls_used"], 2)
        self.assertNotIn("inquiry_evidence", job["checkpoint"])
        self.assertNotIn("discovery_decision", job["result"])
        self.source.fetch_repository.assert_called_once()
        self.source.search_repositories.assert_not_called()

    def test_partial_selected_set_cannot_be_checkpointed_as_completed_inquiry(self):
        self.target["file_catalog"]["entries"].append({"id": "f1", "path": "src/other.py", "sha": "d" * 40, "kind": "source"})
        self.probe["file_ids"].append("f1")
        job = self.run_job()
        self.assertEqual(job["status"], "failed", job.get("error"))
        self.assertEqual(job["ai_calls_used"], 2)
        self.assertNotIn("inquiry_evidence", job["checkpoint"])
        self.source.fetch_repository.assert_called_once()

    def test_account_switch_after_choice_prevents_the_read(self):
        response = self.response
        def changed(req, **kwargs):
            output = response(req, **kwargs)
            if len(self.wires) == 2:
                self.account = "bob"
            return output
        with mock.patch.object(self, "response", side_effect=changed):
            job = self.run_job()
        self.assertNotEqual(job["status"], "completed")
        self.source.fetch_repository.assert_not_called()

    def test_inquiry_cannot_expand_ids_paths_requirements_or_output_bounds(self):
        request = validate_request(request_raw(), issue())
        for raw in (dict(proposal(), file_ids=["f0", "f0"]), dict(proposal(), file_ids=["../secret"]),
                    dict(proposal(), question=""), dict(proposal(), requirement_ids=["r90"]),
                    dict(proposal("none"), file_ids=["f0"]), dict(proposal(), reason="x" * 25000)):
            with self.subTest(raw=str(raw)[:60]), self.assertRaises(ValueError):
                resolve_inquiry(raw, request, self.target)


class InquiryAcquisitionTests(unittest.TestCase):
    def setUp(self):
        self.fixture = GitHubFixture()
        self.fixture.add("pyproject.toml", "[project]\nname='fixture'")
        self.fixture.add("src/operation.py", "from .helper import helper\ndef operation(x): return helper(x)")
        self.fixture.add("src/helper.py", "def helper(x): return x")
        self.fixture.add("secrets.py", "bad")
        self.fixture.add("linked.py", "src/operation.py", mode="120000")
        self.source = PublicGitHub(self.read)

    def read(self, endpoint, params=None):
        if endpoint == f"repos/sample/project/commits/{REVISION}":
            self.fixture.calls.append((endpoint, params))
            return {"sha": REVISION, "commit": {"tree": {"sha": TREE}}}
        return self.fixture.read(endpoint, params)

    def test_catalog_uses_same_filtered_tree_without_extra_blob_reads(self):
        initial = self.source.fetch_repository("sample/project", reference_paths=[], include_catalog=True)
        paths = [i["path"] for i in initial["file_catalog"]["entries"]]
        self.assertIn("src/operation.py", paths)
        self.assertNotIn("linked.py", paths)
        self.assertEqual(sum("/git/blobs/" in call[0] for call in self.fixture.calls), 1)
        self.assertNotIn("file_catalog", self.source.fetch_repository("sample/project", reference_paths=[]))

    def test_selected_read_is_pinned_exact_and_does_not_follow_imports(self):
        result = self.source.fetch_repository("sample/project", max_files=3,
            pinned_revision=REVISION, selected_paths=["src/operation.py"])
        self.assertEqual([f["path"] for f in result["files"]], ["src/operation.py"])
        self.assertEqual(sum("/git/blobs/" in c[0] for c in self.fixture.calls), 1)
        self.assertIn((f"repos/sample/project/commits/{REVISION}", None), self.fixture.calls)

    def test_unsafe_unoffered_and_secret_content_do_not_read_replacements(self):
        for paths in (["../secret.py"], ["linked.py"], ["missing.py"], ["src/operation.py"] * 4):
            with self.subTest(paths=paths), self.assertRaises(ValueError):
                self.source.fetch_repository("sample/project", max_files=3, pinned_revision=REVISION, selected_paths=paths)
        self.fixture.add("credential.py", "token = 'ghp_" + "A" * 36 + "'")
        result = self.source.fetch_repository("sample/project", max_files=3,
            pinned_revision=REVISION, selected_paths=["credential.py"])
        self.assertEqual(result["files"], [])
        self.assertEqual(result["coverage"]["excluded"]["credential_looking_content"], 1)

    def test_catalog_bounds_and_redacted_paths_are_explicit(self):
        self.fixture.add("ghp_" + "A" * 36 + ".py", "pass")
        for i in range(400):
            self.fixture.add(f"folder/long_name_{i:03d}.py", "pass")
        result = self.source.fetch_repository("sample/project", reference_paths=[], include_catalog=True)
        catalog = result["file_catalog"]
        self.assertLessEqual(len(catalog["entries"]), 300)
        self.assertLessEqual(sum(len(json.dumps(e, ensure_ascii=False).encode()) for e in catalog["entries"]), 24000)
        self.assertGreater(catalog["omitted"], 0)
        self.assertFalse(catalog["complete"])
        self.assertNotIn("ghp_", json.dumps(catalog))

    def test_documentation_directory_cannot_fill_catalogue_before_any_implementation(self):
        for i in range(400):
            self.fixture.add(f"docs/a{i:03d}.md", "Reference documentation")
        result = self.source.fetch_repository("sample/project", reference_paths=[], include_catalog=True)
        self.assertIn("src/operation.py", [e["path"] for e in result["file_catalog"]["entries"]])


if __name__ == "__main__":
    unittest.main()
