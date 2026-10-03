"""Declarations stay type context, not the ID of an acquired runtime mechanism."""
import copy
import unittest
from unittest import mock

from missing_link.context import build_context
from missing_link.provider import Provider
from missing_link.sources import extract_structure
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
        repo["capabilities"] = extract_structure(repo)
        data, report = build_context(repo, None, "capabilities", 180000)
        self.assertEqual(data["repository"]["capabilities"], [])
        self.assertTrue(report["implementation_context_missing"])
        self.assertEqual(len(repo["capabilities"]), 1)
        self.assertTrue(any(source.get("path") == "index.d.ts" for source in data["sources"].values()))


if __name__ == "__main__":
    unittest.main()
