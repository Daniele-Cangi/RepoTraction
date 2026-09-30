"""Explicitly approve one pinned public WASI example through the local API.

Reviewed tests are human-owned fixtures, NOT an imported analysis or an automatic
claim that original criteria passed. No shell, network or host project execution.
"""
import argparse
import json
from pathlib import Path
import urllib.error
import urllib.request
from urllib.parse import urlparse


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8765")
    parser.add_argument("--match-id", required=True)
    parser.add_argument("--entrypoint", required=True, help="bridge/file.py or reviewed_tests/file.py")
    parser.add_argument("--reviewed-test", type=Path, action="append", default=[])
    parser.add_argument("--approve", action="store_true", help="Explicit confirmation after inspecting artifacts")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    origin = args.url.rstrip("/")
    url = urlparse(origin)
    if url.scheme != "http" or url.hostname not in {"127.0.0.1", "localhost", "::1"} or url.path or url.query or url.fragment or url.username:
        parser.error("Use a loopback HTTP origin.")
    if not args.approve:
        parser.error("Review the pinned artifacts first, then supply --approve.")
    if len(args.reviewed_test) > 4 or any(path.is_symlink() or path.stat().st_size > 128000 for path in args.reviewed_test):
        parser.error("Use at most four regular reviewed tests, 128 KB each.")
    body = {"match_id": args.match_id, "entrypoint": args.entrypoint, "approved": True,
        "reviewed_tests": [{"path": path.name, "content": path.read_text(encoding="utf-8")} for path in args.reviewed_test]}
    request = urllib.request.Request(origin + "/api/missing-link/example", data=json.dumps(body).encode(),
        headers={"Origin": origin, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            result = json.load(response)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Local example API returned HTTP {exc.code}; inspect the selected match and runtime status.") from None
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    example = result["isolated_example"]
    print(json.dumps({key: example.get(key) for key in ("id", "status", "exit_code", "context", "request_criteria_verified", "stdout", "stderr")}, indent=2, ensure_ascii=False))
    return 0 if example["status"] == "exited_successfully" else 1


if __name__ == "__main__":
    raise SystemExit(main())
