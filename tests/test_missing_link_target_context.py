"""Offline public-target/reference regressions; no paid calls or acquired execution."""
import unittest
from unittest import mock

from missing_link.analysis import validate_request, validate_matches
from missing_link.context import build_context
from missing_link.sources import PublicGitHub
from missing_link.qualification import tomllib
from test_missing_link import repository, issue, request_raw, raw_match
import test_missing_link as fixtures
from test_missing_link_sources import GitHubFixture, REVISION


def target_file(path, value):
    return {"path": path, "text": value,
        "url": "https://github.com/example/site/blob/" + "b" * 40 + "/" + path}


class ReferenceContextTests(unittest.TestCase):
    def test_unsafe_paths_cannot_consume_reference_cap(self):
        fixture = GitHubFixture()
        fixture.add("client.py", "import tenacity\n")
        fixture.add("helper.py", "import tenacity\n")
        source = PublicGitHub(fixture.read)
        unsafe = " ".join(f"https://github.com/other/project/blob/main/file{i}.py ../../bad{i}.py .env/private{i}.py"
                          for i in range(25))
        with mock.patch.object(source, "fetch_repository", wraps=source.fetch_repository) as fetch:
            context = source.fetch_reference_context({"url": "https://github.com/sample/project/issues/8",
                "body": unsafe, "comments": [{"body": "client.py client.py "
                    "https://github.com/sample/project/blob/main/helper.py"}]})
        self.assertEqual(fetch.call_args.kwargs["reference_paths"], ["client.py", "helper.py"])
        self.assertEqual({f["path"] for f in context["files"]}, {"client.py", "helper.py"})

    def test_safe_reference_paths_remain_deduplicated_and_capped(self):
        source = PublicGitHub(lambda *args: None)
        body = " ".join(f"file{i}.py file{i}.py" for i in range(25))
        with mock.patch.object(source, "fetch_repository", return_value={"id": 1, "revision": REVISION, "files": []}) as fetch:
            source.fetch_reference_context({"url": "https://github.com/sample/project/issues/8", "body": body})
        self.assertEqual(fetch.call_args.kwargs["reference_paths"], [f"file{i}.py" for i in range(20)])

    def evaluate(self, repo=None, demand=None):
        repo, demand = repo or repository(), demand or issue()
        return validate_matches([raw_match()], repo, demand, validate_request(request_raw(), demand), "model")[0]

    def test_pyyaml_plain_possessive_and_static_yaml_import_are_reference_hints(self):
        repo = repository()
        repo["full_name"] = "yaml/pyyaml"
        repo["files"] += [target_file("lib/yaml/__init__.py", "from .loader import SafeLoader\n")]
        for mention in ("PyYAML's Loader is unsafe; use SafeLoader.", "import yaml as y", "from yaml import safe_load"):
            demand = issue()
            demand["body"] += " " + mention
            assessment = self.evaluate(repo, demand)["discovery_assessment"]
            self.assertEqual(assessment["status"], "reference_review")
            self.assertFalse(assessment["eligible_for_followup"])

    @unittest.skipIf(tomllib is None, "Optional TOML backport not installed on Python 3.10")
    def test_target_dependency_field_catches_genai_prior_use_not_manifest_prose(self):
        repo = repository()
        repo["full_name"] = "jd/tenacity"
        demand = issue()
        demand["target_context"] = {"public": True, "revision": "b" * 40,
            "files": [target_file("pyproject.toml", '[project]\nname="consumer"\ndependencies=["tenacity>=8.2.3, <9.2.0"]\n')]}
        match = self.evaluate(repo, demand)
        ref = match["discovery_assessment"]["references"][0]
        self.assertEqual(ref["kind"], "dependency_declaration_hint")
        self.assertEqual(ref["source_id"], "target:pyproject.toml")
        self.assertIn(ref["quote"], demand["target_context"]["files"][0]["text"])
        self.assertFalse(match["discovery_assessment"]["eligible_for_followup"])
        demand["target_context"]["files"][0]["text"] = '[project]\nname="consumer"\ndescription="tenacity library"\n'
        self.assertEqual(self.evaluate(repo, demand)["discovery_assessment"]["references"], [])

    def test_scoped_npm_identity_and_exact_dependency_names(self):
        repo = repository()
        repo["files"].append(target_file("package.json", '{"name":"@scope/actual-name"}'))
        for deps, count in (({"@scope/actual-name": "^1"}, 1), ({"@scope/actual-name-extra": "^1"}, 0)):
            import json
            demand = issue()
            demand["target_context"] = {"public": True, "files": [target_file("package.json", json.dumps({"dependencies": deps}))]}
            self.assertEqual(self.evaluate(repo, demand)["discovery_assessment"]["reference_count"], count)

    def test_real_target_import_but_not_a_docstring_is_a_hint(self):
        repo = repository()
        repo["full_name"] = "jd/tenacity"
        for value, count in (("import tenacity as retries\n", 1), ('"""import tenacity"""\n', 0), ('x="import tenacity"\n', 0)):
            demand = issue()
            demand["target_context"] = {"public": True, "files": [target_file("client.py", value)]}
            self.assertEqual(self.evaluate(repo, demand)["discovery_assessment"]["reference_count"], count)

    def test_target_context_never_enters_independent_requirement_extraction(self):
        demand = issue()
        demand["target_context"] = {"public": True, "files": [target_file("client.py", "import tenacity\n")]}
        data, _ = build_context(None, demand, "request", 180000)
        self.assertFalse(any(ref.startswith("target:") for ref in data["sources"]))
        data, report = build_context(repository(), demand, "matches", 180000)
        self.assertIn("target:client.py", data["sources"])
        self.assertNotIn("path", data["sources"]["target:client.py"])
        self.assertFalse(report["target_reference_context"]["absence_proves_novelty"])

    def test_target_code_cannot_substitute_for_source_implementation_evidence(self):
        demand = issue()
        demand["target_context"] = {"public": True, "files": [target_file("client.py", "def trim(): pass\n")]}
        raw = raw_match()
        raw["checks"][0]["source_ids"] = ["target:client.py"]
        match = validate_matches([raw], repository(), demand, validate_request(request_raw(), demand), "model")[0]
        self.assertEqual(match["checks"][0]["status"], "undetermined")

    def test_missing_target_sample_cannot_be_followup_ready(self):
        demand = issue()
        demand["body"] = "without splitting words"
        raw_request, raw = request_raw(), raw_match()
        raw_request["requirements"] = raw_request["requirements"][:1]
        raw["checks"] = raw["checks"][:1]
        match = validate_matches([raw], repository(), demand, validate_request(raw_request, demand), "model")[0]
        self.assertEqual(match["discovery_assessment"]["status"], "needs_review")

    def test_target_acquisition_is_pinned_bounded_and_safety_filtered(self):
        fixture = GitHubFixture()
        fixture.add("pyproject.toml", '[project]\nname="target"\n')
        fixture.add("client.py", "import tenacity\n")
        fixture.add("unmentioned.py", "raise RuntimeError('never execute')\n")
        fixture.add("secret.py", "sk-" + "A" * 30)
        fixture.add("linked.py", "import tenacity\n", mode="120000")
        context = PublicGitHub(fixture.read).fetch_reference_context({"url": "https://github.com/sample/project/issues/8",
            "body": "See client.py, secret.py and linked.py; ignore ../../outside.py"})
        self.assertEqual(context["revision"], REVISION)
        self.assertEqual([f["path"] for f in context["files"]], ["pyproject.toml", "client.py"])
        self.assertTrue(context["reference_only"])
        self.assertLessEqual(len([call for call in fixture.calls if "/git/blobs/" in call[0]]), 4)
        fixture.repo["private"] = True
        with self.assertRaisesRegex(ValueError, "public"):
            PublicGitHub(fixture.read).fetch_reference_context({"url": "https://github.com/sample/project/issues/8"})

    def test_target_blob_links_in_later_comments_are_tree_constrained(self):
        fixture = GitHubFixture()
        fixture.add("client.py", "import tenacity\n")
        fixture.add("foreign.py", "raise RuntimeError('never execute')\n")
        context = PublicGitHub(fixture.read).fetch_reference_context({"url": "https://github.com/sample/project/issues/8",
            "body": "See https://github.com/other/project/blob/main/foreign.py", "comments": [{
                "body": "Source: https://github.com/Sample/Project/blob/" + "b" * 40 + "/client.py#L1"}]})
        self.assertEqual([file["path"] for file in context["files"]], ["client.py"])
        self.assertEqual(context["revision"], REVISION)  # Current target revision, not the issue link's revision.


