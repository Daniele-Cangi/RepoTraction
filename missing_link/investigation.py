"""Opt-in HTTP observation policy; no import-time work or automatic retries."""
from __future__ import annotations

import http.client
import json
import os
from pathlib import Path
import re
import tempfile
import time
import urllib.error
import urllib.request
from urllib.parse import urlencode


class ObservationError(RuntimeError):
    def __init__(self, code, *, http_status=None):
        self.code = code
        self.http_status = http_status
        super().__init__("Local investigation observation stopped; inspect the saved job before any explicit retry.")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ObservationError("observer_protocol_error")


def local_request(base, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(base + path, data=data,
        headers={"Content-Type": "application/json", "Origin": base})
    with urllib.request.build_opener(NoRedirect()).open(req, timeout=30) as response:
        return json.load(response)


def _call(request, path, body=None):
    try:
        result = request(path, body) if body is not None else request(path)
        if not isinstance(result, dict):
            raise ObservationError("observer_protocol_error")
        return result
    except ObservationError:
        raise
    except urllib.error.HTTPError as exc:
        status = exc.code if type(exc.code) is int and 100 <= exc.code <= 599 else None
        raise ObservationError("observer_http_error", http_status=status) from None
    except TimeoutError:
        raise ObservationError("observer_timeout") from None
    except urllib.error.URLError as exc:
        code = "observer_timeout" if isinstance(exc.reason, TimeoutError) else "observer_network_error"
        raise ObservationError(code) from None
    except (OSError, http.client.HTTPException):
        raise ObservationError("observer_io_error") from None
    except (ValueError, KeyError, TypeError):
        raise ObservationError("observer_protocol_error") from None


class Report:
    """Own a new report before mutations; atomic updates never truncate it."""

    def __init__(self, path, payload):
        self.path = Path(path) if path else None
        self.payload = payload
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("x", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2, ensure_ascii=False)

    def save(self):
        if not self.path:
            return
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.path.parent, delete=False) as handle:
                temporary = Path(handle.name)
                json.dump(self.payload, handle, indent=2, ensure_ascii=False)
            os.replace(temporary, self.path)
        except OSError:
            raise ObservationError("observer_report_error") from None
        finally:
            if temporary and temporary.exists():
                try:
                    temporary.unlink()
                except OSError:
                    pass  # Only an owned incomplete report temp may remain.


