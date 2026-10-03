"""HTTP observer fixtures; no server, real store, GitHub or provider calls."""
import copy
import io
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import socket
import tempfile
import threading
from types import SimpleNamespace
import unittest
import urllib.error
from unittest import mock

from missing_link.investigation import ObservationError, Report, local_request, run_investigation


class InvestigationTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "new-report.json"
        self.args = SimpleNamespace(repo="example/words", issue=[], query="", max_candidates=3,
            use_ai=True, resume=None, report=self.path)
        self.job = {"id": "a" * 32, "status": "running", "stage": "requirements", "ai_calls_used": 1,
            "cost_reserved_usd": .1, "result": {"match_ids": []},
            "input": {"repo": "example/words", "issue_url": "", "use_ai": True}}
        self.initial = {"provider": {"configured": True, "model": "fixture"}, "jobs": []}
        self.messages = []

    def execute(self, outcomes, clock=None):
        request = mock.Mock(side_effect=outcomes)
        result = run_investigation(self.args, request, emit=self.messages.append,
            monotonic=mock.Mock(side_effect=clock or [0] * 20), sleep=mock.Mock())
        report = json.loads(self.path.read_text(encoding="utf-8"))
        return result, report, request

    def assert_no_replacement(self, request, *, mutations=1):
        posts = [call for call in request.call_args_list if len(call.args) > 1]
        self.assertEqual(len(posts), mutations)
        self.assertNotIn("private", "\n".join(self.messages))

    def test_poll_timeout_keeps_known_id_last_state_and_does_not_cancel_or_retry(self):
        self.args.issue = ["https://github.com/example/target/issues/1", "https://github.com/example/target/issues/2"]
        result, report, request = self.execute([self.initial, {"job_id": self.job["id"]},
            {"jobs": [self.job]}, socket.timeout("private prompt credential")])
        failure = report["observation_failure"]
        self.assertEqual(result, 1)
        self.assertEqual(failure["code"], "observer_timeout")
        self.assertEqual(failure["job_id"], self.job["id"])
        self.assertTrue(failure["backend_may_be_running"])
        self.assertEqual(failure["cancellation"], "not_requested")
        self.assertFalse(failure["automatic_retry"])
        self.assertEqual(report["jobs"][0]["job"], self.job)
        self.assertEqual(len(report["jobs"]), 1)
        self.assert_no_replacement(request)

    def test_id_is_already_on_disk_when_first_poll_fails(self):
        def failed_poll(*_args):
            saved = json.loads(self.path.read_text())
            self.assertEqual(saved["jobs"][0]["job_id"], self.job["id"])
            raise urllib.error.URLError("private network cause")
        request = mock.Mock()
        values = iter([self.initial, {"job_id": self.job["id"]}])
        def dispatch(*args):
            try:
                return next(values)
            except StopIteration:
                return failed_poll(*args)
        request.side_effect = dispatch
        self.assertEqual(run_investigation(self.args, request, emit=self.messages.append, monotonic=lambda: 0), 1)
        self.assertEqual(json.loads(self.path.read_text())["observation_failure"]["code"], "observer_network_error")
        self.assert_no_replacement(request)

    def test_unknown_start_response_never_creates_a_replacement(self):
        for response in (socket.timeout("private"), {"job_id": "private invalid"}):
            with self.subTest(response=type(response).__name__):
                self.path = self.path.with_name(self.path.stem + "-next.json")
                self.args.report = self.path
                result, report, request = self.execute([self.initial, response])
                self.assertEqual(result, 1)
                self.assertIsNone(report["observation_failure"]["job_id"])
                self.assertTrue(report["observation_failure"]["backend_may_be_running"])
                self.assert_no_replacement(request)

    def test_failed_resume_acknowledgement_keeps_original_id(self):
        self.args.resume = self.job["id"]
        self.job.update(status="paused", error="Fixture stop", error_diagnostic={"code": "fixture"})
        initial = dict(self.initial, jobs=[self.job])
        for response in (socket.timeout("private resume"), {}, {"job_id": "b" * 32}):
            with self.subTest(response=type(response).__name__):
                self.path = self.path.with_name(self.path.stem + "-next.json")
                self.args.report = self.path
                _, report, request = self.execute([initial, response])
                self.assertEqual(report["observation_failure"]["job_id"], self.job["id"])
                self.assertEqual(report["jobs"][0]["job_id"], self.job["id"])
                self.assertEqual(report["jobs"][0]["job"], self.job)
                self.assertEqual(request.call_args_list[1].args[0], "/api/missing-link/resume")
                self.assertTrue(report["observation_failure"]["backend_may_be_running"])
                self.assert_no_replacement(request)

    def test_resume_snapshot_is_on_disk_before_post_and_remains_unknown_after_failed_poll(self):
        self.args.resume = self.job["id"]
        self.job.update(status="paused", error="Fixture stop", error_diagnostic={"code": "fixture"})
        previous = copy.deepcopy(self.job)
        calls = []
        def request(path, body=None):
            calls.append((path, body))
            if len(calls) == 1:
                return dict(self.initial, jobs=[self.job])
            if body is not None:
                saved = json.loads(self.path.read_text())
                self.assertEqual(saved["jobs"][0]["job"], previous)
                # The captured snapshot cannot become the mutable post-resume state.
                self.job.update(status="running", error=None, cost_reserved_usd=.2)
                return {"job_id": previous["id"]}
            raise socket.timeout("private poll")
        self.assertEqual(run_investigation(self.args, request, emit=self.messages.append, monotonic=lambda: 0), 1)
        report = json.loads(self.path.read_text())
        self.assertEqual(report["jobs"][0]["job"], previous)
        self.assertTrue(report["observation_failure"]["backend_may_be_running"])
        self.assertEqual(report["observation_failure"]["phase"], "poll")
        self.assertEqual(sum(body is not None for _, body in calls), 1)

    def test_fresh_post_resume_observation_replaces_preflight_snapshot(self):
        self.args.resume = self.job["id"]
        self.job.update(status="paused", error="Fixture stop")
        resumed = dict(self.job, status="completed", error=None, stage="completed", ai_calls_used=2, cost_reserved_usd=.2)
        result, report, request = self.execute([dict(self.initial, jobs=[self.job]),
            {"job_id": self.job["id"]}, {"jobs": [resumed]}])
        self.assertEqual(result, 0)
        self.assertEqual(report["jobs"][0]["job"], resumed)
        self.assert_no_replacement(request)

    def test_resume_mismatch_does_not_mutate(self):
        self.args.resume = self.job["id"]
        _, report, request = self.execute([self.initial])
        self.assertEqual(report["observation_failure"]["code"], "observer_resume_input_mismatch")
        self.assertFalse(report["observation_failure"]["backend_may_be_running"])
        self.assert_no_replacement(request, mutations=0)

    def test_deadline_requests_cancellation_once_but_does_not_certify_worker_exit(self):
        for response, expected in (({"job": {"id": self.job["id"], "status": "cancelled"}}, "acknowledged"),
                ({"job": None}, "unconfirmed"), ({}, "unconfirmed"),
                ({"job": {"id": "wrong", "status": "cancelled"}}, "unconfirmed")):
            with self.subTest(expected=expected, response=response):
                self.path = self.path.with_name(self.path.stem + "-next.json")
                self.args.report = self.path
                _, report, request = self.execute([self.initial, {"job_id": self.job["id"]}, response], clock=[0, 901])
                self.assertEqual(report["observation_failure"]["code"], "observer_deadline_exceeded")
                self.assertEqual(report["observation_failure"]["cancellation"], expected)
                self.assertTrue(report["observation_failure"]["backend_may_be_running"])
                self.assertEqual(request.call_args_list[-1].args[0], "/api/missing-link/cancel")
                self.assert_no_replacement(request, mutations=2)

    def test_failed_deadline_cancellation_is_not_reported_as_cancelled(self):
        _, report, request = self.execute([self.initial, {"job_id": self.job["id"]},
            socket.timeout("private cancellation")], clock=[0, 901])
        self.assertEqual(report["observation_failure"]["cancellation"], "failed")
        self.assertTrue(report["observation_failure"]["backend_may_be_running"])
        self.assert_no_replacement(request, mutations=2)

    def test_diagnostic_only_and_missing_jobs_stop_without_export(self):
        for state, code in (({"diagnostic_only": True}, "observer_identity_unverified"),
                ({"jobs": []}, "observer_job_unavailable"),
                ({"jobs": [dict(self.job, status="completed", result=None)]}, "observer_protocol_error")):
            with self.subTest(code=code):
                self.path = self.path.with_name(self.path.stem + "-next.json")
                self.args.report = self.path
                _, report, request = self.execute([self.initial, {"job_id": self.job["id"]}, state])
                self.assertEqual(report["observation_failure"]["code"], code)
                self.assert_no_replacement(request)

    def test_preflight_failure_never_submits_a_job(self):
        error = urllib.error.HTTPError("private url", 409, "private header", {}, io.BytesIO(b"private body"))
        _, report, request = self.execute([error])
        self.assertEqual(report["observation_failure"]["http_status"], 409)
        self.assertFalse(report["observation_failure"]["backend_may_be_running"])
        self.assert_no_replacement(request, mutations=0)

    def test_export_failure_keeps_terminal_job_and_previous_exports(self):
        job = copy.deepcopy(self.job)
        job.update(status="completed", result={"match_ids": ["first", "second"]})
        exported = {"match": {"classification": "investigate", "analysis_source": "fixture", "summary": "Fixture"}}
        _, report, request = self.execute([self.initial, {"job_id": job["id"]}, {"jobs": [job]},
            exported, urllib.error.URLError("private export")])
        self.assertFalse(report["observation_failure"]["backend_may_be_running"])
        self.assertEqual(report["jobs"][0]["matches"], [exported])
        self.assertEqual(report["jobs"][0]["job"], job)
        self.assert_no_replacement(request)

    def test_completed_and_backend_failed_outcomes_remain_distinct_from_observer_failure(self):
        for status, partial, code in (("completed", False, 0), ("completed", True, 1), ("failed", False, 1)):
            with self.subTest(status=status, partial=partial):
                self.path = self.path.with_name(self.path.stem + "-next.json")
                self.args.report = self.path
                job = dict(self.job, status=status, result={"match_ids": [], "partial": partial})
                result, report, request = self.execute([self.initial, {"job_id": job["id"]}, {"jobs": [job]}])
                self.assertEqual(result, code)
                self.assertNotIn("observation_failure", report)
                self.assertEqual(report["jobs"][0]["job"], job)
                self.assert_no_replacement(request)

    def test_existing_report_is_protected_before_any_request(self):
        self.path.write_text("frozen report", encoding="utf-8")
        request = mock.Mock()
        with self.assertRaises(FileExistsError):
            run_investigation(self.args, request)
        request.assert_not_called()
        self.assertEqual(self.path.read_text(), "frozen report")

    def test_report_write_failure_keeps_known_id_in_console_and_stops(self):
        request = mock.Mock(side_effect=[self.initial, {"job_id": self.job["id"]}])
        with mock.patch.object(Report, "save", side_effect=[None, None,
                ObservationError("observer_report_error"), ObservationError("observer_report_error")]):
            self.assertEqual(run_investigation(self.args, request, emit=self.messages.append), 1)
        failure = json.loads(self.messages[-1])
        self.assertEqual(failure["code"], "observer_report_error")
        self.assertEqual(failure["job_id"], self.job["id"])
        self.assertFalse(failure["report_persisted"])
        self.assertTrue(failure["backend_may_be_running"])
        self.assert_no_replacement(request)

    def test_local_request_keeps_socket_bound_origin_and_redirect_denial(self):
        opener, response = mock.Mock(), mock.MagicMock()
        response.__enter__.return_value.read.return_value = b'{}'
        opener.open.return_value = response
        with mock.patch("urllib.request.build_opener", return_value=opener) as build:
            self.assertEqual(local_request("http://127.0.0.1:8765", "/api/missing-link"), {})
        self.assertEqual(opener.open.call_args.kwargs["timeout"], 30)
        self.assertEqual(opener.open.call_args.args[0].get_header("Origin"), "http://127.0.0.1:8765")
        with self.assertRaises(RuntimeError):
            build.call_args.args[0].redirect_request(None, None, 302, "", {}, "https://private.example")

    def test_actual_http_protocol_failure_keeps_acknowledged_job_without_replacement(self):
        requests = []
        initial, identity = self.initial, self.job["id"]
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def reply(self, raw):
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def do_GET(self):
                requests.append(("GET", self.path))
                raw = json.dumps(initial).encode() if len(requests) == 1 else b"private malformed response"
                self.reply(raw)

            def do_POST(self):
                requests.append(("POST", self.path))
                self.rfile.read(int(self.headers["Content-Length"]))
                self.reply(json.dumps({"job_id": identity}).encode())

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            base = f"http://127.0.0.1:{server.server_port}"
            result = run_investigation(self.args, lambda path, body=None: local_request(base, path, body),
                emit=self.messages.append, monotonic=lambda: 0)
        finally:
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()
        self.assertEqual(result, 1)
        report = json.loads(self.path.read_text())
        self.assertEqual(report["observation_failure"]["job_id"], identity)
        self.assertEqual(report["observation_failure"]["code"], "observer_protocol_error")
        self.assertTrue(report["observation_failure"]["backend_may_be_running"])
        self.assertEqual(requests, [("GET", "/api/missing-link"), ("POST", "/api/missing-link/jobs"),
            ("GET", "/api/missing-link")])
        self.assertNotIn("private", "\n".join(self.messages))


if __name__ == "__main__":
    unittest.main()
