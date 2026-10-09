"""Separate opt-in Responses reader; no import IO or production wiring.

240 active / 600 observed wall seconds; callbacks are measured, never bypassed.
Only open/read exceptions are converted to transport failures. Native terminals
and bounded telemetry remain private, separate from accepted interpretations.
"""
import copy
from contextlib import contextmanager
import http.client
import json
import math
import sys
import time
import urllib.error
import urllib.request

from github_cli import ActiveAccountChangedError
from missing_link.analysis import digest
from missing_link.contracts import validate_shape
from missing_link.provider import NoRedirect, CandidateValidationError
from missing_link.provider_errors import ProviderTransportError, MESSAGES
from missing_link.service import Cancelled, Paused
from scripts.missing_link_repository_only_evaluator import EvaluationStopped
from scripts.missing_link_triage_receipts import ReceiptPersistenceError


class StreamClockError(RuntimeError):
    """Clock observations are not a finite monotonic time source."""


class TelemetryPersistenceError(RuntimeError):
    """Diagnostic storage failed; primary category is bounded, never raw text."""
    def __init__(self, primary):
        super().__init__("Private stream telemetry could not be retained.")
        self.primary = copy.deepcopy(primary)


def _safe_projection(values, depth=0):
    """Even mutable exception fields cannot smuggle arbitrary diagnostic keys."""
    if values is None:
        return None
    if type(values) is not dict or depth > 2:
        return {"category": "callback_or_unclassified"}
    category = values.get("category")
    if type(category) is not str:
        return {"category": "callback_or_unclassified"}
    if category == "telemetry_persistence":
        return {"category": category, "primary": _safe_projection(values.get("primary"), depth + 1)}
    if category == "ai_transport":
        code, phase, status = (values.get(k) for k in ("code", "phase", "http_status"))
        code = code if type(code) is str and code in MESSAGES else "ai_transport_protocol_error"
        phase = phase if type(phase) is str and phase in {"analysis", "capabilities", "request", "matches"} else "analysis"
        result = {"category": category, "code": code, "phase": phase}
        if code == "ai_transport_http_error" and type(status) is int and 100 <= status <= 599:
            result["http_status"] = status
        return result
    allowed = {"receipt_persistence", "candidate_validation", "cancelled", "budget",
               "identity", "integrity", "clock", "callback_or_unclassified"}
    return {"category": category if category in allowed else "callback_or_unclassified"}


def failure_projection(error):
    """Project only fixed categories and concrete allowlisted transport fields."""
    if error is None:
        return None
    if isinstance(error, TelemetryPersistenceError):
        return _safe_projection({"category": "telemetry_persistence",
            "primary": object.__getattribute__(error, "__dict__").get("primary")})
    if isinstance(error, ProviderTransportError):
        values = object.__getattribute__(error, "__dict__")
        return _safe_projection({"category": "ai_transport",
            **{key: values.get(key) for key in ("code", "phase", "http_status")}})
    for cls, category in ((ReceiptPersistenceError, "receipt_persistence"),
            (CandidateValidationError, "candidate_validation"),
            (Cancelled, "cancelled"), (Paused, "budget"),
            (ActiveAccountChangedError, "identity"), (EvaluationStopped, "integrity"),
            (StreamClockError, "clock")):
        if isinstance(error, cls):
            return {"category": category}
    return {"category": "callback_or_unclassified"}


