"""Offline checkpoint engine for a separately reviewed transport successor.

No provider, credential, database, thread or filesystem activity on import.
Scheduling changes the detection boundary; it is not a drop-in replacement for
the consumed reader's per-line contract. Live ownership wiring is separate.
"""
from dataclasses import dataclass
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
import codecs
import hashlib
import math
from pathlib import Path
import re
from threading import Event
import time


class CheckpointFailure(RuntimeError):
    """Global integrity, lifecycle or clock failure; never candidate-local."""


@dataclass(frozen=True)
class FilePin:
    path: Path
    sha256: str
    canonical_lf: bool = False


class PinnedFiles:
    """Hash each distinct path once per audit, without stat/mtime caching.

The caller supplies independently trusted digests. This checks content only;
inventory, held leases, original DB and manifest relationships need their own
    checks. All pins are copied into an immutable tuple before any stream starts.
    At most eight worker batches are outstanding, each reading one file at a
    time. All workers join before returning
    or raising; nothing keeps reading after a failed audit has returned.
"""
    def __init__(self, pins):
        grouped = {}
        for pin in tuple(pins):
            if (type(pin) is not FilePin or not isinstance(pin.path, Path)
                    or not pin.path.is_absolute() or '..' in pin.path.parts
                    or type(pin.sha256) is not str
                    or not re.fullmatch(r'[a-f0-9]{64}', pin.sha256)
                    or type(pin.canonical_lf) is not bool):
                raise ValueError('Invalid immutable file pin.')
            modes = grouped.setdefault(pin.path, {})
            if pin.canonical_lf in modes and modes[pin.canonical_lf] != pin.sha256:
                raise ValueError('Conflicting immutable file pins.')
            modes[pin.canonical_lf] = pin.sha256
        if not grouped:
            raise ValueError('Empty integrity inventory.')
        self._pins = tuple((path, tuple(modes.items())) for path, modes in grouped.items())

    @staticmethod
    def _verify_one(pin):
        path, modes = pin
        hashes = {canonical: hashlib.sha256() for canonical, _ in modes}
        decoder = codecs.getincrementaldecoder('utf-8')() if True in hashes else None
        pending_cr = False

        def canonical_chunk(raw, *, final=False):
            nonlocal pending_cr
            text = ('\r' if pending_cr else '') + decoder.decode(raw, final=final)
            pending_cr = not final and text.endswith('\r')
            if pending_cr:
                text = text[:-1]
            hashes[True].update(text.replace('\r\n', '\n').replace('\r', '\n').encode('utf-8'))

        with path.open('rb') as stream:
            while chunk := stream.read(65536):
                if False in hashes:
                    hashes[False].update(chunk)
                if decoder is not None:
                    canonical_chunk(chunk)
        if decoder is not None:
            canonical_chunk(b'', final=True)
        for canonical, expected in modes:
            if hashes[canonical].hexdigest() != expected:
                raise CheckpointFailure('Pinned content changed.')

    def verify(self):
        if len(self._pins) == 1:
            self._verify_one(self._pins[0])
            return
        stopped = Event()
        workers = min(8, len(self._pins))

        def verify_batch(batch):
            try:
                for pin in batch:
                    if stopped.is_set():
                        return
                    self._verify_one(pin)
            except BaseException:
                stopped.set()
                raise

        with ThreadPoolExecutor(max_workers=8, thread_name_prefix='checkpoint-audit') as pool:
            pending = {pool.submit(verify_batch, self._pins[n::workers]) for n in range(workers)}
            try:
                while pending:
                    done, pending = wait(pending, return_when=FIRST_COMPLETED)
                    for future in done:
                        future.result()
            except BaseException:
                stopped.set()
                for future in pending:
                    future.cancel()
                raise  # The context manager joins all running reads first.


