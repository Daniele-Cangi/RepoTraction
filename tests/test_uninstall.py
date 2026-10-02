"""Windows uninstall regression in owned fixtures, never the real installation."""
import base64
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


@unittest.skipUnless(sys.platform == "win32", "Windows PowerShell uninstaller")
class UninstallTests(unittest.TestCase):
    def run_uninstall(self, remove_data, analytics_junction=False, storage_junction=False):
        junction_name = "analytics" if analytics_junction else "storage" if storage_junction else None
        shells = [path for name in ("powershell.exe", "pwsh.exe") if (path := shutil.which(name))]
        self.assertTrue(shells, "PowerShell required for Windows uninstall tests")
        for shell in shells:
            with self.subTest(shell=shell, remove_data=remove_data), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary).resolve()
                installed = root / "RepoTraction"
                programs = root / "Programs"
                installed.mkdir()
                programs.mkdir()
                history = installed / "data" / "fixture.sqlite3"
                history.parent.mkdir()
                history.write_bytes(b"fixture history, not a user database")
                config = installed / ".env"
                config.write_bytes(b"# fixture configuration")
                unrelated = installed / "keep.txt"
                unrelated.write_bytes(b"not installer owned")
                sibling = root / "unrelated-sibling.txt"
                sibling.write_bytes(b"outside installation")
                shortcut = programs / "RepoTraction.lnk"
                shortcut.write_bytes(b"fixture shortcut")
                for name in ("app.py", "github_cli.py", "start.ps1", "start.cmd", "README.md", "LICENSE", "uninstall.ps1"):
                    (installed / name).write_bytes(b"installer owned fixture")
                for name in ("static", "analytics", "analytics/__pycache__", "storage", "storage/__pycache__"):
                    if junction_name and name.split("/", 1)[0] == junction_name:
                        continue
                    directory = installed / name
                    directory.mkdir(parents=True, exist_ok=True)
                    (directory / "fixture.txt").write_bytes(b"installer owned fixture")
                linked = root / "linked-fixture"
                linked.mkdir()
                (linked / "keep.txt").write_bytes(b"linked fixture must survive")

                def quoted(value):
                    return "'" + str(value).replace("'", "''") + "'"

                script = Path(__file__).resolve().parents[1] / "uninstall.ps1"
                # Replace only the two environment-derived paths in an in-memory
                # copy. Fail if the anchors drift; never call the real default
                # uninstaller, alter environment variables or patch its file.
                code = f"""
$ErrorActionPreference = 'Stop'
$taskRoot = [IO.Path]::GetFullPath({quoted(root)})
$taskInstalled = [IO.Path]::GetFullPath({quoted(installed)})
$taskPrograms = [IO.Path]::GetFullPath({quoted(programs)})
if ([IO.Path]::GetDirectoryName($taskInstalled) -ne $taskRoot -or
    [IO.Path]::GetDirectoryName($taskPrograms) -ne $taskRoot) {{ throw 'Fixture path escaped root' }}
{("New-Item -ItemType Junction -Path (Join-Path $taskInstalled " + quoted(junction_name) + ") -Target " + quoted(linked) + " -ErrorAction Stop | Out-Null") if junction_name else ''}
$taskSource = Get-Content -LiteralPath {quoted(script)} -Raw
$taskInstallAnchor = '$InstallDirectory = Join-Path ([Environment]::GetFolderPath("LocalApplicationData")) "RepoTraction"'
$taskProgramsAnchor = '$ProgramsDirectory = [Environment]::GetFolderPath("Programs")'
foreach ($taskAnchor in @($taskInstallAnchor, $taskProgramsAnchor)) {{
    if ([regex]::Matches($taskSource, [regex]::Escape($taskAnchor)).Count -ne 1) {{ throw 'Uninstall fixture anchor changed' }}
}}
$taskSource = $taskSource.Replace($taskInstallAnchor, '$InstallDirectory = $taskInstalled')
$taskSource = $taskSource.Replace($taskProgramsAnchor, '$ProgramsDirectory = $taskPrograms')
& ([scriptblock]::Create($taskSource)) {'-RemoveData' if remove_data else ''}
"""
                encoded = base64.b64encode(code.encode("utf-16-le")).decode("ascii")
                result = subprocess.run([shell, "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
                                        capture_output=True, text=True, timeout=30)
                if junction_name:
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(f"{junction_name} link or junction", result.stderr)
                    self.assertEqual((linked / "keep.txt").read_bytes(), b"linked fixture must survive")
                    self.assertEqual(history.read_bytes(), b"fixture history, not a user database")
                    continue
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertFalse((installed / "analytics").exists())
                self.assertFalse((installed / "storage").exists())
                self.assertFalse((installed / "static").exists())
                self.assertFalse((installed / "app.py").exists())
                self.assertFalse((installed / "github_cli.py").exists())
                self.assertFalse(shortcut.exists())
                self.assertEqual(config.read_bytes(), b"# fixture configuration")
                self.assertEqual(unrelated.read_bytes(), b"not installer owned")
                self.assertEqual(sibling.read_bytes(), b"outside installation")
                if remove_data:
                    self.assertFalse(history.parent.exists())
                else:
                    self.assertEqual(history.read_bytes(), b"fixture history, not a user database")

    def test_uninstall_removes_analytics_and_preserves_history(self):
        self.run_uninstall(False)

    def test_explicit_remove_data_also_removes_analytics(self):
        self.run_uninstall(True)

    def test_analytics_junction_is_not_followed_or_recursively_removed(self):
        self.run_uninstall(True, analytics_junction=True)

    def test_storage_junction_is_not_followed_or_recursively_removed(self):
        self.run_uninstall(True, storage_junction=True)
