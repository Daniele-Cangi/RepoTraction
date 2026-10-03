"""Selected-operation bodies, not signatures or neighboring functions, earn credit."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from missing_link.analysis import validate_matches
from missing_link.context import build_context
from missing_link.provider import Provider
from missing_link.sources import extract_structure
from missing_link.store import Store
import test_missing_link_partial_support as partial_fixtures


class OperationEvidenceTests(unittest.TestCase):
    def case(self, source=None, name="failure", path="core.ts"):
        repo, issue, request, raw = partial_fixtures.PartialSupportTests().case()
        source = source or ("export function safeParse(schema, value) {\n"
            "    return schema.run(value);\n}\n"
            "function failure(issues) {\n    return {success: false, error: new Error(issues)};\n}\n")
        repo["files"] = [{"path": path, "kind": "source", "text": source,
            "url": "https://github.com/example/words/blob/" + "a" * 40 + "/" + path}]
        repo["capabilities"] = extract_structure(repo)
        cap = next(cap for cap in repo["capabilities"] if cap["entrypoint"].endswith(":" + name))
        raw["capability_id"] = cap["id"]
        raw.setdefault("obstacles", [])
        return repo, issue, request, raw

    def result(self, case, refs, expected):
        repo, issue, request, raw = case
        raw["checks"][0]["source_ids"] = refs
        raw["partial_support"][0]["source_ids"] = refs
        before = copy.deepcopy(case)
        for source in ("model", "coding_agent_import"):
            result = validate_matches([raw], repo, issue, request, source)[0]
            self.assertEqual(result["checks"][0]["contribution"], expected)
            self.assertEqual(result["checks"][0]["status"], "undetermined")
            self.assertEqual(result["checks"][0]["partial_support"], raw["partial_support"][0])
            self.assertFalse(result["discovery_assessment"]["eligible_for_followup"])
        self.assertEqual(case, before)
        return result

    def test_sibling_function_and_shared_file_excerpt_cannot_implement_selected_helper(self):
        for refs in (["file:core.ts#L1-L3"], ["file:core.ts"],
                     ["file:core.ts#L1-L6"], ["file:core.ts#L2-L2", "file:core.ts#L5-L5"]):
            with self.subTest(refs=refs):
                self.result(self.case(), refs, "not_demonstrated")

    def test_declaration_only_citation_does_not_prove_an_enum_extraction_body(self):
        case = self.case("export function getEnumValues(entries: EnumLike): EnumValue[] {\n"
            "    return Object.values(entries);\n}\n", name="getEnumValues")
        for refs in (["file:core.ts#L1-L1"], ["c0:0"]):
            with self.subTest(refs=refs):
                self.result(case, refs, "not_demonstrated")

    def test_actual_selected_body_and_multiple_precise_anchors_keep_partial_credit(self):
        for refs in (["file:core.ts#L4-L6"], ["file:core.ts#L5-L5"],
                     ["file:core.ts#L4-L4", "file:core.ts#L5-L6"]):
            with self.subTest(refs=refs):
                self.result(self.case(), refs, "partial_behavior")

    def test_empty_comment_only_or_ellipsis_body_stays_unknown(self):
        for source, name, path in (
            ("function empty() {\n    // Nothing is implemented.\n}\n", "empty", "core.js"),
            ("function empty() { }\n", "empty", "core.js"),
            ("def empty():\n    ...\n", "empty", "core.py"),
            ("def empty():\n    return ...\n", "empty", "core.py"),
            ("def empty():\n    result: str\n", "empty", "core.py"),
            ('def empty():\n    """An interface description."""\n    pass\n', "empty", "core.py")):
            with self.subTest(source=source):
                self.result(self.case(source, name=name, path=path), ["file:" + path], "not_demonstrated")

    def test_multiline_python_signature_is_not_body_but_forwarding_is(self):
        source = "def forward(\n    value,\n):\n    return delegate(value)\n\ndef unrelated(value):\n    return hash(value)\n"
        self.result(self.case(source, name="forward", path="core.py"), ["file:core.py#L1-L3"], "not_demonstrated")
        self.result(self.case(source, name="forward", path="core.py"), ["file:core.py#L1-L4"], "partial_behavior")
        self.result(self.case(source, name="forward", path="core.py"), ["file:core.py#L6-L7"], "not_demonstrated")

    def test_lexical_lookalikes_and_unclosed_javascript_are_not_body_proof(self):
        for source in ("/*\nfunction failure(issues) {\n return issues;\n}\n*/\n",
                       "function failure(issues) {\n return issues;\n",
                       "const quoted = `\nfunction failure(issues) {\n return issues;\n}\n`;\n"):
            with self.subTest(source=source):
                self.result(self.case(source), ["file:core.ts"], "not_demonstrated")

    def test_context_offers_exact_selected_implementation_span_before_broad_prefix(self):
        repo, issue, request, raw = self.case()
        data, report = build_context(repo, issue, "matches", 180000)
        self.assertIn("file:core.ts#L4-L6", data["sources"])
        self.assertLess(list(data["sources"]).index("file:core.ts#L4-L6"), list(data["sources"]).index("file:core.ts#L1-L6"))

    def test_claiming_full_support_cannot_bypass_the_body_gate(self):
        for reference in ("file:core.ts#L1-L3", "file:core.ts#L4-L4", "file:core.ts#L1-L6"):
            with self.subTest(reference=reference):
                repo, issue, request, raw = self.case()
                raw["checks"][0].update(status="satisfied", contribution="existing_behavior", source_ids=[reference])
                raw["partial_support"] = []
                result = validate_matches([raw], repo, issue, request, "model")[0]
                self.assertEqual(result["checks"][0]["status"], "undetermined")
                self.assertEqual(result["checks"][0]["contribution"], "not_demonstrated")
                self.assertFalse(result["discovery_assessment"]["eligible_for_followup"])

    def test_single_line_function_body_is_distinct_from_a_signature(self):
        case = self.case("function failure(issues) { return new Error(issues); }\n")
        self.result(case, ["file:core.ts#L1-L1"], "partial_behavior")
        repo, issue, request, raw = case
        repo["capabilities"][0]["evidence"][0]["quote"] = "function failure(issues)"
        self.result(case, ["c0:0"], "not_demonstrated")

    def test_exact_whole_operation_quote_accepts_line_terminators(self):
        for source, path in (("def failure(value):\n    return delegate(value)", "core.py"),
                             ("function failure(value) {\n    return delegate(value);\n}", "core.js")):
            for ending in ("", "\n", "\r\n"):
                with self.subTest(path=path, ending=ending):
                    text = source.replace("\n", "\r\n") + ending if ending == "\r\n" else source + ending
                    self.result(self.case(text, path=path), ["file:" + path], "partial_behavior")

    def test_same_line_sibling_cannot_be_separated_by_a_line_only_citation(self):
        self.result(self.case("function failure(issues) { return issues; } function other(x) { return parse(x); }\n"),
            ["file:core.ts#L1-L1"], "not_demonstrated")

    def test_truncated_quotes_cannot_borrow_body_words_from_docstrings_or_defaults(self):
        source = 'def failure(value):\n    """return value\n' + "    " + "x" * 2000 + '\n    """\n    return value\n'
        self.result(self.case(source, path="core.py"), ["file:core.py"], "not_demonstrated")
        case = self.case('function failure(value = "return value;") { return value; }\n')
        case[0]["capabilities"][0]["evidence"][0]["quote"] = 'function failure(value = "return value;") {'
        self.result(case, ["c0:0"], "not_demonstrated")

    def test_provider_and_storage_keep_downgrade_and_review_without_live_calls(self):
        repo, issue, request, raw = self.case()
        raw["checks"][0]["source_ids"] = ["file:core.ts#L1-L6"]
        raw["partial_support"][0]["source_ids"] = ["file:core.ts#L1-L6"]
        provider = Provider({"REPOTRACTION_AI_URL": "http://localhost/v1", "REPOTRACTION_AI_MODEL": "fixture"})
        budget = mock.Mock()
        with mock.patch.object(provider, "complete", return_value={"matches": [raw]}), \
             mock.patch("urllib.request.build_opener", side_effect=AssertionError("No paid calls")):
            result = provider.evaluate(repo, issue, request, budget)[0]
        self.assertEqual(result["checks"][0]["contribution"], "not_demonstrated")
        self.assertEqual(result["checks"][0]["partial_support"], raw["partial_support"][0])
        budget.reserve_ai.assert_not_called()
        with tempfile.TemporaryDirectory() as directory:
            store = Store(Path(directory) / "fixture.sqlite3", "fixture")
            store.put("matches", result["id"], result)
            self.assertEqual(Store(store.path, "fixture").get("matches", result["id"]), result)


if __name__ == "__main__":
    unittest.main()