class CheckpointCadence:
    """Single-owner, fail-stop checks with forced start/end barriers.

fast: cancellation, held lease identity, bounded cached account identity and
      in-memory request/config bindings, with no historical hashing.
critical: code, owned anchors/evidence/inventory/journal content checks.
history: complete original DB/prefix, protected history and Git/tree checks.

Critical checks are due after 1 second, history after 30 seconds, measured from
their last successful completion. Every barrier does critical/history/critical
regardless of freshness. Call poll before AND after every returned stream read.
No callback may suppress a failure and continue this same controller.
"""
    CRITICAL_SECONDS = 1.0
    HISTORY_SECONDS = 30.0

    def __init__(self, *, fast, critical, history, clock=time.monotonic):
        if not all(callable(callback) for callback in (fast, critical, history, clock)):
            raise TypeError('Explicit checkpoint callbacks and clock required.')
        self._callbacks = {'fast': fast, 'critical': critical, 'history': history}
        self._clock = clock
        self._last = self._critical_at = self._history_at = None
        self._clock_valid = True
        self._state, self._failure, self._busy = 'new', None, False
        self._counts = {name: 0 for name in self._callbacks}
        self._seconds = {name: 0.0 for name in self._callbacks}

    def _now(self):
        try:
            value = self._clock()
        except BaseException:
            self._clock_valid = False
            raise
        if self._failure is not None:
            self._clock_valid = False
            raise self._failure
        if (type(value) not in (int, float) or not math.isfinite(value)
                or (self._last is not None and value < self._last)):
            self._clock_valid = False
            raise CheckpointFailure('Invalid checkpoint clock.')
        self._last = value
        return value

    def _invoke(self, name):
        start = self._now()
        self._counts[name] += 1
        primary = None
        try:
            self._callbacks[name]()
            if self._failure is not None:  # A callback caught a reentrant failure.
                raise self._failure
        except BaseException as exc:
            primary = exc
            raise
        finally:
            try:
                self._seconds[name] += self._now() - start
            except BaseException:
                if primary is None:
                    raise
        return self._last

    def _critical(self):
        self._invoke('fast')
        self._critical_at = self._invoke('critical')
        self._invoke('fast')

    def _barrier(self):
        self._critical()
        self._history_at = self._invoke('history')
        # Check immediate state and code again after a potentially long audit.
        self._critical()

    def _perform(self, operation):
        if self._failure is not None:
            raise self._failure
        if self._busy:
            self._failure = CheckpointFailure('Reentrant checkpoint operation.')
            self._state = 'failed'
            raise self._failure
        self._busy = True
        try:
            operation()
            if self._failure is not None:
                raise self._failure
        except BaseException as exc:
            self._failure, self._state = exc, 'failed'
            raise
        finally:
            self._busy = False

    def start(self):
        def operation():
            if self._state != 'new':
                raise CheckpointFailure('Checkpoint controller already consumed.')
            self._barrier()
            self._state = 'streaming'
        self._perform(operation)

    def poll(self):
        def operation():
            if self._state != 'streaming':
                raise CheckpointFailure('Stream checkpoint outside active lifecycle.')
            self._invoke('fast')
            now = self._now()
            # Expensive history cannot be starved by frequent critical checks.
            if now - self._history_at >= self.HISTORY_SECONDS:
                self._barrier()
            elif now - self._critical_at >= self.CRITICAL_SECONDS:
                self._critical()
        self._perform(operation)

    def barrier(self):
        """Mandatory before/after owned writes and before any output acceptance."""
        def operation():
            if self._state != 'streaming':
                raise CheckpointFailure('Forced barrier outside active lifecycle.')
            self._barrier()
        self._perform(operation)

    def finish(self):
        """Force a fresh full audit; success closes this one-shot controller."""
        def operation():
            if self._state != 'streaming':
                raise CheckpointFailure('Checkpoint controller is not streaming.')
            self._barrier()
            self._state = 'finished'
        self._perform(operation)

    def snapshot(self):
        """No clock read, paths, upstream content or exception messages."""
        bound = 32_000_032
        saturated = any(v > bound for v in self._counts.values()) or any(v > 86400 for v in self._seconds.values())
        return {'version': 1, 'state': self._state, 'clock_valid': self._clock_valid,
                'counts': {k: min(bound, v) for k, v in self._counts.items()},
                'seconds': {k: min(86400, v) if self._clock_valid else None for k, v in self._seconds.items()},
                'saturated': saturated}
