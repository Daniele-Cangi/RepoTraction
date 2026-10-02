"""Literal acquired API hints improve bounded context, not parser completeness."""
import copy
import unittest
from unittest import mock

from missing_link.context import build_context, select_capabilities
from missing_link.discovery import problem_queries
from missing_link.provider import Provider
from missing_link.public_api import public_api_hints, MAX_PUBLIC_API_HINTS, MAX_INITIALIZERS, MAX_INITIALIZER_CHARS
from missing_link.sources import extract_structure
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
