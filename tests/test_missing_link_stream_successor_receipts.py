"""Authored streams/virtual clocks only; no sockets, keys or original database."""
import copy
import json
import unittest
import urllib.error
from unittest.mock import Mock, patch

from missing_link.provider import Provider, CandidateValidationError
from missing_link.provider_errors import ProviderTransportError
from missing_link.service import Budget, Cancelled
from scripts import missing_link_stream_successor_receipts as reader
from scripts.missing_link_repository_only_evaluator import EvaluationStopped
from test_missing_link_repository_only_evaluator import terminal


def event(value):
    return ("data: " + json.dumps(value) + "\n").encode()


class Clock:
    def __init__(self): self.value = 0
    def __call__(self): return self.value


class Stream:
    def __init__(self, lines, clock, delay=0, on_read=lambda: None):
        self.lines, self.clock, self.delay = iter(lines), clock, delay
        self.on_read, self.active = on_read, False
        self.entered, self.closed, self.close_calls = False, False, 0
    def __enter__(self): self.active = True; self.entered = True; return self
    def __exit__(self, *args): self.close(); return False
    def close(self):
        self.close_calls += 1
        self.closed, self.active = True, False
    def readline(self, limit):
        self.clock.value += self.delay
        self.on_read()
        value = next(self.lines, b"")
        if isinstance(value, BaseException): raise value
        return value


