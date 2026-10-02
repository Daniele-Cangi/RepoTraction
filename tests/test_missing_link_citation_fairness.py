"""Later human demand citations survive long supplied root reports, offline."""
import copy
import json
import unittest
from unittest import mock

from missing_link.analysis import evidence_catalog
from missing_link.context import build_context
from missing_link.demand import citation_spans
from missing_link.provider import Provider
from test_missing_link import issue, request_raw, request_completion


class CitationFairnessTests(unittest.TestCase):
    def case(self):
        demand = issue()
        demand.update(body="\n".join(f"Report item {i}: " + "description " * 15 for i in range(180)),
            context_complete=False, comments=[
                {"url": demand["url"] + "#issuecomment-1", "body": "Please give feedback on this report and suggest improvements."},
                {"url": demand["url"] + "#issuecomment-2", "body": "The source translation keys should determine the direction."},
                {"url": demand["url"] + "#issuecomment-3", "body": "Please review the file-level scope too."}])
        return demand

    def test_long_report_cannot_consume_all_later_comment_citations(self):
        demand = self.case()
        original = copy.deepcopy(demand)
        data, _ = build_context(None, demand, "request", 180000)
        spans, report = citation_spans(data["sources"], evidence_catalog({}, demand), 18000)
        self.assertEqual({entry["source_id"] for entry in spans.values()}, {"q0", "q1", "q2", "q3"})
        self.assertLessEqual(len(json.dumps(spans, ensure_ascii=False).encode()), 18000)
        self.assertGreater(report["omitted_visible_spans"], 0)
        self.assertFalse(report["complete"])
        self.assertEqual(report["source_count_without_spans"], 0)
        self.assertEqual(demand, original)
        catalog = evidence_catalog({}, demand)
        for entry in spans.values():
            self.assertIn(entry["quote"], catalog[entry["source_id"]]["quote"])
            self.assertNotIn("[OMITTED MIDDLE]", entry["quote"])

    def test_later_feedback_is_extractable_without_fabricating_non_demand(self):
        demand = self.case()
        raw = request_raw()
        raw["requirements"] = [dict(raw["requirements"][0], text="Review report and suggest improvements",
            source_id="q1", quote=demand["comments"][0]["body"])]
        provider = Provider({"REPOTRACTION_AI_URL": "http://localhost/v1", "REPOTRACTION_AI_MODEL": "fixture"})
        with mock.patch.object(provider, "complete", side_effect=request_completion(raw)) as complete:
            request = provider.interpret_request(demand, mock.Mock())
        complete.assert_called_once()
        self.assertEqual(request["requirements"][0]["source"]["source_id"], "q1")
        self.assertEqual(request["requirements"][0]["source"]["quote"], demand["comments"][0]["body"])
        self.assertEqual(request["status"], "unclear")
        self.assertFalse(request["context_complete"])

    def test_many_long_comments_do_not_evict_short_root_demand_clauses(self):
        demand = issue()
        demand["comments"] = [{"url": demand["url"] + f"#issuecomment-{i}", "body": "context " * 190}
                              for i in range(20)]
        data, _ = build_context(None, demand, "request", 180000)
        spans, report = citation_spans(data["sources"], evidence_catalog({}, demand), 18000)
        root_quotes = [entry["quote"] for entry in spans.values() if entry["source_id"] == "q0"]
        self.assertTrue(any("without splitting words" in quote for quote in root_quotes))
        self.assertIn("Must work in native CSS without Python.", root_quotes)
        self.assertFalse(report["complete"])

    def test_ids_are_original_offset_based_not_round_robin_position(self):
        catalog = {"q0": {"quote": "First sentence. Second sentence."}, "q1": {"quote": "Please review this."}}
        sources = {ref: dict(entry, url=f"https://example.test/{ref}") for ref, entry in catalog.items()}
        first, _ = citation_spans(sources, catalog, 18000)
        second, _ = citation_spans(dict(reversed(list(sources.items()))), catalog, 18000)
        self.assertEqual(first, second)

    def test_tiny_bound_reports_sources_that_could_not_fit(self):
        sources = {"q0": {"quote": "x" * 1500}, "q1": {"quote": "Please review."}}
        spans, report = citation_spans(sources, sources, 150)
        self.assertEqual({entry["source_id"] for entry in spans.values()}, {"q1"})
        self.assertEqual(report["sources_without_spans"], ["q0"])
        self.assertEqual(report["source_count_without_spans"], 1)
        self.assertFalse(report["complete"])

    def test_duplicate_visible_excerpts_keep_stable_unique_ids(self):
        original = "Head.\nKeep this constraint.\nTail."
        visible = original + "\n[SELECTED CONSTRAINT EXCERPT]\nKeep this constraint."
        sources = {"q0": {"quote": visible}}
        spans, _ = citation_spans(sources, {"q0": {"quote": original}}, 18000)
        self.assertEqual(sum(entry["quote"] == "Keep this constraint." for entry in spans.values()), 1)


if __name__ == "__main__":
    unittest.main()
