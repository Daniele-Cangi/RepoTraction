"""Case-only bindings to existing Service/Provider/Budget/Store; no agent runner.

CLI access for BOTH solvers: `note ARM input.json` or `github ARM input.json`.
The operator initializes clocks separately; these commands cannot reset them.
"""
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from github_cli import verify_cli_account
from missing_link.analysis import digest, evidence_catalog, resolve_evidence
from missing_link.config import provider_environment
from missing_link.contracts import obj, string
from missing_link.provider import Provider
from missing_link.service import Budget, Paused, Service
from missing_link.sources import PublicGitHub, _redact
from missing_link.store import Store, redact_payload
from missing_link.lease import WorkerLease

FROZEN = ROOT / "docs/experiments/paired-assistance-2026-10-23"
DATA = ROOT / "data/paired-assistance-2026-10-23/execution-2026-10-24"
ACCOUNT = "Daniele-Cangi"
PIN = "9d866a5f447d9fe1c989b31f90c520dc2813ee26"
FINGERPRINT = "bd2749aeabe5d3b0f98ec883d73e6db8f7312532849866913330f1e5d15fc143"


def state(arm):
    if arm not in {"A", "B"}:
        raise ValueError("Unknown frozen arm")
    return json.loads((DATA / arm / "clock.json").read_text(encoding="utf-8"))


def verify(arm, phase_deadline=None):
    record = state(arm)
    deadline = min(record["deadline_monotonic"], phase_deadline or float("inf"))
    if time.monotonic() >= deadline:
        raise Paused("Frozen arm/phase deadline reached; no new operation")
    return verify_cli_account(ACCOUNT, run=subprocess.run)


class RecordedProvider(Provider):
    def _encode_prompt(self, instruction, data, schema, phase):
        endpoint, payload, _ = super()._encode_prompt(instruction, data, schema, phase)
        # Explicit Standard processing, the published rate checked for this cohort.
        payload["service_tier"] = "default"
        return endpoint, payload, json.dumps(payload, ensure_ascii=False).encode("utf-8")

    def complete(self, instruction, data, budget, schema=None, phase="analysis"):
        # Preserve effective public inputs in the ordinary private job checkpoint.
        budget.job["checkpoint"].setdefault("effective_calls", []).append({
            "phase": phase, "instruction": instruction, "data": copy.deepcopy(data),
            "schema": copy.deepcopy(schema), "attempt": budget.job["ai_calls_used"] + 1})
        budget.save()
        return super().complete(instruction, data, budget, schema, phase)


def provider(arm):
    state(arm)  # Arm must already have an operator-created clock.
    env = provider_environment()
    if env.get("REPOTRACTION_AI_URL", "").rstrip("/") != "https://api.openai.com/v1":
        raise ValueError("Frozen standard endpoint changed")
    env.update(REPOTRACTION_AI_MODEL="gpt-6-luna", REPOTRACTION_AI_API_KIND="responses",
        REPOTRACTION_AI_RESPONSE_FORMAT="json_schema", REPOTRACTION_AI_REASONING_EFFORT="medium",
        REPOTRACTION_AI_STREAMING="1", REPOTRACTION_AI_MAX_CALLS="6",
        REPOTRACTION_AI_MAX_PROMPT_BYTES="180000", REPOTRACTION_AI_MAX_OUTPUT_TOKENS="12000",
        REPOTRACTION_AI_INPUT_USD_PER_MILLION="0.1", REPOTRACTION_AI_OUTPUT_USD_PER_MILLION="0.5",
        REPOTRACTION_AI_MAX_COST_USD="0.15", REPOTRACTION_AI_TOTAL_BUDGET_USD="0.15",
        REPOTRACTION_AI_BUDGET_ID="paired-cycles-2026-10-23-" + ("direct" if arm == "A" else "assisted") + "-v1")
    result = RecordedProvider(env)
    if not result.describe()["configured"]:
        raise ValueError("Frozen provider is not configured")
    return result


def store(arm):
    return Store(DATA / arm / "ledger.sqlite3", ACCOUNT)


def helper_budget(arm):
    verify(arm)
    ledger, model, record = store(arm), provider(arm), state(arm)
    job = ledger.get("jobs", record["job_id"])

    def save():
        ledger.put("jobs", job["id"], job)

    budget = Budget(job, save, lambda: ledger.is_cancelled(job["id"]), lambda: verify(arm),
        reserve_total=lambda cost: ledger.reserve_ai_allowance(model.budget_id, job["id"], cost, .15))
    return model, budget


def raw_read(arm, budget, endpoint, params=None):
    budget.github()
    budget.job["checkpoint"].setdefault("github_reads", []).append({"endpoint": endpoint, "params": params})
    budget.save()
    value = fetch_get(endpoint, params)
    budget.checkpoint()
    return value


def fetch_get(endpoint, params=None):
    # Service budgets its own reads; helper raw_read budgets helper reads once.
    args = ["gh", "api", "--method", "GET", endpoint]
    for key, value in (params or {}).items():
        args += ["-f", str(key) + "=" + str(value)]
    result = subprocess.run(args, capture_output=True, encoding="utf-8", timeout=45, check=False)
    if result.returncode:
        raise ValueError("GitHub GET failed; raw CLI diagnostics withheld")
    return json.loads(result.stdout)


def note(arm, value):
    serialized = json.dumps(value, ensure_ascii=False)
    if redact_payload(serialized) != serialized:
        raise ValueError("Only public note context without credential-like values is allowed")
    model, budget = helper_budget(arm)
    return model.complete(value["instruction"], value["data"], budget, obj(notes=string()), "analysis")


