"""Deadline reproduction against the frozen reader, no sockets or original state."""
import subprocess
import sys
import unittest
from unittest.mock import patch

from missing_link.service import Cancelled
from scripts import missing_link_stream_checkpoint_diagnostics as diagnostics


class StreamCheckpointDiagnosticsTests(unittest.TestCase):
    def test_fixed_controls_are_credential_free_and_network_free(self):
        with patch("missing_link.provider.provider_environment", side_effect=AssertionError("No keys")):
            controls = diagnostics.authored_controls()
        for result in controls.values():
            self.assertEqual(result["actual_network_calls"], 0)
            self.assertEqual(result["mock_open_invocations"], 1)
            self.assertEqual(result["synthetic_reservations"], 1)
        self.assertTrue(controls["buffered_fast_61_pairs"]["parsed_output"])
        self.assertEqual(controls["buffered_fast_61_pairs"]["stream_checkpoints"], 122)
        self.assertEqual(controls["buffered_fast_61_pairs"]["last_read_virtual_seconds"], 0)

    def test_deadline_boundary_accepts_240_but_local_guards_expire_buffered_stream(self):
        controls = diagnostics.authored_controls()
        boundary = controls["buffered_guard_1s_60_pairs"]
        self.assertTrue(boundary["terminal_retained"])
        self.assertTrue(boundary["parsed_output"])
        self.assertEqual(boundary["last_read_virtual_seconds"], 240)
        expired = controls["buffered_guard_1s_61_pairs"]
        self.assertEqual(expired["transport_code"], "ai_stream_deadline_exceeded")
        self.assertEqual(expired["last_read_virtual_seconds"], 242)
        self.assertEqual(expired["stream_checkpoints"], 121)
        self.assertFalse(expired["terminal_retained"])
        self.assertFalse(expired["parsed_output"])
        self.assertEqual(expired["synthetic_usage_records"], 0)

    def test_five_second_guards_expire_after_25_nonterminal_checkpoints(self):
        result = diagnostics.authored_controls()["buffered_guard_5s_13_pairs"]
        self.assertEqual(result["transport_code"], "ai_stream_deadline_exceeded")
        self.assertEqual(result["stream_checkpoints"], 25)
        self.assertEqual(result["last_read_virtual_seconds"], 250)
        self.assertFalse(result["terminal_retained"])

    def test_slow_read_can_produce_same_code_without_local_delay(self):
        result = diagnostics.authored_controls()["slow_read_terminal"]
        self.assertEqual(result["transport_code"], "ai_stream_deadline_exceeded")
        self.assertEqual(result["stream_checkpoints"], 0)
        self.assertEqual(result["last_read_virtual_seconds"], 241)
        self.assertFalse(result["terminal_retained"])

    def test_same_failure_class_has_distinct_codes_without_receipts_or_usage(self):
        controls = diagnostics.authored_controls()
        for name, code in (("missing_terminal", "ai_stream_missing_terminal"),
                           ("malformed_event", "ai_stream_invalid_event"),
                           ("open_timeout", "ai_transport_timeout"),
                           ("open_http_503", "ai_transport_http_error")):
            with self.subTest(name=name):
                result = controls[name]
                self.assertEqual(result["transport_code"], code)
                self.assertFalse(result["terminal_retained"])
                self.assertFalse(result["parsed_output"])
                self.assertEqual(result["synthetic_usage_records"], 0)
                self.assertEqual(result["http_status"], 503 if name == "open_http_503" else None)

    def test_guard_failure_is_not_swallowed_or_converted_to_transport(self):
        calls = 0

        def guard():
            nonlocal calls
            calls += 1
            if calls == 5:  # After reserve/pre-open checkpoints, during first delta.
                raise RuntimeError("Authored integrity failure")

        with self.assertRaisesRegex(RuntimeError, "Authored integrity failure"):
            diagnostics._exercise(diagnostics._deltas(1) + [diagnostics._terminal()], guard=guard)
        self.assertEqual(calls, 5)

    def test_cancellation_is_not_swallowed(self):
        with self.assertRaises(Cancelled):
            diagnostics._exercise([diagnostics._terminal()], cancelled=lambda: True)

    def test_import_does_not_read_configuration_open_files_or_start_network(self):
        code = '''from unittest.mock import patch
from contextlib import ExitStack
import scripts.missing_link_triage_receipts
with ExitStack() as stack:
    for target in ("builtins.open", "pathlib.Path.read_bytes", "pathlib.Path.read_text",
                   "missing_link.provider.provider_environment", "socket.socket",
                   "urllib.request.build_opener", "threading.Thread.start"):
        stack.enter_context(patch(target, side_effect=AssertionError(target)))
    import scripts.missing_link_stream_checkpoint_diagnostics
'''
        result = subprocess.run([sys.executable, "-c", code], cwd=diagnostics.ROOT,
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
