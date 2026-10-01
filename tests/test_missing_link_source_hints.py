"""Static source acquisition regressions; acquired JS/TS is never executed."""
import json
import unittest

from missing_link.source_hints import export_hints, MAX_EXPORT_HINTS
from missing_link.js_lexical import MAX_LEXICAL_NESTING
from missing_link.sources import PublicGitHub, source_role
from test_missing_link_sources import GitHubFixture


class ExportHintTests(unittest.TestCase):
    def test_compact_reexports_allow_adjacent_punctuation_not_joined_keywords(self):
        for extension in (".js", ".mjs", ".cjs", ".jsx", ".ts", ".tsx"):
            for clause in ('export*from"./engine.js";', "export{parse}from'./engine.js';",
                           'export*as engine from"./engine.js";', 'export {parse}from"./engine.js";',
                           'export* from"./engine.js";', 'export{parse} from"./engine.js";'):
                with self.subTest(extension=extension, clause=clause):
                    self.assertEqual(export_hints("index" + extension, clause, {"engine.ts": {}}),
                                     (["engine.ts"], True))
        for clause in ('exported{parse}from"./engine.js";', 'export{parse}fromage"./engine.js";',
                       'export*asengine from"./engine.js";', 'export*as enginefrom"./engine.js";'):
            with self.subTest(clause=clause):
                self.assertEqual(export_hints("index.ts", clause, {"engine.ts": {}}), ([], True))

    def test_compact_barrels_reach_engine_with_fixed_read_budget(self):
        fixture = GitHubFixture()
        fixture.add("index.ts", 'export*from"./src/index.js";')
        fixture.add("src/index.ts", 'export{parse}from"./engine.js";')
        fixture.add("src/engine.ts", "export function parse(value) { return value; }")
        for i in range(40):
            fixture.add(f"unrelated{i:02d}.ts", "export function helper() { return true; }")
        snapshot = PublicGitHub(fixture.read).fetch_repository("sample/project", 3)
        self.assertEqual([f["path"] for f in snapshot["files"]], ["index.ts", "src/index.ts", "src/engine.ts"])
        self.assertEqual(sum("/git/blobs/" in call[0] for call in fixture.calls), 3)
        self.assertEqual(snapshot["coverage"]["static_export_hints"],
                         [{"from": "index.ts", "path": "src/index.ts"},
                          {"from": "src/index.ts", "path": "src/engine.ts"}])
        self.assertTrue(snapshot["coverage"]["export_hints_complete"])
        self.assertFalse(snapshot["coverage"]["eligible_sample_complete"])

    def test_compact_reexports_keep_lexical_and_destination_safety_guards(self):
        fake = 'export{parse}from"./obsolete.js";'
        real = 'export*from"./real.js";'
        for prefix in (f"/*\n{fake}\n*/\n", f"const example = `\n{fake}\n`;\n",
                       "const example = \"continued\\\nexport{parse}from'./obsolete.js';\\\n\";\n",
                       "// export*from'./obsolete.js';\n"):
            with self.subTest(prefix=prefix):
                self.assertEqual(export_hints("index.ts", prefix + real, {"obsolete.ts": {}, "real.ts": {}}),
                                 (["real.ts"], True))
        for spec in ("./types.d.ts", "../../engine.js", "https://host/engine.js", "./*.ts", "./engine.js?secret"):
            with self.subTest(spec=spec):
                self.assertEqual(export_hints("src/index.ts", f'export{{parse}}from"{spec}";',
                                             {"src/types.d.ts": {}, "engine.ts": {}, "src/engine.ts": {}}),
                                 ([], True))

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

    def test_multiline_barrels_prioritize_implementation_with_fixed_read_budget(self):
        fixture = GitHubFixture()
        fixture.add("index.ts", "export {\n  parse as parseValue,\n}\nfrom './src/index.js';")
        fixture.add("src/index.ts", 'export {\r\n\tparse,\r\n} from "./engine.js";')
        fixture.add("src/engine.ts", "export function parse(value) { return value; }")
        for i in range(40):
            fixture.add(f"unrelated{i:02d}.ts", "export function helper() { return true; }")
        snapshot = PublicGitHub(fixture.read).fetch_repository("sample/project", 3)
        self.assertEqual([f["path"] for f in snapshot["files"]], ["index.ts", "src/index.ts", "src/engine.ts"])
        self.assertEqual(sum("/git/blobs/" in call[0] for call in fixture.calls), 3)
        self.assertEqual(len(snapshot["coverage"]["static_export_hints"]), 2)
        self.assertTrue(snapshot["coverage"]["export_hints_complete"])
        self.assertFalse(snapshot["coverage"]["eligible_sample_complete"])

    def test_multiline_named_exports_keep_target_safety_filters(self):
        eligible = {"src/parse.ts": {}, "src/types.d.ts": {}}
        value = "\n".join(f'export {{\n parse as parseValue,\n}}\nfrom "{spec}";' for spec in (
            "./parse.js", "./types.d.ts", "../../parse.js", "https://host/parse.js", "./*.ts", "./parse.js?secret"))
        targets, complete = export_hints("src/index.ts", value, eligible)
        self.assertEqual(targets, ["src/parse.ts"])
        self.assertTrue(complete)

    def test_multiline_hint_overflow_remains_explicit_and_bounded(self):
        eligible = {f"source{i}.ts": {} for i in range(MAX_EXPORT_HINTS + 1)}
        for template in ("export {{\n item{i},\n}} from './source{i}.js';", "export{{item{i}}}from'./source{i}.js';"):
            with self.subTest(template=template):
                value = "\n".join(template.format(i=i) for i in range(MAX_EXPORT_HINTS + 1))
                targets, complete = export_hints("index.ts", value, eligible)
                self.assertEqual(targets, list(eligible)[:MAX_EXPORT_HINTS])
                self.assertFalse(complete)

    def test_non_code_reexports_cannot_spend_the_implementation_blob_slot(self):
        fake = 'export * from "./obsolete.js";'
        real = 'export {\n parse,\n} from "./real.js";'
        for prefix in (f"/*\n{fake}\n*/\n", f"const example = `\n{fake}\n`;\n",
                       f"const example = `outer ${{`\n{fake}\n`}}`;\n",
                       "const example = \"continued\\\nexport * from './obsolete.js';\\\n\";\n"):
            with self.subTest(prefix=prefix):
                fixture = GitHubFixture()
                fixture.add("index.ts", prefix + real)
                fixture.add("obsolete.ts", "export function obsolete() { return false; }")
                fixture.add("real.ts", "export function parse(value) { return value; }")
                snapshot = PublicGitHub(fixture.read).fetch_repository("sample/project", 2)
                self.assertEqual([f["path"] for f in snapshot["files"]], ["index.ts", "real.ts"])
                self.assertEqual(sum("/git/blobs/" in call[0] for call in fixture.calls), 2)
                self.assertEqual(snapshot["coverage"]["static_export_hints"], [{"from": "index.ts", "path": "real.ts"}])
                self.assertTrue(snapshot["coverage"]["export_hints_complete"])

    def test_literal_delimiters_and_interpolation_do_not_expose_fake_exports(self):
        eligible = {"obsolete.ts": {}, "real.ts": {}}
        fake = 'export * from "./obsolete.js";'
        real = 'export * from "./real.js";'
        prefixes = ("// export * from './obsolete.js';\n", "const url = 'https://host/*not-comment*/';\n",
                    "const pattern = /[\"'`{}]/g; const ratio = size / 2;\n",
                    f"const sample = `escaped \\`\n{fake}\n`;\n",
                    f"const sample = `outer ${{({{text: '}}', pattern: /[}}'`]/}})}}\n{fake}\n`;\n")
        for prefix in prefixes:
            with self.subTest(prefix=prefix):
                self.assertEqual(export_hints("index.ts", prefix + real, eligible), (["real.ts"], True))

    def test_comments_between_real_export_tokens_are_not_destinations(self):
        text = 'export /* names */ {\n parse, // note\n} /* clause */ from /* module */ "./real.js";'
        self.assertEqual(export_hints("index.ts", text, {"real.ts": {}}), (["real.ts"], True))

    def test_unterminated_non_code_regions_report_incomplete_scan(self):
        fake = 'export * from "./obsolete.js";'
        real = 'export * from "./real.js";\n'
        for prefix in ("/*\n", "const sample = `\n", "const sample = 'continued\\\n", "const pattern = /unfinished\n"):
            with self.subTest(prefix=prefix):
                self.assertEqual(export_hints("index.ts", real + prefix + fake, {"real.ts": {}, "obsolete.ts": {}}),
                                 (["real.ts"], False))

    def test_template_depth_limit_cannot_expose_tail_as_code(self):
        real = 'export * from "./real.js";\n'
        nested = "const sample = " + "`${" * MAX_LEXICAL_NESTING + "value" + "}`" * MAX_LEXICAL_NESTING
        fake = '\nexport * from "./obsolete.js";'
        self.assertEqual(export_hints("index.ts", real + nested + fake, {"real.ts": {}, "obsolete.ts": {}}),
                         (["real.ts"], False))

    def test_regexp_division_ambiguity_is_reported_without_losing_later_hint(self):
        real = 'export * from "./real.js";'
        for prefix in ('if (ready) /["\'`]/.test(value);\n', "const value = read() / denominator / scale;\n"):
            with self.subTest(prefix=prefix):
                self.assertEqual(export_hints("index.ts", prefix + real, {"real.ts": {}}), (["real.ts"], False))
        self.assertEqual(export_hints("index.ts", "const value = read() / 2;\n" + real, {"real.ts": {}}),
                         (["real.ts"], True))

    def test_repeated_malformed_slash_probes_have_a_shared_work_bound(self):
        real = 'export * from "./real.js";\n'
        malformed = "read() /[x) " * 1000
        fake = '\nexport * from "./obsolete.js";'
        self.assertEqual(export_hints("index.ts", real + malformed + fake, {"real.ts": {}, "obsolete.ts": {}}),
                         (["real.ts"], False))

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

    def test_auxiliary_file_names_are_not_implementation_outside_auxiliary_directories(self):
        for path in ("benchmark.js", "bench.mjs", "benchmarks.ts", "fixture.ts", "fixtures.tsx",
                     "benchmark-runner.py", "parser.bench.ts", "data.fixture.js", "src/BENCHMARK.JS:run"):
            with self.subTest(path=path):
                self.assertEqual(source_role(path), "infrastructure")
        for path in ("src/parse.ts", "benchmarking.py", "benchpress.ts", "fixtureFactory.js", "fixturescope.ts"):
            with self.subTest(path=path):
                self.assertEqual(source_role(path), "implementation")
