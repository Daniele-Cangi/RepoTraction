import base64
import copy
import sys
import unittest
from collections import deque
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from missing_link.sources import (  # noqa: E402
    MAX_FILE_BYTES,
    MAX_DISCUSSION_CHARS,
    PublicGitHub,
    extract_structure,
    parse_issue_url,
    redact_public_text,
    validate_repository,
    _select_files,
    source_role,
    _kind,
    SUPPORTED_CODE,
    _initializer_imports,
)


REVISION = "a" * 40
TREE = "b" * 40


class GitHubFixture:
    def __init__(self):
        self.calls = []
        self.repo = {"id": 1, "full_name": "sample/project", "private": False,
                     "visibility": "public", "default_branch": "feature/main",
                     "description": "Example public code", "license": {"spdx_id": "MIT"}}
        self.entries = []
        self.blobs = {}
        self.tree_truncated = False
        self.issue = {"id": 80, "title": "Preserve rows while converting data", "body": "I need JSON from CSV.",
                      "state": "open", "state_reason": None, "updated_at": "2026-09-30T10:00:00Z",
                      "user": {"login": "human", "type": "User"}, "labels": [], "comments": 0}
        self.comment_pages = {1: []}
        self.timeline_pages = {1: []}
        self.search_pages = {}

    def add(self, path, text, mode="100644"):
        index = len(self.entries) + 1
        sha = f"{index:040x}"
        raw = text if isinstance(text, bytes) else text.encode()
        self.entries.append({"path": path, "type": "blob", "mode": mode, "sha": sha, "size": len(raw)})
        self.blobs[sha] = {"sha": sha, "encoding": "base64", "content": base64.b64encode(raw).decode()}
        return sha

    def read(self, endpoint, params=None):
        self.calls.append((endpoint, params))
        if endpoint == "repos/sample/project":
            return copy.deepcopy(self.repo)
        if endpoint == "repos/sample/project/commits/feature%2Fmain":
            return {"sha": REVISION, "commit": {"tree": {"sha": TREE}}}
        if endpoint == f"repos/sample/project/git/trees/{TREE}":
            return {"tree": copy.deepcopy(self.entries), "truncated": self.tree_truncated}
        if "/git/blobs/" in endpoint:
            return copy.deepcopy(self.blobs[endpoint.rsplit("/", 1)[1]])
        if endpoint == "repos/sample/project/issues/8":
            return copy.deepcopy(self.issue)
        if endpoint.endswith("/issues/8/comments"):
            return copy.deepcopy(self.comment_pages.get(params["page"], []))
        if endpoint.endswith("/issues/8/timeline"):
            return copy.deepcopy(self.timeline_pages.get(params["page"], []))
        if endpoint == "search/issues":
            return copy.deepcopy(self.search_pages[params["page"]])
        raise AssertionError(f"Unexpected endpoint: {endpoint}")


