"""Owned cadence integration exercised with an explicit authored transport.

Only temporary ledgers are created here. There is deliberately no paid CLI,
credential loading, original ledger reservation, or authorization constructor.
The same reader/executor and all ownership callbacks run in offline rehearsals.
"""
import copy
import hashlib
import json
import time

from missing_link.lease import WorkerLease
from missing_link.store import Store
from scripts.missing_link_cadence_checks import held_leases, database_snapshot
from scripts.missing_link_checkpoint_cadence import PinnedFiles
from scripts.missing_link_cadence_executor import execute_cases
from scripts.missing_link_repository_only_evaluator import ReservationBinding, require, verify_prefix
from scripts.missing_link_repository_only_run import inventory, load, sha
from scripts.missing_link_stream_successor_receipts import failure_projection


class OwnedEvidence:
    def __init__(self, out, leases, code_pins):
        self.out, self.leases = out, tuple(leases)
        self.code = PinnedFiles(code_pins)
        self.hashes, self.rows = {}, []

    def save(self, name, value):
        raw = json.dumps(value, ensure_ascii=False, indent=2).encode()
        with (self.out/name).open('xb') as stream:
            stream.write(raw)
        self.hashes[name] = hashlib.sha256(raw).hexdigest()

    def fast(self):
        held_leases(self.leases)

    def critical(self):
        self.fast()
        self.code.verify()
        require(inventory(self.out) == set(self.hashes) | {'run.missing-link.lock'}, 'Owned inventory changed')
        require(all(sha(self.out/name) == value for name, value in self.hashes.items()), 'Owned evidence changed')
        names = sorted(name for name in self.hashes if name.startswith('reservation-'))
        require(names == [f'reservation-{n:02}.json' for n in range(1, len(self.rows)+1)]
                and [load(self.out/name) for name in names] == self.rows, 'Owned reservation journal changed')
        self.fast()

    def seal(self):
        self.critical()
        stream = self.leases[0].file
        stream.seek(0)
        lock_hash = hashlib.sha256(stream.read()).hexdigest()
        stream.seek(0)
        self.save('owned-artifacts.json', dict(self.hashes, **{'run.missing-link.lock': lock_hash}))


def run_offline_owned(workspace, *, provider, packets, manifest, read, code_pins,
                      historical_audit, identity, opener_factory, allowance, account,
                      base_reserved, ceiling, cancelled=lambda: False, clock=time.monotonic,
                      observe=lambda stage, owner: None, case_limit=11,
                      measure=lambda name, callback: callback()):
    """Exclusive owned run; atomically reserve only a freshly created scratch DB.

    Historical audit includes the actual read-only DB in a private rehearsal.
    Identity/opener are authored collaborators; they must never acquire live
    credentials. The original DB path cannot be supplied to this entry point.
    """
    require(callable(opener_factory), 'An explicit offline transport is required')
    workspace.mkdir()  # Exclusive; even failed preparation is never resumed.
    out = workspace/'evidence'
    out.mkdir()
    database = workspace/'authored-ledger.sqlite3'
    store = Store(database, account)
    store.reserve_ai_allowance(allowance, 'authored-prior-reservations', base_reserved, 10)
    before = database_snapshot(database, allowance)
    leases = [WorkerLease(out/'run'), WorkerLease(database)]
    acquired, results, failure, active = [], [], None, None
    owner = OwnedEvidence(out, leases, code_pins)
    owner.save('prepared.json', {'mode': 'offline_authored_only', 'manifest': manifest,
                              'original_calls': 0, 'original_reservations': 0})
    owner.save('baseline.json', before)
    counters = {}

    def history_work():
        historical_audit()
        verify_prefix(before, database_snapshot(database, allowance), owner.rows,
                      allowance=allowance, ceiling=ceiling)
        observe('history', owner)

    def history():
        measure('history', history_work)

    def critical():
        measure('critical', owner.critical)
        observe('critical', owner)

    def barrier():
        owner.fast(); critical(); owner.fast(); history(); owner.fast(); critical(); owner.fast()

    def claim(slot):
        nonlocal active
        active = slot['metadata']['slot']
        owner.save(f'attempt-{active:02}.json', slot['metadata'])
        owner.save(f'request-{active:02}.json', {'metadata': slot['metadata'], 'payload': slot['payload']})
        observe('claim', owner)

    def persist(number, job):
        counters[number] = counters.get(number, 0) + 1
        owner.save(f'checkpoint-{number:02}-{counters[number]:03}.json', job)
        observe('persist', owner)

    def journal(number, row):
        owner.rows.append(copy.deepcopy(row))
        owner.save(f'reservation-{number:02}.json', row)
        observe('reservation', owner)

    binding = ReservationBinding(store, allowance=allowance, ceiling=ceiling, verify=barrier, persist=journal)

    def reserve(job_id, cost):
        binding.expect(job_id, cost)
        binding(allowance, job_id, cost, 10)

    def record(result):
        owner.save(f'result-{result["slot"]:02}.json', result)
        results.append(copy.deepcopy(result))
        observe('result', owner)

    def retain_terminal(number, event):
        owner.save(f'terminal-{number:02}.json', event)
        observe('terminal', owner)

    def finish(completed):
        owner.save('summary.json', {'mode': 'offline_authored_only',
            'results': [{k: r[k] for k in ('slot', 'job_id', 'disposition')} for r in completed],
            'failure': None, 'unattempted': list(range(len(completed)+1, 12)), 'retries': False})
        owner.save('final-integrity.json', database_snapshot(database, allowance))

    try:
        for lease in leases:
            require(lease.acquire(), 'A worker lease is held')
            acquired.append(lease)
        barrier()
        owner.save('started.json', {'one_shot': True, 'mode': 'offline_authored_only'})
        barrier()
        execute_cases(provider, packets, manifest=manifest, read=read, fast=owner.fast,
            critical=critical, history=history, identity=identity, claim=claim, reserve=reserve,
            reservation_observed=lambda job_id, cost: any(r == {'job_id': job_id, 'cost': cost} for r in binding.rows),
            persist=persist, retain_terminal=retain_terminal,
            retain_telemetry=lambda n, value: owner.save(f'diagnostics-{n:02}.json', value),
            record=record, cancelled=cancelled, finish=finish, opener_factory=opener_factory,
            clock=clock, case_limit=case_limit)
        barrier()
        verify_prefix(before, load(out/'final-integrity.json'), owner.rows, allowance=allowance, ceiling=ceiling)
        owner.seal()
        barrier()
    except BaseException as exc:
        failure = {'diagnostic': failure_projection(exc), 'stopped_slot': active,
                   'sealed': False, 'retries': False,
                   'unattempted': [n for n in range(1, 12) if not (out/f'attempt-{n:02}.json').exists()]}
        # Best-effort failure evidence cannot override the original exception or
        # mint a success seal after a latched integrity/transport/storage failure.
        try:
            owner.save('failure.json', failure)
        except BaseException:
            pass
        raise
    finally:
        for lease in reversed(acquired):
            lease.release()
    return {'results': results, 'receipt_sha256': sha(out/'owned-artifacts.json')}
