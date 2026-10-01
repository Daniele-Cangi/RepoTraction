"""Bounded public excerpts reproduce the four live quotation failures offline."""
import copy
import json
import unittest
from unittest import mock

from missing_link.analysis import evidence_catalog, validate_request, validate_matches
from missing_link.context import build_context
from missing_link.contracts import schema_for, validate_shape
from missing_link.demand import citation_spans
from missing_link.provider import Provider, CandidateValidationError
from test_missing_link import issue, request_raw, request_completion, repository, raw_match


class DemandSpanTests(unittest.TestCase):
    def test_live_markdown_failures_use_original_spans_not_model_repairs(self):
        pairs = [
            ("- Use **panel-assessed `vN_severity` only** (never `body_severity`).",
             "Use **panel-assessed `vN_severity` only (never `body_severity`)."),
            ("| Recommended after #135 lands; benefits from #137 |", "Recommended after `#135` lands"),
            ("- `X-Timezone` (and profile) drive UTC storage vs. displayed instants; optional cultural rules extend formatting.",
             "X-Timezone (and profile) drive UTC storage vs. displayed instants"),
            ("  - GAIA Agent base class patterns (`Agent`, `_register_tools()`, `_get_system_prompt()`)",
             "GAIA Agent base class patterns (`Agent`, `_register_tools()`, `_get_system_prompt()` )"),
        ]
        provider = Provider({"REPOTRACTION_AI_URL": "http://localhost/v1", "REPOTRACTION_AI_MODEL": "fixture"})
        for original, rewritten in pairs:
            demand = dict(issue(), body=original, comments=[])
            raw = request_raw()
            raw["requirements"] = [dict(raw["requirements"][0], quote=rewritten)]
            with self.subTest(original=original):
                with self.assertRaises(ValueError):
                    validate_request(raw, demand)  # Legacy/manual imports remain strict.
                saved = []
                def completion(instruction, data, budget, schema, phase):
                    raw["requirements"][0]["quote"] = original.strip()
                    attempt = request_completion(raw)(instruction, data, budget, schema, phase)
                    saved.append(copy.deepcopy(attempt))
                    validate_shape(attempt, schema)
                    return attempt
                with mock.patch.object(provider, "complete", side_effect=completion) as complete:
                    result = provider.interpret_request(demand, mock.Mock())
                source = result["requirements"][0]["source"]
                self.assertEqual(source["quote"], original.strip())
                self.assertEqual(source["quote_match"], "exact")
                self.assertNotIn("quote", saved[0]["requirements"][0])
                self.assertEqual(complete.call_count, 1)

    def test_catalog_cannot_quote_synthetic_seams_or_unsent_middle(self):
        demand = dict(issue(), body="begin\n" + "padding\n" * 2500 + "hidden detail\n" + "tail\n" * 2500, comments=[])
        data, _ = build_context(None, demand, "request", 180000)
        spans, _ = citation_spans(data["sources"], evidence_catalog({}, demand), 18000)
        quotes = [span["quote"] for span in spans.values()]
        self.assertNotIn("hidden detail", quotes)
        self.assertFalse(any("[OMITTED MIDDLE]" in quote for quote in quotes))
        self.assertTrue(all(quote in demand["body"] or quote == demand["title"] for quote in quotes))

    def test_selected_middle_constraint_is_citable_without_inventing_its_full_line(self):
        demand = dict(issue(), body="prefix " * 1800 + "Must not use Node.js. " + "suffix " * 1800, comments=[])
        data, report = build_context(None, demand, "request", 180000)
        spans, _ = citation_spans(data["sources"], evidence_catalog({}, demand), 18000)
        quotes = [span["quote"] for span in spans.values()]
        self.assertTrue(any("Must not use Node.js." in quote for quote in quotes))
        self.assertTrue(all(quote in data["sources"]["q0"]["quote"] for quote in quotes))
        self.assertTrue(all(quote in evidence_catalog({}, demand)["q0"]["quote"] for quote in quotes))
        self.assertFalse(report["discussion_complete"])

    def test_ids_stable_and_catalog_schema_bounded_with_visible_omissions(self):
        demand = dict(issue(), body="\n".join(f"Requirement number {i}." for i in range(600)), comments=[])
        data, _ = build_context(None, demand, "request", 180000)
        catalog = evidence_catalog({}, demand)
        spans, report = citation_spans(data["sources"], catalog, 18000)
        self.assertLessEqual(len(spans), 400)
        self.assertLessEqual(len(json.dumps(spans, ensure_ascii=False).encode()), 18000)
        self.assertFalse(report["complete"])
        self.assertGreater(report["omitted_visible_spans"], 0)
        small, _ = citation_spans(data["sources"], catalog, 4000)
        self.assertTrue(set(small) <= set(spans))
        schema = schema_for("request", source_ids=[f"q{i}" for i in range(400)], citation_ids=[f"s{i}" for i in range(400)])
        def enum_count(value):
            if isinstance(value, dict):
                return len(value.get("enum", [])) + sum(enum_count(item) for item in value.values())
            return sum(enum_count(item) for item in value) if isinstance(value, list) else 0
        self.assertLess(enum_count(schema), 1000)

    def test_ids_are_bound_to_actual_source_text_and_issue_not_only_offsets(self):
        original = dict(issue(), body="Keep ANSI.", comments=[])
        keys = []
        for demand in (original, dict(original, body="Drop ANSI."),
                       dict(original, url="https://github.com/example/site/issues/8")):
            data, _ = build_context(None, demand, "request", 180000)
            spans, _ = citation_spans(data["sources"], evidence_catalog({}, demand), 18000)
            keys.append(set(spans))
        self.assertFalse(keys[0] & keys[2])
        self.assertNotEqual(keys[0], keys[1])

    def test_free_quotes_and_invented_span_ids_fail_without_retry_or_echo(self):
        provider = Provider({"REPOTRACTION_AI_URL": "http://localhost/v1", "REPOTRACTION_AI_MODEL": "fixture"})
        for raw in (request_raw(), dict(request_raw(), requirements=[{
                "text": "Untrusted", "mandatory": True, "explicit": True, "citation_id": "private-secret", "inference": ""}])):
            with mock.patch.object(provider, "complete", return_value=raw) as complete:
                with self.assertRaises(CandidateValidationError) as raised:
                    provider.interpret_request(issue(), mock.Mock())
                self.assertNotIn("private-secret", str(raised.exception))
                self.assertNotIn("private-secret", json.dumps(raised.exception.diagnostics))
                complete.assert_called_once()