class SourceValidationTests(unittest.TestCase):
    def test_complete_selection_uses_queue_removals_and_preserves_bounded_prefix(self):
        removals = []
        class TrackingQueue(deque):
            def popleft(self):
                item = super().popleft()
                removals.append(item["path"])
                return item
        entries = [{"path": f"pkg/mod_{index:05d}.py", "size": 200} for index in range(10000)]
        entries += [{"path": "README.md", "size": 100}, {"path": "pyproject.toml", "size": 100},
                    {"path": "tests/test_engine.py", "size": 100}, {"path": "pkg/core.py", "size": 200}]
        bounded = _select_files(entries, 6)
        self.assertEqual([e["path"] for e in bounded],
                         ["README.md", "pyproject.toml", "pkg/core.py", "pkg/mod_00000.py",
                          "tests/test_engine.py", "pkg/mod_00001.py"])
        with mock.patch("missing_link.sources.deque", TrackingQueue, create=True):
            complete = _select_files(entries, len(entries))
        self.assertEqual(complete[:6], bounded)
        self.assertEqual(len(complete), len(entries))
        self.assertEqual(len(removals), len(entries))
        self.assertEqual(len({entry["path"] for entry in complete}), len(entries))

    def test_build_directories_are_sampling_hints_not_product_implementation(self):
        for path in ("winbuild/build_prepare.py", "ci_tools/update.py", "_custom_build/backend.py:compile"):
            self.assertEqual(source_role(path), "infrastructure")
        self.assertEqual(source_role("src/PIL/Image.py:open"), "implementation")

    def test_standalone_test_and_spec_basenames_are_not_implementation(self):
        for extension in SUPPORTED_CODE:
            for name in ("test", "tests", "spec", "specs"):
                for prefix in ("", "src/"):
                    path = prefix + name + extension
                    with self.subTest(path=path):
                        self.assertEqual(_kind(path), "test")
                        self.assertEqual(source_role(path), "test")
                        self.assertEqual(source_role(path + ":test_behavior"), "test")
        self.assertEqual(_kind("TEST.JS"), "test")
        self.assertEqual(source_role("SPEC.TS:behavior"), "test")
        for path in ("testimony.py", "specification.ts", "contest.js", "src/testing.py", "src/testament.py"):
            with self.subTest(path=path):
                self.assertEqual(_kind(path), "source")
                self.assertEqual(source_role(path), "implementation")

    def test_acquisition_keeps_root_tests_as_references_not_product_capabilities(self):
        fixture = GitHubFixture()
        for path in ("test.py", "spec.ts", "tests.js"):
            fixture.add(path, "def test_transform():\n    assert transform('value') == 'value'\n" if path.endswith(".py")
                        else "function testTransform() { return true; }\n")
        fixture.add("src/library.py", "def transform(value):\n    return value\n")
        result = PublicGitHub(fixture.read).fetch_repository("sample/project")
        kinds = {file["path"]: file["kind"] for file in result["files"]}
        self.assertEqual(kinds, {"test.py": "test", "spec.ts": "test", "tests.js": "test", "src/library.py": "source"})
        caps = extract_structure(result)
        self.assertTrue(any(cap["name"] == "transform" for cap in caps))
        self.assertFalse(any(cap.get("entrypoint", "").split(":", 1)[0] in {"test.py", "spec.ts", "tests.js"} for cap in caps))

    def test_infrastructure_does_not_crowd_out_product_source(self):
        fixture = GitHubFixture()
        for index in range(40):
            fixture.add(f"checks/check_{index:02d}.py", "def check(): return True\n")
        for path in ("setup.py", "conftest.py", "selftest.py", ".github/compare-dist-sizes.py"):
            fixture.add(path, "def helper(): return True\n")
        for path in ("src/PIL/Image.py", "src/PIL/ImageOps.py", "src/PIL/Font.py"):
            fixture.add(path, "def transform(image): return image\n")
        result = PublicGitHub(fixture.read).fetch_repository("sample/project")
        self.assertEqual([f["path"] for f in result["files"] if f["kind"] == "source"][:3],
                         ["src/PIL/Font.py", "src/PIL/Image.py", "src/PIL/ImageOps.py"])
        self.assertEqual(result["coverage"]["acquired_source_roles"]["implementation"], 3)
        self.assertFalse(result["coverage"]["complete"])
        self.assertIn("not export verification", result["coverage"]["sampling_policy"])

    def test_missing_implementation_sample_is_explicit(self):
        fixture = GitHubFixture()
        fixture.add("README.md", "documentation")
        fixture.add("src/library.py", "def solve(): return True\n")
        result = PublicGitHub(fixture.read).fetch_repository("sample/project", max_files=1)
        self.assertTrue(any("cannot represent product" in x for x in result["coverage"]["limitations"]))

    def test_tiny_initializers_do_not_crowd_out_deeper_implementation(self):
        fixture = GitHubFixture()
        for index in range(30):
            fixture.add(f"pkg{index:02d}/__init__.py", "" if index % 2 else "# package marker\n")
        fixture.add("src/deep/implementation.py", "def convert(value):\n    return value\n")
        result = PublicGitHub(fixture.read).fetch_repository("sample/project")
        paths = [file["path"] for file in result["files"]]
        self.assertEqual(len(paths), 24)
        self.assertEqual(paths[0], "src/deep/implementation.py")
        self.assertEqual(sum(path.endswith("__init__.py") for path in paths), 23)

    def test_initializers_remain_eligible_and_substantial_ones_are_not_demoted(self):
        markers = [{"path": f"pkg{index:02d}/__init__.py", "size": 0} for index in range(30)]
        self.assertEqual(len(_select_files(markers, 24)), 24)
        entries = markers + [{"path": "meaningful/__init__.py", "size": 400},
                             {"path": "src/deep/implementation.py", "size": 2000},
                             {"path": "cli.py", "size": 200}]
        selected = _select_files(entries, 3)
        self.assertEqual([entry["path"] for entry in selected],
                         ["cli.py", "meaningful/__init__.py", "src/deep/implementation.py"])

    def test_repository_and_issue_urls_are_strict(self):
        self.assertEqual(validate_repository("sample/project"), "sample/project")
        self.assertEqual(parse_issue_url("https://github.com/sample/project/issues/8"), ("sample/project", 8))
        for invalid in ("../repo", "sample/..", "sample/repo?foo", "sample/repo/extra", "sample/repo#x", "", None):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                validate_repository(invalid)
        for invalid in (
            "http://github.com/sample/project/issues/8", "https://github.com.evil/sample/project/issues/8",
            "https://user@github.com/sample/project/issues/8", "https://github.com:443/sample/project/issues/8",
            "https://github.com/sample/project/pull/8", "https://github.com/sample/project/issues/8?foo=1",
            "https://github.com/sample/project/issues/8#comment", "https://github.com/sample/project/issues/0",
            "https://github.com/sample/project/issues/2147483648", "https://github.com/sample/project/issues/%38",
        ):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                parse_issue_url(invalid)

    def test_private_repository_is_rejected_before_any_source_or_issue_read(self):
        fixture = GitHubFixture()
        fixture.repo["private"] = True
        reader = PublicGitHub(fixture.read)
        with self.assertRaisesRegex(ValueError, "public"):
            reader.fetch_repository("sample/project")
        self.assertEqual(len(fixture.calls), 1)
        fixture.calls = []
        with self.assertRaisesRegex(ValueError, "public"):
            reader.fetch_issue("https://github.com/sample/project/issues/8")
        self.assertEqual(len(fixture.calls), 1)

    def test_metadata_without_explicit_public_flag_is_not_trusted(self):
        fixture = GitHubFixture()
        del fixture.repo["private"]
        with self.assertRaises(ValueError):
            PublicGitHub(fixture.read).fetch_repository("sample/project")

    def test_missing_identity_cannot_mix_repository_history(self):
        fixture = GitHubFixture()
        del fixture.repo["id"]
        with self.assertRaisesRegex(ValueError, "identity"):
            PublicGitHub(fixture.read).fetch_repository("sample/project")
        self.assertEqual(len(fixture.calls), 1)

    def test_budget_checkpoint_can_cancel_without_being_swallowed(self):
        fixture = GitHubFixture()
        def checkpoint():
            raise RuntimeError("cancelled")
        with self.assertRaisesRegex(RuntimeError, "cancelled"):
            PublicGitHub(fixture.read, checkpoint).fetch_repository("sample/project")
        self.assertEqual(fixture.calls, [])

    def test_redacts_common_credentials_and_bounds_text(self):
        token = "ghp_" + "a" * 36
        self.assertNotIn(token, redact_public_text("token: " + token))
        self.assertIn("[REDACTED]", redact_public_text("api_key='a-real-secret-key-0123456789'"))
        self.assertEqual(len(redact_public_text("a" * 100000)), 65536)


