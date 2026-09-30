"""WASI boundary configuration and receipt tests; no runtime downloads in CI."""
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from missing_link.wasi_runner import WasiRunner, MAX_MEMORY
from missing_link.service import Service
from missing_link.store import Store
from missing_link.provider import Provider
from test_missing_link_proofs import fixture


class WasiTests(unittest.TestCase):
    def test_missing_runtime_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            runner = WasiRunner(temp)
            self.assertFalse(runner.describe()["execution_enabled"])
            self.assertEqual(runner.run({"test.py": "raise Exception()"}, "test.py")["status"], "not_executed")

    def test_command_grants_only_ephemeral_directory_not_host_env_network(self):
        runner = WasiRunner()
        command = runner.command(Path("ephemeral"), "bridge/test.py")
        self.assertEqual(command.count("--dir"), 1)
        self.assertEqual(command[command.index("--dir") + 1], "ephemeral::/sandbox")
        for flag in ("inherit-env=n", "inherit-network=n", "tcp=n", "udp=n", "http=n", "threads=n"):
            self.assertIn(flag, command)
        self.assertIn(f"max-memory-size={MAX_MEMORY}", command)
        self.assertNotIn("--allow-precompiled", command)
        self.assertNotIn("-m", command)
        python_args = command[command.index(str(runner.module.resolve())) + 1:]
        self.assertEqual(python_args[:3], ["-S", "-P", "-c"])
        self.assertFalse(any(argument.startswith("PYTHONPATH=") for argument in command))
        self.assertNotIn("runpy", python_args[3])

    @unittest.skipUnless(WasiRunner().describe()["available"], "Optional pinned Windows WASI runtime unavailable")
    def test_real_runtime_does_not_autorun_or_shadow_startup_modules(self):
        files = {"project/sitecustomize.py": "raise RuntimeError('UNREVIEWED SITE STARTUP')\n",
                 "project/usercustomize.py": "raise RuntimeError('UNREVIEWED USER STARTUP')\n",
                 "project/encodings.py": "raise RuntimeError('UNREVIEWED ENCODINGS')\n",
                 "project/types.py": "raise RuntimeError('UNREVIEWED STDLIB SHADOW')\n",
                 "bridge/sitecustomize.py": "raise RuntimeError('UNREVIEWED BRIDGE STARTUP')\n",
                 "project/library.py": "def reviewed_dependency():\n    return 'DEPENDENCY OK'\n",
                 "bridge/example.py": "import sys, types\nfrom library import reviewed_dependency\n"
                    "assert sys.flags.no_site and sys.flags.safe_path\n"
                    "assert types.__file__.startswith('/sandbox/runtime/')\n"
                    "assert sys.argv == [__file__]\nprint('APPROVED ENTRY', reviewed_dependency())\n"}
        result = WasiRunner().run(files, "bridge/example.py")
        self.assertEqual(result["status"], "exited_successfully", result)
        self.assertIn("APPROVED ENTRY DEPENDENCY OK", result["stdout"])
        self.assertNotIn("UNREVIEWED", result["stdout"] + result["stderr"])

    def test_artifacts_are_bounded_portable_and_collisions_rejected_before_launch(self):
        runner = WasiRunner()
        for files in ({"test.py": "", "../bad.py": ""}, {"test.py": "", "TEST.py": ""},
            {"test.py": "", "a": "", "a/b": ""}, {"test.py": "x" * 262145}, {"test.py": None}):
            with self.subTest(files=list(files)), mock.patch.object(runner, "describe", return_value={"available": True}), \
                    mock.patch("subprocess.Popen") as launch, self.assertRaises(ValueError):
                runner.run(files, "test.py")
            launch.assert_not_called()

    def test_approval_is_required_and_receipts_are_separate_from_importable_records(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "account.sqlite3"
            service = Service(path, "alice", lambda _: {}, lambda: "alice", provider=Provider({}))
            with self.assertRaises(ValueError):
                service.execute_example({"approved": False})
            service.store.save_proof({"id": "proof", "match_id": "m", "status": "failed"})
            restarted = Store(path, "alice")
            self.assertEqual(restarted.proofs("m")[0]["status"], "failed")
            with self.assertRaises(ValueError):
                restarted.put("proofs", "proof", {"status": "success"})

    def test_runner_receipt_survives_match_refresh_and_export_without_promoting_analysis(self):
        with tempfile.TemporaryDirectory() as temp:
            service = Service(Path(temp) / "alice.sqlite3", "alice", lambda _: {}, lambda: "alice", provider=Provider({}))
            match, repo = fixture()
            repo.update(id=7, public=True)
            match.update(repo_id=7, analysis_source="model", source_fingerprint="fixture-fingerprint")
            service.store.put("repositories", 7, repo)
            service.store.save_matches([match], repo)
            with mock.patch("missing_link.wasi_runner.WasiRunner.describe", return_value={"available": True}), \
                    mock.patch("missing_link.wasi_runner.WasiRunner.run", return_value={"status": "failed", "request_criteria_verified": False}) as run:
                receipt = service.execute_example({"approved": True, "match_id": match["id"], "entrypoint": "bridge/example.py"})["isolated_example"]
            self.assertEqual(receipt["status"], "failed")
            self.assertEqual(run.call_args.args[0]["project/library.py"], repo["files"]["library.py"])
            service.store.save_matches([match], repo)
            exported = service.export(match["id"])
            self.assertEqual(exported["isolated_examples"][0]["id"], receipt["id"])
            self.assertEqual(exported["verification"]["status"], "not_executed")
            self.assertEqual(exported["match"]["classification"], "adapter")
            self.assertTrue(exported["isolated_examples"][0]["applies_to_current_bridge"])
            match["bridge"]["files"][0]["content"] += "# changed proposal\n"
            service.store.save_matches([match], repo)
            self.assertFalse(service.export(match["id"])["isolated_examples"][0]["applies_to_current_bridge"])
            with self.assertRaises(ValueError):
                service.execute_example({"approved": True, "match_id": match["id"], "entrypoint": "project/library.py"})

    def test_renamed_changed_issue_blocks_example_before_runner(self):
        for legacy in (False, True):
            with self.subTest(legacy=legacy), tempfile.TemporaryDirectory() as temp:
                service = Service(Path(temp) / "alice.sqlite3", "alice", lambda _: {}, lambda: "alice", provider=Provider({}))
                match, repo = fixture()
                repo.update(id=7, public=True)
                match.update(repo_id=7, analysis_source="model", source_fingerprint="fixture-fingerprint")
                service.store.put("repositories", 7, repo)
                service.store.save_matches([match], repo)
                changed = dict(match["request"], url="https://github.com/fixture/renamed-app/issues/1",
                               fingerprint="changed-after-rename")
                service.store.put("discussions", changed["url"] if legacy else changed["id"], changed)
                restarted = Service(service.store.path, "alice", lambda _: {}, lambda: "alice", provider=Provider({}))
                with mock.patch("missing_link.wasi_runner.WasiRunner.run") as run:
                    with self.assertRaisesRegex(ValueError, "discussion changed"):
                        restarted.execute_example({"approved": True, "match_id": match["id"], "entrypoint": "bridge/example.py"})
                    run.assert_not_called()
                self.assertEqual(restarted.store.proofs(match["id"]), [])


if __name__ == "__main__":
    unittest.main()
