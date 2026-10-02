"""Literal acquired API hints improve bounded context, not parser completeness."""
import copy
import unittest
from unittest import mock

from missing_link.context import build_context, select_capabilities, size
from missing_link.discovery import problem_queries
from missing_link.provider import Provider
from missing_link.public_api import (public_api_hints, public_api_report, MAX_PUBLIC_API_HINTS,
    MAX_INITIALIZERS, MAX_INITIALIZER_CHARS, MAX_PUBLIC_API_REPORT_BYTES)
from missing_link.sources import extract_structure, _safe_path, MAX_FILE_BYTES
import test_missing_link as fixtures


class PublicApiTests(unittest.TestCase):
    def file(self, path, text):
        return {"path": path, "text": text, "kind": "source",
                "url": "https://github.com/example/words/blob/" + "a" * 40 + "/" + path}

    def dotenv_shaped(self):
        repo = fixtures.repository()
        helpers = "\n".join(f'def helper_{i}(value):\n    """Internal parsing helper."""\n    return value\n' for i in range(40))
        repo["files"] = [self.file("src/env/__init__.py", 'from .main import load_dotenv, dotenv_values\n__all__ = ["load_dotenv", "dotenv_values"]\n'),
            self.file("src/env/main.py", helpers + '\ndef load_dotenv(path):\n    """Load environment variables from a file."""\n    return path\n\ndef dotenv_values(path):\n    """Read environment configuration values."""\n    return path\n'),
            self.file("src/env/cli.py", 'def cli(value):\n    """Command line parsing tooling."""\n    return value\n')]
        repo["capabilities"] = extract_structure(repo)
        return repo

    def test_direct_literal_exports_have_exact_acquired_targets(self):
        repo = self.dotenv_shaped()
        before = copy.deepcopy(repo)
        hints = public_api_hints(repo["files"])
        self.assertEqual(hints["entrypoints"], ["src/env/main.py:load_dotenv", "src/env/main.py:dotenv_values"])
        self.assertTrue(hints["scan_complete"])
        self.assertEqual(repo, before)

    def test_core_api_definitions_reach_context_before_many_internal_helpers(self):
        repo = self.dotenv_shaped()
        before = copy.deepcopy(repo)
        data, report = build_context(repo, None, "capabilities", 180000)
        offered = data["repository"]["capabilities"]
        self.assertLessEqual(len(offered), 30)
        self.assertEqual([c["name"] for c in offered[:2]], ["load_dotenv", "dotenv_values"])
        for cap in offered[:2]:
            self.assertTrue(cap["public_api_hint"])
            original = next(c for c in repo["capabilities"] if c["id"] == cap["id"])
            definition = original["definition"]
            self.assertIn(f'file:{definition["path"]}#L{definition["line"]}-L{definition["end_line"]}', data["sources"])
        self.assertEqual(report["public_api_hints"]["entrypoints"], public_api_hints(repo["files"])["entrypoints"])
        self.assertEqual(repo, before)

    def long_path_repository(self):
        repo = fixtures.repository()
        prefix = "/".join(["package" + "x" * 67] * 12)
        names = [f"function_{i}" for i in range(MAX_PUBLIC_API_HINTS)]
        repo["files"] = [self.file(prefix + "/__init__.py",
            "from .api import " + ", ".join(names) + "\n__all__ = " + repr(names)),
            self.file(prefix + "/api.py", "\n".join(f"def {name}():\n    return 1" for name in names))]
        repo["files"] += [self.file(f"src/ordinary{i}.py", ("# " + "x" * 197 + "\n") * 300) for i in range(2)]
        repo["capabilities"] = extract_structure(repo)
        self.assertTrue(all(_safe_path(file["path"]) for file in repo["files"]))
        self.assertTrue(all(len(file["text"].encode("utf-8")) <= MAX_FILE_BYTES for file in repo["files"]))
        return repo

    def test_long_public_api_metadata_shares_source_packing_budget(self):
        repo = self.long_path_repository()
        original = copy.deepcopy(repo)
        expected = public_api_hints(repo["files"])
        self.assertEqual(len(expected["entrypoints"]), MAX_PUBLIC_API_HINTS)
        for phase, demand in (("capabilities", None), ("matches", fixtures.issue())):
            with self.subTest(phase=phase):
                data, report = build_context(repo, demand, phase, 180000)
                self.assertLessEqual(size(data), 180000 - 16000)
                shown = report["public_api_hints"]
                self.assertLessEqual(size(shown), MAX_PUBLIC_API_REPORT_BYTES)
                self.assertEqual(shown["entrypoints"], expected["entrypoints"][:len(shown["entrypoints"])])
                self.assertEqual(shown["omitted_entrypoint_count"], MAX_PUBLIC_API_HINTS - len(shown["entrypoints"]))
                self.assertGreater(shown["omitted_entrypoint_count"], 0)
                self.assertFalse(shown["entrypoint_list_complete"])
                self.assertTrue(shown["scan_complete"])
                self.assertEqual(len(data["repository"]["capabilities"]), 30)
                # Reporting omissions cannot remove hints from candidate ranking.
                self.assertTrue(all(cap["public_api_hint"] for cap in data["repository"]["capabilities"]))
                self.assertFalse(report["implementation_context_missing"])
                self.assertTrue(any(entry.get("path", "").endswith("/api.py") for entry in data["sources"].values()))
                self.assertGreater(report["omitted_source_count"], 0)
                if demand:
                    self.assertIn("q0", data["sources"])
        self.assertEqual(repo, original)

    def test_report_bound_counts_utf8_and_json_escaping_not_only_characters(self):
        for prefix in ("x", "é", '"'):
            with self.subTest(prefix=prefix):
                hints = {"entrypoints": [prefix * 900 + f"/api.py:function_{i}" for i in range(64)],
                         "scan_complete": True, "method": "fixture"}
                original = copy.deepcopy(hints)
                report = public_api_report(hints)
                self.assertLessEqual(size(report), MAX_PUBLIC_API_REPORT_BYTES)
                self.assertGreater(report["omitted_entrypoint_count"], 0)
                self.assertFalse(report["entrypoint_list_complete"])
                self.assertEqual(len(report["entrypoints"]) + report["omitted_entrypoint_count"], 64)
                self.assertEqual(hints, original)

    def test_small_and_empty_reports_keep_all_scanned_hints(self):
        for repo in (self.dotenv_shaped(), {"files": []}):
            hints = public_api_hints(repo["files"])
            report = public_api_report(hints)
            self.assertEqual(report["entrypoints"], hints["entrypoints"])
            self.assertTrue(report["entrypoint_list_complete"])
            self.assertEqual(report["omitted_entrypoint_count"], 0)
            self.assertEqual(report["scan_complete"], hints["scan_complete"])

    def test_long_api_reports_pass_real_transport_preflight_without_http_or_spend(self):
        repo = self.long_path_repository()
        # Keep this transport fixture's declaration sample small; all 64 API
        # hints still participate. The 30-candidate packing boundary is tested
        # above, separately from repeated long source-ID schema overhead.
        repo["capabilities"] = repo["capabilities"][:8]
        demand = fixtures.issue()
        request = fixtures.validate_request(fixtures.request_raw(), demand)
        original = copy.deepcopy((repo, demand, request))
        for api in ("chat", "responses"):
            for response_format in ("json_object", "json_schema"):
                for phase in ("capabilities", "matches"):
                    with self.subTest(api=api, response_format=response_format, phase=phase):
                        provider = Provider({"REPOTRACTION_AI_URL": "http://localhost/v1",
                            "REPOTRACTION_AI_MODEL": "fixture", "REPOTRACTION_AI_API_KIND": api,
                            "REPOTRACTION_AI_RESPONSE_FORMAT": response_format,
                            "REPOTRACTION_AI_INPUT_USD_PER_MILLION": "1",
                            "REPOTRACTION_AI_OUTPUT_USD_PER_MILLION": "1"})
                        budget = mock.Mock()
                        budget.reserve_ai.side_effect = RuntimeError("fixture reservation stop")
                        with mock.patch("missing_link.provider.urllib.request.build_opener") as opener:
                            with self.assertRaisesRegex(RuntimeError, "fixture reservation stop"):
                                if phase == "capabilities":
                                    provider.interpret_capabilities(repo, budget)
                                else:
                                    provider.evaluate(repo, demand, request, budget)
                            opener.assert_not_called()
                        budget.reserve_ai.assert_called_once()
                        budget.checkpoint.assert_not_called()
                        input_bytes = round(budget.reserve_ai.call_args.args[0] * 1000000 - provider.max_tokens - 2048)
                        self.assertLessEqual(input_bytes, provider.max_bytes)
        self.assertEqual((repo, demand, request), original)

    def test_public_apis_rank_before_reviewed_internal_cli_queries_without_raising_query_limit(self):
        repo = self.dotenv_shaped()
        for cap in repo["capabilities"]:
            if cap["name"] == "cli":
                cap.update(claim_source="model", search_terms=["internal cli tooling"])
        queries = problem_queries(repo)
        self.assertLessEqual(len(queries), 3)
        self.assertTrue(any("environment" in query for query in queries[:2]))
        self.assertFalse(any("internal cli tooling" in query for query in queries[:2]))
        self.assertTrue(all("-repo:example/words" in query for query in queries))

    def test_aliases_and_initializer_definitions_do_not_promote_neighbors(self):
        files = [self.file("pkg/__init__.py", 'from .api import solve as public_solve\ndef local():\n    return 1\n__all__ = ("public_solve", "local")\n'),
                 self.file("pkg/api.py", "def solve(): pass\ndef neighbor(): pass\n")]
        self.assertEqual(public_api_hints(files)["entrypoints"], ["pkg/api.py:solve", "pkg/__init__.py:local"])

    def test_dynamic_all_conditional_writes_mutation_and_truncation_are_unknown(self):
        for declaration in ('__all__ = discover_names()', '__all__ = [name for name in names]',
                            '__all__ = ["solve"]\n__all__.append("other")',
                            '__all__ = ["solve"]\n__all__ += ["other"]',
                            'if enabled:\n    __all__ = ["solve"]'):
            with self.subTest(declaration=declaration):
                files = [self.file("pkg/__init__.py", "from .api import solve\n" + declaration),
                         self.file("pkg/api.py", "def solve(): pass")]
                hints = public_api_hints(files)
                self.assertEqual(hints["entrypoints"], [])
                self.assertFalse(hints["scan_complete"])
        file = self.file("pkg/__init__.py", '__all__ = ["solve"]')
        file["truncated"] = True
        self.assertFalse(public_api_hints([file])["scan_complete"])

    def test_missing_absolute_star_and_parent_imports_are_not_resolved_or_executed(self):
        text = 'from .missing import absent\nfrom external import remote\nfrom ..other import parent\nfrom .api import *\n__all__ = ["absent", "remote", "parent", "solve"]\nraise AssertionError("must never execute")'
        files = [self.file("pkg/__init__.py", text), self.file("pkg/api.py", "def solve(): pass")]
        self.assertEqual(public_api_hints(files)["entrypoints"], [])

    def test_top_level_rebound_import_is_not_prioritized(self):
        files = [self.file("pkg/__init__.py", 'from .api import solve\nsolve = 0\n__all__ = ["solve"]'),
                 self.file("pkg/api.py", "def solve(): pass")]
        self.assertEqual(public_api_hints(files)["entrypoints"], [])

    def test_hint_and_initializer_scan_caps_are_visible(self):
        names = [f"function_{i}" for i in range(80)]
        text = "from .api import " + ", ".join(names) + "\n__all__ = " + repr(names)
        files = [self.file("pkg/__init__.py", text), self.file("pkg/api.py", "# acquired")]
        hints = public_api_hints(files)
        self.assertEqual(len(hints["entrypoints"]), MAX_PUBLIC_API_HINTS)
        self.assertFalse(hints["scan_complete"])
        self.assertFalse(public_api_hints([self.file(f"pkg{i}/__init__.py", "") for i in range(MAX_INITIALIZERS + 1)])["scan_complete"])
        self.assertFalse(public_api_hints([self.file("pkg/__init__.py", " " * (MAX_INITIALIZER_CHARS + 1))])["scan_complete"])

    def test_public_hint_cannot_override_source_role_or_bypass_implementation_gate(self):
        repo = fixtures.repository()
        script = copy.deepcopy(repo["capabilities"][0])
        script.update(id="script", entrypoint="scripts/tool.py:trim")
        library = dict(repo["capabilities"][0], entrypoint="words.py:trim")
        selected = select_capabilities([script, library], limit=1, public_entrypoints=[script["entrypoint"]])
        self.assertEqual(selected, [library])

    def test_enrichment_receives_public_api_hint_but_not_execution_or_export_claim(self):
        repo = self.dotenv_shaped()
        provider = Provider({"REPOTRACTION_AI_URL": "http://localhost/v1", "REPOTRACTION_AI_MODEL": "fixture"})
        with mock.patch.object(provider, "complete", return_value={"capabilities": []}) as complete:
            provider.interpret_capabilities(repo, mock.Mock())
        instruction, data = complete.call_args.args[:2]
        self.assertIn("not proof of exports", instruction)
        self.assertTrue(data["repository"]["capabilities"][0]["public_api_hint"])
        self.assertFalse(data["context_coverage"]["implementation_context_missing"])
