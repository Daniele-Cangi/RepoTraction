"""Provider contract/context/budget fixtures, never presented as real AI results."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from missing_link.analysis import analysis_contract, validate_request
from missing_link.config import provider_environment
from missing_link.context import build_context, normalize_references
from missing_link.analysis import evidence_catalog
from missing_link.contracts import schema_for, validate_shape
from missing_link.provider import Provider
from missing_link.store import Store
from test_missing_link import issue, repository, request_raw


class ProviderContractTests(unittest.TestCase):
    def test_remote_requires_shared_allowance_and_prompt_limit_is_honored(self):
        env = {"REPOTRACTION_AI_URL": "https://provider.example/v1", "REPOTRACTION_AI_MODEL": "fixture",
            "REPOTRACTION_AI_ALLOW_REMOTE": "1", "REPOTRACTION_AI_MAX_COST_USD": "2",
            "REPOTRACTION_AI_INPUT_USD_PER_MILLION": "0.10", "REPOTRACTION_AI_OUTPUT_USD_PER_MILLION": "0.50",
            "REPOTRACTION_AI_MAX_PROMPT_BYTES": "150000"}
        self.assertFalse(Provider(env).describe()["configured"])
        env.update(REPOTRACTION_AI_TOTAL_BUDGET_USD="2", REPOTRACTION_AI_BUDGET_ID="explicit")
        self.assertTrue(Provider(env).describe()["configured"])
        self.assertEqual(Provider(env).max_bytes, 150000)

    def test_examples_use_valid_enums_and_schema_is_closed(self):
        example = analysis_contract()
        validate_shape(example["request"], schema_for("request"))
        validate_shape({"matches": example["matches"]}, schema_for("matches"))
        wrong = copy.deepcopy(example["request"])
        wrong["status"] = "unresolved|resolved"
        with self.assertRaises(ValueError):
            validate_shape(wrong, schema_for("request"))
        wrong["status"] = "unclear"
        wrong["execute"] = True
        with self.assertRaises(ValueError):
            validate_shape(wrong, schema_for("request"))

    def test_dotenv_is_allowlisted_and_never_evaluates_shell_or_interpolation(self):
        with tempfile.TemporaryDirectory() as temp, mock.patch.dict("os.environ", {}, clear=True):
            path = Path(temp) / ".env"
            path.write_text('REPOTRACTION_AI_KEY="$(danger) ${OTHER}"\n', encoding="utf-8")
            self.assertEqual(provider_environment(path)["REPOTRACTION_AI_KEY"], "$(danger) ${OTHER}")
            path.write_text("PATH=bad\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                provider_environment(path)

    def test_large_context_is_bounded_and_later_resolution_survives(self):
        demand = issue()
        demand["body"] = "Need word boundaries. " * 10000
        demand["comments"] = [{"url": demand["url"] + f"#issuecomment-{index}", "body": "Long old comment. " * 2000}
            for index in range(20)]
        demand["comments"].append({"url": demand["url"] + "#issuecomment-last", "body": "Solved by the maintainer yesterday."})
        data, report = build_context(None, demand, "request", 60000)
        self.assertLess(len(json.dumps(data).encode()), 44000)
        self.assertIn("Solved by the maintainer", data["sources"]["q21"]["quote"])
        self.assertFalse(report["discussion_complete"])
        self.assertNotIn("repository", data)
        self.assertNotIn("capability_ids", report)

    def test_large_repository_uses_line_spans_and_reports_omissions(self):
        repo = repository()
        repo["files"][0]["text"] += "# lots of unrelated source\n" * 10000
        data, report = build_context(repo, None, "capabilities", 60000)
        self.assertLess(len(json.dumps(data).encode()), 44000)
        self.assertTrue(report["omitted_source_count"])
        self.assertIn("file:words.py#L1-L3", data["sources"])
        self.assertNotIn("files", data["repository"])

    def test_precise_subspans_and_long_citations_require_all_visible_lines(self):
        repo = repository()
        repo["files"][0]["text"] = "# source\n" * 180
        data, _ = build_context(repo, None, "capabilities", 60000)
        catalog = evidence_catalog(repo, {"url": ""})
        self.assertEqual(normalize_references(["file:words.py#L20-L80"], data["sources"], catalog),
            ["file:words.py#L20-L79", "file:words.py#L80-L80"])
        del data["sources"]["file:words.py#L61-L120"]
        with self.assertRaises(ValueError):
            normalize_references(["file:words.py#L20-L80"], data["sources"], catalog)

    def test_selected_definition_precedes_large_manifest_or_unrelated_source(self):
        for kind in ("manifest", "source"):
            for with_issue in (False, True):
                with self.subTest(kind=kind, with_issue=with_issue):
                    repo = repository()
                    repo["files"][0]["text"] = "# unrelated prefix " + "x" * 120 + "\n"
                    repo["files"][0]["text"] *= 500
                    repo["files"][0]["text"] += ("# selected implementation " + "y" * 110 + "\n") * 120
                    repo["capabilities"][0]["definition"] = {"end_line": 620}
                    repo["capabilities"][0]["evidence"][0].update(line=501, end_line=503)
                    repo["files"].insert(0, {"path": "package.json" if kind == "manifest" else "early.py",
                        "kind": kind, "text": ("# broad coverage " + "z" * 120 + "\n") * 1000,
                        "url": "https://github.com/example/words/blob/" + "a" * 40 + "/early"})
                    demand = issue() if with_issue else None
                    data, report = build_context(repo, demand, "matches" if with_issue else "capabilities", 60000)
                    catalog = evidence_catalog(repo, demand or {"url": ""})
                    self.assertEqual(normalize_references(["file:words.py#L501-L620"], data["sources"], catalog),
                        ["file:words.py#L501-L560", "file:words.py#L561-L620"])
                    self.assertIn("trim", report["capability_ids"])
                    self.assertTrue(report["omitted_source_count"])
                    self.assertLess(len(json.dumps(data).encode()), 44000)
                    if with_issue:
                        self.assertIn("q0", data["sources"])

    def complete_fixture(self, result, data=None):
        provider = Provider({"REPOTRACTION_AI_URL": "http://127.0.0.1:9000/v1", "REPOTRACTION_AI_MODEL": "fixture",
            "REPOTRACTION_AI_API_KIND": "responses", "REPOTRACTION_AI_RESPONSE_FORMAT": "json_schema"})
        response = mock.MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps(result).encode()
        opener = mock.Mock()
        opener.open.return_value = response
        budget = mock.Mock()
        with mock.patch("urllib.request.build_opener", return_value=opener):
            outcome = provider.complete("Extract JSON", data or {}, budget, schema_for("request"), "request")
        return outcome, opener, budget

    def test_responses_schema_transport_and_usage(self):
        result = {"id": "resp_fixture", "status": "completed", "output": [{"type": "message", "content": [
            {"type": "output_text", "text": json.dumps(request_raw())}]}], "usage": {"input_tokens": 100, "output_tokens": 200}}
        outcome, opener, budget = self.complete_fixture(result)
        self.assertEqual(outcome["status"], "unresolved")
        sent = opener.open.call_args.args[0]
        payload = json.loads(sent.data)
        self.assertTrue(sent.full_url.endswith("/responses"))
        self.assertFalse(payload["store"])
        self.assertEqual(payload["text"]["format"]["type"], "json_schema")
        self.assertTrue(payload["text"]["format"]["strict"])
        self.assertNotIn("temperature", payload)
        budget.record_usage.assert_called_once_with(100, 200, 0)

    def test_streaming_accepts_only_terminal_response_not_partial_deltas(self):
        provider = Provider({"REPOTRACTION_AI_URL": "http://localhost/v1", "REPOTRACTION_AI_MODEL": "fixture",
            "REPOTRACTION_AI_API_KIND": "responses", "REPOTRACTION_AI_STREAMING": "1"})
        result = {"id": "resp_fixture", "status": "completed", "output": [{"type": "message", "content": [
            {"type": "output_text", "text": json.dumps(request_raw())}]}]}
        for terminal in (True, False):
            response = mock.MagicMock()
            lines = [b'event: response.created\n', b'data: {"type":"response.output_text.delta","delta":"partial"}\n']
            if terminal:
                lines.append(("data: " + json.dumps({"type": "response.completed", "response": result}) + "\n").encode())
            response.__enter__.return_value.readline.side_effect = lines + [b""]
            opener = mock.Mock()
            opener.open.return_value = response
            with mock.patch("urllib.request.build_opener", return_value=opener):
                if terminal:
                    self.assertEqual(provider.complete("Extract", {}, mock.Mock(), schema_for("request"))["status"], "unresolved")
                else:
                    with self.assertRaises(ValueError):
                        provider.complete("Extract", {}, mock.Mock(), schema_for("request"))

    def test_transport_validation_errors_never_leak_header_credentials(self):
        provider = Provider({"REPOTRACTION_AI_URL": "http://localhost/v1", "REPOTRACTION_AI_MODEL": "fixture"})
        opener = mock.Mock()
        opener.open.side_effect = ValueError("Invalid header value Bearer sensitive-fixture-key")
        with mock.patch("urllib.request.build_opener", return_value=opener), self.assertRaises(ValueError) as error:
            provider.complete("Extract", {}, mock.Mock())
        self.assertNotIn("sensitive-fixture-key", str(error.exception))
        self.assertFalse(Provider({"REPOTRACTION_AI_URL": "http://localhost/v1", "REPOTRACTION_AI_MODEL": "fixture",
            "REPOTRACTION_AI_KEY": "invalid\ncredential"}).describe()["configured"])

    def test_incomplete_refusal_and_invalid_shape_do_not_become_analysis(self):
        for result in ({"status": "incomplete"}, {"status": "completed", "output": [{"type": "message",
            "content": [{"type": "refusal", "refusal": "No"}]}]}, {"status": "completed", "output": [{"type": "message",
            "content": [{"type": "output_text", "text": '{"status":"unresolved|resolved"}'}]}]}):
            with self.subTest(result=result), self.assertRaises(ValueError):
                self.complete_fixture(result)

    def test_quoted_requirements_from_unsent_context_are_rejected(self):
        provider = Provider({"REPOTRACTION_AI_URL": "http://localhost/v1", "REPOTRACTION_AI_MODEL": "fixture"})
        raw = request_raw()
        raw["requirements"][0]["quote"] = "Never supplied to provider"
        with mock.patch.object(provider, "complete", return_value=raw), self.assertRaises(ValueError):
            provider.interpret_request(issue(), mock.Mock())

    def test_whitespace_only_quotes_recover_original_not_model_reformatting(self):
        provider = Provider({"REPOTRACTION_AI_URL": "http://localhost/v1", "REPOTRACTION_AI_MODEL": "fixture"})
        demand = issue()
        demand["body"] = "I need plain text shortened without\r\n    splitting\twords. Must work in native CSS without Python."
        raw = request_raw()
        with mock.patch.object(provider, "complete", return_value=raw):
            result = provider.interpret_request(demand, mock.Mock())
        source = result["requirements"][0]["source"]
        self.assertEqual(source["quote"], "without\r\n    splitting\twords")
        self.assertEqual(source["quote_match"], "whitespace_normalized")
        self.assertIn(source["quote"], demand["body"])
        self.assertEqual(raw["requirements"][0]["quote"], "without splitting words")

    def test_whitespace_tolerance_does_not_allow_paraphrases_or_omitted_middle(self):
        provider = Provider({"REPOTRACTION_AI_URL": "http://localhost/v1", "REPOTRACTION_AI_MODEL": "fixture"})
        demand = issue()
        demand["body"] = "start " + "padding\n" * 2000 + "hidden requirement" + "padding\n" * 2000 + " end"
        for quote in ("without dividing words", "hidden requirement", "start end", " "):
            raw = request_raw()
            raw["requirements"][0]["quote"] = quote
            with self.subTest(quote=quote), mock.patch.object(provider, "complete", return_value=raw), self.assertRaises(ValueError):
                provider.interpret_request(demand, mock.Mock())

    def test_persisted_allowance_is_shared_by_jobs_and_survives_restart(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "alice.sqlite3"
            store = Store(path, "alice")
            store.reserve_ai_allowance("explicit", "job-a", 3, 5)
            restarted = Store(path, "alice")
            with self.assertRaises(ValueError):
                restarted.reserve_ai_allowance("explicit", "job-b", 3, 5)
            self.assertEqual(restarted.ai_reserved("explicit"), 3)
            restarted.reserve_ai_allowance("explicit", "job-b", 2, 5)
            self.assertEqual(store.ai_reserved("explicit"), 5)


if __name__ == "__main__":
    unittest.main()
