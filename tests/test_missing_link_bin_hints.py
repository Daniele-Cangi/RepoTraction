"""Bounded executable-package sampling; neither npm nor acquired code is run."""
import json
import unittest

from missing_link.source_hints import export_hints, MAX_EXPORT_HINTS
from missing_link.sources import PublicGitHub
from test_missing_link_sources import GitHubFixture


class BinHintTests(unittest.TestCase):
    def test_bin_strings_and_command_maps_follow_only_eligible_entrypoints(self):
        for value in ("cli.js", "./cli.js", {"tool": "cli.js"}, {"tool": "./cli.js"}):
            with self.subTest(value=value):
                self.assertEqual(export_hints("package.json", json.dumps({"bin": value}), {"cli.ts": {}}), (["cli.ts"], True))
        self.assertEqual(export_hints("packages/app/package.json", '{"bin":"../shared/cli.js"}',
                                     {"packages/shared/cli.ts": {}}), (["packages/shared/cli.ts"], True))

    def test_bin_paths_keep_exact_preference_deduplication_and_extensionless_resolution(self):
        eligible = {"cli.js": {}, "cli.ts": {}, "other.cjs": {}}
        metadata = {"source": "./cli.js", "bin": {"tool": "./cli.js", "alias": "cli.js", "other": "other.cjs"}}
        self.assertEqual(export_hints("package.json", json.dumps(metadata), eligible), (["cli.js", "other.cjs"], True))
        self.assertEqual(export_hints("package.json", '{"bin":"src/cli"}', {"src/cli.ts": {}}), (["src/cli.ts"], True))

    def test_bin_hints_do_not_bypass_relative_path_or_eligible_tree_guards(self):
        eligible = {"src/cli.ts": {}, "src/types.d.ts": {}}
        for path in ("../../src/cli.js", "/src/cli.js", "https://host/cli.js", "src/cli.js?secret",
                     "src/cli.js#fragment", "src/*.js", "src\\cli.js", "src/types.d.ts", "missing.js"):
            with self.subTest(path=path):
                self.assertEqual(export_hints("package.json", json.dumps({"bin": path}), eligible), ([], True))

    def test_bin_hints_share_the_manifest_cap_and_report_overflow(self):
        eligible = {f"cli{index}.ts": {} for index in range(MAX_EXPORT_HINTS + 1)}
        bins = {f"tool{index}": f"./cli{index}.js" for index in range(MAX_EXPORT_HINTS + 1)}
        self.assertEqual(export_hints("package.json", json.dumps({"bin": bins}), eligible),
                         (list(eligible)[:MAX_EXPORT_HINTS], False))
        metadata = {"source": "./cli0.js", "exports": {key: path for key, path in list(bins.items())[1:MAX_EXPORT_HINTS]},
                    "bin": f"./cli{MAX_EXPORT_HINTS}.js"}
        self.assertEqual(export_hints("package.json", json.dumps(metadata), eligible),
                         (list(eligible)[:MAX_EXPORT_HINTS], False))

    def test_bin_only_cli_is_acquired_with_the_existing_two_read_budget(self):
        for value in ("bin/run.js", {"tool": "bin/run.js"}):
            with self.subTest(value=value):
                fixture = GitHubFixture()
                fixture.add("package.json", json.dumps({"bin": value}))
                fixture.add("bin/run.ts", "export function run(value) { return value; }")
                for index in range(40):
                    fixture.add(f"aaa_unrelated{index:02d}.ts", "export function helper() {}")
                snapshot = PublicGitHub(fixture.read).fetch_repository("sample/project", 2)
                self.assertEqual([file["path"] for file in snapshot["files"]], ["package.json", "bin/run.ts"])
                self.assertEqual(sum("/git/blobs/" in call[0] for call in fixture.calls), 2)
                self.assertEqual(snapshot["coverage"]["static_export_hints"], [{"from": "package.json", "path": "bin/run.ts"}])
                self.assertTrue(snapshot["coverage"]["export_hints_complete"])
                self.assertFalse(snapshot["coverage"]["eligible_sample_complete"])

    def test_rejected_cli_blob_does_not_expand_the_read_budget(self):
        fixture = GitHubFixture()
        fixture.add("package.json", '{"bin":"bin/run.js"}')
        fixture.add("bin/run.ts", b"binary\x00data")
        fixture.add("aaa_unrelated.ts", "export function helper() {}")
        snapshot = PublicGitHub(fixture.read).fetch_repository("sample/project", 2)
        self.assertEqual([file["path"] for file in snapshot["files"]], ["package.json"])
        self.assertEqual(sum("/git/blobs/" in call[0] for call in fixture.calls), 2)


if __name__ == "__main__":
    unittest.main()
