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
    parser.add_argument("--repo", default="")
    parser.add_argument("--from-request", action="store_true",
                        help="Let Missing Link choose operations and one source from the issue; requires --use-ai.")
    parser.add_argument("--issue", action="append", default=[])
    parser.add_argument("--query", default="")
    parser.add_argument("--max-candidates", type=int)
    parser.add_argument("--use-ai", action="store_true")
    parser.add_argument("--report", type=Path, help="New report path; existing reports are never replaced.")
    parser.add_argument("--resume", help="Explicitly resume a failed/paused job as the first selected issue.")
    args = parser.parse_args()
    if args.from_request:
        if args.repo or args.query or not args.use_ai or len(args.issue) != 1:
            parser.error("--from-request needs one --issue and --use-ai, without --repo or --query.")
        if args.max_candidates not in (None, 1):
            parser.error("--from-request inspects one autonomously selected source.")
    elif not args.repo:
        parser.error("Supply --repo or use --from-request with one --issue.")
    if args.max_candidates is None:
        args.max_candidates = 1 if args.from_request else 2
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