def run_investigation(args, request, *, emit=print, monotonic=time.monotonic, sleep=time.sleep):
    """GET failure leaves the known backend alone; deadline requests cancellation once."""
    payload = {"context": "real_public_github_and_provider_api" if args.use_ai else "real_public_github_structural",
        "manual_analysis_imported": False, "repository": args.repo, "provider": None, "jobs": []}
    report = Report(args.report, payload)
    job_id, entry, phase = None, None, "preflight"

    def output(value):
        emit(json.dumps(value, ensure_ascii=False))

    try:
        state = _call(request, "/api/missing-link")
        if state.get("diagnostic_only") or not isinstance(state.get("provider"), dict):
            raise ObservationError("observer_identity_unverified")
        if args.use_ai and not state["provider"].get("configured"):
            raise ObservationError("observer_provider_unconfigured")
        payload["provider"] = state["provider"]
        report.save()
        resume = args.resume
        for issue_url in args.issue or [""]:
            phase, job_id = "start", None
            entry = {"job_id": None, "job": None, "matches": []}
            payload["jobs"].append(entry)
            report.save()
            if resume:
                previous_job = next((item for item in state.get("jobs", []) if item.get("id") == resume), None)
                if not previous_job or any(previous_job.get("input", {}).get(key) != value
                        for key, value in {"repo": args.repo, "issue_url": issue_url, "use_ai": args.use_ai}.items()):
                    phase = "preflight"
                    raise ObservationError("observer_resume_input_mismatch")
                job_id = resume
                entry["job_id"] = job_id
                report.save()
                started = _call(request, "/api/missing-link/resume", {"job_id": resume})
                resume = None
            else:
                started = _call(request, "/api/missing-link/jobs", {"repo": args.repo, "action": "discover",
                    "issue_url": issue_url, "query": args.query, "max_candidates": args.max_candidates,
                    "max_requests": 80, "use_ai": args.use_ai})
            job_id = started.get("job_id")
            if not isinstance(job_id, str) or not re.fullmatch(r"[0-9a-f]{32}", job_id):
                job_id = None
                raise ObservationError("observer_protocol_error")
            entry["job_id"] = job_id
            phase = "poll"
            output({"job_id": job_id, "issue": issue_url, "status": "started"})
            # Persist acknowledgement before the first GET; the job can outlive this driver.
            report.save()
            deadline, previous = monotonic() + 900, None
            while monotonic() < deadline:
                state = _call(request, "/api/missing-link")
                if state.get("diagnostic_only"):
                    raise ObservationError("observer_identity_unverified")
                job = next((item for item in state.get("jobs", []) if item.get("id") == job_id), None)
                if not isinstance(job, dict) or job.get("status") not in {"queued", "running", "completed", "failed", "paused", "cancelled"}:
                    raise ObservationError("observer_job_unavailable")
                result = job.get("result")
                if (not isinstance(result, dict) or not isinstance(result.get("match_ids"), list)
                        or any(not isinstance(value, str) or not value for value in result["match_ids"])):
                    raise ObservationError("observer_protocol_error")
                entry["job"] = job
                report.save()
                update = (job["status"], job.get("stage"), job.get("ai_calls_used"))
                if update != previous:
                    output({"job_id": job_id, "status": job["status"], "stage": job.get("stage"),
                        "ai_calls": job.get("ai_calls_used"), "reserved_usd": job.get("cost_reserved_usd")})
                    previous = update
                if job["status"] not in {"queued", "running"}:
                    break
                sleep(2)
            else:
                cancellation = "unconfirmed"
                try:
                    result = _call(request, "/api/missing-link/cancel", {"job_id": job_id})
                    cancelled_job = result.get("job")
                    if isinstance(cancelled_job, dict) and cancelled_job.get("id") == job_id and cancelled_job.get("status") == "cancelled":
                        cancellation = "acknowledged"
                except ObservationError:
                    cancellation = "failed"
                payload["cancellation"] = cancellation
                raise ObservationError("observer_deadline_exceeded")
            phase = "export"
            for match_id in job.get("result", {}).get("match_ids", []):
                exported = _call(request, "/api/missing-link/export?" + urlencode({"match_id": match_id}))
                entry["matches"].append(exported)
                report.save()
                output({"match_id": match_id, "classification": exported["match"]["classification"],
                    "analysis_source": exported["match"]["analysis_source"], "summary": exported["match"]["summary"]})
            if job["status"] != "completed" or job.get("result", {}).get("partial"):
                output({"error": job.get("error"), "candidate_errors": job.get("result", {}).get("candidate_errors", []),
                    "partial": bool(job.get("result", {}).get("partial")), "report": str(args.report) if args.report else None})
                return 1
        output({"completed": True, "report": str(args.report) if args.report else None})
        return 0
    except (ObservationError, KeyError, TypeError, AttributeError) as exc:
        code = exc.code if isinstance(exc, ObservationError) else "observer_protocol_error"
        terminal = entry and entry.get("job") and entry["job"]["status"] not in {"queued", "running"}
        payload["observation_failure"] = {"code": code, "phase": phase, "job_id": job_id,
            "backend_may_be_running": phase in {"start", "poll"} and not bool(terminal),
            "cancellation": payload.get("cancellation", "not_requested"), "automatic_retry": False,
            "message": "Observation is not a backend outcome. Inspect the known job before any explicit retry; no replacement was started."}
        if isinstance(exc, ObservationError) and exc.http_status is not None:
            payload["observation_failure"]["http_status"] = exc.http_status
        try:
            report.save()
        except ObservationError:
            payload["observation_failure"]["report_persisted"] = False
        output(payload["observation_failure"])
        return 1