class RepositoryAcquisitionTests(unittest.TestCase):
    def test_same_package_absolute_hints_stay_in_the_initializer_layout(self):
        for prefix in ("", "src/"):
            for statement in ("import pkg.engine", "import pkg.engine as api",
                              "from pkg.engine import run", "from pkg import engine"):
                with self.subTest(prefix=prefix, statement=statement):
                    initializer = prefix + "pkg/__init__.py"
                    own_engine = prefix + "pkg/engine.py"
                    eligible = {path: {} for path in ("pkg/__init__.py", "pkg/engine.py",
                                                       "src/pkg/__init__.py", "src/pkg/engine.py")}
                    self.assertEqual(_initializer_imports(initializer, statement, eligible), [own_engine])
                    del eligible[own_engine]
                    self.assertEqual(_initializer_imports(initializer, statement, eligible), [])

    def test_nested_initializer_uses_own_layout_for_absolute_package_imports(self):
        for prefix in ("", "src/"):
            with self.subTest(prefix=prefix):
                eligible = {path: {} for path in ("pkg/__init__.py", "pkg/engine.py",
                                                   "src/pkg/__init__.py", "src/pkg/engine.py")}
                self.assertEqual(_initializer_imports(prefix + "pkg/plugins/__init__.py",
                                                      "import pkg.engine", eligible),
                                 [prefix + "pkg/__init__.py", prefix + "pkg/engine.py"])

    def test_other_package_hints_prefer_local_layout_without_claiming_runtime_resolution(self):
        eligible = {"other/engine.py": {}, "src/other/engine.py": {}}
        self.assertEqual(_initializer_imports("src/pkg/__init__.py", "import other.engine", eligible),
                         ["src/other/engine.py", "other/engine.py"])
        self.assertEqual(_initializer_imports("pkg/__init__.py", "import other.engine", eligible),
                         ["other/engine.py", "src/other/engine.py"])
        # A root package literally named src is not a src-layout search root.
        self.assertEqual(_initializer_imports("src/__init__.py", "import src.engine",
                                              {"src/engine.py": {}, "src/src/engine.py": {}}),
                         ["src/engine.py"])

    def test_acquired_initializer_cannot_follow_same_package_in_another_layout(self):
        for prefix in ("", "src/"):
            for own_exists in (True, False):
                with self.subTest(prefix=prefix, own_exists=own_exists):
                    fixture = GitHubFixture()
                    other_prefix = "" if prefix else "src/"
                    initializer = prefix + "pkg/__init__.py"
                    helper = prefix + "pkg/a_helper.py"
                    own_engine = prefix + "pkg/engine.py"
                    other_engine = other_prefix + "pkg/engine.py"
                    fixture.add(initializer, "# Public package interface\n" * 4 + "import pkg.engine\n")
                    fixture.add(helper, "def helper(): pass\n")
                    other_sha = fixture.add(other_engine, "def unrelated_engine(): pass\n")
                    if own_exists:
                        fixture.add(own_engine, "def execute(): pass\n")
                    # The regression concerns an already acquired initializer,
                    # independent of which layout the path heuristic sees first.
                    def selected(entries, limit):
                        ordered = _select_files(entries, limit)
                        return ([entry for entry in ordered if entry["path"] == initializer] +
                                [entry for entry in ordered if entry["path"] == helper] +
                                [entry for entry in ordered if entry["path"] not in {initializer, helper}])
                    with mock.patch("missing_link.sources._select_files", side_effect=selected):
                        result = PublicGitHub(fixture.read).fetch_repository("sample/project", max_files=2)
                    self.assertEqual([f["path"] for f in result["files"]],
                                     [initializer, own_engine if own_exists else helper])
                    self.assertEqual(result["coverage"]["initializer_import_hints"],
                                     [{"from": initializer, "path": own_engine}] if own_exists else [])
                    blob_calls = [endpoint for endpoint, _ in fixture.calls if "/git/blobs/" in endpoint]
                    self.assertEqual(len(blob_calls), 2)
                    self.assertNotIn(f"repos/sample/project/git/blobs/{other_sha}", blob_calls)

    def test_dotted_imports_prioritize_intermediate_initializers_before_final_module(self):
        for prefix, statement in (
            ("", "import pkg.plugins.engine"),
            ("src/", "import pkg.plugins.engine as engine"),
            ("", "from pkg.plugins.engine import execute"),
            ("src/", "from pkg.plugins import engine as public_engine"),
            ("", "from .plugins.engine import execute"),
            ("src/", "from .plugins import engine"),
        ):
            with self.subTest(prefix=prefix, statement=statement):
                fixture = GitHubFixture()
                initializer = prefix + "pkg/__init__.py"
                intermediate = prefix + "pkg/plugins/__init__.py"
                engine = prefix + "pkg/plugins/engine.py"
                fixture.add(initializer, "# Public package interface\n" * 4 + statement + "\n")
                fixture.add(prefix + "pkg/a_helper.py", "def helper(): pass\n")
                fixture.add(intermediate, "# Plugin registration\n")
                fixture.add(engine, "def execute(): pass\n")
                result = PublicGitHub(fixture.read).fetch_repository("sample/project", max_files=3)
                self.assertEqual([f["path"] for f in result["files"]], [initializer, intermediate, engine])
                self.assertEqual(result["coverage"]["initializer_import_hints"],
                                 [{"from": initializer, "path": intermediate},
                                  {"from": initializer, "path": engine}])
                self.assertEqual(result["coverage"]["omitted_initializer_imports"], [])
                self.assertEqual(sum("/git/blobs/" in endpoint for endpoint, _ in fixture.calls), 3)

    def test_intermediate_initializers_supply_further_hints_without_expanding_budget(self):
        fixture = GitHubFixture()
        fixture.add("pkg/__init__.py", "# Public package interface\n" * 4 + "import pkg.plugins.engine\n")
        fixture.add("pkg/a_helper.py", "def helper(): pass\n")
        fixture.add("pkg/plugins/__init__.py", "from .registry import register\n")
        fixture.add("pkg/plugins/registry.py", "raise RuntimeError('never execute')\n")
        engine_sha = fixture.add("pkg/plugins/engine.py", "def execute(): pass\n")
        result = PublicGitHub(fixture.read).fetch_repository("sample/project", max_files=3)
        self.assertEqual([f["path"] for f in result["files"]],
                         ["pkg/__init__.py", "pkg/plugins/__init__.py", "pkg/plugins/registry.py"])
        self.assertEqual(result["coverage"]["omitted_initializer_imports"], ["pkg/plugins/engine.py"])
        blob_calls = [endpoint for endpoint, _ in fixture.calls if "/git/blobs/" in endpoint]
        self.assertEqual(len(blob_calls), 3)
        self.assertNotIn(f"repos/sample/project/git/blobs/{engine_sha}", blob_calls)

    def test_deep_imports_keep_ancestor_order_and_skip_unsafe_or_absent_initializers(self):
        fixture = GitHubFixture()
        fixture.add("pkg/__init__.py", "# Public package interface\n" * 4 +
                    "import pkg.ns.plugins.deep.more.engine\nimport pkg.ns.plugins.deep.more.engine as duplicate\n")
        fixture.add("pkg/a_helper.py", "def helper(): pass\n")
        # ns is a namespace package (no initializer); plugins is excluded.
        unsafe_sha = fixture.add("pkg/ns/plugins/__init__.py", "secret", mode="120000")
        fixture.add("pkg/ns/plugins/deep/__init__.py", "# Package marker\n")
        fixture.add("pkg/ns/plugins/deep/more/__init__.py", "# Package marker\n")
        fixture.add("pkg/ns/plugins/deep/more/engine.py", "def execute(): pass\n")
        result = PublicGitHub(fixture.read).fetch_repository("sample/project", max_files=4)
        self.assertEqual([f["path"] for f in result["files"]],
                         ["pkg/__init__.py", "pkg/ns/plugins/deep/__init__.py",
                          "pkg/ns/plugins/deep/more/__init__.py", "pkg/ns/plugins/deep/more/engine.py"])
        self.assertEqual(len(result["coverage"]["initializer_import_hints"]), 3)
        blob_calls = [endpoint for endpoint, _ in fixture.calls if "/git/blobs/" in endpoint]
        self.assertEqual(len(blob_calls), 4)
        self.assertNotIn(f"repos/sample/project/git/blobs/{unsafe_sha}", blob_calls)

    def test_intermediate_import_hint_chain_keeps_existing_metadata_and_read_caps(self):
        fixture = GitHubFixture()
        parts = ["pkg"] + [f"p{i:02d}" for i in range(80)]
        fixture.add("pkg/__init__.py", "import " + ".".join(parts) + ".engine\n")
        for depth in range(2, len(parts) + 1):
            fixture.add("/".join(parts[:depth]) + "/__init__.py", "# Package marker\n")
        fixture.add("/".join(parts) + "/engine.py", "def execute(): pass\n")
        result = PublicGitHub(fixture.read).fetch_repository("sample/project", max_files=3)
        self.assertEqual([f["path"] for f in result["files"]],
                         ["pkg/__init__.py", "pkg/p00/__init__.py", "pkg/p00/p01/__init__.py"])
        self.assertEqual(len(result["coverage"]["initializer_import_hints"]), 64)
        self.assertFalse(result["coverage"]["initializer_import_hints_complete"])
        self.assertEqual(len(result["coverage"]["omitted_initializer_imports"]), 62)
        self.assertEqual(sum("/git/blobs/" in endpoint for endpoint, _ in fixture.calls), 3)

    def test_repeated_hints_do_not_consume_extra_attempts_or_repeat_blob_reads(self):
        fixture = GitHubFixture()
        fixture.add("pkg/__init__.py", "# Public package interface\n" * 4 + "from pkg import b, c\n")
        fixture.add("pkg/a_helper.py", "def helper(): pass\n")
        # b's initializer repeats c's existing hint.
        fixture.add("pkg/b/__init__.py", "# Public package interface\n" * 4 + "from pkg import c\n")
        fixture.add("pkg/c.py", "def validate(value): return value\n")
        result = PublicGitHub(fixture.read).fetch_repository("sample/project", max_files=4)
        self.assertEqual([f["path"] for f in result["files"]],
                         ["pkg/__init__.py", "pkg/b/__init__.py", "pkg/c.py", "pkg/a_helper.py"])
        blob_calls = [endpoint for endpoint, _ in fixture.calls if "/git/blobs/" in endpoint]
        self.assertEqual(len(blob_calls), 4)
        self.assertEqual(len(set(blob_calls)), 4)
        self.assertTrue(result["coverage"]["complete"])

    def test_from_imports_follow_eligible_child_modules_and_keep_base_module(self):
        for prefix, statement, base, child in (
            ("", "from pkg import z_engine", None, "pkg/z_engine.py"),
            ("src/", "from pkg import z_engine as engine", None, "src/pkg/z_engine.py"),
            ("", "from pkg import z_engine", None, "pkg/z_engine/__init__.py"),
            ("", "from .nested import z_engine as engine", "pkg/nested/__init__.py", "pkg/nested/z_engine.py"),
        ):
            with self.subTest(statement=statement, child=child):
                fixture = GitHubFixture()
                initializer = prefix + "pkg/__init__.py"
                fixture.add(initializer, "# Public package interface\n" * 4 + statement + "\n")
                fixture.add(prefix + "pkg/a_helper.py", "def helper(): pass\n")
                if base:
                    fixture.add(base, "# nested package marker\n")
                fixture.add(child, "def validate(value): return value\n")
                expected = [initializer] + ([base] if base else []) + [child]
                result = PublicGitHub(fixture.read).fetch_repository("sample/project", max_files=len(expected))
                self.assertEqual([f["path"] for f in result["files"]], expected)
                self.assertEqual(sum("/git/blobs/" in endpoint for endpoint, _ in fixture.calls), len(expected))
                self.assertEqual(result["coverage"]["initializer_import_hints"],
                                 [{"from": initializer, "path": path} for path in expected[1:]])

    def test_from_import_child_hints_exclude_symlinks_and_do_not_expand_star(self):
        fixture = GitHubFixture()
        fixture.add("pkg/__init__.py", "# Public package interface\n" * 4 +
                    "from pkg import secret, z_engine as engine, z_engine\nfrom pkg import *\n")
        secret_sha = fixture.add("pkg/secret.py", "secret", mode="120000")
        fixture.add("pkg/a_helper.py", "def helper(): pass\n")
        fixture.add("pkg/z_engine.py", "def execute(): pass\n")
        result = PublicGitHub(fixture.read).fetch_repository("sample/project", max_files=2)
        self.assertEqual([f["path"] for f in result["files"]], ["pkg/__init__.py", "pkg/z_engine.py"])
        self.assertEqual(result["coverage"]["initializer_import_hints"],
                         [{"from": "pkg/__init__.py", "path": "pkg/z_engine.py"}])
        self.assertNotIn(f"repos/sample/project/git/blobs/{secret_sha}", [c[0] for c in fixture.calls])

    def test_plain_initializer_imports_prioritize_module_or_package_within_budget(self):
        for prefix, statement, target in (
            ("", "import pkg.z_engine", "pkg/z_engine.py"),
            ("src/", "import pkg.z_engine as engine", "src/pkg/z_engine.py"),
            ("", "import pkg.z_engine as engine", "pkg/z_engine/__init__.py"),
        ):
            with self.subTest(statement=statement, target=target):
                fixture = GitHubFixture()
                initializer = prefix + "pkg/__init__.py"
                fixture.add(initializer, "# Public package interface\n" * 4 + statement + "\n")
                fixture.add(prefix + "pkg/a_helper.py", "def helper(): pass\n")
                fixture.add(target, "def validate(value): return value\n")
                result = PublicGitHub(fixture.read).fetch_repository("sample/project", max_files=2)
                self.assertEqual([f["path"] for f in result["files"]], [initializer, target])
                self.assertEqual(result["coverage"]["initializer_import_hints"],
                                 [{"from": initializer, "path": target}])
                self.assertEqual(result["coverage"]["omitted_initializer_imports"], [])
                self.assertEqual(sum("/git/blobs/" in endpoint for endpoint, _ in fixture.calls), 2)

    def test_plain_import_hints_resolve_multiple_names_only_against_safe_tree(self):
        fixture = GitHubFixture()
        fixture.add("pkg/__init__.py", "# Public package interface\n" * 4 +
                    "import external_library, pkg.secret, pkg.z_engine as engine, pkg.z_late\n")
        fixture.add("pkg/a_helper.py", "def helper(): pass\n")
        secret_sha = fixture.add("pkg/secret.py", "secret", mode="120000")
        fixture.add("pkg/z_engine.py", "raise RuntimeError('never execute')\n")
        late_sha = fixture.add("pkg/z_late.py", "def late(): pass\n")
        result = PublicGitHub(fixture.read).fetch_repository("sample/project", max_files=2)
        self.assertEqual([f["path"] for f in result["files"]], ["pkg/__init__.py", "pkg/z_engine.py"])
        self.assertEqual(result["coverage"]["initializer_import_hints"],
                         [{"from": "pkg/__init__.py", "path": "pkg/z_engine.py"},
                          {"from": "pkg/__init__.py", "path": "pkg/z_late.py"}])
        self.assertEqual(result["coverage"]["omitted_initializer_imports"], ["pkg/z_late.py"])
        endpoints = [endpoint for endpoint, _ in fixture.calls]
        self.assertEqual(sum("/git/blobs/" in endpoint for endpoint in endpoints), 2)
        for sha in (secret_sha, late_sha):
            self.assertNotIn(f"repos/sample/project/git/blobs/{sha}", endpoints)

    def test_import_hint_ledger_has_a_bound_independent_of_file_budget(self):
        for statement in ("from .module_{i:02d} import item", "import pkg.module_{i:02d}"):
            with self.subTest(statement=statement):
                fixture = GitHubFixture()
                fixture.add("pkg/__init__.py", "\n".join(statement.format(i=i) for i in range(80)))
                for i in range(80):
                    fixture.add(f"pkg/module_{i:02d}.py", "def item(): pass\n")
                result = PublicGitHub(fixture.read).fetch_repository("sample/project", max_files=2)
                self.assertEqual(len(result["files"]), 2)
                self.assertEqual(len(result["coverage"]["initializer_import_hints"]), 64)
                self.assertFalse(result["coverage"]["initializer_import_hints_complete"])

    def test_large_first_module_cannot_hide_later_public_engine(self):
        fixture = GitHubFixture()
        fixture.add("pkg/core.py", "\n".join(f"def helper_{i}(): return True" for i in range(120)))
        fixture.add("pkg/engine.py", "class _Internal:\n" +
                    "\n".join(f"    def hidden_{i}(self): pass" for i in range(120)) +
                    "\ndef validate(value): return value\n")
        snapshot = PublicGitHub(fixture.read).fetch_repository("sample/project")
        capabilities = extract_structure(snapshot)
        self.assertEqual(len(capabilities), 100)
        self.assertIn("pkg/engine.py:validate", [cap["entrypoint"] for cap in capabilities])
        self.assertTrue(snapshot["coverage"]["analysis"]["capability_limit_reached"])

    def test_initializer_imports_preserve_public_engine_within_existing_budget(self):
        fixture = GitHubFixture()
        fixture.add("pkg/__init__.py", "# Public package interface\n" * 4 + "from pkg.validators import validate\nfrom .errors import Error\n")
        for index in range(30):
            fixture.add(f"pkg/a_helper_{index:02d}.py", "def helper(): return True\n")
        fixture.add("pkg/validators.py", "def validate(value): return value\n")
        fixture.add("pkg/errors.py", "class Error(Exception): pass\n")
        result = PublicGitHub(fixture.read).fetch_repository("sample/project", max_files=3)
        self.assertEqual([f["path"] for f in result["files"]],
                         ["pkg/__init__.py", "pkg/validators.py", "pkg/errors.py"])
        self.assertEqual(sum("/git/blobs/" in endpoint for endpoint, _ in fixture.calls), 3)
        self.assertEqual(result["coverage"]["omitted_initializer_imports"], [])
        self.assertFalse(result["coverage"]["complete"])

    def test_import_hints_are_safe_bounded_static_and_support_src_layout(self):
        fixture = GitHubFixture()
        fixture.add("src/pkg/__init__.py", "# Public package interface\n" * 4 + "from pkg.engine import execute\nfrom . import late\nfrom .secret import token\n")
        fixture.add("src/pkg/engine.py", "raise RuntimeError('never execute')\n")
        fixture.add("src/pkg/late.py", "def late(): pass\n")
        fixture.add("src/pkg/secret.py", "secret", mode="120000")
        result = PublicGitHub(fixture.read).fetch_repository("sample/project", max_files=2)
        self.assertEqual([f["path"] for f in result["files"]], ["src/pkg/__init__.py", "src/pkg/engine.py"])
        self.assertEqual(result["coverage"]["omitted_initializer_imports"], ["src/pkg/late.py"])
        self.assertEqual(len([c for c in fixture.calls if "/git/blobs/" in c[0]]), 2)

    def test_invalid_initializer_or_nested_dynamic_import_keeps_heuristic_sample(self):
        fixture = GitHubFixture()
        fixture.add("pkg/__init__.py", "# Public package interface\n" * 4 +
                    "def later():\n    from .z_engine import execute\n    import pkg.z_engine\n")
        fixture.add("pkg/a_helper.py", "def helper(): pass\n")
        fixture.add("pkg/z_engine.py", "def execute(): pass\n")
        result = PublicGitHub(fixture.read).fetch_repository("sample/project", max_files=2)
        self.assertEqual([f["path"] for f in result["files"]], ["pkg/__init__.py", "pkg/a_helper.py"])
        self.assertEqual(result["coverage"]["initializer_import_hints"], [])

    def test_pins_revision_reads_docs_source_tests_and_exact_license(self):
        fixture = GitHubFixture()
        fixture.add("README.md", "# Tool\n\nConvert records.")
        fixture.add("LICENSE.txt", "MIT License\nCopyright Example")
        fixture.add("pyproject.toml", "[project]\nname='tool'")
        fixture.add("src/converter.py", "def convert(rows):\n    return rows\n")
        fixture.add("tests/test_converter.py", "def test_rows():\n    assert convert([]) == []\n")
        result = PublicGitHub(fixture.read).fetch_repository("sample/project")
        self.assertEqual(result["revision"], REVISION)
        self.assertEqual(result["coverage"]["language_counts"]["Python"], 2)
        self.assertTrue(result["coverage"]["complete"])
        self.assertEqual(result["license"]["spdx_id"], "MIT")
        self.assertEqual(result["license_files"][0]["path"], "LICENSE.txt")
        for file in result["files"]:
            self.assertIn(f"/blob/{REVISION}/", file["url"])
            self.assertNotIn("feature/main", file["url"])
        self.assertIn(("repos/sample/project/commits/feature%2Fmain", None), fixture.calls)

    def test_never_acquires_sensitive_or_symlink_paths_and_discards_secret_content(self):
        fixture = GitHubFixture()
        excluded_shas = {
            fixture.add(".env", "TOKEN=x"), fixture.add("private.key", "secret"),
            fixture.add("../escape.py", "raise RuntimeError()"), fixture.add("/absolute.py", "x=1"),
            fixture.add("source\\unsafe.py", "x=1"), fixture.add("node_modules/a.js", "x=1"),
            fixture.add("link.py", "../../etc/secret", "120000"),
        }
        secret_sha = fixture.add("leak.py", "TOKEN = 'ghp_" + "a" * 36 + "'")
        fixture.add("good.py", "def local(): return 1")
        result = PublicGitHub(fixture.read).fetch_repository("sample/project")
        self.assertEqual([file["path"] for file in result["files"]], ["good.py"])
        endpoints = {endpoint for endpoint, _ in fixture.calls}
        for sha in excluded_shas:
            self.assertNotIn(f"repos/sample/project/git/blobs/{sha}", endpoints)
        self.assertIn(f"repos/sample/project/git/blobs/{secret_sha}", endpoints)
        self.assertEqual(result["coverage"]["excluded"]["credential_looking_content"], 1)

    def test_handles_binary_oversize_and_invalid_blob_without_claiming_full_sample(self):
        fixture = GitHubFixture()
        fixture.add("binary.py", b"hello\x00world")
        fixture.add("huge.py", "x" * (MAX_FILE_BYTES + 1))
        corrupt_sha = fixture.add("corrupt.py", "x=1")
        fixture.blobs[corrupt_sha]["content"] = "not base64!"
        fixture.add("good.py", "x=1")
        result = PublicGitHub(fixture.read).fetch_repository("sample/project")
        self.assertFalse(result["coverage"]["complete"])
        self.assertEqual(result["coverage"]["files_scanned"], 1)
        self.assertEqual(result["coverage"]["excluded"]["file_size"], 1)

    def test_truncated_tree_and_file_budget_are_visible_not_absence_of_capabilities(self):
        fixture = GitHubFixture()
        fixture.tree_truncated = True
        fixture.add("README.md", "docs")
        fixture.add("core.py", "def solve(): return 1")
        result = PublicGitHub(fixture.read).fetch_repository("sample/project", max_files=1)
        self.assertEqual(len(result["files"]), 1)
        self.assertTrue(result["coverage"]["tree_truncated"])
        self.assertFalse(result["coverage"]["complete"])
        self.assertTrue(any("budget" in limitation for limitation in result["coverage"]["limitations"]))

    def test_invalid_git_revision_cannot_form_permalink(self):
        fixture = GitHubFixture()
        def read(endpoint, params=None):
            if "/commits/" in endpoint:
                return {"sha": "main", "commit": {"tree": {"sha": TREE}}}
            return fixture.read(endpoint, params)
        with self.assertRaisesRegex(ValueError, "pinned"):
            PublicGitHub(read).fetch_repository("sample/project")


