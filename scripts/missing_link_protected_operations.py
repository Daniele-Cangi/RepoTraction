"""Explicit single-owner mutation units, fresh full boundaries, no import IO."""
from threading import Lock, get_ident

from scripts.missing_link_cadence_checks import Checks
from scripts.missing_link_checkpoint_cadence import CheckpointFailure


STEPS = (('claim', ('claim',)),
         ('reserve', ('reservation', 'checkpoint')),
         ('account', ('checkpoint', 'checkpoint', 'checkpoint')),
         ('validate', ('result',)),
         ('telemetry', ('telemetry',)),
         ('finish', ('finish',)))


class _OwnedStream:
    """Check exit ownership before consuming the owner's cleanup opportunity."""
    def __init__(self, checks, timing):
        self._checks, self._timing, self._state = checks, timing, 'new'

    def __enter__(self):
        def attach():
            if self._state != 'new' or self._checks.timing is not None:
                self._checks._reject('Invalid or overlapping stream context')
            self._state = 'active'
            self._checks.timing = self._timing
        return self._checks._perform(attach)

    def __exit__(self, kind, error, traceback):
        self._checks._check_owner()  # A rejected exit leaves this context active.
        if self._state == 'new':
            self._checks._reject('Stream context was not entered')
        if self._state == 'active':
            self._state = 'closed'
            self._checks.timing = None  # Owner cleanup also runs after a failure.
            if error is not None:
                self._checks.abort(error)
        if self._checks.failure is not None:
            raise self._checks.failure
        return False


class ProtectedOperations(Checks):
    """Every unit owns one unconditional full barrier before and after its body.

    Inner commits force immediate/code/owned checks on both sides. The ordinary
    poll still enforces elapsed one-second/thirty-second cadence inside units.
    Ordered write steps are fixed; nothing returns from a unit before its full
    post-barrier succeeds. This is a new contract, not implicit audit freshness.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._owner = get_ident()
        self._failure_lock = Lock()
        self._unit, self._phase, self._writing, self._index = None, None, False, 0
        self._steps = dict(STEPS)
        self._units = {name: 0 for name, _ in STEPS}
        self._commits = 0

    def _latch(self, error):
        with self._failure_lock:
            if self.failure is None:
                self.failure = error

    def _reject(self, message):
        self._latch(CheckpointFailure(message))
        raise self.failure

    def _check_owner(self):
        if get_ident() != self._owner:
            self._reject('Cross-thread protected operation')

    def abort(self, error):
        self._check_owner()
        self._latch(error)

    def stream(self, timing):
        return _OwnedStream(self, timing)

    def _perform(self, callback):
        if self.failure is not None:
            raise self.failure
        self._check_owner()
        try:
            value = callback()
            if self.failure is not None:
                raise self.failure
            return value
        except BaseException as exc:
            self.abort(exc)
            raise self.failure

    def operation(self, name, callback):
        def run():
            if self._unit is not None or name not in self._steps or not callable(callback):
                self._reject('Invalid or overlapping protected unit')
            self._unit, self._phase, self._index = name, 'entry', 0
            self._units[name] += 1
            try:
                self.barrier()
                self._phase = 'body'
                value = callback()
                if self.failure is not None:
                    raise self.failure
                if self._index != len(self._steps[name]):
                    self._reject('Incomplete protected unit')
                self._phase = 'exit'
                self.barrier()
                return value
            finally:
                self._unit, self._phase = None, None
        return self._perform(run)

    def guard(self):
        def run():
            if self._phase != 'body':
                self._reject('Protected guard outside unit body')
            self.poll()  # An overdue history audit is never deferred to unit exit.
            self.controller.critical_barrier()
        return self._perform(run)

    def commit(self, step, callback):
        def run():
            if (self._phase != 'body' or self._writing or not callable(callback)
                    or self._index >= len(self._steps[self._unit])
                    or step != self._steps[self._unit][self._index]):
                self._reject('Invalid or overlapping protected commit')
            self._writing = True
            try:
                self.guard()
                self._commits += 1
                value = callback()
                self._index += 1
                self.guard()
                return value
            finally:
                self._writing = False
        return self._perform(run)

    def snapshot(self):
        value = super().snapshot()
        bound = 32_000_032
        value['protected_units'] = {name: min(count, bound) for name, count in self._units.items()}
        value['protected_commits'] = min(self._commits, bound)
        value['saturated'] |= self._commits > bound or any(n > bound for n in self._units.values())
        return value
