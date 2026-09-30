"""Opt-in Python example runner inside Wasmtime/WASI, never host Python.

No network, inherited guest environment, shell, native project extensions or host
directory grants. Only an ephemeral copy of stdlib and approved public artifacts
is preopened. This is a capability sandbox, not a VM or a target integration.
"""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import time

from .proofs import safe_relative_path

ENGINE_HASH = "ea76fcf3f3015b46020755fe76779f483240f8377a80bda767ee6e295c782aa8"
PYTHON_HASH = "d24bd98d3071af6b17d51d53a08700b9acef59172a0afcb6adb733645c2a1715"
MAX_MEMORY = 268435456
MAX_OUTPUT = 32768
FUEL = 5000000000


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class WasiRunner:
    def __init__(self, root=None):
        self.root = Path(root) if root else Path(__file__).resolve().parents[1] / "data" / "wasi-runtime"
        self.engine = self.root / "wasmtime" / "wasmtime-v49.0.1-x86_64-windows" / "wasmtime.exe"
        self.module = self.root / "cpython" / "python.wasm"
        self.library = self.root / "cpython" / "lib"

    def describe(self):
        try:
            if os.name != "nt" or not self.library.is_dir() or sha(self.engine) != ENGINE_HASH or sha(self.module) != PYTHON_HASH:
                raise ValueError("Pinned WASI runtime is missing or has changed.")
            if any(path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())
                    for path in [self.root, self.engine, self.module, self.library, *self.library.rglob("*")]):
                raise ValueError("WASI runtime links/junctions are not permitted.")
        except (OSError, ValueError) as exc:
            return {"available": False, "execution_enabled": False, "backend": "wasi", "reason": str(exc)}
        return {"available": True, "execution_enabled": True, "backend": "wasmtime-wasi",
            "scope": "Opt-in pure-Python isolated examples, not native/target/service integration.",
            "network": False, "guest_inherits_env": False, "memory_bytes": MAX_MEMORY,
            "fuel": FUEL, "wasm_timeout_seconds": 15, "host_timeout_seconds": 45,
            "output_bytes_per_stream": MAX_OUTPUT, "persistent_guest_writes": False}

    def command(self, directory, entrypoint):
        return [str(self.engine.resolve()), "run", "-W", f"max-memory-size={MAX_MEMORY}",
            "-W", f"fuel={FUEL}", "-W", "timeout=15s", "-W", "max-memories=1", "-W", "max-instances=1",
            "-W", "threads=n", "-W", "shared-memory=n",
            "-S", "inherit-env=n", "-S", "inherit-stdin=n", "-S", "inherit-network=n",
            "-S", "tcp=n", "-S", "udp=n", "-S", "http=n", "-S", "tls=n", "-S", "listenfd=n",
            "-S", "config=n", "-S", "keyvalue=n", "-S", "nn=n", "-S", "threads=n",
            "-S", "max-resources=128", "-S", "hostcall-fuel=16777216",
            "--dir", str(directory) + "::/sandbox", "--env", "PYTHONHOME=/sandbox/runtime",
            "--env", "PYTHONPATH=/sandbox/work/project:/sandbox/work/bridge",
            "--env", "PYTHONDONTWRITEBYTECODE=1", str(self.module.resolve()), "/sandbox/work/" + entrypoint]

    def run(self, files, entrypoint):
        status = self.describe()
        if not status["available"]:
            return {"status": "not_executed", "isolation": status}
        if not isinstance(files, dict) or not 1 <= len(files) <= 64:
            raise ValueError("WASI examples accept 1–64 text artifacts.")
        entrypoint = safe_relative_path(entrypoint)
        if not entrypoint.endswith(".py") or entrypoint not in files:
            raise ValueError("Choose a Python entry point from the approved artifact set.")
        manifest, portable, total = {}, set(), 0
        for path, content in files.items():
            path = safe_relative_path(path)
            if not isinstance(content, str) or len(content.encode()) > 262144:
                raise ValueError("WASI artifacts must be bounded text.")
            key = path.casefold()
            if key in portable or any(key.startswith(other + "/") or other.startswith(key + "/") for other in portable):
                raise ValueError("WASI artifact path collision.")
            portable.add(key)
            total += len(content.encode())
            manifest[path] = hashlib.sha256(content.encode()).hexdigest()
        if total > 2000000:
            raise ValueError("WASI artifact byte limit exceeded.")
        started = time.monotonic()
        with tempfile.TemporaryDirectory(prefix="repotraction-wasi-") as scratch:
            directory = Path(scratch)
            shutil.copytree(self.library, directory / "runtime" / "lib")
            for path, content in files.items():
                target = directory / "work" / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
            # Host runtime has only OS-loader variables; no GitHub/AI/session values.
            environment = {key: os.environ[key] for key in ("SystemRoot", "WINDIR") if key in os.environ}
            environment["TEMP"] = environment["TMP"] = str(directory)
            process = subprocess.Popen(self.command(directory, entrypoint), stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=directory, env=environment,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            streams = {"stdout": bytearray(), "stderr": bytearray()}
            exceeded = threading.Event()

            def drain(name, pipe):
                while chunk := pipe.read(4096):
                    room = MAX_OUTPUT - len(streams[name])
                    streams[name].extend(chunk[:room])
                    if len(chunk) > room:
                        exceeded.set()
                        process.kill()
                pipe.close()

            readers = [threading.Thread(target=drain, args=(name, pipe), daemon=True)
                for name, pipe in (("stdout", process.stdout), ("stderr", process.stderr))]
            for reader in readers:
                reader.start()
            timed_out = False
            try:
                process.wait(timeout=45)
            except subprocess.TimeoutExpired:
                timed_out = True
                process.kill()
                process.wait(timeout=5)
            for reader in readers:
                reader.join(timeout=5)
            result = {"status": "timeout" if timed_out else "output_limit" if exceeded.is_set() else
                "exited_successfully" if process.returncode == 0 else "failed", "exit_code": process.returncode,
                "context": "isolated_wasi_example", "request_criteria_verified": False,
                "duration_seconds": round(time.monotonic() - started, 3), "isolation": status,
                "runtime": {"wasmtime": "49.0.1", "cpython_wasi": "3.14.7", "engine_sha256": ENGINE_HASH, "module_sha256": PYTHON_HASH},
                "artifact_sha256": manifest, "entrypoint": entrypoint,
                **{name: output.decode("utf-8", errors="replace").replace(str(self.module.resolve()), "[pinned Python WASM]")
                    .replace(str(directory), "/sandbox") for name, output in streams.items()},
                "limitations": ["Exit code alone does not prove original request criteria.",
                    "This is an isolated example, not target-application or live-service integration.",
                    "WASI and a trusted runtime enforce the boundary; runtime vulnerabilities remain a risk."]}
        return result