class TargetPersistenceTests(unittest.TestCase):
    setUp = fixtures.ServiceTests.setUp
    fake_sources = fixtures.ServiceTests.fake_sources

    def test_different_issues_in_same_target_do_not_reuse_the_wrong_cited_file_sample(self):
        source = self.fake_sources()
        first = dict(issue(), body=issue()["body"] + " See first.py")
        second = dict(issue(), id=9, url=issue()["url"] + "9", fingerprint="different-discussion",
            body=issue()["body"] + " See second.py")
        source.search_issues.return_value = {"items": [{"url": first["url"]}, {"url": second["url"]}]}
        source.fetch_issue.side_effect = [first, second]
        with mock.patch("missing_link.service.PublicGitHub", return_value=source), \
             mock.patch("missing_link.service.extract_structure", return_value=repository()["capabilities"]):
            started = self.service.start({"repo": "example/words", "query": "custom request"}, background=False)
        job = self.service.store.get("jobs", started["job_id"])
        self.assertEqual(job["status"], "completed", job.get("error"))
        self.assertEqual(source.fetch_reference_context.call_count, 2)
        self.assertEqual(len(job["checkpoint"]["target_contexts"]), 2)

    def test_target_snapshot_survives_job_and_match_export_without_reacquisition(self):
        source = self.fake_sources()
        with mock.patch("missing_link.service.PublicGitHub", return_value=source), \
             mock.patch("missing_link.service.extract_structure", return_value=repository()["capabilities"]):
            started = self.service.start({"repo": "example/words", "issue_url": issue()["url"]}, background=False)
        job = self.service.store.get("jobs", started["job_id"])
        self.assertEqual(job["status"], "completed", job.get("error"))
        source.fetch_reference_context.assert_called_once()
        mid = job["result"]["match_ids"][0]
        snapshot = self.service.store.match_snapshot(mid)
        self.assertEqual(snapshot["issue"]["target_context"]["revision"], "b" * 40)
        self.assertEqual(self.service.export(mid)["request"]["source_issue"]["target_context"]["revision"], "b" * 40)


if __name__ == "__main__":
    unittest.main()
