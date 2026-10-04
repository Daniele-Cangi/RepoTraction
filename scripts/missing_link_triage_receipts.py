"""Opt-in experimental Responses stream reader; no production imports this module.

Keep the frozen production Provider untouched. Reuse its encoding, limits, redirect
policy, errors and Budget contract, but save the complete terminal event before
interpreting output. The caller must store receipts privately, not in job/UI data.
"""
import copy
import http.client
import json
import time
import urllib.error
import urllib.request

from missing_link.analysis import digest
from missing_link.contracts import validate_shape
from missing_link.provider import NoRedirect, ResponseError, CandidateValidationError


class ReceiptPersistenceError(RuntimeError):
    """Private terminal storage failed; no acceptance or continuation is allowed."""


def complete_with_receipt(provider, instruction, data, budget, *, schema, retain_terminal,
                          phase="analysis"):
    """One bounded request, no retry. Receipt/persistence errors stop the caller.

Only a status-consistent terminal event is a receipt. Preserve its entire decoded
JSON (not wire whitespace or prior deltas), including incomplete/failed/refused
content. Acceptance and native-usage accounting remain separate from preservation.
"""
    if not provider.describe()["configured"]:
        raise ValueError(provider.error or "Configure an interpretive provider.")
    if provider.api_kind != "responses" or not provider.streaming:
        raise ValueError("Experimental receipts require Responses streaming.")
    endpoint, payload, body = provider._encode_prompt(instruction, data, schema, phase)
    if len(body) > provider.max_bytes:
        raise ValueError("Source context exceeds AI prompt bound.")
    reserved = ((len(body) + 2048) * provider.input_price + provider.max_tokens * provider.output_price) / 1_000_000
    budget.reserve_ai(reserved, provider.max_calls, provider.max_cost if provider.remote else None)
    headers = {"Content-Type": "application/json"}
    if provider.key:
        headers["Authorization"] = "Bearer " + provider.key
    budget.checkpoint()
    request = urllib.request.Request(provider.url + endpoint, data=body, headers=headers, method="POST")
    opener = urllib.request.build_opener(NoRedirect())
    try:
        with opener.open(request, timeout=55) as response:
            received, terminal = 0, None
            deadline = time.monotonic() + 240
            while line := response.readline(512001):
                received += len(line)
                if received > 8_000_000 or len(line) > 512000:
                    raise ResponseError("ai_transport_size_exceeded", phase=phase)
                if time.monotonic() > deadline:
                    raise ResponseError("ai_stream_deadline_exceeded", phase=phase)
                if not line.startswith(b"data: "):
                    budget.checkpoint()
                    continue
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
                    budget.checkpoint()
                    raise ResponseError("ai_stream_invalid_event", phase=phase) from None
                if terminal is not None:
                    # Before stream close, parsing, accounting or acceptance. Do
                    # not convert a storage failure into a candidate/HTTP error.
                    try:
                        retain_terminal(copy.deepcopy(terminal))
                    except Exception:
                        raise ReceiptPersistenceError("Private terminal receipt could not be saved.") from None
                    break
                budget.checkpoint()
            if terminal is None:
                raise ResponseError("ai_stream_missing_terminal", phase=phase)
    except ResponseError as exc:
        exc.phase = phase if phase in {"analysis", "capabilities", "request", "matches"} else "analysis"
        raise
    except urllib.error.HTTPError as exc:
        raise ResponseError("ai_transport_http_error", phase=phase, http_status=exc.code) from None
    except TimeoutError:
        raise ResponseError("ai_transport_timeout", phase=phase) from None
    except urllib.error.URLError as exc:
        code = "ai_transport_timeout" if isinstance(exc.reason, TimeoutError) else "ai_transport_network_error"
        raise ResponseError(code, phase=phase) from None
    except (OSError, http.client.HTTPException):
        raise ResponseError("ai_transport_io_error", phase=phase) from None
    result = terminal["response"]
    usage = result.get("usage")
    if isinstance(usage, dict):
        tokens = (usage.get("input_tokens"), usage.get("output_tokens"))
        if all(isinstance(v, int) and not isinstance(v, bool) and v >= 0 for v in tokens):
            budget.record_usage(*tokens, (tokens[0] * provider.input_price + tokens[1] * provider.output_price) / 1_000_000)
    budget.record_call({"phase": phase, "model": provider.model, "api_kind": provider.api_kind,
        "response_id": str(result.get("id", ""))[:150], "response_status": str(result.get("status", ""))[:30],
        "request_sha256": digest(payload), "request_bytes": len(body),
        "context_coverage": data.get("context_coverage", {})})
    try:
        if result.get("status") != "completed":
            raise ValueError("AI response is incomplete; no partial analysis is accepted.")
        blocks = [part for item in result["output"] if item.get("type") == "message" for part in item.get("content", [])]
        if any(part.get("type") == "refusal" for part in blocks):
            raise ValueError("AI refused this analysis; no compatibility result was stored.")
        parsed = json.loads("".join(part["text"] for part in blocks if part.get("type") == "output_text"))
    except (KeyError, IndexError, TypeError, AttributeError, json.JSONDecodeError):
        raise CandidateValidationError("AI returned malformed structured output; no partial analysis is accepted.") from None
    except ValueError as exc:
        raise CandidateValidationError(str(exc)) from None
    budget.record_output(phase, parsed)
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
