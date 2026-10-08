"""Explicit prepare/verify/run for the frozen four-source, one-shot protocol.

Preparation never reads credentials or calls a provider. Run requires a separately
owned freeze on reviewed, merged main. Private files are exclusive and immutable;
the original database is touched only by Store's atomic allowance reservation.
"""
from __future__ import annotations

import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from github_cli import verify_cli_account
from missing_link.config import provider_environment
from missing_link.lease import WorkerLease
from missing_link.provider import Provider
from missing_link.service import Service
from missing_link.store import Store, redact_payload
from scripts.missing_link_repository_only_evaluator import (
    PinnedSource, ReceiptProvider, ReservationBinding, configuration, execute_slots, require, verify_prefix)
from scripts.missing_link_triage_transport import IdentityCheck

PREP = ROOT / "data/missing-link-repository-only-fresh-protocol-2026-10-08"
DB = ROOT / "data/repotraction-daniele-cangi.sqlite3"
ACCOUNT = "Daniele-Cangi"
ALLOWANCE = "missing-link-verification-2026-09-30"
CEILING = 8.4904081
PROTOCOL = ROOT / "docs/missing-link-repository-only-fresh-protocol-2026-10-08.md"
ADAPTERS = ("scripts/missing_link_repository_only_evaluator.py", "scripts/missing_link_repository_only_run.py",
            "scripts/missing_link_triage_receipts.py",
            "scripts/missing_link_triage_transport.py", "tests/test_missing_link_repository_only_evaluator.py")
REQUIRED_EVIDENCE = {"prepared.json", "baseline.json", "started.json", "summary.json", "final-integrity.json",
                     "evaluation.sqlite3", "evaluation.sqlite3.missing-link.lock"}


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(out, name, value):
    with (out / name).open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)


def sha(path, *, canonical=False):
    content = path.read_text(encoding="utf-8").encode() if canonical else path.read_bytes()
    return hashlib.sha256(content).hexdigest()


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True,
                          text=True, timeout=55).stdout.strip()


