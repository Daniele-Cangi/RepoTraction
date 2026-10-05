"""Explicit owned-probe safety gates; no IO, configuration or paid call on import.

Caller supplies real snapshot/fingerprint/main checks and atomic Store reservation.
No production imports this module. Never reuse obsolete pre-payment history after
the owned reservation; validate only the declared increment below, without repair.
"""
import hashlib
import json
import math

from scripts import missing_link_triage_native_probe as probe

CONFIG_FIELDS = ("model", "api_kind", "response_format", "max_tokens", "max_bytes",
    "reasoning_effort", "streaming", "input_price", "output_price", "max_calls",
    "max_cost", "total_budget", "budget_id", "url")
ACCOUNTING_TABLES = {"ml_ai_allowances", "ml_ai_reservations"}


def configuration(provider):
    """Whitelist public knobs only; never include or inspect the credential."""
    return {key: getattr(provider, key) for key in CONFIG_FIELDS}


def verify_request(provider, *, case, payload, metadata, config):
    """Reproduce the frozen request/configuration; no network or reservation."""
    if configuration(provider) != config:
        raise ValueError("Native probe provider configuration changed")
    current = probe.build_case()
    if current != case:
        raise ValueError("Native probe authored context changed")
    schema = probe.schema_for_context(current["data"])
    endpoint, encoded_payload, body = provider._encode_prompt(probe.PROMPT, current["data"], schema, "analysis")
    reservation = ((len(body) + 2048) * provider.input_price + provider.max_tokens * provider.output_price) / 1e6
    actual = {"endpoint": endpoint, "request_bytes": len(body), "request_sha256": hashlib.sha256(body).hexdigest(),
        "prompt_characters": len(probe.PROMPT), "prompt_sha256": hashlib.sha256(probe.PROMPT.encode()).hexdigest(),
        "schema_sha256": hashlib.sha256(json.dumps(schema, sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
        "reservation_usd": reservation}
    if encoded_payload != payload or actual != metadata or len(body) > provider.max_bytes:
        raise ValueError("Native probe frozen request changed")
    if not math.isfinite(reservation) or reservation <= 0 or reservation > provider.max_cost:
        raise ValueError("Native probe exceeds prepared job reservation cap")
    return reservation


def verify_increment(before, after, *, allowance, job_id, reservation, ceiling):
    """Permit zero/one exact owned row and its allowance increment; reject others.

Snapshots are supplied by the existing read-only reader, including full ordered
reservation/allowance rows. No table or historical artifact is rewritten here.
    """
    def require(condition, message):
        if not condition:
            raise ValueError(message)
    require(after["artifacts"] == before["artifacts"] and not after["active_jobs"], "Native probe history/worker changed")
    require(set(after["tables"]) == set(before["tables"]), "Native probe table set changed")
    for name, digest in before["tables"].items():
        if name not in ACCOUNTING_TABLES:
            require(after["tables"][name] == digest, "Native probe non-accounting table changed")
    old = before["reservation_rows"]
    require(after["reservation_rows"][:len(old)] == old, "Native probe prior reservation changed")
    require(not any(row[2] == job_id for row in old), "Native probe job already reserved")
    added = after["reservation_rows"][len(old):]
    require(len(added) <= 1, "Native probe added more than one reservation")
    require(after["reservations"] == before["reservations"] + len(added), "Native probe reservation count changed")
    for row in added:
        require(len(row) >= 4 and row[1] == allowance and row[2] == job_id,
            "Native probe foreign reservation")
        require(isinstance(row[3], (float, int)) and not isinstance(row[3], bool)
            and math.isfinite(row[3]) and abs(row[3] - reservation) < 1e-12, "Native probe reservation amount changed")
    increment = reservation if added else 0
    require(abs(after["reserved_usd"] - before["reserved_usd"] - increment) < 1e-8
        and after["reserved_usd"] <= ceiling + 1e-8, "Native probe cumulative reservation changed")
    old_allowances, new_allowances = dict(before["allowance_rows"]), dict(after["allowance_rows"])
    require(len(new_allowances) == len(after["allowance_rows"])
        and set(new_allowances) == set(old_allowances) and allowance in old_allowances,
        "Native probe allowance set changed")
    for key, amount in old_allowances.items():
        require(abs(new_allowances[key] - amount - (increment if key == allowance else 0)) < 1e-8,
            "Native probe allowance balance changed")
    if not added:
        for name in ACCOUNTING_TABLES:
            require(after["tables"][name] == before["tables"][name], "Native probe unowned accounting change")


def claim_start(path, metadata):
    """Exclusive marker; never remove/rewrite it, even after a failed attempt."""
    with path.open("x", encoding="utf-8") as handle:
        json.dump(metadata, handle, ensure_ascii=False, indent=2)


def run_once(*, preflight, merged, lease, identity, marker, marker_metadata, execute, verify_after):
    """No automatic retries; block before reservation if merged/frozen/lease fail.

Both preflight checks must reproduce snapshot/code/config/request fingerprints.
The merged callback must verify the reviewed revision on freshly fetched main.
The execute callback is the owned single-request probe with atomic reservation.
    """
    preflight()
    if merged() is not True:
        raise RuntimeError("Native probe reviewed revision is not on main")
    if not lease.acquire():
        raise RuntimeError("Native probe worker already owned")
    try:
        preflight()
        identity(force=True)
        claim_start(marker, marker_metadata)
        return execute()
    finally:
        try:
            lease.release()
        finally:
            verify_after()
