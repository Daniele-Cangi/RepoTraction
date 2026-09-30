"""Explicit optional WASI runtime download, no installer/system changes or execution.

Pinned Wasmtime vendor release and unofficial CPython WASI build. GitHub release
asset SHA256 values checked before safe extraction. Never downloads project code.
"""
import hashlib
import io
import os
from pathlib import Path
import stat
import sys
import tempfile
import urllib.request
import uuid
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from missing_link.proofs import safe_relative_path


ASSETS = [
    ("wasmtime", "https://github.com/bytecodealliance/wasmtime/releases/download/v49.0.1/wasmtime-v49.0.1-x86_64-windows.zip",
        "db0dd3dd77696fa189b08e256a50ddbe46d10a4d1e6c862d8d268ad0abc8c2c1"),
    ("cpython", "https://github.com/brettcannon/cpython-wasi-build/releases/download/v3.14.7/python-3.14.7-wasi_sdk-24.zip",
        "2e064d3fb8172471d39d741348efa722349c40b96301f69968dff714999c584b"),
]


MAX_ARCHIVE_BYTES = 32000000


def no_links(path):
    # Do not follow a user-controlled symlink/junction while repairing/installing.
    for item in (path, *path.parents):
        if item.is_symlink() or (hasattr(item, "is_junction") and item.is_junction()):
            raise ValueError("Runtime paths must not contain links or junctions.")


def download(url):
    with urllib.request.urlopen(url, timeout=45) as response:
        return response.read(MAX_ARCHIVE_BYTES + 1)


def archive_bytes(root, name, url, expected, fetch):
    cache = root / ".archives"
    no_links(cache)
    cache.mkdir(exist_ok=True)
    path = cache / (name + "-" + expected + ".zip")
    no_links(path)
    data = path.read_bytes() if path.is_file() and path.stat().st_size <= MAX_ARCHIVE_BYTES else b""
    if data and hashlib.sha256(data).hexdigest() == expected:
        return data
    print("Downloading", name, flush=True)
    data = fetch(url)
    if len(data) > MAX_ARCHIVE_BYTES or hashlib.sha256(data).hexdigest() != expected:
        raise ValueError("Runtime release archive failed the size/integrity check.")
    # Cache only verified vendor bytes, atomically. Never trust a local manifest
    # claiming arbitrary files belong to a pinned archive.
    with tempfile.TemporaryDirectory(prefix=".download-", dir=cache) as scratch:
        staged = Path(scratch) / "asset.zip"
        staged.write_bytes(data)
        os.replace(staged, path)
    return data


def checked_entries(archive):
    if len(archive.infolist()) > 5000 or sum(item.file_size for item in archive.infolist()) > 250000000:
        raise ValueError("Runtime archive exceeds extraction limits.")
    entries, seen = [], {}
    for info in archive.infolist():
        path = safe_relative_path(info.filename.rstrip("/"))
        mode = stat.S_IFMT(info.external_attr >> 16)
        key = path.casefold()
        if mode not in (0, stat.S_IFREG, stat.S_IFDIR) or key in seen:
            raise ValueError("Runtime archive contains a link, special file or path collision.")
        if any(seen.get("/".join(key.split("/")[:index])) is False for index in range(1, len(key.split("/")))):
            raise ValueError("Runtime archive has a file/directory collision.")
        if not info.is_dir() and any(previous.startswith(key + "/") for previous in seen):
            raise ValueError("Runtime archive has a file/directory collision.")
        seen[key] = info.is_dir()
        entries.append((info, path))
    return entries


def stream_hash(stream):
    digest = hashlib.sha256()
    while block := stream.read(65536):
        digest.update(block)
    return digest.hexdigest()


def asset_matches(destination, archive, entries):
    no_links(destination)
    if not destination.is_dir():
        return False
    expected = {path for info, path in entries if not info.is_dir()}
    actual = set()
    for item in destination.rglob("*"):
        no_links(item)
        if item.is_file():
            actual.add(item.relative_to(destination).as_posix())
        elif not item.is_dir():
            return False
    if actual != expected:
        return False
    for info, path in entries:
        target = destination / path
        if info.is_dir():
            if not target.is_dir():
                return False
            continue
        if target.stat().st_size != info.file_size:
            return False
        with target.open("rb") as local, archive.open(info) as vendor:
            if stream_hash(local) != stream_hash(vendor):
                return False
    return True


def extract_asset(destination, archive, entries):
    for info, path in entries:
        target = destination / path
        if info.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(info))


def install_assets(root, assets=ASSETS, fetch=download):
    root = Path(root).absolute()
    no_links(root)
    root.mkdir(parents=True, exist_ok=True)
    for name, url, expected in assets:
        if safe_relative_path(name) != name or "/" in name:
            raise ValueError("Asset names must be single directory components.")
        destination = root / name
        no_links(destination)
        data = archive_bytes(root, name, url, expected, fetch)
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            entries = checked_entries(archive)
            if asset_matches(destination, archive, entries):
                print(name, "already verified; reused", flush=True)
                continue
            # Extraction failures leave the previous destination untouched.
            with tempfile.TemporaryDirectory(prefix="." + name + "-stage-", dir=root) as scratch:
                staged = Path(scratch) / name
                staged.mkdir()
                extract_asset(staged, archive, entries)
                if not asset_matches(staged, archive, entries):
                    raise ValueError("Staged runtime did not match the pinned archive.")
                backup = None
                if destination.exists():
                    # Both targets are explicit siblings inside this validated
                    # runtime root; preserve unknown/partial old content, never delete it.
                    backup = root / (name + ".previous-" + uuid.uuid4().hex)
                    destination.rename(backup)
                try:
                    staged.rename(destination)
                except BaseException:
                    if backup is not None and not destination.exists():
                        backup.rename(destination)
                    raise
                if backup is not None:
                    print("Previous runtime preserved in", backup.name, flush=True)
        print(name, "verified", expected, "files", len(entries), flush=True)


def main():
    install_assets(Path(__file__).resolve().parents[1] / "data" / "wasi-runtime")
    print("Downloaded optional runtime only; no project code has been executed.", flush=True)


if __name__ == "__main__":
    main()
