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

    def test_field_syntax_does_not_turn_mandatory_behavior_optional(self):
        raw = self.requirements()
        raw["requirements"][1]["mandatory"] = True
        self.assertTrue(validate_request(raw, self.demand())["requirements"][1]["mandatory"])
