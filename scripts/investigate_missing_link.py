"""Opt-in real Missing Link investigation through the local HTTP API, no imports.

This can spend the explicitly configured provider allowance with --use-ai.
It never supplies prewritten interpretations, executes bridges or publishes.
"""
import argparse
from pathlib import Path
import sys
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from missing_link.investigation import local_request, run_investigation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8765")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--issue", action="append", default=[])
    parser.add_argument("--query", default="")
    parser.add_argument("--max-candidates", type=int, default=2)
    parser.add_argument("--use-ai", action="store_true")
    parser.add_argument("--report", type=Path, help="New report path; existing reports are never replaced.")
    parser.add_argument("--resume", help="Explicitly resume a failed/paused job as the first selected issue.")
    args = parser.parse_args()
    base = args.url.rstrip("/")
    parsed = urlparse(base)
    if (parsed.hostname not in {"localhost", "127.0.0.1", "::1"} or parsed.scheme != "http"
            or parsed.path or parsed.query or parsed.fragment or parsed.username or parsed.password):
        parser.error("Use a local loopback HTTP base URL without credentials.")
    try:
        return run_investigation(args, lambda path, body=None: local_request(base, path, body),
            emit=lambda message: print(message, flush=True))
    except FileExistsError:
        parser.error("Report already exists; select a new path. No job was started.")


if __name__ == "__main__":
    raise SystemExit(main())
