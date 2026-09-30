"""Fixture tests exercise packaging; they are not live capability proofs."""

import hashlib
import io
import json
import sys
import unittest
import zipfile
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from missing_link.proofs import build_package, export_handoff, isolation_status, safe_relative_path


def fixture():
    match = {
        "id": "fixture-match", "repo": "fixture/library", "revision": "a" * 40,
        "classification": "adapter", "summary": "Fixture-only request and bridge.",
        "request": {"id": "fixture-request", "title": "Fixture requirement", "url": "https://github.com/fixture/app/issues/1", "updated_at": "2026-09-30T00:00:00Z", "fingerprint": "fixture-fingerprint", "context_complete": True,
                    "requirements": [{"id": "r1", "text": "Keep complete words", "mandatory": True, "explicit": True, "source": {"url": "https://github.com/fixture/app/issues/1", "quote": "Keep complete words"}}]},
        "capability": {"evidence": [{"path": "library.py", "line": 2, "end_line": 3, "url": "https://github.com/fixture/library/blob/" + "a" * 40 + "/library.py#L2-L3"}]},
        "bridge": {"kind": "adapter", "summary": "Fixture proposal", "existing_contribution": "Boundary handling", "new_logic": "CLI wrapper", "steps": ["Review the package"], "files": [{"path": "example.py", "content": "# inspection only\n"}], "success_criteria": ["Optional wrapper check"], "verification": {"status": "passed"}},
    }
    repo = {"full_name": "fixture/library", "revision": "a" * 40, "license": {"spdx_id": "MIT"}, "files": {"library.py": "# fixture source\ndef boundary(value):\n    return value\n", "LICENSE": "Fixture license metadata only"}, "api_key": "never-export-me", "database_path": "C:/Users/private.sqlite3"}
    match["capability_id"] = match["capability"]["id"] = "fixture-capability"
    repo["capabilities"] = [dict(match["capability"])]
    return match, repo


class ProofPackagingTests(unittest.TestCase):
    def test_package_contains_pinned_evidence_and_license_with_integrity_hashes(self):
        match, repo = fixture()
        with zipfile.ZipFile(io.BytesIO(build_package(match, repo))) as archive:
            manifest = json.loads(archive.read("manifest.json"))
            self.assertEqual(manifest["revision"], "a" * 40)
            self.assertEqual(manifest["request"]["fingerprint"], "fixture-fingerprint")
            self.assertEqual(manifest["verification"]["status"], "not_executed")
            self.assertEqual(archive.read("evidence/01-library.py.txt"), b"def boundary(value):\n    return value\n")
            self.assertIn("licenses/LICENSE", archive.namelist())
            for item in manifest["files"]:
                self.assertEqual(hashlib.sha256(archive.read(item["path"])).hexdigest(), item["sha256"])
                self.assertEqual(len(archive.read(item["path"])), item["bytes"])
            self.assertNotIn(b"never-export-me", archive.read("handoff.json"))
            self.assertNotIn(b"private.sqlite3", archive.read("handoff.json"))

    def test_rejects_windows_and_posix_unsafe_paths(self):
        for path in ("../outside", "/absolute", "C:/private", "a\\b", "a//b", "a/./b", "NUL.txt", "a/CON", "a/COM1.log", "x. ", "a:stream", "a\x00b", "LPT9", "b?", "CONIN$", "COM¹.txt"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                safe_relative_path(path)
        self.assertEqual(safe_relative_path("src/example.py"), "src/example.py")

    def test_path_validation_applies_to_bridge_and_case_insensitive_duplicates(self):
        match, repo = fixture()
        for files in ([{"path": "../private.txt", "content": "x"}], [{"path": "a.py", "content": "x"}, {"path": "A.py", "content": "y"}], [{"path": "src", "content": "x"}, {"path": "src/a.py", "content": "y"}]):
            match["bridge"]["files"] = files
            with self.assertRaises(ValueError):
                build_package(match, repo)
            with self.assertRaises(ValueError):
                export_handoff(match, repo)

    def test_limits_files_and_uncompressed_size(self):
        match, repo = fixture()
        match["bridge"]["files"] = [{"path": "x.py", "content": "x" * 128001}]
        with self.assertRaises(ValueError):
            build_package(match, repo)
        match["bridge"]["files"] = [{"path": f"{index}.py", "content": "x"} for index in range(33)]
        with self.assertRaises(ValueError):
            build_package(match, repo)

    def test_redacts_credentials_without_reading_paths_or_executing(self):
        match, repo = fixture()
        match["bridge"]["files"][0]["content"] = "token='ghp_" + "x" * 36 + "'\n"
        with mock.patch("subprocess.run", side_effect=AssertionError("No host execution")), mock.patch.object(Path, "read_text", side_effect=AssertionError("No local file reading")):
            package = build_package(match, repo)
        with zipfile.ZipFile(io.BytesIO(package)) as archive:
            self.assertIn(b"REDACTED CREDENTIAL", archive.read("bridge/example.py"))
            self.assertNotIn(b"ghp_", archive.read("bridge/example.py"))
            handoff = json.loads(archive.read("handoff.json"))
            self.assertIn("Credential-shaped content was redacted.", handoff["warnings"])

    def test_original_requirements_and_added_checks_remain_distinct(self):
        match, repo = fixture()
        handoff = export_handoff(match, repo)
        self.assertEqual(handoff["acceptance_criteria_from_request"][0]["text"], "Keep complete words")
        self.assertEqual(handoff["bridge_additional_checks"], ["Optional wrapper check"])
        self.assertEqual(handoff["verification"]["label"], "NOT EXECUTED")
        self.assertFalse(isolation_status()["available"])

    def test_warns_about_unpinned_revision_and_partial_discussion(self):
        match, repo = fixture()
        match["revision"] = "main"
        repo["revision"] = "main"
        match["request"]["context_complete"] = False
        handoff = export_handoff(match, repo)
        self.assertEqual(len(handoff["warnings"]), 2)

    def test_rejects_revision_mismatch_private_snapshots_and_symlink_files(self):
        match, repo = fixture()
        repo["revision"] = "b" * 40
        with self.assertRaises(ValueError):
            export_handoff(match, repo)
        repo["revision"] = "a" * 40
        repo["private"] = True
        with self.assertRaises(ValueError):
            export_handoff(match, repo)
        repo["private"] = False
        match["bridge"]["files"][0]["type"] = "symlink"
        with self.assertRaises(ValueError):
            build_package(match, repo)

    def test_output_is_reproducible_and_supports_list_snapshot_files(self):
        match, repo = fixture()
        repo["files"] = [{"path": path, "text": content} for path, content in repo["files"].items()]
        self.assertEqual(build_package(match, repo), build_package(match, repo))

    def test_exports_acquired_public_issue_context_but_not_private_context(self):
        match, repo = fixture()
        match["request"]["source_issue"] = {"public": True, "body": "Original public need", "comments": [{"body": "Later requirement", "url": "https://github.com/fixture/app/issues/1#issuecomment-1"}], "timeline": [], "context_complete": True, "credentials": "never"}
        handoff = export_handoff(match, repo)
        self.assertEqual(handoff["request"]["source_issue"]["comments"][0]["body"], "Later requirement")
        self.assertNotIn("credentials", handoff["request"]["source_issue"])
        match["request"]["source_issue"]["public"] = False
        with self.assertRaises(ValueError):
            export_handoff(match, repo)


if __name__ == "__main__":
    unittest.main()
