"""Explicit optional WASI runtime download, no installer/system changes or execution.

Pinned Wasmtime vendor release and unofficial CPython WASI build. GitHub release
asset SHA256 values checked before safe extraction. Never downloads project code.
"""
import hashlib
import io
from pathlib import Path
import stat
import sys
import urllib.request
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from missing_link.proofs import safe_relative_path


ASSETS = [
    ("wasmtime", "https://github.com/bytecodealliance/wasmtime/releases/download/v49.0.1/wasmtime-v49.0.1-x86_64-windows.zip",
        "db0dd3dd77696fa189b08e256a50ddbe46d10a4d1e6c862d8d268ad0abc8c2c1"),
    ("cpython", "https://github.com/brettcannon/cpython-wasi-build/releases/download/v3.14.7/python-3.14.7-wasi_sdk-24.zip",
        "2e064d3fb8172471d39d741348efa722349c40b96301f69968dff714999c584b"),
]


def main():
    root = Path(__file__).resolve().parents[1] / "data" / "wasi-runtime"
    for name, url, expected in ASSETS:
        destination = root / name
        if destination.exists():
            raise ValueError("Runtime destination already exists; not overwriting an existing installation.")
        print("Downloading", name, flush=True)
        with urllib.request.urlopen(url, timeout=45) as response:
            data = response.read(32000001)
        if len(data) > 32000000 or hashlib.sha256(data).hexdigest() != expected:
            raise ValueError("Runtime release archive failed the size/integrity check.")
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            if len(archive.infolist()) > 5000 or sum(item.file_size for item in archive.infolist()) > 250000000:
                raise ValueError("Runtime archive exceeds extraction limits.")
            entries, seen = [], set()
            for info in archive.infolist():
                path = safe_relative_path(info.filename.rstrip("/"))
                if stat.S_ISLNK(info.external_attr >> 16) or path.casefold() in seen:
                    raise ValueError("Runtime archive contains a link or path collision.")
                seen.add(path.casefold())
                entries.append((info, path))
            for info, path in entries:
                target = destination / path
                if info.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(archive.read(info))
        print(name, "verified", expected, "files", len(entries), flush=True)
    print("Downloaded optional runtime only; no project code has been executed.", flush=True)


if __name__ == "__main__":
    main()