class SuccessorReceiptTests(unittest.TestCase):
    def setUp(self):
        self.clock, self.receipts, self.telemetry, self.charges = Clock(), [], [], []
        self.provider = Provider({"REPOTRACTION_AI_URL": "http://127.0.0.1:1/v1",
            "REPOTRACTION_AI_MODEL": "authored", "REPOTRACTION_AI_API_KIND": "responses",
            "REPOTRACTION_AI_STREAMING": "1", "REPOTRACTION_AI_MAX_CALLS": "1",
            "REPOTRACTION_AI_INPUT_USD_PER_MILLION": "0.10",
            "REPOTRACTION_AI_OUTPUT_USD_PER_MILLION": "0.50"})
        self.job = {"id": "authored", "ai_calls_used": 0, "cost_reserved_usd": 0, "checkpoint": {}}
        self.full, self.light, self.cancelled = Mock(), Mock(), lambda: False
        self.budget = Budget(self.job, lambda: None, lambda: self.cancelled(), lambda: self.full(), self.charges.append)

    def run_stream(self, lines=None, *, delay=0, on_read=lambda: None, open_error=None,
                   retain=None, diagnostic=None, observed=None, on_open=lambda: None):
        stream = Stream(lines if lines is not None else [event(terminal({"value": "authored"}))],
                        self.clock, delay, on_read)
        opener = Mock()
        opener.open.return_value = stream
        def open_response(*args, **kwargs):
            on_open()
            return stream
        opener.open.side_effect = open_error if open_error is not None else open_response
        with patch("urllib.request.build_opener", return_value=opener), \
                patch("socket.socket", side_effect=AssertionError("Offline sockets forbidden")), \
                patch("missing_link.provider.provider_environment", side_effect=AssertionError("No config")):
            try:
                return reader.complete_with_receipt(self.provider, "Authored", {}, self.budget,
                    schema=None, retain_terminal=retain or self.receipts.append,
                    retain_telemetry=diagnostic or self.telemetry.append,
                    light_checkpoint=self.light, clock=self.clock,
                    reservation_observed=observed or (lambda: bool(self.charges)))
            finally:
                self.assertLessEqual(opener.open.call_count, 1)
                self.opens = opener.open.call_count
                self.stream = stream

    def test_buffered_deltas_with_expensive_full_guards_finish(self):
        def full():
            self.clock.value += 10
        self.full.side_effect = full
        lines = [event({"type": "response.output_text.delta", "delta": "authored"}), b"\n"] * 150
        self.assertEqual(self.run_stream(lines + [event(terminal({"value": "authored"}))]), {"value": "authored"})
        trace = self.telemetry[0]
        self.assertEqual(trace["lines"], 301)
        self.assertEqual(trace["full_checkpoints"], 3)  # 128, 256, fresh post-terminal.
        self.assertEqual(trace["full_checkpoint_seconds"], 30)
        self.assertEqual(trace["active_stream_seconds"], 0)
        self.assertEqual(trace["wall_stream_seconds"], 30)
        self.assertEqual(trace["light_checkpoints"], 602)
        self.assertTrue(trace["terminal_retained"])
        self.assertTrue(trace["reservation_committed"])
        self.assertTrue(self.stream.closed)
        self.assertEqual(self.stream.close_calls, 1)

    def test_expensive_light_guards_are_measured_once_and_count_toward_wall(self):
        self.light.side_effect = lambda: setattr(self.clock, "value", self.clock.value + 5)
        lines = [b"\n"] * 25 + [event(terminal({"value": "authored"}))]
        self.run_stream(lines)
        trace = self.telemetry[0]
        self.assertEqual(trace["active_stream_seconds"], 0)
        self.assertEqual(trace["wall_stream_seconds"], 260)
        self.assertEqual(trace["light_checkpoint_seconds"], 260)
        self.assertGreater(trace["full_checkpoints"], 1)  # 30-wall-second cadence.

    def test_30_seconds_triggers_full_checkpoint_before_terminal(self):
        self.run_stream([b"\n", event(terminal({"value": "authored"}))], delay=30)
        self.assertEqual(self.telemetry[0]["full_checkpoints"], 2)

    def test_active_limit_equality_accepts_terminal(self):
        self.run_stream(delay=240)
        self.assertEqual(self.telemetry[0]["active_stream_seconds"], 240)
        self.assertTrue(self.telemetry[0]["terminal_retained"])

    def test_slow_read_expires_active_limit_without_retaining_late_terminal(self):
        with self.assertRaises(ProviderTransportError): self.run_stream(delay=241)
        trace = self.telemetry[0]
        self.assertEqual(trace["deadline_kind"], "active_stream")
        self.assertEqual(trace["reading_seconds"], 241)
        self.assertFalse(trace["terminal_retained"])
        self.assertNotIn("reported_usage", self.job)

    def test_wall_limit_equality_and_expiry_after_full_checkpoint(self):
        for duration in (600, 601):
            with self.subTest(duration=duration):
                self.setUp()
                self.full.side_effect = lambda: setattr(self.clock, "value", self.clock.value + duration)
                if duration == 600:
                    self.run_stream()
                    self.assertIsNone(self.telemetry[0]["deadline_kind"])
                else:
                    with self.assertRaises(ProviderTransportError): self.run_stream()
                    self.assertEqual(self.telemetry[0]["deadline_kind"], "wall_stream")
                    self.assertNotIn("reported_usage", self.job)
                self.assertTrue(self.telemetry[0]["terminal_retained"])
                self.assertEqual(self.telemetry[0]["active_stream_seconds"], 0)

    def test_failed_callback_timing_and_exception_are_preserved(self):
        original = OSError("authored callback")
        def light():
            self.clock.value += 7
            raise original
        self.light.side_effect = light
        with self.assertRaises(OSError) as raised: self.run_stream()
        self.assertIs(raised.exception, original)
        self.assertEqual(self.telemetry[0]["light_checkpoint_seconds"], 7)
        self.assertEqual(self.telemetry[0]["failure"], {"category": "callback_or_unclassified"})

    def test_history_guard_failure_after_receipt_stops_before_usage_or_parse(self):
        def full():
            if self.receipts: raise EvaluationStopped("Authored history change")
        self.full.side_effect = full
        with self.assertRaises(EvaluationStopped): self.run_stream()
        self.assertTrue(self.telemetry[0]["terminal_retained"])
        self.assertNotIn("reported_usage", self.job)
        self.assertNotIn("ai_outputs", self.job["checkpoint"])

    def test_missing_or_invalid_native_usage_stops_before_usage_trace_or_output(self):
        missing = object()
        cases = [missing, None, [], {}, {"input_tokens": 1}, {"output_tokens": 1}]
        for key in ("input_tokens", "output_tokens"):
            for value in (None, True, False, -1, 1.0, "1"):
                cases.append({"input_tokens": 1, "output_tokens": 1, key: value})
        for usage in cases:
            with self.subTest(usage=usage):
                self.setUp()
                native = terminal({"value": "authored"})
                if usage is missing:
                    del native["response"]["usage"]
                else:
                    native["response"]["usage"] = usage
                with patch.object(self.budget, "record_usage") as record_usage, \
                        patch.object(self.budget, "record_call") as record_call, \
                        patch.object(self.budget, "record_output") as record_output:
                    with self.assertRaises(CandidateValidationError):
                        self.run_stream([event(native)])
                    record_usage.assert_not_called()
                    record_call.assert_not_called()
                    record_output.assert_not_called()
                self.assertEqual(self.receipts, [native])
                self.assertEqual(len(self.charges), 1)
                self.assertTrue(self.telemetry[0]["reservation_committed"])
                self.assertTrue(self.telemetry[0]["terminal_retained"])
                self.assertEqual(self.telemetry[0]["failure"], {"category": "candidate_validation"})
                self.assertEqual(self.telemetry[0]["full_checkpoints"], 1)

    def test_valid_native_usage_including_zero_is_reported_exactly(self):
        for input_tokens, output_tokens in ((0, 0), (0, 25), (50, 0), (50, 25)):
            with self.subTest(tokens=(input_tokens, output_tokens)):
                self.setUp()
                native = terminal({"value": "authored"})
                native["response"]["usage"] = {"input_tokens": input_tokens, "output_tokens": output_tokens}
                self.assertEqual(self.run_stream([event(native)]), {"value": "authored"})
                self.assertEqual(self.job["reported_usage"], [{"input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "estimated_cost_usd_at_configured_prices":
                        (input_tokens * self.provider.input_price + output_tokens * self.provider.output_price) / 1_000_000}])
                self.assertIsNone(self.telemetry[0]["failure"])
                self.assertEqual(len(self.charges), 1)

    def test_missing_malformed_inconsistent_and_oversized_events_are_global(self):
        malformed = terminal({}); malformed["response"]["status"] = "incomplete"
        for lines, code in (([b"\n"], "ai_stream_missing_terminal"),
                ([b"data: {\n"], "ai_stream_invalid_event"),
                ([event([])], "ai_stream_invalid_event"),
                ([event(malformed)], "ai_stream_invalid_event"),
                ([b"x" * 512001], "ai_transport_size_exceeded"),
                ([b"x" * 500000] * 17, "ai_transport_size_exceeded")):
            with self.subTest(code=code):
                self.setUp()
                with self.assertRaises(ProviderTransportError): self.run_stream(lines)
                self.assertEqual(self.telemetry[0]["failure"]["code"], code)
                self.assertFalse(self.telemetry[0]["terminal_retained"])
                self.assertEqual(len(self.charges), 1)

    def test_network_errors_are_projected_without_raw_messages_or_body(self):
        errors = [(TimeoutError("PRIVATE"), "ai_transport_timeout"),
            (urllib.error.URLError(TimeoutError("PRIVATE")), "ai_transport_timeout"),
            (urllib.error.URLError("PRIVATE"), "ai_transport_network_error"),
            (OSError("PRIVATE"), "ai_transport_io_error"),
            (urllib.error.HTTPError("http://localhost", 503, "PRIVATE", {}, None), "ai_transport_http_error")]
        for error, code in errors:
            with self.subTest(code=code):
                self.setUp()
                with self.assertRaises(ProviderTransportError): self.run_stream(open_error=error)
                trace = self.telemetry[0]
                self.assertEqual(trace["failure"]["code"], code)
                self.assertIsNone(trace["lines"])
                self.assertIsNone(trace["terminal_retained"])
                self.assertIsNone(trace["reading_seconds"])
                self.assertNotIn("PRIVATE", json.dumps(trace))
                self.assertFalse(self.stream.closed)
                self.assertEqual(self.stream.close_calls, 0)

    def test_read_timeout_keeps_observed_stream_counts(self):
        with self.assertRaises(ProviderTransportError): self.run_stream([b"\n", TimeoutError("authored")], delay=2)
        self.assertEqual(self.telemetry[0]["lines"], 1)
        self.assertEqual(self.telemetry[0]["reading_seconds"], 4)

    def test_incomplete_failed_refused_and_invalid_native_outputs_stay_private_and_global(self):
        cases = [terminal({}, "incomplete"), terminal({}, "failed"), terminal({}, refusal=True), terminal([])]
        malformed = terminal({}); malformed["response"]["output"][0]["content"][0]["text"] = "{"
        cases.append(malformed)
        for native in cases:
            with self.subTest(status=native["response"]["status"]):
                self.setUp()
                with self.assertRaises(CandidateValidationError): self.run_stream([event(native)])
                self.assertEqual(self.receipts, [native])
                self.assertTrue(self.telemetry[0]["terminal_retained"])
                self.assertEqual(self.telemetry[0]["failure"]["category"], "candidate_validation")

    def test_receipt_storage_failure_is_global_and_retention_uncertain(self):
        def save(value): raise OSError("PRIVATE")
        with self.assertRaises(reader.ReceiptPersistenceError): self.run_stream(retain=save)
        # Writer may have partially succeeded; do not claim absence or completion.
        self.assertIsNone(self.telemetry[0]["terminal_retained"])
        self.assertNotIn("reported_usage", self.job)

    def test_telemetry_storage_failure_preserves_primary_bounded_category(self):
        def save(value): raise OSError("PRIVATE")
        with self.assertRaises(reader.TelemetryPersistenceError) as raised:
            self.run_stream(open_error=TimeoutError("PRIVATE"), diagnostic=save)
        self.assertEqual(raised.exception.primary["code"], "ai_transport_timeout")
        self.assertNotIn("PRIVATE", str(raised.exception))

    def test_reservation_loss_after_commit_is_observed_without_claiming_zero(self):
        def charge(value):
            self.charges.append(value)
            raise OSError("Authored journal failure")
        self.budget.reserve_total = charge
        with self.assertRaises(OSError): self.run_stream()
        self.assertTrue(self.telemetry[0]["reservation_committed"])
        self.assertEqual(self.opens, 0)

    def test_cancel_before_open_and_during_stream_is_global(self):
        self.cancelled = lambda: True
        with self.assertRaises(Cancelled): self.run_stream()
        self.assertEqual(self.opens, 0)
        self.assertFalse(self.telemetry[0]["reservation_committed"])
        self.setUp()
        def light():
            if self.cancelled(): raise Cancelled("Authored cancellation")
        self.light.side_effect=light
        def changed(): self.cancelled=lambda:True
        with self.assertRaises(Cancelled): self.run_stream(on_read=changed)
        self.assertEqual(self.opens,1)
        self.assertFalse(self.telemetry[0]["terminal_retained"])

    def test_invalid_clock_does_not_replace_failed_callback(self):
        def light():
            self.clock.value = float("nan")
            raise OSError("Authored guard failure")
        self.light.side_effect = light
        with self.assertRaises(OSError): self.run_stream()
        self.assertFalse(self.telemetry[0]["clock_valid"])
        self.assertIsNone(self.telemetry[0]["wall_stream_seconds"])

    def test_backward_nan_infinite_boolean_clocks_stop_without_open(self):
        for value in (-1, float("nan"), float("inf"), True):
            with self.subTest(value=value):
                self.setUp()
                self.full.side_effect = lambda: setattr(self.clock, "value", value)
                with self.assertRaises(reader.StreamClockError): self.run_stream()
                self.assertEqual(self.opens, 0)
                self.assertFalse(self.telemetry[0]["clock_valid"])
                self.assertIsNone(self.telemetry[0]["terminal_retained"])
                self.assertIsNone(self.telemetry[0]["lines"])

    def test_invalid_stream_start_clock_keeps_opened_absence_and_observed_zero_counts(self):
        for value in (-1, float("nan"), float("inf"), True, None, "invalid"):
            with self.subTest(value=value):
                self.setUp()
                def enter(stream):
                    stream.active = True
                    self.clock.value = value
                    return stream
                # The opener's observations succeeded; corrupt only the first
                # stream-clock sample, before any read or terminal retention.
                with patch.object(Stream, "__enter__", enter), self.assertRaises(reader.StreamClockError):
                    self.run_stream()
                trace = self.telemetry[0]
                self.assertEqual(self.opens, 1)
                self.assertEqual(len(self.charges), 1)
                self.assertTrue(trace["reservation_committed"])
                self.assertIs(trace["terminal_retained"], False)
                self.assertFalse(trace["clock_valid"])
                self.assertEqual(trace["failure"], {"category": "clock"})
                self.assertEqual(self.receipts, [])
                for key in ("lines", "bytes", "light_checkpoints", "full_checkpoints"):
                    self.assertEqual(trace[key], 0)
                for key in ("opening_seconds", "reading_seconds", "light_checkpoint_seconds",
                            "full_checkpoint_seconds", "active_stream_seconds", "wall_stream_seconds"):
                    self.assertIsNone(trace[key])
                self.assertNotIn("reported_usage", self.job)
                self.assertNotIn("ai_outputs", self.job["checkpoint"])

    def test_transport_projection_ignores_overridden_diagnostic_and_mutable_invalid_fields(self):
        error = ProviderTransportError("ai_transport_http_error", http_status=503)
        error.diagnostic = lambda: {"private": "PRIVATE"}
        error.code, error.phase, error.http_status = ["PRIVATE"], "PRIVATE", True
        result = reader.failure_projection(error)
        self.assertEqual(result, {"category": "ai_transport", "code": "ai_transport_protocol_error", "phase": "analysis"})

    def test_post_open_invalid_clock_closes_response_with_known_absence_before_enter(self):
        for value in (-1, float("nan"), float("inf"), True, None, "invalid"):
            with self.subTest(value=value):
                self.setUp()
                with self.assertRaises(reader.StreamClockError):
                    self.run_stream(on_open=lambda: setattr(self.clock, "value", value))
                trace = self.telemetry[0]
                self.assertEqual(self.opens, 1)
                self.assertTrue(self.stream.closed)
                self.assertEqual(self.stream.close_calls, 1)
                self.assertFalse(self.stream.entered)
                self.assertEqual(len(self.charges), 1)
                self.assertTrue(trace["reservation_committed"])
                self.assertIs(trace["terminal_retained"], False)
                self.assertFalse(trace["clock_valid"])
                self.assertEqual(trace["failure"], {"category": "clock"})
                for key in ("lines", "bytes", "light_checkpoints", "full_checkpoints"):
                    self.assertEqual(trace[key], 0)
                for key in ("opening_seconds", "reading_seconds", "light_checkpoint_seconds",
                            "full_checkpoint_seconds", "active_stream_seconds", "wall_stream_seconds"):
                    self.assertIsNone(trace[key])
                self.assertEqual(self.receipts, [])
                self.assertNotIn("reported_usage", self.job)
                self.assertNotIn("ai_trace", self.job)
                self.assertNotIn("ai_outputs", self.job["checkpoint"])

    def test_post_open_context_entry_failure_closes_response_without_transport_conversion(self):
        error = OSError("PRIVATE entry failure")
        with patch.object(Stream, "__enter__", side_effect=error), self.assertRaises(OSError) as raised:
            self.run_stream()
        self.assertIs(raised.exception, error)
        self.assertTrue(self.stream.closed)
        self.assertEqual(self.stream.close_calls, 1)
        self.assertEqual(self.opens, 1)
        self.assertIs(self.telemetry[0]["terminal_retained"], False)
        self.assertEqual(self.telemetry[0]["lines"], 0)
        self.assertEqual(self.telemetry[0]["failure"], {"category": "callback_or_unclassified"})
        self.assertNotIn("PRIVATE", json.dumps(self.telemetry))
        self.assertEqual(self.receipts, [])
        self.assertNotIn("reported_usage", self.job)

    def test_post_open_cleanup_failure_cannot_replace_primary_clock_failure(self):
        with patch.object(Stream, "close", side_effect=OSError("PRIVATE cleanup failure")) as close, \
                self.assertRaises(reader.StreamClockError):
            self.run_stream(on_open=lambda: setattr(self.clock, "value", float("nan")))
        close.assert_called_once_with()
        self.assertEqual(self.opens, 1)
        self.assertIs(self.telemetry[0]["terminal_retained"], False)
        self.assertEqual(self.telemetry[0]["failure"], {"category": "clock"})
        self.assertFalse(self.telemetry[0]["clock_valid"])
        self.assertNotIn("PRIVATE", json.dumps(self.telemetry))
        self.assertEqual(self.receipts, [])
        self.assertNotIn("reported_usage", self.job)

    def test_mutated_secondary_diagnostic_is_sanitized_and_redirect_phase_is_request(self):
        error=reader.TelemetryPersistenceError(None)
        error.primary={"category":"ai_transport","code":"PRIVATE","phase":"PRIVATE","body":"PRIVATE"}
        self.assertNotIn("PRIVATE",json.dumps(reader.failure_projection(error)))
        with self.assertRaises(ProviderTransportError):
            self.run_stream(open_error=ProviderTransportError("ai_transport_redirect"))
        self.assertEqual(self.telemetry[0]["failure"],
            {"category":"ai_transport","code":"ai_transport_redirect","phase":"request"})

    def test_entered_response_exit_failure_preserves_primary_transport_clock_and_integrity(self):
        for category in ("ai_transport", "clock", "integrity"):
            with self.subTest(category=category):
                self.setUp()
                lines, seen = None, []
                if category == "ai_transport":
                    lines = [TimeoutError("PRIVATE primary transport")]
                    expected_type = ProviderTransportError
                elif category == "clock":
                    self.light.side_effect = lambda: setattr(self.clock, "value", float("nan"))
                    expected_type = reader.StreamClockError
                else:
                    def full():
                        if self.receipts: raise EvaluationStopped("PRIVATE primary integrity")
                    self.full.side_effect = full
                    expected_type = EvaluationStopped
                def exit_failure(stream, *info):
                    seen.append(info)
                    stream.close()
                    raise OSError("PRIVATE secondary cleanup")
                with patch.object(Stream, "__exit__", exit_failure), self.assertRaises(BaseException) as raised:
                    self.run_stream(lines)
                self.assertIsInstance(raised.exception, expected_type)
                self.assertEqual(len(seen), 1)
                self.assertIs(seen[0][0], expected_type)
                self.assertIs(seen[0][1], raised.exception)
                self.assertIsNotNone(seen[0][2])
                self.assertTrue(self.stream.entered)
                self.assertTrue(self.stream.closed)
                self.assertEqual(self.stream.close_calls, 1)
                trace = self.telemetry[0]
                self.assertEqual(trace["failure"]["category"], category)
                if category == "ai_transport":
                    self.assertEqual(trace["failure"]["code"], "ai_transport_timeout")
                    self.assertEqual(trace["failure"]["phase"], "request")
                self.assertIs(trace["terminal_retained"], category == "integrity")
                self.assertEqual(len(self.receipts), int(category == "integrity"))
                self.assertEqual(self.opens, 1)
                self.assertEqual(len(self.charges), 1)
                self.assertTrue(trace["reservation_committed"])
                self.assertNotIn("PRIVATE", json.dumps(trace))
                self.assertNotIn("reported_usage", self.job)
                self.assertNotIn("ai_trace", self.job)
                self.assertNotIn("ai_outputs", self.job["checkpoint"])

    def test_entered_response_exit_failure_without_primary_is_global_before_usage(self):
        error, seen = OSError("PRIVATE cleanup only"), []
        def exit_failure(stream, *info):
            seen.append(info)
            stream.close()
            raise error
        with patch.object(Stream, "__exit__", exit_failure), self.assertRaises(OSError) as raised:
            self.run_stream()
        self.assertIs(raised.exception, error)
        self.assertEqual(seen, [(None, None, None)])
        self.assertTrue(self.stream.closed)
        self.assertEqual(self.stream.close_calls, 1)
        self.assertTrue(self.telemetry[0]["terminal_retained"])
        self.assertEqual(self.telemetry[0]["failure"], {"category": "callback_or_unclassified"})
        self.assertNotIn("PRIVATE", json.dumps(self.telemetry))
        self.assertEqual(len(self.receipts), 1)
        self.assertEqual(len(self.charges), 1)
        self.assertNotIn("reported_usage", self.job)
        self.assertNotIn("ai_trace", self.job)
        self.assertNotIn("ai_outputs", self.job["checkpoint"])

    def test_entered_response_exit_cannot_suppress_primary_global_failure(self):
        seen = []
        def suppress(stream, *info):
            seen.append(info)
            stream.close()
            return True
        with patch.object(Stream, "__exit__", suppress), self.assertRaises(BaseException) as raised:
            self.run_stream([TimeoutError("PRIVATE primary transport")])
        self.assertIsInstance(raised.exception, ProviderTransportError)
        self.assertEqual(raised.exception.code, "ai_transport_timeout")
        self.assertIs(seen[0][1], raised.exception)
        self.assertTrue(self.stream.closed)
        self.assertEqual(self.stream.close_calls, 1)
        self.assertEqual(self.telemetry[0]["failure"]["code"], "ai_transport_timeout")
        self.assertIs(self.telemetry[0]["terminal_retained"], False)
        self.assertEqual(self.receipts, [])
        self.assertNotIn("reported_usage", self.job)


if __name__ == "__main__": unittest.main()