class IssueAcquisitionTests(unittest.TestCase):
    def test_comment_context_timeline_and_fingerprint_change_with_new_evidence(self):
        fixture = GitHubFixture()
        fixture.issue["comments"] = 1
        fixture.comment_pages[1] = [{"id": 9, "body": "Correction: use UTF-16 input.",
                                     "user": {"login": "human", "type": "User"}, "updated_at": "time1"}]
        fixture.timeline_pages[1] = [{"id": 1, "event": "closed", "state_reason": "completed"},
                                     {"id": 2, "event": "reopened"}, {"id": 3, "event": "marked_as_duplicate"}]
        reader = PublicGitHub(fixture.read)
        result = reader.fetch_issue("https://github.com/sample/project/issues/8")
        self.assertTrue(result["context_complete"])
        self.assertEqual(result["repo_id"], fixture.repo["id"])
        self.assertEqual(result["comments"][0]["author"], "human")
        self.assertEqual(result["timeline"][2]["event"], "marked_as_duplicate")
        fixture.comment_pages[1][0]["updated_at"] = "time2"
        changed = reader.fetch_issue("https://github.com/sample/project/issues/8")
        self.assertNotEqual(result["fingerprint"], changed["fingerprint"])

    def test_exact_page_limit_probes_for_more_context(self):
        fixture = GitHubFixture()
        fixture.issue["comments"] = 2
        fixture.comment_pages[1] = [{"id": 1, "body": "first", "user": {"login": "human"}}]
        fixture.comment_pages[2] = [{"id": 2, "body": "already solved", "user": {"login": "human"}}]
        result = PublicGitHub(fixture.read).fetch_issue("https://github.com/sample/project/issues/8", max_comments=1)
        self.assertFalse(result["context_complete"])
        self.assertEqual(len(result["comments"]), 1)
        self.assertTrue(any("Comment limit" in text for text in result["limitations"]))
        self.assertIn(("repos/sample/project/issues/8/comments", {"per_page": 1, "page": 2}), fixture.calls)

    def test_bot_context_is_marked_and_sensitive_discussion_redacted(self):
        fixture = GitHubFixture()
        fixture.issue["body"] = "Access token ghp_" + "a" * 36
        fixture.issue["user"] = {"login": "automated[bot]", "type": "Bot"}
        result = PublicGitHub(fixture.read).fetch_issue("https://github.com/sample/project/issues/8")
        self.assertTrue(result["bot"])
        self.assertFalse(result["context_complete"])
        self.assertIn("[REDACTED]", result["body"])
        self.assertNotIn("ghp_", result["body"])

    def test_pull_request_not_treated_as_demand(self):
        fixture = GitHubFixture()
        fixture.issue["pull_request"] = {"url": "ignored"}
        with self.assertRaisesRegex(ValueError, "pull request"):
            PublicGitHub(fixture.read).fetch_issue("https://github.com/sample/project/issues/8")
        self.assertEqual(len(fixture.calls), 2)

    def test_total_discussion_text_budget_is_explicitly_incomplete(self):
        fixture = GitHubFixture()
        fixture.issue["comments"] = 10
        fixture.comment_pages[1] = [{"id": index, "body": "x" * 65536, "user": None}
                                     for index in range(10)]
        result = PublicGitHub(fixture.read).fetch_issue("https://github.com/sample/project/issues/8")
        total = len(result["title"]) + len(result["body"]) + sum(len(item["body"]) for item in result["comments"])
        self.assertLessEqual(total, MAX_DISCUSSION_CHARS)
        self.assertFalse(result["context_complete"])
        self.assertTrue(result["comments"][-1]["truncated"])

    def test_cross_referenced_discussion_is_not_followed_or_claimed_complete(self):
        fixture = GitHubFixture()
        fixture.timeline_pages[1] = [{"id": 5, "event": "cross-referenced", "source": {
            "issue": {"number": 99, "html_url": "https://github.com/private/other/issues/99",
                      "repository": {"private": True}}}}]
        result = PublicGitHub(fixture.read).fetch_issue("https://github.com/sample/project/issues/8")
        self.assertFalse(result["context_complete"])
        self.assertIn("Cross-referenced discussions not fetched; resolution may need review.", result["limitations"])
        self.assertEqual(result["timeline"][0]["source_issue_number"], 99)
        self.assertNotIn("url", result["timeline"][0])
        self.assertFalse(any("private/other" in endpoint for endpoint, _ in fixture.calls))