class AtomicDemandTests(unittest.TestCase):
    def test_support_text_cannot_prove_behavior_even_with_code_elsewhere_in_prompt(self):
        for path in ("README.md", "index.d.ts", "benchmarks/example.ts", "fixtures/sample.ts",
                     "test.js", "test.py", "spec.ts", "tests.cjs", "specs.tsx"):
            repo = repository()
            repo["files"].append({"path": path, "text": "Describes all desired behavior.", "kind": "source",
                "url": "https://github.com/example/words/blob/" + "a" * 40 + "/" + path})
            raw = raw_match()
            raw["checks"][0]["source_ids"] = ["file:" + path]
            match = validate_matches([raw], repo, issue(), validate_request(request_raw(), issue()), "model")[0]
            self.assertEqual(match["checks"][0]["status"], "undetermined")
            self.assertEqual(match["discovery_assessment"]["supported_requirement_ids"], [])

    def demand(self):
        return dict(issue(), comments=[], body="Implement output budgets and head/tail capture.\n"
            "Optionally strip ANSI escape codes.\nstrip_ansi?: boolean;\nmax_total_bytes?: number;")

    def requirements(self):
        raw = request_raw()
        raw["requirements"] = [
            {"text": "Implement output budgets and head/tail capture", "mandatory": True, "explicit": True,
             "source_id": "q0", "quote": "Implement output budgets and head/tail capture.", "inference": ""},
            {"text": "strip_ansi: optional ANSI cleanup", "mandatory": False, "explicit": True,
             "source_id": "q0", "quote": "strip_ansi?: boolean;", "inference": "Read the optional narrative separately."},
            {"text": "max_total_bytes: configure output budget", "mandatory": True, "explicit": True,
             "source_id": "q0", "quote": "max_total_bytes?: number;", "inference": "Optional argument is not optional implementation."}]
        return raw

    def test_optional_ansi_contribution_survives_full_request_rejection(self):
        demand = self.demand()
        raw = self.requirements()
        provider = Provider({"REPOTRACTION_AI_URL": "http://localhost/v1", "REPOTRACTION_AI_MODEL": "fixture"})
        with mock.patch.object(provider, "complete", side_effect=request_completion(raw)) as complete:
            request = provider.interpret_request(demand, mock.Mock())
        self.assertIn("atomic independently checkable", complete.call_args.args[0])
        self.assertEqual([r["mandatory"] for r in request["requirements"]], [True, False, True])
        self.assertFalse(request["constraint_review"]["qualification_blockers"])
        repo = repository()
        repo["files"][0]["text"] = "export default function stripAnsi(value) { return value.replace(ansiRegex(), ''); }"
        match = raw_match()
        match["checks"] = [dict(requirement_id=f"r{i}", status="satisfied" if i == 1 else "incompatible",
            contribution="existing_behavior" if i == 1 else "not_demonstrated", reason="Fixture, not a model judgment.",
            source_ids=["file:words.py#L1-L1"]) for i in range(3)]
        result = validate_matches([match], repo, demand, request, "model")[0]
        self.assertEqual(result["classification"], "rejected")
        self.assertEqual(result["discovery_assessment"]["status"], "partial_contribution")
        self.assertEqual(result["discovery_assessment"]["supported_requirement_ids"], ["r1"])
        self.assertFalse(result["discovery_assessment"]["eligible_for_followup"])
        self.assertNotIn("strip_ansi: optional ANSI cleanup", result["bridge"]["success_criteria"])

    def test_omitted_or_bundled_fields_require_review_not_synthetic_support(self):
        raw = self.requirements()
        raw["requirements"] = raw["requirements"][:1]
        request = validate_request(raw, self.demand())
        review = request["constraint_review"]["optional_field_review"]
        self.assertTrue(all(item["needs_review"] for item in review["items"]))
        self.assertEqual(len(request["requirements"]), 1)
        raw = self.requirements()
        raw["requirements"][1]["text"] += " and max_total_bytes budgets"
        request = validate_request(raw, self.demand())
        self.assertTrue(request["constraint_review"]["optional_field_review"]["items"][0]["needs_review"])

    def test_optional_field_sentence_citations_do_not_require_entire_line(self):
        body = "Use strip_ansi?: boolean. This strips ANSI.\nMore context."
        demand = dict(issue(), body=body, comments=[])
        for quote in ("Use strip_ansi?: boolean.", body):
            with self.subTest(quote=quote):
                raw = request_raw()
                raw["requirements"] = [dict(raw["requirements"][0], text="strip_ansi: ANSI cleanup", quote=quote)]
                provider = Provider({"REPOTRACTION_AI_URL": "http://localhost/v1", "REPOTRACTION_AI_MODEL": "fixture"})
                # The short quote is a real selectable sentence; broad manual
                # citations retain their existing exact-span validation too.
                if quote == body:
                    request = validate_request(raw, demand)
                else:
                    with mock.patch.object(provider, "complete", side_effect=request_completion(raw)):
                        request = provider.interpret_request(demand, mock.Mock())
                self.assertEqual(request["requirements"][0]["source"]["quote"], quote)
                review = request["constraint_review"]["optional_field_review"]["items"][0]
                self.assertEqual(review["represented_by"], ["r0"])
                self.assertFalse(review["needs_review"])
                self.assertFalse(request["constraint_review"]["qualification_blockers"])

    def test_optional_field_short_quote_keeps_identifier_source_and_atomicity_guards(self):
        demand = dict(issue(), body="Use strip_ansi?: boolean. This strips ANSI.\nmax_total_bytes?: number;",
                      comments=[{"url": issue()["url"] + "#issuecomment-9", "body": "Use strip_ansi?: boolean.",
                                 "author_association": "MEMBER"}])
        base = dict(request_raw()["requirements"][0], text="strip_ansi: ANSI cleanup", quote="Use strip_ansi?: boolean.")
        for override in ({"quote": "This strips ANSI."}, {"source_id": "q1"}, {"explicit": False},
                         {"text": "model behavior"}, {"text": "strip_ansi and max_total_bytes behavior"}):
            with self.subTest(override=override):
                raw = request_raw()
                raw["requirements"] = [dict(base, **override)]
                review = validate_request(raw, demand)["constraint_review"]["optional_field_review"]["items"][0]
                self.assertEqual(review["represented_by"], [])
                self.assertTrue(review["needs_review"])

    def test_overlapping_optional_identifiers_are_independently_represented(self):
        fields = ("mode", "colorMode", "fallback_color_mode")
        demand = dict(issue(), body="\n".join(f"{field}?: string;" for field in fields), comments=[])
        provider = Provider({"REPOTRACTION_AI_URL": "http://localhost/v1", "REPOTRACTION_AI_MODEL": "fixture"})
        for names in (fields, ("mode", "color mode", "fallback color mode")):
            with self.subTest(names=names):
                raw = request_raw()
                raw["requirements"] = [dict(raw["requirements"][0], text=name + " behavior", quote=f"{field}?: string;")
                                       for field, name in zip(fields, names)]
                with mock.patch.object(provider, "complete", side_effect=request_completion(raw)) as complete:
                    request = provider.interpret_request(demand, mock.Mock())
                complete.assert_called_once()
                review = request["constraint_review"]["optional_field_review"]["items"]
                self.assertEqual([item["represented_by"] for item in review], [["r0"], ["r1"], ["r2"]])
                self.assertFalse(request["constraint_review"]["qualification_blockers"])
                match = raw_match()
                match["checks"] = [dict(requirement_id=f"r{index}", status="satisfied", contribution="existing_behavior",
                    reason="Offline structural fixture, not a compatibility claim.", source_ids=["c0:0"])
                    for index in range(3)]
                self.assertEqual(validate_matches([match], repository(), demand, request, "model")[0]["classification"], "direct")

    def test_overlapping_field_names_do_not_clear_bundled_or_misidentified_requirements(self):
        demand = dict(issue(), body="mode?: string;\ncolorMode?: string;", comments=[])
        for name in ("colorMode and mode behavior", "mode and colorMode behavior", "color mode and mode behavior"):
            with self.subTest(name=name):
                raw = dict(request_raw(), requirements=[dict(request_raw()["requirements"][0],
                    text=name, quote="colorMode?: string;")])
                review = validate_request(raw, demand)["constraint_review"]["optional_field_review"]["items"]
                self.assertTrue(all(item["needs_review"] for item in review))
                self.assertTrue(all(not item["represented_by"] for item in review))
        # The short field cannot borrow the longer field's name in prose, nor
        # can the longer field borrow a citation to only the short declaration.
        for name, quote in (("colorMode behavior", "mode?: string;"), ("mode behavior", "colorMode?: string;")):
            with self.subTest(name=name, quote=quote):
                raw = dict(request_raw(), requirements=[dict(request_raw()["requirements"][0], text=name, quote=quote)])
                review = validate_request(raw, demand)["constraint_review"]["optional_field_review"]["items"]
                self.assertTrue(all(item["needs_review"] for item in review))

    def test_repeated_field_mentions_do_not_hide_an_omitted_overlapping_field(self):
        demand = dict(issue(), body="mode?: string;\ncolorMode?: string;", comments=[])
        raw = dict(request_raw(), requirements=[dict(request_raw()["requirements"][0],
            text="colorMode behavior and color mode defaults", quote="colorMode?: string;")])
        review = validate_request(raw, demand)["constraint_review"]["optional_field_review"]["items"]
        self.assertTrue(review[0]["needs_review"])
        self.assertEqual(review[0]["represented_by"], [])
        self.assertFalse(review[1]["needs_review"])
        self.assertEqual(review[1]["represented_by"], ["r0"])

    def test_identifier_without_prose_tokens_does_not_match_arbitrary_text(self):
        demand = dict(issue(), body="_?: string;", comments=[])
        raw = dict(request_raw(), requirements=[dict(request_raw()["requirements"][0],
            text="arbitrary behavior", quote="_?: string;")])
        review = validate_request(raw, demand)["constraint_review"]["optional_field_review"]["items"][0]
        self.assertEqual(review["represented_by"], [])
        self.assertTrue(review["needs_review"])

    def test_field_syntax_does_not_turn_mandatory_behavior_optional(self):
        raw = self.requirements()
        raw["requirements"][1]["mandatory"] = True
        self.assertTrue(validate_request(raw, self.demand())["requirements"][1]["mandatory"])

    def test_unestablished_comment_authority_and_model_word_are_not_field_coverage(self):
        demand = dict(issue(), body="Keep words intact.", comments=[{"url": issue()["url"] + "#issuecomment-8",
            "body": "mode?: string;", "author": "third-party"}])
        raw = request_raw()
        raw["requirements"] = [{"text": "model behavior", "mandatory": True, "explicit": True,
            "source_id": "q1", "quote": "mode?: string;", "inference": ""}]
        request = validate_request(raw, demand)
        review = request["constraint_review"]["optional_field_review"]["items"][0]
        self.assertFalse(review["represented_by"])
        self.assertTrue(review["needs_review"])
        raw["requirements"][0]["text"] = "mode behavior"
        review = validate_request(raw, demand)["constraint_review"]["optional_field_review"]["items"][0]
        self.assertEqual(review["represented_by"], ["r0"])
        self.assertTrue(review["needs_review"])
