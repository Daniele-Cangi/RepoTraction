"""Tests for the frozen study's selector and native-test glue, without target imports."""
import importlib.util
import json
from pathlib import Path
import unittest


STUDY = Path(__file__).resolve().parents[1] / "docs/experiments/demand-first-target-2026-10-11"


def load(name):
    spec = importlib.util.spec_from_file_location(name, STUDY / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DemandFirstStudyTests(unittest.TestCase):
    def setUp(self):
        self.selector = load("discover_sources")
        self.protocol = json.loads((STUDY / "protocol.json").read_text(encoding="utf-8"))
        self.batches = json.loads((STUDY / "search-results.json").read_text(encoding="utf-8"))["batches"]

    def test_frozen_selection_replays_without_package_substitutions(self):
        selected = self.selector.select(self.protocol, self.batches)
        self.assertEqual([row["repository"] for row in selected],
                         ["sebastianruder/NLP-progress", "dmort27/panphon", "hearsaycorp/normalize"])
        self.assertEqual([row["upstream_rank"] for row in selected], [1, 1, 1])
        with self.assertRaises(ValueError):
            self.selector.select(self.protocol, list(reversed(self.batches)))

    def test_selection_excludes_target_duplicates_and_ineligible_sources(self):
        self.batches[0]["items"] = [dict(full_name=self.protocol["target_repository"]),
                                    dict(full_name="a/valid"), dict(full_name="next/valid")]
        self.batches[1]["items"] = [dict(full_name="a/valid"), dict(full_name="no/private", private=True)]
        self.batches[2]["items"] = [dict(full_name="no/archived", archived=True),
                                    dict(full_name="no/fork", fork=True), dict(full_name="no/lang", language="Go")]
        self.assertEqual([r["repository"] for r in self.selector.select(self.protocol, self.batches)],
                         ["a/valid", "next/valid"])

    def test_direct_key_preserves_frozen_acceptance_and_rejects_wrong_target(self):
        native = load("native_http")
        namespace = {}
        exec("import unicodedata\n" + native.DIRECT_KEY, namespace)
        key = namespace["_author_order_key"]
        cases = json.loads((STUDY / "acceptance.json").read_text(encoding="utf-8"))
        for case in cases:
            with self.subTest(case=case["id"]):
                self.assertEqual(sorted(case["names"], key=key), case["expected"])
        for source in ("", native.OLD_KEY, "def get_sorted_entries():\n    pass"):
            with self.assertRaises(ValueError):
                native.direct_correction(source)

    def test_http_parser_reads_rendered_rows_only(self):
        parser = load("native_http").Entries()
        parser.feed('<div id="1" class="navigation"></div><div class="entry_row even" id="12"></div>')
        self.assertEqual(parser.ids, [12])
