"""Authored offline reproduction of the frozen reader's wall-clock deadline.

Run as a standalone process: patches are process-wide and not thread-safe.
No configuration, credentials, acquired inputs, database or owned run is read.
The real receipt reader and Budget run against a mocked opener and virtual clock;
socket construction is forbidden. Import performs no IO or patching.
"""
import json
from pathlib import Path
import sys
import urllib.error
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from missing_link.provider import Provider
from missing_link.provider_errors import ProviderTransportError
from missing_link.service import Budget
from scripts.missing_link_triage_receipts import complete_with_receipt


def _event(value):
    return ("data: " + json.dumps(value) + "\n").encode()


def _terminal():
    return _event({"type": "response.completed", "response": {
        "id": "authored-offline", "status": "completed",
        "usage": {"input_tokens": 1, "output_tokens": 1},
        "output": [{"type": "message", "content": [
            {"type": "output_text", "text": '{"value":"authored"}'}]}]}})


def _deltas(pairs):
    return [_event({"type": "response.output_text.delta", "delta": "authored"}), b"\n"] * pairs


class _Clock:
    def __init__(self):
        self.seconds = 0

    def monotonic(self):
        return self.seconds


class _Stream:
    def __init__(self, lines, clock, read_seconds):
        self.lines, self.clock, self.read_seconds = iter(lines), clock, read_seconds
        self.active, self.reads, self.last_read_seconds = False, 0, 0
        self.started = 0

    def __enter__(self):
        self.active, self.started = True, self.clock.seconds
        return self

    def __exit__(self, *args):
        self.active = False
        return False

    def readline(self, limit):
        self.clock.seconds += self.read_seconds
        self.reads += 1
        self.last_read_seconds = self.clock.seconds - self.started
        return next(self.lines, b"")


def _exercise(lines, *, guard_seconds=0, read_seconds=0, open_error=None,
              guard=None, cancelled=lambda: False):
    """Fixture-only experiment; reservations and receipts exist in memory."""
    clock = _Clock()
    stream = _Stream(lines, clock, read_seconds)
    reservations, receipts = [], []
    counters = {"guards": 0, "stream_checkpoints": 0}
    job = {"id": "authored-offline", "ai_calls_used": 0,
           "cost_reserved_usd": 0, "checkpoint": {}}

    def gate():
        counters["guards"] += 1
        clock.seconds += guard_seconds
        if guard is not None:
            guard()

    def checkpoint():
        if stream.active:
            counters["stream_checkpoints"] += 1
        # Match v3 verify_checkpoint's two gates; identity cost is omitted.
        gate()
        gate()

    provider = Provider({
        "REPOTRACTION_AI_URL": "http://127.0.0.1:1/v1",
        "REPOTRACTION_AI_MODEL": "authored-offline",
        "REPOTRACTION_AI_API_KIND": "responses",
        "REPOTRACTION_AI_STREAMING": "1",
        "REPOTRACTION_AI_MAX_CALLS": "1",
        "REPOTRACTION_AI_INPUT_USD_PER_MILLION": "0.10",
        "REPOTRACTION_AI_OUTPUT_USD_PER_MILLION": "0.50"})
    budget = Budget(job, lambda: None, cancelled, checkpoint, reservations.append)
    opener = Mock()
    opener.open.return_value = stream
    opener.open.side_effect = open_error
    code, status, parsed = None, None, None
    with patch("urllib.request.build_opener", return_value=opener), \
            patch("scripts.missing_link_triage_receipts.time.monotonic", clock.monotonic), \
            patch("socket.socket", side_effect=AssertionError("Offline sockets forbidden")) as socket:
        try:
            parsed = complete_with_receipt(provider, "Authored offline diagnostic", {}, budget,
                schema=None, retain_terminal=receipts.append, phase="request")
        except ProviderTransportError as exc:
            # Reader-created typed errors only; never print exception text/body.
            code, status = exc.code, exc.http_status
        socket.assert_not_called()
    return {"transport_code": code, "http_status": status,
        "terminal_retained": bool(receipts), "parsed_output": parsed is not None,
        "synthetic_reservations": len(reservations),
        "synthetic_usage_records": len(job.get("reported_usage", [])),
        "mock_open_invocations": opener.open.call_count, "actual_network_calls": 0,
        "stream_checkpoints": counters["stream_checkpoints"],
        "simulated_guard_invocations": counters["guards"],
        "last_read_virtual_seconds": stream.last_read_seconds}


def authored_controls():
    """Fixed scenarios; no user-supplied endpoint, key, run or retry option."""
    return {
        "buffered_fast_61_pairs": _exercise(_deltas(61) + [_terminal()]),
        "buffered_guard_1s_60_pairs": _exercise(_deltas(60) + [_terminal()], guard_seconds=1),
        "buffered_guard_1s_61_pairs": _exercise(_deltas(61) + [_terminal()], guard_seconds=1),
        "buffered_guard_5s_13_pairs": _exercise(_deltas(13) + [_terminal()], guard_seconds=5),
        "slow_read_terminal": _exercise([_terminal()], read_seconds=241),
        "missing_terminal": _exercise(_deltas(1)),
        "malformed_event": _exercise([b"data: {\n"]),
        "open_timeout": _exercise([], open_error=TimeoutError("authored")),
        "open_http_503": _exercise([], open_error=urllib.error.HTTPError(
            "http://127.0.0.1:1", 503, "authored", {}, None)),
    }


if __name__ == "__main__":
    if len(sys.argv) != 1:
        raise SystemExit("This offline diagnostic accepts no arguments.")
    print(json.dumps({"authored_only": True, "actual_network_calls": 0,
                      "controls": authored_controls()}, indent=2))
