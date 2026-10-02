"""Exact acquired npm-bin roles: offline fixtures, never executable/AI proof."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from missing_link.analysis import analysis_contract, validate_matches, validate_request
from missing_link.context import build_context, select_capabilities
from missing_link.contracts import MAX_SCOPED_IDS, validate_shape
from missing_link.discovery import problem_queries
from missing_link.provider import CandidateValidationError, Provider
from missing_link.source_hints import MAX_EXPORT_HINTS
from missing_link.sources import (MAX_CAPABILITIES, MAX_FILE_BYTES, PublicGitHub,
                                  extract_structure, runtime_bin_entrypoints, source_role)
from missing_link.store import Store
from test_missing_link_sources import GitHubFixture


CLI = "export function run(value) { return value; }"


def source(path, text=CLI, kind="source", **extra):
    return {"path": path, "text": text, "kind": kind,
            "url": "https://github.com/sample/project/blob/" + "a" * 40 + "/" + path, **extra}


def snapshot(path="scripts/cli.js", bin_value=None, extra_files=()):
    manifest = source("package.json", json.dumps({"bin": bin_value if bin_value is not None else path}), "manifest")
    text = "def run(value):\n    return value\n" if path.endswith(".py") else CLI
    repo = {"id": 1, "full_name": "sample/project", "revision": "a" * 40,
            "public": True, "license": {"spdx_id": "MIT"}, "coverage": {},
            "files": [manifest, source(path, text), *extra_files]}
    repo["capabilities"] = extract_structure(repo)
    return repo


def demand_and_request():
    demand = {"id": 7, "url": "https://github.com/other/project/issues/7", "state": "open",
              "title": "Return the command argument", "body": "Please return the command argument unchanged.",
              "author": "requester", "author_type": "User", "comments": [], "context_complete": True,
              "updated_at": "2026-09-29T12:00:00Z", "fetched_at": "2026-09-30T12:00:00Z"}
    raw = copy.deepcopy(analysis_contract()["request"])
    raw.update(outcome="Return the argument", status="unresolved", status_reason="Offline fixture only.")
    raw["requirements"][0].update(text="Return the command argument unchanged", quote=demand["body"])
    return demand, validate_request(raw, demand)


def match_raw(repo, ref):
    result = copy.deepcopy(analysis_contract()["matches"][0])
    result.update(capability_id=repo["capabilities"][0]["id"], classification="direct",
                  summary="Offline role-guard fixture, not a semantic AI evaluation.")
    result["checks"][0].update(status="satisfied", contribution="existing_behavior", source_ids=[ref])
    return result


class BinRoleTests(unittest.TestCase):
    def test_acquired_bin_overrides_only_its_script_or_tool_directory_role(self):
        cases = (("scripts/cli.js", "scripts/cli.js"),
                 ("tools/cli.js", {"tool": "./tools/cli.js"}),
                 ("scripts/cli.ts", "scripts/cli.js"),
                 ("tools/cli.tsx", "./tools/cli.jsx"),
                 ("scripts/CLI.TS", {"tool": "scripts/CLI.TS"}))
        for path, value in cases:
            with self.subTest(path=path, value=value):
                fixture = GitHubFixture()
                fixture.add("package.json", json.dumps({"bin": value}))
                fixture.add(path, CLI)
                for index in range(35):
                    fixture.add(f"aaa_unrelated{index:02d}.ts", CLI)
                repo = PublicGitHub(fixture.read).fetch_repository("sample/project", 2)
                self.assertEqual([f["path"] for f in repo["files"]], ["package.json", path])
                self.assertEqual(sum("/git/blobs/" in call[0] for call in fixture.calls), 2)
                scope = {path: "package.json"}
                self.assertEqual(runtime_bin_entrypoints(repo["files"]), scope)
                self.assertEqual(repo["coverage"]["runtime_bin_entrypoints"], scope)
                self.assertEqual(repo["coverage"]["acquired_source_roles"], {"implementation": 1})
                self.assertEqual(source_role(path), "infrastructure")
                self.assertEqual(source_role(path + ":run", runtime_entrypoints=scope), "implementation")
                repo["capabilities"] = extract_structure(repo)
                self.assertEqual(len(repo["capabilities"]), 1)
                for phase, issue in (("capabilities", None), ("matches", demand_and_request()[0])):
                    data, report = build_context(repo, issue, phase, 60000)
                    self.assertIn("file:" + path + "#L1-L1", data["sources"])
                    self.assertEqual(report["runtime_bin_entrypoints"], scope)
                    self.assertEqual(report["selected_capability_roles"], {"implementation": 1})
                    self.assertEqual(report["implementation_source_paths"], [path])
                    self.assertFalse(report["implementation_context_missing"])

    def test_bin_authority_does_not_propagate_to_helpers_reexports_or_main(self):
        repo = snapshot(extra_files=[source("tools/helper.js"), source("scripts/other.js")])
        repo["files"][1]["text"] = "export {run} from '../tools/helper.js';\n" + CLI
        repo["files"][0]["text"] = json.dumps({"bin": "scripts/cli.js", "main": "scripts/other.js"})
        scope = runtime_bin_entrypoints(repo["files"])
        self.assertEqual(scope, {"scripts/cli.js": "package.json"})
        self.assertEqual(source_role("tools/helper.js", runtime_entrypoints=scope), "infrastructure")
        self.assertEqual(source_role("scripts/other.js", runtime_entrypoints=scope), "infrastructure")
        _, report = build_context(repo, None, "capabilities", 60000)
        self.assertEqual(report["implementation_source_paths"], ["scripts/cli.js"])
        self.assertEqual(report["selected_capability_roles"], {"implementation": 1, "infrastructure": 2})

    def test_scope_is_rederived_from_actual_manifest_not_cached_claims(self):
        mutations = (None, "{}", '{"main":"scripts/cli.js"}', '{"bin":"scripts/missing.js"}',
                     '{"bin":"scripts/CLI.js"}', "not JSON")
        for manifest in mutations:
            with self.subTest(manifest=manifest):
                repo = snapshot()
                if manifest is None:
                    repo["files"].pop(0)
                else:
                    repo["files"][0]["text"] = manifest
                repo["coverage"]["runtime_bin_entrypoints"] = {"scripts/cli.js": "package.json"}
                repo["capabilities"][0]["source_role"] = "implementation"
                self.assertEqual(runtime_bin_entrypoints(repo["files"]), {})
                _, report = build_context(repo, None, "capabilities", 60000)
                self.assertEqual(report["runtime_bin_entrypoints"], {})
                self.assertTrue(report["implementation_context_missing"])

    def test_declared_tests_mocks_fixtures_build_helpers_and_types_stay_excluded(self):
        paths = ("scripts/test.js", "tools/specs/cli.ts", "scripts/cli.test.js", "tools/__mocks__/cli.js",
                 "scripts/fixtures/cli.js", "scripts/cli.example.js", "tools/benchmark.js",
                 "scripts/docs/cli.js", "tools/ci_tools/cli.py", "scripts/winbuild/cli.py",
                 "scripts/cli.d.ts", "tools/cli.D.TS", "scripts/conftest.py", "tools/selftest.py")
        demand, request = demand_and_request()
        for path in paths:
            with self.subTest(path=path):
                repo = snapshot(path)
                self.assertTrue(repo["capabilities"])
                self.assertEqual(runtime_bin_entrypoints(repo["files"]), {})
                self.assertNotEqual(source_role(path, runtime_entrypoints={path}), "implementation")
                _, report = build_context(repo, demand, "matches", 60000)
                self.assertTrue(report["implementation_context_missing"])
                provider, budget = Provider({}), mock.Mock()
                with mock.patch.object(provider, "complete") as complete:
                    with self.assertRaises(CandidateValidationError):
                        provider.interpret_capabilities(repo, budget)
                    with self.assertRaises(CandidateValidationError):
                        provider.evaluate(repo, demand, request, budget)
                    complete.assert_not_called()
                    self.assertFalse(budget.mock_calls)

    def test_only_string_or_bounded_command_to_path_bin_shapes_authorize_roles(self):
        invalid = ([], ["scripts/cli.js"], 1, True, {"tool": 1},
                   {"tool": {"default": "scripts/cli.js"}}, {"tool": ["scripts/cli.js"]},
                   {str(i): "scripts/cli.js" for i in range(MAX_EXPORT_HINTS + 1)})
        for value in invalid:
            with self.subTest(value_type=type(value).__name__):
                self.assertEqual(runtime_bin_entrypoints(snapshot(bin_value=value)["files"]), {})
        files = []
        for index in range(MAX_EXPORT_HINTS + 1):
            path = f"packages/app{index}/tools/cli.js"
            files.extend([source(f"packages/app{index}/package.json", '{"bin":"tools/cli.js"}', "manifest"), source(path)])
        self.assertEqual(len(runtime_bin_entrypoints(files)), MAX_EXPORT_HINTS)

    def test_relative_nested_manifest_target_uses_existing_safe_literal_resolver(self):
        files = [source("packages/app/package.json", '{"bin":{"tool":"../shared/tools/cli.js"}}', "manifest"),
                 source("packages/shared/tools/cli.ts")]
        self.assertEqual(runtime_bin_entrypoints(files), {"packages/shared/tools/cli.ts": "packages/app/package.json"})
        for target in ("/scripts/cli.js", "../../scripts/cli.js", "https://host/scripts/cli.js", "scripts/*.js",
                       "scripts/cli.js?token", "scripts/cli.js#fragment", "scripts\\cli.js"):
            with self.subTest(target=target):
                self.assertEqual(runtime_bin_entrypoints(snapshot(bin_value=target)["files"]), {})

    def test_unsafe_unacquired_symlink_and_oversize_files_cannot_authorize_bin_role(self):
        for index, change in ((0, {"text": '{"bin":"scripts/cli.js","token":"ghp_' + "x" * 40 + '"}'}),
                              (0, {"mode": "120000"}), (1, {"mode": "120000"}),
                              (1, {"text": "-----BEGIN PRIVATE KEY-----"}),
                              (1, {"text": "x" * (MAX_FILE_BYTES + 1)}), (1, {"kind": "test"})):
            with self.subTest(index=index, field=list(change)):
                repo = snapshot()
                repo["files"][index].update(change)
                self.assertEqual(runtime_bin_entrypoints(repo["files"]), {})
        repo = snapshot()
        repo["files"].pop(1)
        self.assertEqual(runtime_bin_entrypoints(repo["files"]), {})

    def test_declared_cli_reaches_existing_capability_limits_before_unlisted_scripts(self):
        files = [source(f"tools/helper{i}.js", "\n".join(f"export function fn{j}() {{}}" for j in range(40)))
                 for i in range(4)]
        repo = snapshot(extra_files=files)
        self.assertEqual(len(repo["capabilities"]), MAX_CAPABILITIES)
        self.assertEqual(repo["capabilities"][0]["entrypoint"], "scripts/cli.js:run")
        selected = select_capabilities(repo["capabilities"], runtime_entrypoints=runtime_bin_entrypoints(repo["files"]))
        self.assertEqual(len(selected), 30)
        self.assertEqual(selected[0]["entrypoint"], "scripts/cli.js:run")
        data, report = build_context(repo, None, "capabilities", 180000)
        self.assertEqual(len(report["capability_ids"]), 30)
        self.assertLessEqual(len(data["sources"]), MAX_SCOPED_IDS)
        self.assertLess(report["payload_bytes"], 180000)
        self.assertEqual(report["implementation_source_paths"], ["scripts/cli.js"])
        self.assertEqual(report["selected_capability_roles"], {"implementation": 1, "infrastructure": 29})

    def test_discovery_ranking_uses_exact_bin_scope_without_promoting_neighbor_helpers(self):
        repo = snapshot(extra_files=[source(f"tools/helper{i}.js") for i in range(4)])
        for index, cap in enumerate(repo["capabilities"]):
            cap.update(claim_source="model", summary="Offline reviewed fixture",
                       search_terms=["command argument" if index == 0 else f"fixture helper{index}"])
        repo["capabilities"] = repo["capabilities"][1:] + repo["capabilities"][:1]
        queries = problem_queries(repo)
        self.assertEqual(len(queries), 3)
        self.assertTrue(queries[0].startswith("command argument "))
        repo["files"][0]["text"] = "{}"
        repo["coverage"]["runtime_bin_entrypoints"] = {"scripts/cli.js": "package.json"}
        self.assertTrue(all("command argument" not in query for query in problem_queries(repo)))

    def test_declared_but_byte_omitted_cli_does_not_pass_implementation_preflight(self):
        repo = snapshot()
        repo["files"][1]["text"] = CLI + " /*" + "x" * 40000 + "*/"
        repo["capabilities"] = extract_structure(repo)
        self.assertTrue(repo["capabilities"])
        self.assertEqual(runtime_bin_entrypoints(repo["files"]), {"scripts/cli.js": "package.json"})
        _, report = build_context(repo, None, "capabilities", 60000)
        self.assertTrue(report["implementation_context_missing"])
        self.assertEqual(report["runtime_bin_entrypoints"], {})
        self.assertTrue(report["omitted_source_count"])
        provider, budget = Provider({}), mock.Mock()
        provider.max_bytes = 60000
        with mock.patch.object(provider, "complete") as complete:
            with self.assertRaises(CandidateValidationError):
                provider.interpret_capabilities(repo, budget)
            complete.assert_not_called()
            self.assertFalse(budget.mock_calls)

    def test_mock_provider_enrichment_comparison_and_restart_use_same_bin_scope(self):
        repo, (demand, request) = snapshot(), demand_and_request()
        original = copy.deepcopy((repo, demand, request))
        provider, budget = Provider({}), mock.Mock()
        phases = []

        def complete(instruction, data, ignored_budget, schema, phase):
            phases.append(phase)
            ref = "file:scripts/cli.js#L1-L1"
            self.assertIn(ref, data["sources"])
            self.assertFalse(data["context_coverage"]["implementation_context_missing"])
            if phase == "capabilities":
                cap = {"id": data["repository"]["capabilities"][0]["id"], "name": "run", "summary": "Fixture command",
                       "outcome": "Return the argument", "standalone": "yes", "source_ids": [ref]}
                cap.update({key: [] for key in ("inputs", "outputs", "preconditions", "dependencies", "limitations", "search_terms")})
                result = {"capabilities": [cap]}
            else:
                result = {"matches": [match_raw(repo, ref)]}
            validate_shape(result, schema)
            return result

        with mock.patch.object(provider, "complete", side_effect=complete):
            enriched = provider.interpret_capabilities(repo, budget)
            self.assertEqual((repo, demand, request), original)
            interpreted = dict(repo, capabilities=enriched)
            matches = provider.evaluate(interpreted, demand, request, budget)
        self.assertEqual(phases, ["capabilities", "matches"])
        self.assertFalse(budget.mock_calls)
        self.assertEqual(matches[0]["classification"], "direct")
        self.assertEqual(matches[0]["checks"][0]["contribution"], "existing_behavior")
        self.assertEqual(matches[0]["bridge"]["verification"]["status"], "not_executed")
        with tempfile.TemporaryDirectory() as temp:
            db_path = Path(temp) / "bin-fixture.sqlite3"
            Store(db_path, "fixture").save_matches(matches, interpreted)
            restored = Store(db_path, "fixture")
            saved = restored.get("matches", matches[0]["id"])
            pinned = restored.match_snapshot(saved["id"])
            self.assertEqual(pinned["repository"]["files"], interpreted["files"])
            self.assertEqual(runtime_bin_entrypoints(pinned["repository"]["files"]), {"scripts/cli.js": "package.json"})
            checked = validate_matches([match_raw(interpreted, "file:scripts/cli.js#L1-L1")],
                                       pinned["repository"], pinned["issue"], saved["request"], "model")
            self.assertEqual(checked[0]["classification"], "direct")
            self.assertEqual(checked[0]["id"], saved["id"])
        self.assertEqual((repo, demand, request), original)

    def test_each_affirmative_check_still_needs_its_own_scoped_implementation_citation(self):
        repo = snapshot(extra_files=[source("tools/helper.js")])
        repo["capabilities"][0]["standalone"] = "yes"
        demand, request = demand_and_request()
        for ref in ("file:tools/helper.js#L1-L1", "file:package.json#L1-L1"):
            with self.subTest(ref=ref):
                result = validate_matches([match_raw(repo, ref)], repo, demand, request, "model")[0]
                self.assertEqual(result["classification"], "investigate")
                self.assertEqual(result["checks"][0]["status"], "undetermined")
                self.assertEqual(result["checks"][0]["contribution"], "not_demonstrated")
        result = validate_matches([match_raw(repo, "file:scripts/cli.js#L1-L1")], repo, demand, request, "model")[0]
        self.assertEqual(result["classification"], "direct")

    def test_bin_declaration_alone_does_not_establish_callable_or_executed_interface(self):
        repo = snapshot()
        self.assertEqual(repo["capabilities"][0]["standalone"], "unknown")
        demand, request = demand_and_request()
        result = validate_matches([match_raw(repo, "file:scripts/cli.js#L1-L1")], repo, demand, request, "model")[0]
        self.assertEqual(result["checks"][0]["status"], "satisfied")
        self.assertEqual(result["classification"], "investigate")
        self.assertEqual(result["bridge"]["verification"]["status"], "not_executed")


if __name__ == "__main__":
    unittest.main()