def github(arm, value):
    _, budget = helper_budget(arm)
    endpoint, params = value["endpoint"], value.get("params")
    if any(part in {".", ".."} for part in endpoint.split("/")) or re.search(r"[?#\\\s]", endpoint):
        raise ValueError("Only plain repository endpoint paths are allowed")
    match = re.fullmatch(r"repos/([\w.-]+/[\w.-]+)(?:/.*)?", endpoint)
    source = PublicGitHub(lambda path, params=None: raw_read(arm, budget, path, params))
    if match:
        source._public_repo(match[1])
    elif endpoint == "search/repositories":
        params = dict(params or {})
        params["q"] = str(params.get("q", "")) + " is:public"
    else:
        raise ValueError("Only public repository GETs/repository search are offered")
    return raw_read(arm, budget, endpoint, params)


class FrozenService(Service):
    def __init__(self, *args, **kwargs):
        self.frozen = json.loads((FROZEN / "frozen-inputs.json").read_text(encoding="utf-8"))
        if digest(self.frozen) != FINGERPRINT or self.frozen["target"]["revision"] != PIN:
            raise ValueError("Frozen issue/target content changed")
        super().__init__(*args, **kwargs)

    def _dispatch(self, job, background=True):
        # Bind the ordinary generated job ID to B's already running shared clock.
        path = DATA / "B/clock.json"
        record = state("B")
        record["job_id"] = job["id"]
        path.write_text(json.dumps(record), encoding="utf-8", newline="\n")
        return super()._dispatch(job, background)

    def _prepare_request_discovery(self, job, source, budget, stage, save):
        frozen = self.frozen

        class FrozenReads:
            def fetch_issue(self, url):
                if url != frozen["issue"]["url"]:
                    raise ValueError("Only the frozen issue is allowed")
                return copy.deepcopy(frozen["issue"])

            def fetch_reference_context(self, issue, *, include_catalog=False):
                if issue["fingerprint"] != frozen["issue"]["fingerprint"]:
                    raise ValueError("Frozen discussion changed")
                return copy.deepcopy(frozen["target"])

            def __getattr__(self, name):
                return getattr(source, name)

        return super()._prepare_request_discovery(job, FrozenReads(), budget, stage, save)


def packet(job):
    items = job.get("result", {}).get("strategies", {}).get("0", {}).get("items", [])
    if job["status"] != "completed" or not items or items[0]["relevance"] != "pertinent":
        return None
    item = items[0]
    repo = job["checkpoint"]["repository"]
    if (repo.get("public") is not True or repo["id"] != item["repo_id"]
            or repo["revision"] != item["revision"]):
        raise ValueError("Strategy/source identity differs")
    files = {f["path"]: f for f in repo["files"]}
    catalog = evidence_catalog(repo, job["checkpoint"]["discussions"]["0"])
    if not item["evidence"]:
        raise ValueError("Strategy evidence is empty")
    for evidence in item["evidence"]:
        file = files[evidence["path"]]
        expected = resolve_evidence(evidence["source_id"], catalog)
        if (file["sha"] != evidence["sha"] or not evidence["quote"].strip() or
                any(evidence[key] != expected[key] for key in ("path", "line", "end_line", "quote"))):
            raise ValueError("Unavailable exact strategy evidence")
    fields = ("repo", "repo_id", "revision", "title", "mechanism", "relevance", "reason",
        "requirement_ids", "evidence", "adaptation", "assumptions", "limitations",
        "direct_alternative", "expected_advantage", "verification", "benefit_status")
    value = {key: item[key] for key in fields}
    value["coverage"] = repo["coverage"]
    value["file_flags"] = [{key: f.get(key) for key in ("path", "sha", "redacted", "truncated")}
                           for f in repo["files"] if f["path"] in {e["path"] for e in item["evidence"]}]
    payload = (json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n").encode()
    clean, redacted, truncated = _redact(payload.decode())
    if len(payload) > 16000 or clean.encode() != payload or redacted or truncated:
        raise ValueError("Packet exceeds frozen limit or needs redaction; no substitution")
    return payload


def initialize(arm):
    """Operator-only preparation; not exposed by the solver CLI."""
    directory = DATA / arm
    if (directory / "clock.json").exists():
        raise ValueError("Arm already started; no clock/allowance resets")
    directory.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    record = {"arm": arm, "started_at": datetime.now(timezone.utc).isoformat(),
        "start_monotonic": started, "deadline_monotonic": started + 1200, "job_id": uuid.uuid4().hex}
    (directory / "clock.json").write_text(json.dumps(record), encoding="utf-8", newline="\n")
    if arm == "A":
        store(arm).put("jobs", record["job_id"], {"id": record["job_id"], "account": ACCOUNT,
            "input": {"max_requests": 120}, "status": "running", "requests_used": 0,
            "ai_calls_used": 0, "cost_reserved_usd": 0., "checkpoint": {}, "result": {}})
    return record


if __name__ == "__main__":
    operation, arm, input_file = sys.argv[1:]
    if operation not in {"note", "github"}:
        raise ValueError("Solver CLI cannot initialize, reset, discover or dispatch")
    value = json.loads(Path(input_file).read_text(encoding="utf-8"))
    lease = WorkerLease(DATA / arm / "ledger.sqlite3")
    if not lease.acquire():
        raise ValueError("Another operation owns this arm ledger; helpers must run serially")
    try:
        print(json.dumps((note if operation == "note" else github)(arm, value), ensure_ascii=False))
    finally:
        lease.release()