class _Timing:
    """Nonoverlapping callback durations; snapshot never reads the clock."""
    def __init__(self, clock):
        self.clock, self.last, self.started, self.ended = clock, None, None, None
        self.valid, self.deadline_kind = True, None
        self.durations = {k: None for k in ("opening", "reading", "light", "full")}
        self.counts = {k: None for k in ("lines", "bytes", "light", "full")}
        self.receipt, self.reservation = None, None

    def now(self):
        value = self.clock()
        if (type(value) not in (int, float) or not math.isfinite(value)
                or (self.last is not None and value < self.last)):
            self.valid = False
            raise StreamClockError("Invalid stream clock.")
        self.last = value
        return value

    def opened(self):
        # Opening succeeded: absence/counts do not depend on a valid clock.
        self.receipt = False
        for key in ("reading", "light", "full"):
            self.durations[key] = 0
        for key in self.counts:
            self.counts[key] = 0

    def start(self):
        self.started = self.now()

    def measure(self, kind, callback):
        before = self.now()
        counted = kind == "opening" or (self.started is not None and self.ended is None)
        if counted and kind in ("light", "full"):
            self.counts[kind] += 1
        error = None
        try:
            return callback()
        except BaseException as exc:
            error = exc
            raise
        finally:
            try:
                elapsed = self.now() - before
                if counted:
                    self.durations[kind] = (self.durations[kind] or 0) + elapsed
            except StreamClockError:
                if error is None:
                    raise
                # Clock damage must not replace an already-global callback error.

    def limits(self):
        if self.started is None or self.ended is not None:
            return
        wall = self.now() - self.started
        active = wall - self.durations["light"] - self.durations["full"]
        if wall > 600 or active > 240:
            self.deadline_kind = "wall_stream" if wall > 600 else "active_stream"
            raise ProviderTransportError("ai_stream_deadline_exceeded", phase="request")

    def checkpoint(self, kind, callback):
        self.limits()
        self.measure(kind, callback)
        self.limits()

    def snapshot(self, error):
        # Seconds capped at a day, counters at wire-bound maximum plus one line.
        # Saturation is explicit; missing/invalid observations stay null.
        saturated = False

        def seconds(value):
            nonlocal saturated
            if value is None or not self.valid:
                return None
            saturated |= value > 86400
            return min(86400, max(0, value))

        def counter(value, bound):
            nonlocal saturated
            if value is None:
                return None
            saturated |= value > bound
            return min(bound, value)

        wall = (self.ended if self.ended is not None else self.last)
        wall = None if self.started is None or wall is None else wall - self.started
        active = None if wall is None else wall - self.durations["light"] - self.durations["full"]
        result = {"version": 1, "failure": failure_projection(error),
            "reservation_committed": self.reservation, "terminal_retained": self.receipt,
            "clock_valid": self.valid, "deadline_kind": self.deadline_kind,
            "lines": counter(self.counts["lines"], 8_000_001),
            "bytes": counter(self.counts["bytes"], 8_512_001),
            "light_checkpoints": counter(self.counts["light"], 16_000_004),
            "full_checkpoints": counter(self.counts["full"], 8_000_004),
            "opening_seconds": seconds(self.durations["opening"]),
            "reading_seconds": seconds(self.durations["reading"]),
            "light_checkpoint_seconds": seconds(self.durations["light"]),
            "full_checkpoint_seconds": seconds(self.durations["full"]),
            "active_stream_seconds": seconds(active), "wall_stream_seconds": seconds(wall)}
        result["saturated"] = saturated
        return result


def _io(callback):
    """Called ONLY around network open/read, never guards or storage."""
    try:
        return callback()
    except ProviderTransportError as exc:
        safe = failure_projection(exc)
        raise ProviderTransportError(safe["code"], phase="request", http_status=safe.get("http_status")) from None
    except urllib.error.HTTPError as exc:
        raise ProviderTransportError("ai_transport_http_error", phase="request", http_status=exc.code) from None
    except TimeoutError:
        raise ProviderTransportError("ai_transport_timeout", phase="request") from None
    except urllib.error.URLError as exc:
        code = "ai_transport_timeout" if isinstance(exc.reason, TimeoutError) else "ai_transport_network_error"
        raise ProviderTransportError(code, phase="request") from None
    except (OSError, http.client.HTTPException):
        raise ProviderTransportError("ai_transport_io_error", phase="request") from None


@contextmanager
def _response_stream(opener, request, timing):
    """Own the returned response before post-open timing or context entry."""
    response, entered = None, False
    failure = (None, None, None)

    def open_response():
        nonlocal response
        response = _io(lambda: opener.open(request, timeout=55))
        timing.opened()
        return response

    try:
        timing.measure("opening", open_response)
        enter_response = type(response).__enter__
        exit_response = type(response).__exit__
        enter_response(response)
        entered = True
        yield response
    except BaseException:
        failure = sys.exc_info()
        raise
    finally:
        if response is not None:
            try:
                if entered:
                    # Exit is cleanup only: it cannot suppress a global error.
                    exit_response(response, *failure)
                else:
                    response.close()
            except BaseException:
                # Preserve the actual primary exception/traceback in every
                # lifecycle phase. A sole cleanup failure remains global.
                if failure[0] is None:
                    raise