class SearchTests(unittest.TestCase):
    @staticmethod
    def item(number, bot=False):
        return {"id": number, "html_url": f"https://github.com/sample/project/issues/{number}",
                "title": f"Request {number}", "body": "This full body must not be retained in broad retrieval.",
                "user": {"login": "tool[bot]" if bot else "human", "type": "Bot" if bot else "User"}}

    def test_public_search_deduplicates_and_excludes_prs_and_bots(self):
        fixture = GitHubFixture()
        pr = self.item(3)
        pr["pull_request"] = {}
        fixture.search_pages[1] = {"total_count": 6, "incomplete_results": True,
                                   "items": [self.item(1), self.item(2, bot=True), pr]}
        fixture.search_pages[2] = {"total_count": 6, "incomplete_results": False,
                                   "items": [self.item(1), self.item(4), self.item(5)]}
        result = PublicGitHub(fixture.read).search_issues("CSV JSON", page_size=3)
        self.assertEqual([item["number"] for item in result["items"]], [1, 4, 5])
        self.assertTrue(result["incomplete_results"])
        self.assertTrue(result["incomplete"])
        self.assertEqual(result["excluded_bots"], 1)
        self.assertIn("is:public", fixture.calls[0][1]["q"])
        self.assertTrue(all("body" not in item for item in result["items"]))

    def test_local_pagination_limit_remains_incomplete(self):
        fixture = GitHubFixture()
        fixture.search_pages[1] = {"total_count": 3000, "incomplete_results": False, "items": [self.item(1)]}
        result = PublicGitHub(fixture.read).search_issues("CSV", max_pages=1, page_size=1)
        self.assertFalse(result["incomplete_results"])
        self.assertTrue(result["incomplete"])

    def test_empty_result_is_not_no_demand_claim(self):
        fixture = GitHubFixture()
        fixture.search_pages[1] = {"total_count": 0, "items": [], "incomplete_results": False}
        result = PublicGitHub(fixture.read).search_issues("rare mechanism")
        self.assertTrue(any("do not establish" in text for text in result["limitations"]))

    def test_contradictory_private_queries_rejected_before_network(self):
        fixture = GitHubFixture()
        for query in ("is:private", "type:pr", "foo -is:public", "visibility:private", "", "x" * 257):
            with self.subTest(query=query), self.assertRaises(ValueError):
                PublicGitHub(fixture.read).search_issues(query)
        self.assertEqual(fixture.calls, [])


