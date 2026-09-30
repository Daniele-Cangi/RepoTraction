"""Transactional bootstrap fixtures; no downloads, installs or code execution."""
import hashlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import zipfile

from scripts import bootstrap_missing_link_wasi as bootstrap


def archive_bytes(files):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for path, content in files.items():
            archive.writestr(path, content)
    return buffer.getvalue()


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "runtime"
        self.data = {"fixture:first": archive_bytes({"engine.exe": "fictional fixture, never executed"}),
            "fixture:second": archive_bytes({"python.wasm": "fictional WASM", "lib/module.py": "# fixture only"})}
        self.assets = [(name, url, hashlib.sha256(self.data[url]).hexdigest())
            for name, url in (("wasmtime", "fixture:first"), ("cpython", "fixture:second"))]
        self.quiet = mock.patch("builtins.print")
        self.quiet.start()
        self.addCleanup(self.quiet.stop)

    def install(self, fetch=None, assets=None):
        bootstrap.install_assets(self.root, assets if assets is not None else self.assets, fetch or self.data.__getitem__)

    def test_completed_install_is_verified_and_reused_offline_without_rewriting_files(self):
        self.install()
        engine = self.root / "wasmtime/engine.exe"
        original_time = engine.stat().st_mtime_ns
        offline = mock.Mock(side_effect=AssertionError("Must reuse verified cached archive"))
        self.install(offline)
        offline.assert_not_called()
        self.assertEqual(engine.stat().st_mtime_ns, original_time)
        self.assertFalse(list(self.root.glob("*.previous-*")))

    def test_second_asset_download_failure_can_resume_without_downloading_first_again(self):
        def fail_second(url):
            if url == "fixture:second":
                raise OSError("Simulated network outage")
            return self.data[url]
        with self.assertRaises(OSError):
            self.install(fail_second)
        self.assertTrue((self.root / "wasmtime/engine.exe").is_file())
        self.assertFalse((self.root / "cpython").exists())
        resumed = mock.Mock(side_effect=self.data.__getitem__)
        self.install(resumed)
        resumed.assert_called_once_with("fixture:second")
        self.assertTrue((self.root / "cpython/lib/module.py").is_file())

    def test_extraction_failure_leaves_legacy_partial_install_untouched_and_retry_repairs(self):
        old = self.root / "cpython"
        old.mkdir(parents=True)
        (old / "keep.txt").write_text("pre-existing content", encoding="utf-8")
        def fail_extract(staged, archive, entries):
            (staged / "partial.txt").write_text("incomplete stage", encoding="utf-8")
            raise OSError("Simulated extraction interruption")
        with mock.patch.object(bootstrap, "extract_asset", side_effect=fail_extract), self.assertRaises(OSError):
            self.install(assets=self.assets[1:])
        self.assertEqual((old / "keep.txt").read_text(), "pre-existing content")
        self.assertFalse(list(self.root.glob(".cpython-stage-*")))
        self.install(assets=self.assets[1:])
        self.assertTrue((old / "python.wasm").is_file())
        backups = list(self.root.glob("cpython.previous-*"))
        self.assertEqual(len(backups), 1)
        self.assertEqual((backups[0] / "keep.txt").read_text(), "pre-existing content")

    def test_changed_completed_asset_is_repaired_but_preserved_not_deleted(self):
        self.install()
        engine = self.root / "wasmtime/engine.exe"
        engine.write_text("changed content", encoding="utf-8")
        self.install(mock.Mock(side_effect=AssertionError("Cached pinned bytes are sufficient")))
        self.assertEqual(engine.read_text(), "fictional fixture, never executed")
        backups = list(self.root.glob("wasmtime.previous-*"))
        self.assertEqual(len(backups), 1)
        self.assertEqual((backups[0] / "engine.exe").read_text(), "changed content")

    def test_publication_failure_rolls_back_previous_destination(self):
        old = self.root / "wasmtime"
        old.mkdir(parents=True)
        (old / "keep.txt").write_text("original content", encoding="utf-8")
        rename = Path.rename
        def fail_publication(path, target):
            if ".wasmtime-stage-" in str(path.parent):
                raise OSError("Simulated publication interruption")
            return rename(path, target)
        with mock.patch.object(Path, "rename", fail_publication), self.assertRaises(OSError):
            self.install(assets=self.assets[:1])
        self.assertEqual((old / "keep.txt").read_text(), "original content")
        self.assertFalse(list(self.root.glob("wasmtime.previous-*")))
        self.install(assets=self.assets[:1])
        self.assertTrue((old / "engine.exe").is_file())

    def test_invalid_digest_and_unsafe_archive_never_publish(self):
        with self.assertRaises(ValueError):
            self.install(assets=[("wasmtime", "fixture:first", "0" * 64)])
        self.assertFalse((self.root / "wasmtime").exists())
        for files in ({"../outside.py": "unsafe"}, {"a": "file", "a/child": "collision"},
            {"same.py": "one", "SAME.py": "two"}):
            with self.subTest(files=files):
                payload = archive_bytes(files)
                asset = ("wasmtime", "fixture:unsafe", hashlib.sha256(payload).hexdigest())
                with self.assertRaises(ValueError):
                    self.install(lambda _: payload, assets=[asset])
                self.assertFalse((self.root / "wasmtime").exists())
                self.assertFalse((self.root.parent / "outside.py").exists())


if __name__ == "__main__":
    unittest.main()
