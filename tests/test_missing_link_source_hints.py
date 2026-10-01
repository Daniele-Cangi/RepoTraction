"""Static source acquisition regressions; acquired JS/TS is never executed."""
import json
import unittest

from missing_link.source_hints import export_hints
from missing_link.sources import PublicGitHub, source_role
from test_missing_link_sources import GitHubFixture


class ExportHintTests(unittest.TestCase):
    def test_monorepo_entrypoint_and_reexports_reach_engine_with_fixed_budget(self):
        fixture = GitHubFixture()
        fixture.add("package.json", json.dumps({"source": "./packages/zod/src/index.ts"}))
        for i in range(40):
            fixture.add(f"packages/zod/src/benchmarks/bench{i}.ts", "export function bench() {}")
            fixture.add(f"packages/zod/src/fixtures/data{i}.ts", "export const data = {};")
        fixture.add("packages/zod/src/index.ts", 'export * from "./v4/core/index.js";')
        fixture.add("packages/zod/src/v4/core/index.ts", 'export {parse} from "./parse.js";')
        fixture.add("packages/zod/src/v4/core/parse.ts", "export function parse(value) { return value; }")
        snapshot = PublicGitHub(fixture.read).fetch_repository("sample/project", 4)
        self.assertEqual([f["path"] for f in snapshot["files"]], ["package.json", "packages/zod/src/index.ts",
            "packages/zod/src/v4/core/index.ts", "packages/zod/src/v4/core/parse.ts"])
        self.assertEqual(sum("/git/blobs/" in call[0] for call in fixture.calls), 4)
        self.assertEqual(len(snapshot["coverage"]["static_export_hints"]), 3)
        self.assertIn("not export verification", snapshot["coverage"]["sampling_policy"])

    def test_export_cycles_and_unsafe_targets_do_not_expand_read_budget(self):
        fixture = GitHubFixture()
        fixture.add("index.ts", 'export * from "./other.js";\nexport * from "../../.env";')
        fixture.add("other.ts", 'export * from "./index.js";')
        fixture.add(".env", "secret")
        snapshot = PublicGitHub(fixture.read).fetch_repository("sample/project", 4)
        self.assertEqual(len(snapshot["files"]), 2)
        self.assertEqual(sum("/git/blobs/" in call[0] for call in fixture.calls), 2)
        self.assertFalse(snapshot["coverage"]["omitted_export_paths"])

    def test_only_safety_filtered_literal_relative_exports_are_followed(self):
        eligible = {"src/parse.ts": {}, "src/types.d.ts": {}}
        value = '\n'.join(f'export * from "{spec}";' for spec in (
            "./parse.js", "./types.d.ts", "../../parse.js", "https://host/parse.js", "./*.ts", "./parse.js?secret"))
        targets, complete = export_hints("src/index.ts", value, eligible)
        self.assertEqual(targets, ["src/parse.ts"])
        self.assertTrue(complete)
        self.assertEqual(export_hints("src/index.ts", 'const value = "export * from ./parse.js";', eligible)[0], [])

    def test_manifest_scan_overflow_is_explicit(self):
        exports = {str(i): "./index.js" for i in range(100)}
        targets, complete = export_hints("package.json", json.dumps({"exports": exports}), {"index.ts": {}})
        self.assertEqual(targets, ["index.ts"])
        self.assertFalse(complete)

    def test_manifest_main_can_omit_dot_prefix_but_js_dependency_import_cannot(self):
        eligible = {"lib/index.ts": {}}
        self.assertEqual(export_hints("package.json", '{"main":"lib/index.js"}', eligible)[0], ["lib/index.ts"])
        self.assertEqual(export_hints("index.ts", 'export * from "lib/index.js";', eligible)[0], [])

    def test_fixtures_benchmarks_specs_and_types_are_not_product_engines(self):
        for path in ("pkg/fixtures/data.ts", "pkg/bench/run.ts", "pkg/playground/demo.ts"):
            self.assertEqual(source_role(path), "infrastructure")
        self.assertEqual(source_role("pkg/parse.spec.ts"), "test")
        self.assertEqual(source_role("pkg/index.d.ts"), "support")
        self.assertEqual(source_role("pkg/src/parse.ts"), "implementation")
