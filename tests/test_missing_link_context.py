"""Deterministic prompt-selection tests; no model calls or acquired-code execution."""
import copy
import json
import unittest

from missing_link.context import build_context, select_capabilities
from test_missing_link import repository, issue


class ContextSelectionTests(unittest.TestCase):
    def cap(self, path, name, first=1, last=3):
        cap = copy.deepcopy(repository()["capabilities"][0])
        cap.update(id=path + ":" + name, name=name, entrypoint=path + ":" + name,
                   definition={"end_line": last})
        cap["evidence"][0].update(path=path, line=first, end_line=min(first + 2, last))
        return cap

    def file(self, path, lines=180, width=120):
        return {"path": path, "kind": "source", "text": ("# " + "x" * width + "\n") * lines,
                "url": "https://github.com/example/words/blob/" + "a" * 40 + "/" + path}

    def test_capability_limit_prefers_library_and_diversifies_modules(self):
        caps = [self.cap("winbuild/build_prepare.py", f"build{i}") for i in range(50)]
        caps += [self.cap("src/big.py", f"library{i}") for i in range(40)]
        caps += [self.cap("src/other.py", "solve"), self.cap("tests/test_library.py", "test_solve")]
        selected = select_capabilities(caps)
        self.assertEqual(len(selected), 30)
        self.assertEqual(selected[1]["entrypoint"], "src/other.py:solve")
        self.assertTrue(all(cap["entrypoint"].startswith("src/") for cap in selected))

    def test_entrypoint_absence_uses_evidence_path_for_sampling(self):
        build = self.cap("ci_tools/build.py", "build")
        library = self.cap("src/library.py", "solve")
        for cap in (build, library):
            del cap["entrypoint"]
        self.assertEqual(select_capabilities([build, library], limit=1), [library])

    def test_product_source_reaches_prompt_before_build_infrastructure(self):
        repo = repository()
        repo["files"] = [self.file("winbuild/build_prepare.py", 600), self.file("src/library.py", 3)]
        repo["capabilities"] = [self.cap("winbuild/build_prepare.py", f"build{i}", 1, 180) for i in range(35)]
        repo["capabilities"].append(self.cap("src/library.py", "solve"))
        for demand in (None, issue()):
            data, report = build_context(repo, demand, "matches" if demand else "capabilities", 60000)
            self.assertIn("file:src/library.py#L1-L3", data["sources"])
            self.assertEqual(data["repository"]["capabilities"][0]["name"], "solve")
            self.assertIn("src/library.py", report["implementation_source_paths"])
            self.assertFalse(report["implementation_context_missing"])
            self.assertTrue(report["omitted_source_count"])
            self.assertLess(len(json.dumps(data).encode()), 44000)

    def test_first_span_of_each_definition_precedes_long_definition_tails(self):
        repo = repository()
        repo["files"] = [self.file("src/first.py"), self.file("src/second.py")]
        repo["capabilities"] = [self.cap("src/first.py", "first", 1, 180),
                                self.cap("src/second.py", "second", 1, 180)]
        data, report = build_context(repo, None, "capabilities", 60000)
        ids = list(data["sources"])
        self.assertLess(ids.index("file:src/second.py#L1-L60"), ids.index("file:src/first.py#L61-L120"))
        self.assertEqual(report["selected_capability_roles"], {"implementation": 2})

    def test_infrastructure_only_context_is_explicit_without_discarding_sources(self):
        repo = repository()
        repo["files"] = [self.file("winbuild/build_prepare.py", 3)]
        repo["capabilities"] = [self.cap("winbuild/build_prepare.py", "build")]
        data, report = build_context(repo, None, "capabilities", 60000)
        self.assertTrue(data["sources"])
        self.assertTrue(report["implementation_context_missing"])
        self.assertEqual(report["supplied_source_roles"], {"infrastructure": 1})

    def test_documentation_is_not_reported_as_implementation(self):
        repo = repository()
        repo["files"] = [dict(self.file("README.md", 3), kind="documentation")]
        repo["capabilities"] = [self.cap("README.md", "product")]
        _, report = build_context(repo, None, "capabilities", 60000)
        self.assertTrue(report["implementation_context_missing"])
        self.assertEqual(report["selected_capability_roles"], {"support": 1})


if __name__ == "__main__":
    unittest.main()
