"""Opt-in repository-only evaluation adapters; production never imports these.

Use the unchanged Service and Provider interpretation methods. Only acquisition
pinning, private receipts and the original atomic reservation binding live here.
No IO, credential lookup or execution of acquired code happens on import.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
from urllib.parse import quote

from missing_link.provider import Provider
from scripts.missing_link_triage_receipts import complete_with_receipt

CONFIG_FIELDS = ("model", "api_kind", "response_format", "max_tokens", "max_bytes",
    "reasoning_effort", "streaming", "input_price", "output_price", "max_calls",
    "max_cost", "total_budget", "budget_id", "url")


def configuration(provider):
    """Public configuration only; never include the credential."""
    return {key: getattr(provider, key) for key in CONFIG_FIELDS}


class EvaluationStopped(RuntimeError):
    """Global evaluation failure, never a candidate-local validation failure."""


def require(condition, message):
    if not condition:
        raise EvaluationStopped(message)


class PinnedSource:
    """Route only the source's branch commit read; target acquisition stays live."""
    def __init__(self, read, slot):
        self.read, self.slot = read, slot
        self.metadata_checked = self.commit_checked = False

    def __call__(self, endpoint, *, params=None):
        prefix = "repos/" + self.slot["canonical_name"]
        branch = prefix + "/commits/" + quote(self.slot["default_branch"], safe="")
        if endpoint == branch and not self.commit_checked:
            require(self.metadata_checked, "Source commit precedes verified metadata")
            endpoint = prefix + "/commits/" + self.slot["revision"]
        result = self.read(endpoint, params=params)
        if endpoint == prefix and not self.metadata_checked:
            require(isinstance(result, dict) and result.get("full_name") == self.slot["canonical_name"]
                    and result.get("private") is False and result.get("visibility") == "public"
                    and result.get("archived") is False and result.get("disabled") is False
                    and result.get("has_issues") is True
                    and result.get("default_branch") == self.slot["default_branch"],
                    "Frozen source identity or public acquisition state changed")
            self.metadata_checked = True
        if endpoint == prefix + "/commits/" + self.slot["revision"]:
            require(isinstance(result, dict) and result.get("sha") == self.slot["revision"]
                    and result.get("commit", {}).get("tree", {}).get("sha") == self.slot["commit_tree_sha"],
                    "Frozen source commit/tree changed")
            self.commit_checked = True
        return result

    def verify(self, job):
        repo = job.get("checkpoint", {}).get("repository", {})
        require(self.metadata_checked and self.commit_checked and repo.get("public") is True
                and repo.get("full_name") == self.slot["canonical_name"]
                and repo.get("revision") == self.slot["revision"], "Paid call lacks frozen source acquisition")


class ReservationBinding:
    """Bind Service's private Store method to the original, tighter atomic cap.

The expected request is registered before reserve_ai. Journal only after atomic
commit; a failed journal stops the cohort and leaves the charge retained.
"""
    def __init__(self, store, *, allowance, ceiling, verify, persist):
        self.store, self.allowance, self.ceiling = store, allowance, ceiling
        self.verify, self.persist = verify, persist
        self.rows, self.pending = [], None

    def expect(self, job_id, cost):
        require(self.pending is None and math.isfinite(cost) and cost > 0, "Invalid reservation attempt")
        self.pending = (job_id, cost)

    def __call__(self, allowance, job_id, cost, total):
        require(allowance == self.allowance and total == 10 and self.pending == (job_id, cost),
                "Reservation differs from the owned request")
        self.verify()
        self.store.reserve_ai_allowance(allowance, job_id, cost, self.ceiling)
        self.rows.append({"job_id": job_id, "cost": cost})
        self.pending = None
        self.persist(len(self.rows), copy.deepcopy(self.rows[-1]))
        self.verify()


