"""Partial implementation anchors belong to the selected structural capability."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from missing_link.analysis import ANALYSIS_CONTRACT_VERSION, validate_matches
from missing_link.provider import Provider, CandidateValidationError
from missing_link.service import Service
from missing_link.store import Store
import test_missing_link_partial_support as partial_fixtures


class PartialCapabilityTests(unittest.TestCase):
    def case(self):
        repo, issue, request, raw = partial_fixtures.PartialSupportTests().case()
        file = {"path": "other.py", "text": "def hash_blob(value):\n    return hash(value)\n",
                "url": "https://github.com/example/words/blob/" + "a" * 40 + "/other.py", "kind": "source"}
        repo["files"].append(file)
        other = copy.deepcopy(repo["capabilities"][0])
        other.update(id="hash_blob", name="hash_blob", summary="Hash a blob",
            definition={"path": "other.py", "line": 1, "end_line": 2},
            evidence=[{"path": "other.py", "line": 1, "end_line": 2,
                "quote": file["text"].rstrip(), "url": file["url"], "kind": "declaration"}])
        repo["capabilities"].append(other)
        raw.setdefault("obstacles", [])
        return repo, issue, request, raw

    def assert_contribution(self, case, expected, *, provider_excluded=False):
        repo, issue, request, raw = case
        original = copy.deepcopy(case)
        results = [validate_matches([copy.deepcopy(raw)], repo, issue, request, source)[0]
                   for source in ("model", "coding_agent_import")]
        provider = Provider({"REPOTRACTION_AI_URL": "http://localhost/v1", "REPOTRACTION_AI_MODEL": "fixture"})
        budget = mock.Mock()
        with mock.patch.object(provider, "complete", return_value={"matches": [copy.deepcopy(raw)]}), \
             mock.patch("urllib.request.build_opener", side_effect=AssertionError("No live model calls")) as network:
            if provider_excluded:
                with self.assertRaisesRegex(CandidateValidationError, "not included in this call"):
                    provider.evaluate(repo, issue, request, budget)
            else:
                results.append(provider.evaluate(repo, issue, request, budget)[0])
        network.assert_not_called()
        budget.reserve_ai.assert_not_called()
        for match in results:
            self.assertEqual(match["checks"][0]["contribution"], expected)
            self.assertEqual(match["checks"][0]["status"], "undetermined")
            self.assertEqual(match["checks"][0]["partial_support"], raw["partial_support"][0])
            self.assertEqual(match["discovery_assessment"]["partial_requirement_ids"],
                             ["r0"] if expected == "partial_behavior" else [])
            self.assertFalse(match["discovery_assessment"]["eligible_for_followup"])
        self.assertEqual(case, original)

    def test_foreign_capability_anchors_cannot_launder_partial_credit(self):
        for refs in (["file:other.py"], ["file:other.py#L1-L2"], ["c1:0"],
                     ["file:words.py", "file:other.py"], ["c0:0", "c1:0"]):
            with self.subTest(refs=refs):
                case = self.case()
                raw = case[3]
                raw["checks"][0]["source_ids"] = refs
                raw["partial_support"][0]["source_ids"] = refs
                self.assert_contribution(case, "not_demonstrated")

    def test_selected_capability_anchors_keep_valid_partial_credit(self):
        for index, refs in ((0, ["file:words.py"]), (0, ["file:words.py#L1-L3"]),
                            (0, ["c0:0"]), (1, ["file:other.py"]), (1, ["c1:0"])):
            with self.subTest(index=index, refs=refs):
                case = self.case()
                repo, _, _, raw = case
                raw["capability_id"] = repo["capabilities"][index]["id"]
                raw["checks"][0]["source_ids"] = refs
                raw["partial_support"][0]["source_ids"] = refs
                self.assert_contribution(case, "partial_behavior")

    def test_selected_definition_path_is_valid_even_when_evidence_is_in_wrapper(self):
        case = self.case()
        repo, _, _, raw = case
        repo["capabilities"][0]["definition"] = {"path": "other.py", "line": 1, "end_line": 2}
        raw["checks"][0]["source_ids"] = ["file:other.py#L1-L2"]
        raw["partial_support"][0]["source_ids"] = ["file:other.py#L1-L2"]
        self.assert_contribution(case, "partial_behavior")

    def test_model_interpretation_citations_cannot_expand_structural_ownership(self):
        case = self.case()
        repo, _, _, raw = case
        repo["capabilities"][0]["interpretation_source_ids"] = ["file:other.py"]
        raw["checks"][0]["source_ids"] = ["file:other.py"]
        raw["partial_support"][0]["source_ids"] = ["file:other.py"]
        self.assert_contribution(case, "not_demonstrated")

    def test_missing_selected_evidence_and_definition_fail_closed(self):
        case = self.case()
        case[0]["capabilities"][0]["evidence"] = []
        self.assert_contribution(case, "not_demonstrated")

    def test_owned_docs_tests_types_and_tools_still_do_not_count_as_implementation(self):
        for path in ("README.md", "tests/check.py", "src/trim.d.ts", "scripts/trim.py"):
            with self.subTest(path=path):
                case = self.case()
                repo, _, _, raw = case
                repo["files"][0]["path"] = path
                repo["capabilities"][0]["evidence"][0]["path"] = path
                repo["capabilities"][0]["definition"] = {"path": path, "line": 1, "end_line": 3}
                raw["checks"][0]["source_ids"] = ["file:" + path]
                raw["partial_support"][0]["source_ids"] = ["file:" + path]
                self.assert_contribution(case, "not_demonstrated", provider_excluded=path.endswith(".d.ts"))

    def test_contract21_and22_history_is_preserved_but_not_current(self):
        repo, issue, request, raw = self.case()
        for version in (21, 22):
            with self.subTest(version=version):
                with mock.patch("missing_link.analysis.ANALYSIS_CONTRACT_VERSION", version):
                    historical = validate_matches([copy.deepcopy(raw)], repo, issue, request, "model")[0]
                current = validate_matches([raw], repo, issue, request, "model")[0]
                self.assertEqual(ANALYSIS_CONTRACT_VERSION, 23)
                self.assertNotEqual(historical["id"], current["id"])
                with tempfile.TemporaryDirectory() as directory:
                    store = Store(Path(directory) / "fixture.sqlite3", "fixture")
                    store.put("repositories", repo["id"], repo)
                    store.put("matches", historical["id"], historical)
                    service = Service(store.path, "fixture", mock.Mock(side_effect=AssertionError("No GitHub calls")),
                                      lambda: "fixture", Provider({}))
                    self.assertTrue(service.state()["matches"][0]["stale"])
                    self.assertEqual(store.get("matches", historical["id"]), historical)
                    self.assertEqual(store.ai_reserved("fixture"), 0)


if __name__ == "__main__":
    unittest.main()