class StructuralAnalysisTests(unittest.TestCase):
    def test_public_class_is_not_displaced_by_100_later_public_functions(self):
        fixture = GitHubFixture()
        fixture.add("engine.py", "class Engine:\n    def run(self): pass\n\n" +
                    "\n".join(f"def helper_{i}(): pass" for i in range(100)))
        snapshot = PublicGitHub(fixture.read).fetch_repository("sample/project")
        capabilities = extract_structure(snapshot)
        self.assertEqual(len(capabilities), 100)
        self.assertEqual(capabilities[0]["entrypoint"], "engine.py:Engine")
        self.assertEqual(capabilities[0]["level"], "subsystem")
        self.assertEqual(capabilities[0]["verification"], "not_executed")

    def test_public_top_level_declarations_precede_large_class_method_bodies(self):
        fixture = GitHubFixture()
        fixture.add("engine.py", "class Engine:\n" +
                    "\n".join(f"    def method_{i}(self): pass" for i in range(120)) +
                    "\n\ndef validate(value): return value\n\nclass OtherEngine: pass\n")
        snapshot = PublicGitHub(fixture.read).fetch_repository("sample/project")
        capabilities = extract_structure(snapshot)
        self.assertEqual(len(capabilities), 100)
        self.assertEqual([c["entrypoint"] for c in capabilities[:3]],
                         ["engine.py:Engine", "engine.py:validate", "engine.py:OtherEngine"])
        self.assertIn("engine.py:Engine.method_0", [c["entrypoint"] for c in capabilities])
        self.assertTrue(snapshot["coverage"]["analysis"]["capability_limit_reached"])

    def snapshot(self):
        fixture = GitHubFixture()
        fixture.add("README.md", "# Convert\n\nA converter for records.\n")
        fixture.add("src/internal.py", 'import csv\n\ndef _normalize(rows: list[str]) -> list[str]:\n    """Normalize rows before output."""\n    return rows\n\nclass Converter:\n    def run(self, rows):\n        return _normalize(rows)\n')
        fixture.add("tests/test_internal.py", "def test_internal():\n    assert _normalize([]) == []\n")
        fixture.add("src/widget.ts", "export function renderLabel(text: string) { return text; }\n")
        fixture.add("src/broken.py", "def malformed(")
        return PublicGitHub(fixture.read).fetch_repository("sample/project")

    def test_hidden_python_capability_evidence_and_test_reference_not_execution(self):
        snapshot = self.snapshot()
        capabilities = extract_structure(snapshot)
        hidden = next(item for item in capabilities if item["name"] == "_normalize")
        self.assertEqual(hidden["level"], "mechanism")
        self.assertEqual(hidden["inputs"], ["rows: list[str]"])
        self.assertEqual(hidden["outputs"], ["list[str]"])
        self.assertIn("csv", hidden["dependencies"])
        self.assertEqual(hidden["test_coverage"], "referenced")
        self.assertEqual(hidden["standalone"], "unknown")
        self.assertEqual(hidden["verification"], "not_executed")
        self.assertEqual(hidden["requirements_supported"], [])
        self.assertEqual(hidden["evidence"][0]["line"], 3)
        self.assertIn(REVISION, hidden["evidence"][0]["url"])
        self.assertTrue(any(evidence["kind"] == "test_reference" for evidence in hidden["evidence"]))
        method = next(item for item in capabilities if item["name"] == "Converter.run")
        self.assertEqual(method["standalone"], "no")
        self.assertIn("_normalize", method["calls"])

    def test_unsupported_syntax_and_js_partial_scan_are_explicit(self):
        snapshot = self.snapshot()
        capabilities = extract_structure(snapshot)
        states = {item["path"]: item["status"] for item in snapshot["coverage"]["analysis"]["files"]}
        self.assertEqual(states["src/broken.py"], "parse_failed")
        self.assertEqual(states["src/widget.ts"], "partial_declaration_scan")
        candidate = next(item for item in capabilities if item["name"] == "renderLabel")
        self.assertIn("not a JS/TS parser", candidate["limitations"][0])
        product = next(item for item in capabilities if item["level"] == "product")
        self.assertIn("Documentation claim only", product["limitations"][0])

    def test_analysis_never_imports_or_executes_acquired_source(self):
        fixture = GitHubFixture()
        fixture.add("danger.py", "raise RuntimeError('would execute on import')\n\ndef hidden():\n    return 1\n")
        snapshot = PublicGitHub(fixture.read).fetch_repository("sample/project")
        capabilities = extract_structure(snapshot)
        self.assertEqual(capabilities[0]["name"], "hidden")
        self.assertEqual(snapshot["coverage"]["analysis"]["execution"], "none")

    def test_capability_identity_stable_at_same_revision(self):
        snapshot = self.snapshot()
        first = extract_structure(snapshot)
        second = extract_structure(copy.deepcopy(snapshot))
        self.assertEqual([item["id"] for item in first], [item["id"] for item in second])

    def test_capability_identity_survives_new_revision_and_line_movements(self):
        snapshot = self.snapshot()
        first = next(item for item in extract_structure(snapshot) if item["name"] == "_normalize")
        snapshot["revision"] = "c" * 40
        for file in snapshot["files"]:
            if file["path"] == "src/internal.py":
                file["text"] = "# moved in next commit\n" + file["text"]
                file["url"] = file["url"].replace(REVISION, snapshot["revision"])
        changed = next(item for item in extract_structure(snapshot) if item["name"] == "_normalize")
        self.assertEqual(first["id"], changed["id"])
        self.assertNotEqual(first["evidence"][0]["url"], changed["evidence"][0]["url"])

    def test_structural_analysis_also_excludes_credentials_in_manually_supplied_snapshot(self):
        snapshot = self.snapshot()
        snapshot["files"].append({"path": "bad.py", "text": "token='ghp_" + "a" * 36 + "'\ndef secret(): return token\n",
                                   "url": f"https://github.com/sample/project/blob/{REVISION}/bad.py"})
        capabilities = extract_structure(snapshot)
        self.assertFalse(any(item["name"] == "secret" for item in capabilities))
        status = next(item["status"] for item in snapshot["coverage"]["analysis"]["files"] if item["path"] == "bad.py")
        self.assertEqual(status, "safety_excluded")


if __name__ == "__main__":
    unittest.main()