def complete_with_receipt(provider, instruction, data, budget, *, schema,
                          retain_terminal, retain_telemetry, light_checkpoint,
                          terminal_checkpoint, reservation_observed, clock=time.monotonic):
    """Request phase only. One open; caller supplies full Budget and light gates."""
    timing, error = _Timing(clock), None
    try:
        if not provider.describe()["configured"] or provider.api_kind != "responses" or not provider.streaming:
            raise ValueError("Configured Responses streaming provider required.")
        endpoint, payload, body = provider._encode_prompt(instruction, data, schema, "request")
        if len(body) > provider.max_bytes:
            raise ValueError("Source context exceeds AI prompt bound.")
        reserved = ((len(body) + 2048) * provider.input_price + provider.max_tokens * provider.output_price) / 1_000_000
        timing.measure("full", lambda: budget.reserve_ai(reserved, provider.max_calls,
            provider.max_cost if provider.remote else None))
        timing.measure("full", budget.checkpoint)
        headers = {"Content-Type": "application/json"}
        if provider.key:
            headers["Authorization"] = "Bearer " + provider.key
        request = urllib.request.Request(provider.url + endpoint, data=body, headers=headers, method="POST")
        opener = urllib.request.build_opener(NoRedirect())
        with _response_stream(opener, request, timing) as response:
            timing.start()
            nonterminal, last_full, terminal = 0, timing.started, None
            while True:
                timing.checkpoint("light", light_checkpoint)
                timing.limits()
                line = timing.measure("reading", lambda: _io(lambda: response.readline(512001)))
                if line:
                    timing.counts["lines"] += 1
                    timing.counts["bytes"] += len(line)
                timing.checkpoint("light", light_checkpoint)
                timing.limits()
                if len(line) > 512000 or timing.counts["bytes"] > 8_000_000:
                    raise ProviderTransportError("ai_transport_size_exceeded", phase="request")
                if not line:
                    raise ProviderTransportError("ai_stream_missing_terminal", phase="request")
                if line.startswith(b"data: "):
                    try:
                        event = json.loads(line[6:])
                        if not isinstance(event, dict):
                            raise ValueError("Invalid event")
                        if event.get("type") in {"response.completed", "response.failed", "response.incomplete"}:
                            result = event["response"]
                            if not isinstance(result, dict) or result.get("status") != event["type"].split(".", 1)[1]:
                                raise ValueError("Inconsistent terminal")
                            terminal = event
                    except (KeyError, ValueError, TypeError):
                        raise ProviderTransportError("ai_stream_invalid_event", phase="request") from None
                timing.limits()
                if terminal is not None:
                    # Guards are global callbacks, outside the writer boundary.
                    timing.checkpoint("light", terminal_checkpoint)
                    timing.receipt = None  # A failing writer may have partially persisted.
                    try:
                        retain_terminal(copy.deepcopy(terminal))
                    except Exception:
                        raise ReceiptPersistenceError("Private terminal receipt could not be saved.") from None
                    timing.receipt = True
                    timing.checkpoint("light", terminal_checkpoint)
                    timing.checkpoint("full", budget.checkpoint)
                    timing.ended = timing.now()
                    break
                nonterminal += 1
                if nonterminal >= 128 or timing.now() - last_full >= 30:
                    timing.checkpoint("full", budget.checkpoint)
                    nonterminal, last_full = 0, timing.now()
        result = terminal["response"]
        usage = result.get("usage")
        tokens = (usage.get("input_tokens"), usage.get("output_tokens")) if isinstance(usage, dict) else (None, None)
        if not all(type(v) is int and v >= 0 for v in tokens):
            raise CandidateValidationError("Missing or invalid native usage.")
        budget.record_usage(*tokens, (tokens[0] * provider.input_price + tokens[1] * provider.output_price) / 1_000_000)
        budget.record_call({"phase": "request", "model": provider.model, "api_kind": provider.api_kind,
            "response_id": str(result.get("id", ""))[:150], "response_status": str(result.get("status", ""))[:30],
            "request_sha256": digest(payload), "request_bytes": len(body),
            "context_coverage": data.get("context_coverage", {})})
        try:
            if result.get("status") != "completed":
                raise ValueError("AI response is incomplete.")
            blocks = [part for item in result["output"] if item.get("type") == "message" for part in item.get("content", [])]
            if any(part.get("type") == "refusal" for part in blocks):
                raise ValueError("AI refused this analysis.")
            parsed = json.loads("".join(part["text"] for part in blocks if part.get("type") == "output_text"))
        except (KeyError, IndexError, TypeError, AttributeError, json.JSONDecodeError):
            raise CandidateValidationError("Malformed structured output.") from None
        except ValueError as exc:
            raise CandidateValidationError(str(exc)) from None
        budget.record_output("request", parsed)
        budget.checkpoint()
        try:
            if not isinstance(parsed, dict):
                raise ValueError("AI must return a JSON object.")
            if schema:
                validate_shape(parsed, schema)
        except ValueError as exc:
            raise CandidateValidationError(str(exc)) from None
        budget.checkpoint()
        return parsed
    except BaseException as exc:
        error = exc
        raise
    finally:
        try:
            observed = reservation_observed()
            if observed is not None and type(observed) is not bool:
                raise ValueError("Reservation observation must be bool or null.")
            timing.reservation = observed
            retain_telemetry(timing.snapshot(error))
        except BaseException:
            raise TelemetryPersistenceError(failure_projection(error)) from None
