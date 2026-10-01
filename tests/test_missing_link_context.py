"""Deterministic prompt-selection tests; no model calls or acquired-code execution."""
import copy
import json
import unittest

from missing_link.context import build_context, select_capabilities
from missing_link.contracts import MAX_SCOPED_IDS, schema_for
from test_missing_link import repository, issue


class ContextSelectionTests(unittest.TestCase):
    def busy_issue(self, comments=200):
        demand = issue()
        demand["comments"] = [{"url": demand["url"] + f"#issuecomment-{i}", "body": "Short comment."}
                              for i in range(comments)]
        demand["timeline"] = [{"id": i, "event": "labeled"} for i in range(200)]
        return demand

    def test_packed_scope_and_schema_share_the_same_boundary(self):
        for comments in (199, 200):
            with self.subTest(comments=comments):
                demand = self.busy_issue(comments)
                data, report = build_context(None, demand, "request", 180000)
                self.assertEqual(len(data["sources"]), MAX_SCOPED_IDS)
                schema_for("request", source_ids=data["sources"])
                self.assertEqual(report["source_id_limit"], MAX_SCOPED_IDS)
                self.assertEqual(report["source_id_limit_omissions"], comments - 199)
                self.assertEqual(report["omitted_source_count"], comments - 199)
                self.assertEqual(report["discussion_complete"], comments == 199)
                self.assertIn("q0", data["sources"])
                self.assertIn("t199", data["sources"])

    def test_request_packing_accounts_for_optional_hints_and_rolls_back_rejected_sources(self):
        demand = issue()
        demand["comments"] = [{"url": demand["url"] + f"#issuecomment-{i}",
            "body": f"config_{i}?: string; " + "x" * 1540} for i in range(30)]
        data, report = build_context(None, demand, "request", 60000)
        self.assertLessEqual(len(json.dumps(data, ensure_ascii=False).encode()), 44000)
        self.assertTrue(report["omitted_source_count"])
        self.assertFalse(report["discussion_complete"])
        hints = data["potential_subrequirements"]["items"]
        self.assertTrue(hints)
        self.assertTrue(all(hint["source_id"] in data["sources"] for hint in hints))
        self.assertTrue(all(hint["quote"] in data["sources"][hint["source_id"]]["quote"] for hint in hints))
        self.assertFalse({hint["source_id"] for hint in hints} & set(report["omitted_source_ids"]))

    def test_id_bound_preserves_later_constraint_and_explicitly_omits_old_context(self):
        demand = self.busy_issue()
        demand["comments"][-1]["body"] = "Must not use Node.js."
        data, report = build_context(None, demand, "request", 180000)
        self.assertEqual(len(data["sources"]), MAX_SCOPED_IDS)
        self.assertIn("Must not use Node.js.", data["sources"]["q200"]["quote"])
        self.assertNotIn("q1", data["sources"])
        self.assertIn("q1", report["omitted_source_ids"])
        self.assertEqual(report["omitted_constraint_ids"], [])
        self.assertFalse(report["discussion_complete"])

    def test_busy_discussion_reserves_scope_for_repository_evidence(self):
        data, report = build_context(repository(), self.busy_issue(), "matches", 180000)
        self.assertLessEqual(len(data["sources"]), MAX_SCOPED_IDS)
        self.assertIn("file:words.py#L1-L3", data["sources"])
        self.assertTrue(report["source_id_limit_omissions"])
        self.assertFalse(report["discussion_complete"])
        schema_for("matches", source_ids=data["sources"], capability_ids=report["capability_ids"], requirement_ids=["r0"])

    def target(self, path, value):
        return {"path": path, "text": value,
                "url": "https://github.com/example/site/blob/" + "b" * 40 + "/" + path}

    def test_target_ids_are_not_timeline_or_shortened_discussion(self):
        demand = issue()
        demand["timeline"] = [{"event": "labeled", "id": 99}]
        value = "# target reference only\n" + "x" * 20000
        demand["target_context"] = {"public": True, "revision": "b" * 40,
                                    "files": [self.target("client.py", value)]}
        data, report = build_context(repository(), demand, "matches", 180000)
        self.assertTrue(report["discussion_complete"])
        self.assertEqual(report["shortened_discussion_ids"], [])
        self.assertIn("t0", data["sources"])
        self.assertIn("q1", data["sources"])
        self.assertEqual(data["sources"]["target:client.py"]["quote"], value)
        self.assertEqual(data["sources"]["target:client.py"]["kind"], "target_reference_context")
        ids = list(data["sources"])
        self.assertLess(ids.index("q1"), ids.index("target:client.py"))
        self.assertLess(ids.index("t0"), ids.index("target:client.py"))
        self.assertLess(ids.index("file:words.py#L1-L3"), ids.index("target:client.py"))

    def test_large_target_omissions_do_not_displace_discussion_or_definition(self):
        demand = issue()
        demand["target_context"] = {"files": [self.target(f"client{i}.py", "x" * 32768) for i in range(4)]}
        data, report = build_context(repository(), demand, "matches", 60000)
        self.assertTrue(report["discussion_complete"])
        self.assertEqual(report["shortened_discussion_ids"], [])
        self.assertIn("q0", data["sources"])
        self.assertIn("q1", data["sources"])
        self.assertIn("file:words.py#L1-L3", data["sources"])
        omitted = report["target_reference_context"]["omitted_source_ids"]
        self.assertGreaterEqual(len(omitted), 3)
        self.assertTrue(all(ref.startswith("target:") for ref in omitted))

    def test_target_files_do_not_take_reserved_definition_slot_at_id_limit(self):
        demand = self.busy_issue()
        demand["target_context"] = {"files": [self.target(f"client{i}.py", "import example\n") for i in range(4)]}
        data, report = build_context(repository(), demand, "matches", 180000)
        self.assertIn("file:words.py#L1-L3", data["sources"])
        self.assertLessEqual(len(data["sources"]), MAX_SCOPED_IDS)
        target = report["target_reference_context"]
        self.assertEqual(len(target["source_ids"]) + len(target["omitted_source_ids"]), 4)
        self.assertLess(list(data["sources"]).index("file:words.py#L1-L3"),
                        list(data["sources"]).index(target["source_ids"][0]))
        self.assertFalse(report["discussion_complete"])  # Only real discussion omissions determine this.

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

    def test_root_test_only_context_does_not_certify_implementation(self):
        for path in ("test.js", "test.py", "spec.ts", "tests.cjs", "specs.tsx"):
            with self.subTest(path=path):
                repo = repository()
                # Old/imported metadata can still call the file source; its path
                # must independently prevent promotion to implementation.
                repo["files"] = [self.file(path, 3)]
                repo["capabilities"] = [self.cap(path, "test_behavior")]
                data, report = build_context(repo, None, "capabilities", 60000)
                self.assertTrue(data["sources"])
                self.assertTrue(report["implementation_context_missing"])
                self.assertEqual(report["implementation_source_paths"], [])
                self.assertEqual(report["selected_capability_roles"], {"test": 1})

    def test_colocated_example_only_context_is_retained_but_not_implementation(self):
        for path in ("example.py", "demo.ts", "Button.stories.tsx", "src/widget.example.js", "src/widget.story.jsx"):
            with self.subTest(path=path):
                repo = repository()
                repo["files"] = [self.file(path, 3)]
                repo["capabilities"] = [self.cap(path, "show")]
                data, report = build_context(repo, None, "capabilities", 60000)
                self.assertTrue(data["sources"])
                self.assertTrue(report["implementation_context_missing"])
                self.assertEqual(report["implementation_source_paths"], [])
                self.assertEqual(report["selected_capability_roles"], {"infrastructure": 1})

    def test_auxiliary_directory_only_context_is_retained_but_not_implementation(self):
        for path in ("example/index.py", "demo/index.ts", "demos/index.js", "fixture/data.ts",
                     "story/index.jsx", "stories/Button.tsx", "src/DEMOS/index.cjs"):
            with self.subTest(path=path):
                repo = repository()
                repo["files"] = [self.file(path, 3)]
                repo["capabilities"] = [self.cap(path, "show")]
                for demand in (None, issue()):
                    data, report = build_context(repo, demand, "matches" if demand else "capabilities", 60000)
                    self.assertTrue(any(source_id.startswith("file:" + path) for source_id in data["sources"]))
                    self.assertTrue(report["implementation_context_missing"])
                    self.assertEqual(report["implementation_source_paths"], [])
                    self.assertEqual(report["selected_capability_roles"], {"infrastructure": 1})
                    self.assertEqual(report["supplied_source_roles"], {"infrastructure": 1})

    def test_busy_long_discussion_cannot_consume_implementation_bytes(self):
        demand = issue()
        demand["comments"] = [{"url": demand["url"] + f"#issuecomment-{i}", "body": "Old discussion " * 1300} for i in range(10)]
        repo = repository()
        repo["files"] = [self.file("src/library.py", 3)]
        repo["capabilities"] = [self.cap("src/library.py", "solve")]
        data, report = build_context(repo, demand, "matches", 60000)
        self.assertIn("q0", data["sources"])
        self.assertIn("file:src/library.py#L1-L3", data["sources"])
        self.assertFalse(report["implementation_context_missing"])
        self.assertFalse(report["discussion_complete"])
        self.assertTrue(report["omitted_source_count"])

    def test_typescript_declaration_is_not_implementation_context(self):
        repo = repository()
        repo["files"] = [self.file("index.d.ts", 3)]
        repo["capabilities"] = [self.cap("index.d.ts", "solve")]
        _, report = build_context(repo, None, "capabilities", 60000)
        self.assertTrue(report["implementation_context_missing"])


if __name__ == "__main__":
    unittest.main()
