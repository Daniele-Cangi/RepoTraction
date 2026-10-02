"""JSX lexical exclusions and bounded acquisition; no acquired JS is executed."""
import json
import unittest

from missing_link.js_lexical import export_view, MAX_LEXICAL_NESTING
from missing_link.source_hints import export_hints, MAX_EXPORT_HINTS
from missing_link.sources import PublicGitHub
from test_missing_link_sources import GitHubFixture


class JsxHintTests(unittest.TestCase):
    fake = 'export * from "./obsolete.js";'
    real = 'export * from "./real.js";'
    eligible = {"obsolete.ts": {}, "real.ts": {}}

    def test_rendered_text_is_not_an_esm_or_commonjs_export(self):
        for suffix in (".jsx", ".tsx", ".JsX", ".TSX", ".js", ".mjs", ".cjs"):
            for fake in (self.fake, 'export {parse} from "./obsolete.js";',
                         'module.exports = require("./obsolete.js");', 'exports.parse=require("./obsolete.js");'):
                with self.subTest(suffix=suffix, fake=fake):
                    value = f"const view = <div>\n{fake}\n</div>;\n{self.real}"
                    self.assertEqual(export_hints("index" + suffix, value, self.eligible), (["real.ts"], True))

    def test_named_nested_and_fragment_elements_mask_their_entire_content(self):
        for name in ("div", "Component", "UI.Panel", "my-element", "svg:g", "Ärea"):
            with self.subTest(name=name):
                value = f"const view = <>\n<{name}>\n<span>{self.fake}</span>\n</{name}>\n</>;\n{self.real}"
                self.assertEqual(export_hints("index.tsx", value, self.eligible), (["real.ts"], True))
        self.assertEqual(export_hints("index.jsx", "const view = <Component />;\n" + self.real, self.eligible), (["real.ts"], True))

    def test_attribute_literals_are_raw_text_and_never_module_literals(self):
        values = (f"const view = <Component title='{self.fake}' />;\n",
                  f"const view = <Component title='>\n{self.fake}\n<' />;\n",
                  'const view = <Component title="ends\\" other="text" />;\n')
        for prefix in values:
            with self.subTest(prefix=prefix):
                self.assertEqual(export_hints("index.tsx", prefix + self.real, self.eligible), (["real.ts"], True))

    def test_embedded_expressions_strings_templates_regexps_and_nested_jsx_stay_hidden(self):
        value = ("const view = <Component title={'export * from \"./obsolete.js\";'} "
                 "data={{text: '}'}} {...props}>\n"
                 "{/* export * from './obsolete.js'; */}\n"
                 "{`outer ${`nested export * from './obsolete.js';`}`}\n"
                 "{/[{}'`]/.test(text) ? <span>\n" + self.fake + "\n</span> : null}\n"
                 "{(() => { return <Child label={'fake'} />; })()}\n"
                 "</Component>;\n" + self.real)
        self.assertEqual(export_hints("index.tsx", value, self.eligible), (["real.ts"], True))

    def test_jsx_text_cannot_consume_the_real_implementation_blob_slot(self):
        for suffix in (".jsx", ".tsx", ".JSX", ".js"):
            with self.subTest(suffix=suffix):
                fixture = GitHubFixture()
                barrel = "index" + suffix
                fixture.add("package.json", json.dumps({"source": "./" + barrel}))
                fixture.add(barrel, "const view = <div>\n" + self.fake + "\n</div>;\n" + self.real)
                fixture.add("obsolete.ts", "export function obsolete() { return false; }")
                fixture.add("real.ts", "export function parse(value) { return value; }")
                for index in range(40):
                    fixture.add(f"aaa_unrelated{index:02d}.ts", "export function helper() {}")
                snapshot = PublicGitHub(fixture.read).fetch_repository("sample/project", 3)
                self.assertEqual([file["path"] for file in snapshot["files"]], ["package.json", barrel, "real.ts"])
                self.assertEqual(sum("/git/blobs/" in call[0] for call in fixture.calls), 3)
                self.assertEqual(snapshot["coverage"]["static_export_hints"],
                                 [{"from": "package.json", "path": barrel}, {"from": barrel, "path": "real.ts"}])
                self.assertTrue(snapshot["coverage"]["export_hints_complete"])
                self.assertFalse(snapshot["coverage"]["eligible_sample_complete"])

    def test_mask_offsets_and_real_literal_references_are_preserved(self):
        value = "const view = <div>\n" + self.fake + "\n</div>;\n" + self.real
        visible, code, literals, complete = export_view(value, jsx=True)
        self.assertTrue(complete)
        self.assertEqual(len(visible), len(value))
        self.assertEqual(len(code), len(value))
        start, end = value.index("<div>"), value.index("</div>") + len("</div>")
        self.assertTrue(visible[start:end].isspace())
        self.assertFalse(any(code[start:end]))
        self.assertNotIn(value.index('"./obsolete.js"'), literals)
        self.assertEqual(literals[value.index('"./real.js"')], value.index('"./real.js"') + len('"./real.js"'))

    def test_unterminated_mismatched_and_unsupported_markup_cannot_expose_its_tail(self):
        for prefix in ("const view=<div>\n", "const view=<div></span>;\n", "const view=<Component title='\n",
                       "const view=<Component value={\n", "const view=<Component<Type> value={x}/>;\n",
                       "const view=<Component<Type>>\n"):
            with self.subTest(prefix=prefix):
                self.assertEqual(export_hints("index.tsx", self.real + "\n" + prefix + self.fake, self.eligible),
                                 (["real.ts"], False))

    def test_jsx_depth_uses_the_shared_lexical_bound(self):
        for depth, complete in ((MAX_LEXICAL_NESTING - 1, True), (MAX_LEXICAL_NESTING, False)):
            with self.subTest(depth=depth):
                value = self.real + "\nconst view=" + "<div>" * depth + self.fake + "</div>" * depth + ";"
                self.assertEqual(export_hints("index.tsx", value, self.eligible), (["real.ts"], complete))

    def test_plain_ts_assertions_and_common_tsx_generics_and_comparisons_remain_code(self):
        for path, prefix in (("index.ts", "const value=<Input>data;\n"),
                             ("index.tsx", "const identity=<T,>(value:T)=>value;\n"),
                             ("index.tsx", "function identity<T>(value:T) { return value; }\n"),
                             ("index.tsx", "const smaller = left < right;\n")):
            with self.subTest(path=path, prefix=prefix):
                self.assertEqual(export_hints(path, prefix + self.real, self.eligible), (["real.ts"], True))
        # Grammar-dependent constrained-arrow/JSX ambiguity remains incomplete.
        value = self.real + "\nconst identity=<T extends Input>(value:T)=>value;"
        self.assertEqual(export_hints("index.tsx", value, self.eligible), (["real.ts"], False))

    def test_many_rendered_declarations_do_not_spend_the_export_hint_cap(self):
        rendered = "\n".join(self.fake for _ in range(MAX_EXPORT_HINTS + 20))
        value = "const view=<div>\n" + rendered + "\n</div>;\n" + self.real
        self.assertEqual(export_hints("index.tsx", value, self.eligible), (["real.ts"], True))
        eligible = {f"source{i}.ts": {} for i in range(MAX_EXPORT_HINTS + 1)}
        value = "const view=<div>\n" + rendered + "\n</div>;\n" + "".join(
            f'export * from "./source{i}.js";' for i in range(MAX_EXPORT_HINTS + 1))
        self.assertEqual(export_hints("index.tsx", value, eligible), (list(eligible)[:MAX_EXPORT_HINTS], False))

    def test_block_end_ambiguity_stays_visible_without_rendered_exports(self):
        value = "function render(){}\n<div>\n" + self.fake + "\n</div>;\n" + self.real
        self.assertEqual(export_hints("index.tsx", value, self.eligible), (["real.ts"], False))


if __name__ == "__main__":
    unittest.main()
