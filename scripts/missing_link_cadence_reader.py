"""Separate cadence reader; unchanged wire limits and native validation boundary."""
import copy
import hashlib
import json
import time
import urllib.request

from missing_link.analysis import digest
from missing_link.contracts import validate_shape
from missing_link.provider import NoRedirect, CandidateValidationError
from missing_link.provider_errors import ProviderTransportError
from scripts.missing_link_repository_only_evaluator import require
from scripts.missing_link_protected_operations import ProtectedOperations
from scripts.missing_link_triage_receipts import ReceiptPersistenceError
from scripts.missing_link_stream_successor_receipts import (
    _Timing, _io, _response_stream, failure_projection, TelemetryPersistenceError, StreamClockError)


class StreamTiming(_Timing):
    def now(self):
        try:
            return super().now()
        except BaseException:
            self.valid = False
            raise StreamClockError('Invalid stream clock.') from None


def complete_with_receipt(provider, slot, body, budget, *, checks, retain_terminal,
                          retain_telemetry, reservation_observed, before_open,
                          opener_factory=None, clock=time.monotonic, operations=None):
    """Consume a preverified immutable body once; no per-line encoding or 128-line gate.

    The caller binds slot/body/config before entry. Each actual fast/critical/
    historical callback is metered by Checks, including forced terminal barriers.
    Cleanup preserves the same primary exception and response ownership helpers.
    """
    timing, error = StreamTiming(clock), None
    try:
        require(operations is None or (type(operations) is ProtectedOperations and operations is checks),
                'Invalid protected reader ownership')
        require(type(body) is bytes and len(body) <= provider.max_bytes, 'Invalid bound request body')
        metadata, envelope = slot['metadata'], slot['envelope']
        require(hashlib.sha256(body).hexdigest() == metadata['native_sha256'] and len(body) == metadata['native_bytes'],
                'Bound native body changed')
        def reservation():
            budget.reserve_ai(metadata['reservation_usd'], provider.max_calls,
                              provider.max_cost if provider.remote else None)
            budget.checkpoint()
        if operations is None:
            reservation()
        else:
            operations.operation('reserve', reservation)
        headers = {'Content-Type': 'application/json'}
        if provider.key:
            headers['Authorization'] = 'Bearer ' + provider.key
        request = urllib.request.Request(provider.url + metadata['endpoint'], data=body, headers=headers, method='POST')
        opener = opener_factory() if opener_factory is not None else urllib.request.build_opener(NoRedirect())
        checks.barrier()
        before_open()  # Force account identity after reservation/persistence barriers.
        checks.poll()
        with _response_stream(opener, request, timing) as response:
            timing.start()
            terminal = None
            with checks.stream(timing):
                while True:
                    checks.poll()
                    timing.limits()
                    line = timing.measure('reading', lambda: _io(lambda: response.readline(512001)))
                    if line:
                        timing.counts['lines'] += 1
                        timing.counts['bytes'] += len(line)
                    checks.poll()
                    timing.limits()
                    if len(line) > 512000 or timing.counts['bytes'] > 8_000_000:
                        raise ProviderTransportError('ai_transport_size_exceeded', phase='request')
                    if not line:
                        raise ProviderTransportError('ai_stream_missing_terminal', phase='request')
                    if line.startswith(b'data: '):
                        try:
                            event = json.loads(line[6:])
                            if not isinstance(event, dict):
                                raise ValueError('Invalid event')
                            if event.get('type') in {'response.completed', 'response.failed', 'response.incomplete'}:
                                result = event['response']
                                if not isinstance(result, dict) or result.get('status') != event['type'].split('.', 1)[1]:
                                    raise ValueError('Inconsistent terminal')
                                terminal = event
                        except (KeyError, ValueError, TypeError):
                            raise ProviderTransportError('ai_stream_invalid_event', phase='request') from None
                    timing.limits()
                    if terminal is not None:
                        checks.barrier()
                        timing.receipt = None
                        try:
                            retain_terminal(copy.deepcopy(terminal))
                        except Exception:
                            raise ReceiptPersistenceError('Private terminal receipt could not be saved.') from None
                        timing.receipt = True
                        checks.barrier()
                        timing.limits()
                        timing.ended = timing.last
                        break
        # A terminal is evidence, not acceptance. Cleanup has finished and a
        # fresh barrier must pass before the first accounting/output mutation.
        def account():
            return _account_terminal(provider, slot, body, budget, checks, terminal,
                                     operations=operations)
        if operations is None:
            checks.barrier()
            return account()
        return operations.operation('account', account)
    except BaseException as exc:
        error = exc
        checks.abort(exc)
        raise
    finally:
        try:
            observed = reservation_observed()
            if observed is not None and type(observed) is not bool:
                raise ValueError('Reservation observation must be bool or null.')
            timing.reservation = observed
            cadence = checks.snapshot()
            if not cadence['clock_valid']:
                timing.valid = False
            trace = timing.snapshot(error)
            trace['cadence'] = cadence
            retain_telemetry(trace)
        except BaseException:
            failure = TelemetryPersistenceError(failure_projection(error))
            checks.abort(failure)
            raise failure from None


def _account_terminal(provider, slot, body, budget, checks, terminal, *, operations):
    """Same native/wire/schema checks; only explicit ownership changes guards."""
    def mutate(callback):
        return checks.write(callback) if operations is None else callback()
    result, envelope = terminal['response'], slot['envelope']
    usage = result.get('usage')
    tokens = (usage.get('input_tokens'), usage.get('output_tokens')) if isinstance(usage, dict) else (None, None)
    if not all(type(v) is int and v >= 0 for v in tokens):
        raise CandidateValidationError('Missing or invalid native usage.')
    mutate(lambda: budget.record_usage(*tokens,
        (tokens[0] * provider.input_price + tokens[1] * provider.output_price) / 1_000_000))
    mutate(lambda: budget.record_call({'phase': 'request', 'model': provider.model,
        'api_kind': provider.api_kind, 'response_id': str(result.get('id', ''))[:150],
        'response_status': str(result.get('status', ''))[:30], 'request_sha256': digest(slot['payload']),
        'request_bytes': len(body), 'context_coverage': envelope['context'].get('context_coverage', {})}))
    try:
        if result.get('status') != 'completed':
            raise ValueError('AI response is incomplete.')
        blocks = [part for item in result['output'] if item.get('type') == 'message' for part in item.get('content', [])]
        if any(part.get('type') == 'refusal' for part in blocks):
            raise ValueError('AI refused this analysis.')
        parsed = json.loads(''.join(part['text'] for part in blocks if part.get('type') == 'output_text'))
    except (KeyError, IndexError, TypeError, AttributeError, json.JSONDecodeError):
        raise CandidateValidationError('Malformed structured output.') from None
    except ValueError as exc:
        raise CandidateValidationError(str(exc)) from None
    mutate(lambda: budget.record_output('request', parsed))
    budget.checkpoint()
    try:
        if not isinstance(parsed, dict):
            raise ValueError('AI must return a JSON object.')
        if envelope['schema']:
            validate_shape(parsed, envelope['schema'])
    except ValueError as exc:
        raise CandidateValidationError(str(exc)) from None
    budget.checkpoint()
    return parsed
