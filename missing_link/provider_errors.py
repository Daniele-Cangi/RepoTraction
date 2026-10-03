"""Fixed transport diagnostics, never raw exceptions, bodies or credentials."""
from __future__ import annotations


MESSAGES = {
    "ai_transport_timeout": "AI transport timed out; no complete response receipt is available.",
    "ai_transport_network_error": "AI network request failed; no complete response receipt is available.",
    "ai_transport_io_error": "AI transport I/O failed; no complete response receipt is available.",
    "ai_transport_protocol_error": "AI transport could not process the request or response.",
    "ai_transport_http_error": "AI endpoint returned an HTTP error; no response body or credentials are logged.",
    "ai_transport_redirect": "AI endpoint redirects are not permitted.",
    "ai_transport_invalid_json": "AI transport returned invalid JSON; no complete response receipt is available.",
    "ai_transport_invalid_response": "AI transport response must be an object.",
    "ai_transport_size_exceeded": "AI response size exceeded.",
    "ai_stream_deadline_exceeded": "AI stream time limit exceeded; partial analysis is discarded.",
    "ai_stream_invalid_event": "AI stream event is malformed; partial analysis is discarded.",
    "ai_stream_missing_terminal": "AI stream ended without a complete response; partial analysis is discarded.",
}


class ProviderTransportError(RuntimeError):
    """Global job stop, distinct from candidate-local output validation."""

    def __init__(self, code, *, phase="analysis", http_status=None):
        self.code = code if code in MESSAGES else "ai_transport_protocol_error"
        self.phase = phase if phase in {"analysis", "capabilities", "request", "matches"} else "analysis"
        self.http_status = http_status if type(http_status) is int and 100 <= http_status <= 599 else None
        message = MESSAGES[self.code]
        if self.http_status is not None and self.code == "ai_transport_http_error":
            message = f"AI endpoint returned HTTP {self.http_status}; no response body or credentials are logged."
        super().__init__(message + " Reserved budget remains charged conservatively. No automatic retry.")

    def diagnostic(self):
        result = {"category": "ai_transport", "code": self.code, "phase": self.phase,
            "reservation_retained": True, "response_receipt": "unavailable"}
        if self.http_status is not None and self.code == "ai_transport_http_error":
            result["http_status"] = self.http_status
        return result
