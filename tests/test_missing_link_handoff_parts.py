"""Lossless bounded inspection packaging, never acquired-code execution."""
import copy
import hashlib
import io
import json
import unittest
import zipfile
from unittest import mock

from missing_link.proofs import (MAX_FILE_BYTES, MAX_PACKAGE_BYTES, PackageLimitError,
                                 _add_handoff, _json_bytes, build_package, export_handoff)
import test_missing_link_proofs as fixtures


class HandoffPartsTests(unittest.TestCase):
    def case(self, size=180_000):
        match, repo = fixtures.fixture()
        match["source_issue"] = {"public": True, "body": "Original discussion: " + "é🙂" * (size // 6),
                                 "comments": [], "context_complete": True}
        return match, repo

    def test_large_handoff_is_lossless_under_unchanged_file_and_package_bounds(self):
        match, repo = self.case()
        before = copy.deepcopy((match, repo))
        expected = export_handoff(match, repo)
        with zipfile.ZipFile(io.BytesIO(build_package(match, repo))) as archive:
            index = json.loads(archive.read("handoff.json"))
            self.assertEqual(index["schema_version"], 2)
            self.assertEqual(index["format"], "chunked_handoff")
            self.assertEqual(index["verification"]["status"], "not_executed")
            raw = b""
            for part in index["parts"]:
                fragment = archive.read(part["path"])
                fragment.decode("utf-8")
                self.assertEqual(len(fragment), part["bytes"])
                self.assertLessEqual(len(fragment), MAX_FILE_BYTES)
                self.assertEqual(hashlib.sha256(fragment).hexdigest(), part["sha256"])
                raw += fragment
            self.assertEqual(len(raw), index["bytes"])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), index["sha256"])
            complete = json.loads(raw)
            packaged_evidence = complete.pop("packaged_evidence")
            self.assertTrue(packaged_evidence)
            self.assertEqual(complete, expected)
            self.assertIn(b"not the complete handoff", archive.read("HANDOFF.md"))
            manifest = json.loads(archive.read("manifest.json"))
            self.assertEqual(manifest["handoff_format"], "chunked_handoff")
            self.assertLessEqual(sum(info.file_size for info in archive.infolist()), MAX_PACKAGE_BYTES)
            for info in archive.infolist():
                self.assertLessEqual(info.file_size, MAX_FILE_BYTES)
            for item in manifest["files"]:
                self.assertEqual(hashlib.sha256(archive.read(item["path"])).hexdigest(), item["sha256"])
        self.assertEqual((match, repo), before)
        self.assertEqual(build_package(match, repo), build_package(match, repo))

    def test_small_handoff_keeps_the_original_complete_json_shape(self):
        match, repo = fixtures.fixture()
        with zipfile.ZipFile(io.BytesIO(build_package(match, repo))) as archive:
            handoff = json.loads(archive.read("handoff.json"))
            self.assertEqual(handoff["schema_version"], 1)
            self.assertEqual(handoff["match"]["id"], match["id"])
            self.assertFalse(any(path.startswith("handoff-parts/") for path in archive.namelist()))
            self.assertEqual(json.loads(archive.read("manifest.json"))["handoff_format"], "inline_handoff")

    def test_exact_boundary_stays_inline_and_over_boundary_uses_parts(self):
        payload = {"schema_version": 1, "verification": {"status": "not_executed"}, "text": ""}
        overhead = len(_json_bytes(payload))
        for size, chunked in ((MAX_FILE_BYTES, False), (MAX_FILE_BYTES + 1, True)):
            with self.subTest(size=size):
                payload["text"] = "x" * (size - overhead)
                contents = {}
                self.assertEqual(_add_handoff(payload, contents.__setitem__), chunked)
                if chunked:
                    index = json.loads(contents["handoff.json"])
                    self.assertEqual(b"".join(contents[part["path"]] for part in index["parts"]), _json_bytes(payload))
                else:
                    self.assertEqual(contents["handoff.json"], _json_bytes(payload))

    def test_handoff_above_total_bound_is_not_rescued_by_chunking(self):
        match, repo = self.case(MAX_PACKAGE_BYTES + 10_000)
        with self.assertRaises(PackageLimitError):
            build_package(match, repo)

    def test_overall_bound_includes_part_index_manifest_markdown_and_other_files(self):
        match, repo = self.case(240_000)
        with mock.patch("missing_link.proofs.MAX_PACKAGE_BYTES", len(_json_bytes(export_handoff(match, repo))) + 100):
            with self.assertRaises(PackageLimitError):
                build_package(match, repo)

    def test_generated_files_are_not_split_to_evade_the_file_bound(self):
        match, repo = self.case()
        match["bridge"]["files"] = [{"path": "large.py", "content": "x" * (MAX_FILE_BYTES + 1)}]
        with self.assertRaises(ValueError):
            build_package(match, repo)

    def test_redaction_occurs_before_chunking_and_no_execution_is_invoked(self):
        match, repo = self.case()
        token = "ghp_" + "x" * 36
        match["source_issue"]["body"] += token
        with mock.patch("subprocess.run", side_effect=AssertionError("No acquired-code execution")):
            package = build_package(match, repo)
        with zipfile.ZipFile(io.BytesIO(package)) as archive:
            index = json.loads(archive.read("handoff.json"))
            raw = b"".join(archive.read(part["path"]) for part in index["parts"])
            self.assertNotIn(token.encode(), raw)
            self.assertIn(b"REDACTED CREDENTIAL", raw)


if __name__ == "__main__":
    unittest.main()
