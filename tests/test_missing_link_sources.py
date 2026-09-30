import base64
import copy
import sys
import unittest
from pathlib import Path

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
