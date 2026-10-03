"""Declarations stay type context, not the ID of an acquired runtime mechanism."""
import copy
import unittest
from unittest import mock

from missing_link.context import build_context, capability_path
from missing_link.discovery import _path
from missing_link.provider import Provider
from missing_link.sources import extract_structure, _safe_path, source_role
import test_missing_link as fixtures


class ImplementationSelectionTests(unittest.TestCase):
    def repository(self):
        repo = fixtures.repository()
        repo["files"] = [{"path": path, "text": text, "kind": "source",
            "url": "https://github.com/example/words/blob/" + "a" * 40 + "/" + path}
            for path, text in (
                ("index.js", "export default function escapeStringRegexp(value) {\n    return value.replace(/-/g, '\\\\x2d');\n}\n"),
                ("index.d.ts", "export default function escapeStringRegexp(value: string): string;\n"),
                ("other.js", "export function unrelated(value) { return value; }\n"))]
        repo["capabilities"] = extract_structure(repo)
        return repo

    def test_declaration_id_is_not_offered_as_runtime_capability_in_either_phase(self):
        repo = self.repository()
        before = copy.deepcopy(repo)
        runtime = next(cap for cap in repo["capabilities"] if cap["entrypoint"] == "index.js:escapeStringRegexp")
        declared = next(cap for cap in repo["capabilities"] if cap["entrypoint"] == "index.d.ts:escapeStringRegexp")
        for phase, issue in (("capabilities", None), ("matches", fixtures.issue())):
            with self.subTest(phase=phase):
                data, report = build_context(repo, issue, phase, 180000)
                self.assertIn(runtime["id"], report["capability_ids"])
                self.assertNotIn(declared["id"], report["capability_ids"])
                self.assertIn(declared["id"], report["omitted_capability_ids"])
                self.assertTrue(any(source.get("path") == "index.d.ts" for source in data["sources"].values()))
        self.assertEqual(repo, before)

    def test_enrichment_has_to_choose_the_runtime_id_not_transfer_type_ownership(self):
        repo = self.repository()
        before = copy.deepcopy(repo)
        provider = Provider({"REPOTRACTION_AI_URL": "http://localhost/v1", "REPOTRACTION_AI_MODEL": "fixture"})
        budget = mock.Mock()

        def completion(instruction, data, budget, schema, phase):
            candidates = data["repository"]["capabilities"]
            selected = next((cap for cap in candidates if cap["entrypoint"].startswith("index.d.ts:")), candidates[0])
            return {"capabilities": [{"id": selected["id"], "name": "Literal regex escaping",
                "summary": "Escape hyphens", "outcome": "Escaped text", "standalone": "yes",
                "source_ids": ["file:index.js#L1-L3"]}]}

        with mock.patch.object(provider, "complete", side_effect=completion), \
             mock.patch("urllib.request.build_opener", side_effect=AssertionError("No live provider")):
            enriched = provider.interpret_capabilities(repo, budget)
        self.assertEqual(enriched[0]["entrypoint"], "index.js:escapeStringRegexp")
        declared = next(cap for cap in enriched if cap["entrypoint"].startswith("index.d.ts:"))
        self.assertEqual(declared["claim_source"], "structural")
        self.assertEqual(declared["evidence"][0]["path"], "index.d.ts")
        self.assertNotIn("interpretation_source_ids", declared)
        budget.reserve_ai.assert_not_called()
        self.assertEqual(repo, before)

    def test_colon_paths_keep_runtime_identity_and_exclude_declarations_in_both_phases(self):
        repo = self.repository()
        repo["files"] = repo["files"][:2]
        for file, path in zip(repo["files"], ("src:legacy:compat/index.js", "types:legacy/index.d.ts")):
            self.assertTrue(_safe_path(path))
            file.update(path=path, url=file["url"].rsplit("/", 1)[0] + "/" + path)
        repo["capabilities"] = extract_structure(repo)
        before = copy.deepcopy(repo)
        runtime, declared = repo["capabilities"]
        self.assertEqual(capability_path(runtime), "src:legacy:compat/index.js")
        self.assertEqual(capability_path(declared), "types:legacy/index.d.ts")
        for phase, issue in (("capabilities", None), ("matches", fixtures.issue())):
            with self.subTest(phase=phase):
                data, report = build_context(repo, issue, phase, 180000)
                self.assertEqual(report["capability_ids"], [runtime["id"]])
                self.assertIn(declared["id"], report["declaration_context_only_capability_ids"])
                self.assertIn(declared["id"], report["omitted_capability_ids"])
                self.assertTrue(any(source.get("path") == "types:legacy/index.d.ts" for source in data["sources"].values()))
                self.assertFalse(report["implementation_context_missing"])
        self.assertEqual(repo, before)

    def test_path_decoding_preserves_colons_and_existing_evidence_fallback(self):
        for capability, expected in (
            ({"entrypoint": "types:legacy:compat/index.d.ts:onlyType"}, "types:legacy:compat/index.d.ts"),
            ({"entrypoint": "index.js:runtime"}, "index.js"),
            ({"entrypoint": "", "evidence": [{"path": "src:legacy/index.js"}]}, "src:legacy/index.js"),
            ({}, "unknown")):
            with self.subTest(capability=capability):
                self.assertEqual(capability_path(capability), expected)
                if capability:
                    self.assertEqual(_path(capability), expected)

    def test_source_roles_preserve_supported_colon_paths_and_legacy_entrypoints(self):
        for path, role in (("types:legacy/index.d.ts", "support"),
                           ("src:legacy/index.js", "implementation"),
                           ("tests/fixture:legacy.py", "test"),
                           ("tools/cli:legacy.js", "infrastructure")):
            with self.subTest(path=path):
                self.assertEqual(source_role(path), role)
                self.assertEqual(source_role(path + ":run"), role)
        scope = {"tools/cli:legacy.js"}
        self.assertEqual(source_role("tools/cli:legacy.js", runtime_entrypoints=scope), "implementation")
        self.assertEqual(source_role("tools/cli:legacy.js:run", runtime_entrypoints=scope), "implementation")

    def test_unrelated_runtime_name_does_not_merge_or_promote_a_type_candidate(self):
        repo = self.repository()
        repo["files"] = repo["files"][1:]
        repo["capabilities"] = extract_structure(repo)
        data, report = build_context(repo, None, "capabilities", 180000)
        self.assertEqual([cap["entrypoint"] for cap in data["repository"]["capabilities"]], ["other.js:unrelated"])
        self.assertEqual(len(repo["capabilities"]), 2)
        self.assertEqual(len(report["omitted_capability_ids"]), 1)

    def test_type_only_snapshot_keeps_structural_coverage_and_no_implementation_claim(self):
        repo = self.repository()
        repo["files"] = [repo["files"][1]]
        for path in ("index.d.ts", "types:legacy/index.d.ts"):
            with self.subTest(path=path):
                repo["files"][0]["path"] = path
                repo["capabilities"] = extract_structure(repo)
                data, report = build_context(repo, None, "capabilities", 180000)
                self.assertEqual(data["repository"]["capabilities"], [])
                self.assertTrue(report["implementation_context_missing"])
                self.assertEqual(len(repo["capabilities"]), 1)
                self.assertTrue(any(source.get("path") == path for source in data["sources"].values()))


if __name__ == "__main__":
    unittest.main()