def snapshot(before):
    """Read one consistent original-DB transaction and only protected files."""
    with closing(sqlite3.connect(DB.as_uri() + "?mode=ro", uri=True)) as db:
        db.execute("BEGIN")
        tables = [row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'ml_%'")]
        require(all(re.fullmatch(r"ml_[A-Za-z0-9_]+", table) for table in tables), "Invalid audit table")
        hashes = {table: hashlib.sha256(json.dumps(db.execute(f'SELECT * FROM "{table}" ORDER BY rowid').fetchall(),
            sort_keys=True, ensure_ascii=False).encode()).hexdigest() for table in tables}
        rows = [list(row) for row in db.execute("SELECT * FROM ml_ai_reservations ORDER BY id")]
        allowances = [list(row) for row in db.execute("SELECT * FROM ml_ai_allowances ORDER BY id")]
        jobs = [json.loads(row[0]) for row in db.execute("SELECT payload FROM ml_jobs")]
        count, cost = db.execute("SELECT COUNT(*),SUM(cost) FROM ml_ai_reservations WHERE allowance_id=?", (ALLOWANCE,)).fetchone()
    return {"tables": hashes, "artifacts": {name: sha(ROOT / name) for name in before["artifacts"]},
            "reservations": count, "reserved_usd": cost, "reservation_rows": rows, "allowance_rows": allowances,
            "active_jobs": [job["id"] for job in jobs if job["status"] in {"queued", "running"}]}


def knobs():
    return {"REPOTRACTION_AI_URL": "https://api.openai.com/v1", "REPOTRACTION_AI_MODEL": "gpt-6-luna",
        "REPOTRACTION_AI_ALLOW_REMOTE": "1", "REPOTRACTION_AI_API_KIND": "responses",
        "REPOTRACTION_AI_RESPONSE_FORMAT": "json_schema", "REPOTRACTION_AI_STREAMING": "1",
        "REPOTRACTION_AI_REASONING_EFFORT": "medium", "REPOTRACTION_AI_MAX_OUTPUT_TOKENS": "6000",
        "REPOTRACTION_AI_MAX_PROMPT_BYTES": "180000", "REPOTRACTION_AI_MAX_CALLS": "8",
        "REPOTRACTION_AI_MAX_COST_USD": "0.20", "REPOTRACTION_AI_TOTAL_BUDGET_USD": "10",
        "REPOTRACTION_AI_BUDGET_ID": ALLOWANCE, "REPOTRACTION_AI_INPUT_USD_PER_MILLION": "0.10",
        "REPOTRACTION_AI_OUTPUT_USD_PER_MILLION": "0.50"}


def prepare(out, reviewed_head):
    require(not out.exists(), "Owned output already exists; never replace it")
    git("fetch", "origin", "main")
    require(git("branch", "--show-current") == "main" and not git("status", "--porcelain")
            and git("rev-parse", "HEAD") == git("rev-parse", "origin/main"), "Freeze requires clean merged main")
    require(git("rev-parse", "HEAD^{tree}") == git("rev-parse", reviewed_head + "^{tree}"),
            "Merged tree differs from reviewed head")
    protocol = load(PREP / "prepared.json")
    code = dict(protocol["code_sha256_canonical_lf"])
    require(all(sha(ROOT / path, canonical=True) == value for path, value in code.items()), "Production pipeline changed")
    code.update({name: sha(ROOT / name, canonical=True) for name in ADAPTERS})
    before = load(PREP / "baseline.json")
    require(snapshot(before) == before and before["reservations"] == 529
            and abs(before["reserved_usd"] - 7.6904081) < 1e-8, "Preparation baseline changed")
    for path in PREP.iterdir():
        if path.is_file():
            before["artifacts"][path.relative_to(ROOT).as_posix()] = sha(path)
    require(sha(PROTOCOL, canonical=True) == protocol["protocol_sha256_canonical_lf"], "Protocol changed")
    out.mkdir(parents=True)
    save(out, "baseline.json", before)
    config = knobs()
    # Dummy credential only to reproduce public readiness knobs; never serialized.
    save(out, "prepared.json", {"required_main": git("rev-parse", "HEAD"), "reviewed_head": reviewed_head,
        "reviewed_tree": git("rev-parse", "HEAD^{tree}"), "code_sha256_canonical_lf": code,
        "preparation_sha256": sha(PREP / "prepared.json"), "cohort_sha256": sha(PREP / "cohort.json"),
        "baseline_sha256": sha(out / "baseline.json"), "config_without_key": configuration(Provider(dict(config, REPOTRACTION_AI_KEY="offline"))),
        "slots": load(PREP / "cohort.json")["records"], "ceiling": CEILING,
        "segment_usd": .80, "configured_total_usd": 10, "new_model_calls": 0, "new_reservations": 0})
    verify(out)
    print("Owned successor frozen on reviewed main; no provider request or reservation.")


def frozen(out, provider=None, *, fetch=False):
    manifest = load(out / "prepared.json")
    require(not git("status", "--porcelain"), "Tracked implementation is dirty")
    require(sha(out / "baseline.json") == manifest["baseline_sha256"], "Owned baseline changed")
    require(all(sha(ROOT / path, canonical=True) == value for path, value in manifest["code_sha256_canonical_lf"].items()),
            "Executable fingerprint changed")
    require(sha(PREP / "prepared.json") == manifest["preparation_sha256"]
            and sha(PREP / "cohort.json") == manifest["cohort_sha256"]
            and manifest["slots"] == load(PREP / "cohort.json")["records"]
            and manifest["ceiling"] == CEILING and manifest["segment_usd"] == .80
            and manifest["configured_total_usd"] == 10, "Frozen cohort/config changed")
    if provider is not None:
        require(provider.describe()["configured"] is True
                and configuration(provider) == manifest["config_without_key"], "Provider readiness/config changed")
    if fetch:
        git("fetch", "origin", "main")
    git("merge-base", "--is-ancestor", manifest["required_main"], "origin/main")
    return manifest


def journal(out):
    paths = sorted(out.glob("reservation-*.json"))
    require([path.name for path in paths] == [f"reservation-{index:02}.json" for index in range(1, len(paths) + 1)],
            "Owned reservation journal has gaps")
    return [load(path) for path in paths]


def inventory(out):
    entries = list(out.iterdir())
    require(all(path.is_file() and not path.is_symlink() for path in entries), "Owned directory has unexpected entries")
    return {path.name for path in entries}


def fresh_directory(out):
    require(inventory(out) == {"prepared.json", "baseline.json"}, "Owned directory contains pre-existing execution evidence")


def seal_receipts(out, owned_hashes):
    """Return a digest for retention OUTSIDE the evidence directory.

An adjacent checksum is not a trust anchor. The caller must retain the returned
digest in its independent run log/reviewed report and supply it to later verify.
"""
    sealed = dict(owned_hashes)
    for name in ("evaluation.sqlite3", "evaluation.sqlite3.missing-link.lock"):
        require((out / name).is_file(), "Required private evidence database/lock is missing")
        sealed[name] = sha(out / name)
    require(REQUIRED_EVIDENCE <= set(sealed), "Required execution evidence is missing")
    require(inventory(out) == set(sealed), "Cannot seal an incomplete or unowned evidence inventory")
    require(all(sha(out / name) == value for name, value in sealed.items()), "Evidence changed before sealing")
    save(out, "owned-artifacts.json", sealed)
    return sha(out / "owned-artifacts.json")


def verify_receipts(out, expected_digest):
    require(bool(expected_digest and re.fullmatch(r"[a-f0-9]{64}", expected_digest)), "Independent receipt-manifest digest required")
    require((out / "owned-artifacts.json").is_file(), "Anchored receipt manifest is missing")
    require(sha(out / "owned-artifacts.json") == expected_digest, "Receipt manifest differs from independent digest")
    sealed = load(out / "owned-artifacts.json")
    require(REQUIRED_EVIDENCE <= set(sealed), "Required sealed execution evidence is missing")
    require(inventory(out) == set(sealed) | {"owned-artifacts.json"}, "Sealed evidence inventory changed")
    require(all(sha(out / name) == value for name, value in sealed.items()), "Sealed evidence changed")


def verify(out, expected_digest=None):
    frozen(out)
    if expected_digest is not None or (out / "owned-artifacts.json").exists():
        verify_receipts(out, expected_digest)
    else:
        fresh_directory(out)
    before = load(out / "baseline.json")
    verify_prefix(before, snapshot(before), journal(out), allowance=ALLOWANCE, ceiling=CEILING)
    print("Frozen code/cohort and original history reproduce with only the owned reservation prefix.")


def run(out):
    manifest = frozen(out, fetch=True)
    fresh_directory(out)
    before = load(out / "baseline.json")
    env = provider_environment()
    env.update(REPOTRACTION_AI_MAX_OUTPUT_TOKENS="6000", REPOTRACTION_AI_MAX_CALLS="8", REPOTRACTION_AI_MAX_COST_USD="0.20")
    identity = IdentityCheck(lambda: verify_cli_account(ACCOUNT, run=subprocess.run), time.monotonic)
    lease = WorkerLease(DB)
    binding = None
    active = {}
    required_mutable = set()
    owned_hashes = {"prepared.json": sha(out / "prepared.json"), "baseline.json": sha(out / "baseline.json")}
    def owned_save(name, value):
        save(out, name, value)
        owned_hashes[name] = sha(out / name)
    def integrity():
        require(inventory(out) <= set(owned_hashes) | {"evaluation.sqlite3", "evaluation.sqlite3.missing-link.lock"},
                "Unowned execution file appeared")
        require(all((out / name).is_file() for name in required_mutable), "Claimed private database/lock disappeared")
        require(all(sha(out / name) == value for name, value in owned_hashes.items()), "Owned evidence changed")
        verify_prefix(before, snapshot(before), binding.rows if binding else [], allowance=ALLOWANCE, ceiling=CEILING)
    def retain(kind, attempt, value):
        owned_save(f"{kind}-{active['slot']['order']:02}-{attempt['call_number']:02}.json", value)
    def gate(job):
        frozen(out, provider, fetch=True)
        identity(force=True)
        integrity()
        active["source"].verify(job)
        if "job_id" not in active:
            active["job_id"] = job["id"]
            owned_save(f"slot-{active['slot']['order']:02}.json", {"slot": active["slot"], "job_id": job["id"]})
        require(active["job_id"] == job["id"], "Slot job identity changed")
    provider = ReceiptProvider(env, gate=gate, binding=None, retain=retain)
    frozen(out, provider)
    integrity()
    require(lease.acquire(), "Original worker lease is held")
    summary = {"slots": [], "stopped_order": None, "unattempted": [s["input"] for s in manifest["slots"]], "retries": False}
    try:
        fresh_directory(out)
        integrity()
        identity(force=True)
        owned_save("started.json", {"one_shot": True, "required_main": manifest["required_main"], "ceiling": CEILING})
        evaluation_db = out / "evaluation.sqlite3"
        with evaluation_db.open("xb"):
            pass
        required_mutable.add(evaluation_db.name)
        original = Store(DB, ACCOUNT)
        binding = ReservationBinding(original, allowance=ALLOWANCE, ceiling=CEILING, verify=integrity,
            persist=lambda number, row: owned_save(f"reservation-{number:02}.json", row))
        provider.binding = binding
        reads = 0
        def read(endpoint, *, params=None):
            nonlocal reads
            identity()
            command = ["gh", "api", "--method", "GET", endpoint]
            for key, value in (params or {}).items():
                command += ["-f", f"{key}={value}"]
            try:
                result = subprocess.run(command, capture_output=True, timeout=45, check=False)
                require(result.returncode == 0 and len(result.stdout) <= 8_000_000, "Bounded GitHub acquisition failed")
                value = json.loads(result.stdout)
            except Exception:
                # Service's target-context ValueError handler must not downgrade
                # transport/JSON failures into candidate-local continuation.
                from scripts.missing_link_repository_only_evaluator import EvaluationStopped
                raise EvaluationStopped("Bounded GitHub acquisition failed") from None
            reads += 1
            owned_save(f"acquisition-{reads:03}.json", redact_payload({"endpoint": endpoint, "params": params, "response": value}))
            return value
        def set_slot(slot):
            active.clear()
            active.update(slot=slot, source=PinnedSource(read, slot))
        service = Service(evaluation_db, ACCOUNT, lambda endpoint, params=None: active["source"](endpoint, params=params), identity, provider)
        required_mutable.add(service.lease.path.name)
        service.store.reserve_ai_allowance = binding
        def persist(slot, job):
            # Zero-call acquisition failure still retains the actual allocated job.
            if "job_id" not in active:
                active["job_id"] = job["id"]
                owned_save(f"slot-{slot['order']:02}.json", {"slot": slot, "job_id": job["id"]})
            owned_save(f"job-{slot['order']:02}.json", job)
            owned_save(f"matches-{slot['order']:02}.json", [service.store.get("matches", key) for key in job["result"]["match_ids"]])
            print(json.dumps({"order": slot["order"], "repo": slot["input"], "status": job["status"],
                              "calls": job["ai_calls_used"], "reserved_usd": job["cost_reserved_usd"]}), flush=True)
        summary = execute_slots(service, provider, manifest["slots"], set_slot=set_slot, persist=persist, verify=integrity)
    except Exception as exc:
        summary.update(exception_type=type(exc).__name__, code=getattr(exc, "code", None),
            stopped_order=active.get("slot", {}).get("order"), fatal_attempt=provider.fatal)
        summary["slots"] = [{"slot": load(path)} for path in sorted(out.glob("slot-*.json"))]
        consumed = {record["slot"]["slot"]["input"] for record in summary["slots"]}
        summary["unattempted"] = [slot["input"] for slot in manifest["slots"] if slot["input"] not in consumed]
    finally:
        try:
            owned_save("summary.json", summary)
            integrity()
            owned_save("final-integrity.json", snapshot(before))
            independent_digest = seal_receipts(out, owned_hashes)
            print(json.dumps({"receipt_manifest_sha256": independent_digest,
                              "retain_outside_output_directory": True}), flush=True)
        finally:
            lease.release()
    print(json.dumps(summary), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "verify", "run"))
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--reviewed-head")
    parser.add_argument("--receipt-manifest-sha256", help="Digest retained in an independent run log/report; required after execution")
    args = parser.parse_args()
    if args.action == "prepare":
        require(bool(args.reviewed_head and re.fullmatch(r"[a-f0-9]{40}", args.reviewed_head)), "Reviewed full head required")
        prepare(args.output.resolve(), args.reviewed_head)
    elif args.action == "verify":
        verify(args.output.resolve(), args.receipt_manifest_sha256)
    else:
        run(args.output.resolve())


if __name__ == "__main__":
    main()