def verify_prefix(before, after, rows, *, allowance, ceiling):
    """Only the exact dynamic owned prefix may extend the immutable ledger."""
    require(after["artifacts"] == before["artifacts"] and not after["active_jobs"], "History or original worker changed")
    require(set(after["tables"]) == set(before["tables"]), "History table set changed")
    for table, digest in before["tables"].items():
        if table not in {"ml_ai_allowances", "ml_ai_reservations"}:
            require(after["tables"][table] == digest, "Original non-accounting history changed")
    prior = before["reservation_rows"]
    require(after["reservation_rows"][:len(prior)] == prior, "Previous reservations changed")
    added = after["reservation_rows"][len(prior):]
    require(len(added) == len(rows) and after["reservations"] == before["reservations"] + len(rows),
            "Unowned reservation count")
    for actual, expected in zip(added, rows):
        require(actual[1] == allowance and actual[2] == expected["job_id"]
                and not any(old[2] == expected["job_id"] for old in prior)
                and math.isfinite(actual[3]) and abs(actual[3] - expected["cost"]) < 1e-12,
                "Unowned reservation row")
    increment = sum(row["cost"] for row in rows)
    require(abs(after["reserved_usd"] - before["reserved_usd"] - increment) < 1e-8
            and after["reserved_usd"] <= ceiling + 1e-8, "Cumulative reservation changed")
    old, current = dict(before["allowance_rows"]), dict(after["allowance_rows"])
    require(set(old) == set(current) and len(current) == len(after["allowance_rows"]) and allowance in old,
            "Allowance set changed")
    for key, value in old.items():
        require(abs(current[key] - value - increment) < 1e-8 if key == allowance else current[key] == value,
                "Allowance balance changed")
    if not rows:
        require(after["tables"] == before["tables"], "Unowned accounting mutation")


class ReceiptProvider(Provider):
    """Delegate exact production bodies, latch all transport/wire/gate failures.

CandidateValidationError raised *after* complete returns, by the unchanged
interpretation methods, remains candidate-local. Errors inside complete are fatal.
"""
    def __init__(self, env, *, gate, binding, retain):
        super().__init__(env)
        self.gate, self.binding, self.retain = gate, binding, retain
        self.fatal = None

    def complete(self, instruction, data, budget, schema=None, phase="analysis"):
        require(self.fatal is None, "Evaluation has already stopped")
        try:
            self.gate(budget.job)
            endpoint, payload, body = self._encode_prompt(instruction, data, schema, phase)
            require(len(body) <= self.max_bytes, "Prompt exceeds frozen bound")
            cost = ((len(body) + 2048) * self.input_price + self.max_tokens * self.output_price) / 1e6
            number = budget.job["ai_calls_used"] + 1
            identity = {"job_id": budget.job["id"], "call_number": number, "phase": phase,
                        "endpoint": endpoint, "request_bytes": len(body), "reservation_usd": cost,
                        "request_sha256": hashlib.sha256(body).hexdigest()}
            self.retain("request", identity, {"metadata": identity, "payload": payload, "data": data,
                        "instruction": instruction, "schema": schema})
            self.binding.expect(budget.job["id"], cost)
            result = complete_with_receipt(self, instruction, data, budget, schema=schema, phase=phase,
                retain_terminal=lambda event: self.retain("terminal", identity, event))
            self.gate(budget.job)
            return result
        except Exception as exc:
            self.fatal = {"exception_type": type(exc).__name__, "code": getattr(exc, "code", None), "phase": phase}
            # Never expose upstream text, headers or credentials through Service.
            raise EvaluationStopped("Owned evaluation attempt failed; no continuation") from None


def execute_slots(service, provider, slots, *, set_slot, persist, verify):
    """One initial synchronous Service job per ordered slot, no resume or repair."""
    records = []
    for index, slot in enumerate(slots):
        verify()
        set_slot(slot)
        result = service.start({"repo": slot["input"], "action": "discover", "use_ai": True,
            "max_candidates": 3, "max_requests": 80, "issue_url": "", "query": ""}, background=False)
        job = service.store.get("jobs", result["job_id"])
        persist(slot, job)
        verify()
        records.append({"order": slot["order"], "repo": slot["input"], "job_id": job["id"],
                        "status": job["status"], "ai_calls_used": job["ai_calls_used"]})
        if provider.fatal is not None or job["status"] != "completed":
            return {"slots": records, "stopped_order": slot["order"], "fatal_attempt": provider.fatal,
                    "unattempted": [item["input"] for item in slots[index + 1:]], "retries": False}
    return {"slots": records, "stopped_order": None, "unattempted": [], "retries": False}
