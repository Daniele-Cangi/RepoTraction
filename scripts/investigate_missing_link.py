"""Opt-in real Missing Link investigation through the local HTTP API, no imports.

This can spend the explicitly configured provider allowance with --use-ai.
It never supplies prewritten interpretations, executes bridges or publishes.
"""
import argparse
import json
from pathlib import Path
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse, urlencode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8765")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--issue", action="append", default=[])
    parser.add_argument("--query", default="")
    parser.add_argument("--max-candidates", type=int, default=2)
    parser.add_argument("--use-ai", action="store_true")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--resume", help="Explicitly resume a failed/paused job as the first selected issue.")
    args = parser.parse_args()
    base = args.url.rstrip("/")
    parsed = urlparse(base)
    if parsed.hostname not in {"localhost", "127.0.0.1", "::1"} or parsed.scheme != "http" or parsed.path or parsed.query or parsed.fragment:
        parser.error("Use a local loopback HTTP base URL.")

    def request(path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(base + path, data=data,
            headers={"Content-Type": "application/json", "Origin": base})
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"Local API returned HTTP {exc.code}.") from None

    state = request("/api/missing-link")
    if args.use_ai and not state["provider"]["configured"]:
        parser.error("The server has no configured provider; no paid call started.")
    report = {"context": "real_public_github_and_provider_api" if args.use_ai else "real_public_github_structural",
        "manual_analysis_imported": False, "repository": args.repo, "provider": state["provider"], "jobs": []}
    for issue_url in args.issue or [""]:
        if args.resume:
            previous_job = next(item for item in state["jobs"] if item["id"] == args.resume)
            if previous_job["input"]["repo"] != args.repo or previous_job["input"]["issue_url"] != issue_url or previous_job["input"]["use_ai"] != args.use_ai:
                parser.error("Resume inputs differ from the original job; start a new investigation instead.")
            started = request("/api/missing-link/resume", {"job_id": args.resume})
            args.resume = None
        else:
            started = request("/api/missing-link/jobs", {"repo": args.repo, "action": "discover", "issue_url": issue_url,
                "query": args.query, "max_candidates": args.max_candidates, "max_requests": 80, "use_ai": args.use_ai})
        job_id = started["job_id"]
        print(json.dumps({"job_id": job_id, "issue": issue_url, "status": "started"}), flush=True)
        deadline, previous = time.monotonic() + 900, None
        while time.monotonic() < deadline:
            state = request("/api/missing-link")
            job = next(item for item in state["jobs"] if item["id"] == job_id)
            update = (job["status"], job["stage"], job["ai_calls_used"])
            if update != previous:
                print(json.dumps({"job_id": job_id, "status": job["status"], "stage": job["stage"],
                    "ai_calls": job["ai_calls_used"], "reserved_usd": job["cost_reserved_usd"]}), flush=True)
                previous = update
            if job["status"] not in {"queued", "running"}:
                break
            time.sleep(2)
        else:
            request("/api/missing-link/cancel", {"job_id": job_id})
            raise RuntimeError("Investigation timed out and cancellation was requested.")
        entry = {"job": job, "matches": []}
        for match_id in job["result"]["match_ids"]:
            exported = request("/api/missing-link/export?" + urlencode({"match_id": match_id}))
            entry["matches"].append(exported)
            print(json.dumps({"match_id": match_id, "classification": exported["match"]["classification"],
                "analysis_source": exported["match"]["analysis_source"], "summary": exported["match"]["summary"]}, ensure_ascii=False), flush=True)
        report["jobs"].append(entry)
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        if job["status"] != "completed" or job["result"].get("partial"):
            print(json.dumps({"error": job.get("error"), "candidate_errors": job["result"].get("candidate_errors", []),
                "partial": bool(job["result"].get("partial")), "report": str(args.report) if args.report else None}), flush=True)
            return 1
    print(json.dumps({"completed": True, "report": str(args.report) if args.report else None}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
