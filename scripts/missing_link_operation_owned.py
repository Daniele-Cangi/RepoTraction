"""Owned operation wiring with explicit dependencies; no import-time IO.

Only the CLI facade loads credentials after verifying exact human authorization.
Tests supply authored identities, transports and temporary accounting databases.
"""
import copy
import hashlib
import json
import time

from missing_link.lease import WorkerLease
from missing_link.service import Cancelled
from missing_link.store import Store
from scripts.missing_link_cadence_checks import HistoryAudit, held_leases
from scripts.missing_link_cadence_owned import OwnedEvidence
from scripts.missing_link_database_audit import _transaction
from scripts.missing_link_operation_executor import execute_cases, SETTINGS
from scripts.missing_link_demand_operation_policy_v3_executor import same_slot_structure
from scripts.missing_link_repository_only_evaluator import ReservationBinding, configuration, require, verify_prefix
from scripts.missing_link_repository_only_run import inventory, load, sha
from scripts.missing_link_stream_successor_receipts import failure_projection


def verify_owned_prefix(database, before, rows, *, account, allowance, ceiling):
    """Fresh accounting/identity/job reads; other tables remain full-audit work.

    Reuse only immutable baseline hashes for noncritical tables in this narrower
    comparison. Full HistoryAudit still reads a complete current database image
    at every operation entry/exit and whenever the thirty-second audit is due.
    """
    after = copy.deepcopy(before)
    with _transaction(database) as db:
        require(db.execute('SELECT account FROM ml_identity').fetchall() == [(account.casefold(),)],
                'Accounting database belongs to another account')
        for table in ('ml_ai_reservations', 'ml_ai_allowances'):
            values = db.execute(f'SELECT * FROM "{table}" ORDER BY rowid').fetchall()
            after['tables'][table] = hashlib.sha256(json.dumps(values, sort_keys=True,
                ensure_ascii=False).encode()).hexdigest()
        after['reservation_rows'] = [list(r) for r in db.execute('SELECT * FROM ml_ai_reservations ORDER BY id')]
        after['allowance_rows'] = [list(r) for r in db.execute('SELECT * FROM ml_ai_allowances ORDER BY id')]
        after['reservations'], after['reserved_usd'] = db.execute(
            'SELECT COUNT(*),SUM(cost) FROM ml_ai_reservations WHERE allowance_id=?', (allowance,)).fetchone()
        jobs = [json.loads(r[0]) for r in db.execute('SELECT payload FROM ml_jobs')]
        after['active_jobs'] = [j['id'] for j in jobs if j['status'] in {'queued', 'running'}]
    verify_prefix(before, after, rows, allowance=allowance, ceiling=ceiling)


def unused_job_ids(database, job_ids):
    with _transaction(database) as db:
        used = {r[0] for r in db.execute('SELECT job_id FROM ml_ai_reservations')}
        used.update(r[0] for r in db.execute('SELECT id FROM ml_jobs'))
    require(not used.intersection(job_ids), 'One-shot accounting IDs are already used')


def authorization_scope(anchor, manifest):
    source = manifest['source']
    return {'authorized': True, 'prepared_manifest_sha256': anchor,
        'required_main': manifest['required_main'], 'reviewed_tree': manifest['reviewed_tree'],
        'source_preparation_sha256': manifest['source_preparation_sha256'],
        'owned_output': manifest['owned_output'], 'account': manifest['account'],
        'allowance': manifest['allowance'], 'calls': 11, 'calls_per_slot': 1,
        'configured_total_usd': 10, 'segment_cap_usd': .10,
        'atomic_cumulative_ceiling_usd': manifest['atomic_cumulative_ceiling_usd'],
        'config_without_key': copy.deepcopy(source['config_without_key']),
        'stream_settings': {key: source[key] for key in SETTINGS},
        'job_ids': [r['job_id'] for r in source['requests']],
        'native_sha256': [r['native_sha256'] for r in source['requests']]}


def run_bound_owned(out, *, manifest, anchor, source, authorization, provider, packets, read,
                    database, account, allowance, ceiling, compiled, tree, identity,
                    opener_factory, cancelled=lambda: False, clock=time.monotonic):
    """Execute one already validated, exclusively prepared eleven-slot scope.

    The facade validates approval before loading credentials; recheck it here
    before any owned execution write. This entry point never constructs
    a database, resets an allowance, creates jobs or resumes an attempted scope.
    """
    require(inventory(out) == {'prepared.json', 'baseline.json'}, 'Owned run is already consumed')
    require(same_slot_structure(authorization, authorization_scope(anchor, manifest))
            and same_slot_structure(source, manifest['source'])
            and account == manifest['account'] and allowance == manifest['allowance']
            and type(ceiling) is float and ceiling == manifest['atomic_cumulative_ceiling_usd'],
            'Exact approved owned scope required')
    require(sha(out/'prepared.json') == anchor
            and same_slot_structure(load(out/'prepared.json'), manifest)
            and same_slot_structure(load(out/'baseline.json'), compiled['baseline']), 'Owned anchors changed')
    before, frozen_source = copy.deepcopy(compiled['baseline']), copy.deepcopy(source)
    config, key = copy.deepcopy(source['config_without_key']), provider.key
    leases = [WorkerLease(out/'run'), WorkerLease(database)]
    owner = OwnedEvidence(out, leases, compiled['code_pins'])
    owner.hashes.update({name: sha(out/name) for name in ('prepared.json', 'baseline.json')})
    acquired, counters, active, results, primary = [], {}, None, [], None

    def fast():
        if cancelled(): raise Cancelled('Owned operation run cancelled.')
        identity()
        owner.fast()
        require(same_slot_structure(configuration(provider), config) and provider.key == key,
                'Provider configuration changed')

    def critical():
        fast()
        require(same_slot_structure(source, frozen_source), 'In-memory operation scope changed')
        owner.critical()
        require(same_slot_structure(owner.rows, binding.rows), 'In-memory reservation binding changed')
        verify_owned_prefix(database, before, owner.rows, account=account, allowance=allowance, ceiling=ceiling)
        fast()

    history = HistoryAudit(root=compiled['root'], database=database, baseline=before,
        allowance=allowance, ceiling=ceiling,
        rows=lambda: copy.deepcopy(owner.rows), tree=tree, inventories=compiled['audit'].inventories,
        database_audit=compiled['database_audit'])

    def barrier():
        fast(); critical(); fast(); history(); fast(); critical(); fast()

    # Only reserve_ai_allowance is used. Store.__init__ would perform DDL and
    # identity writes on the original database, which are outside this contract.
    original = object.__new__(Store)
    original.path, original.account = database, account.casefold()

    def journal(number, row):
        owner.rows.append(copy.deepcopy(row))
        owner.save(f'reservation-{number:02}.json', row)

    binding = ReservationBinding(original, allowance=allowance, ceiling=ceiling,
                                 verify=critical, persist=journal)

    def reserve(job_id, cost):
        binding.expect(job_id, cost)
        binding(allowance, job_id, cost, 10)

    def claim(slot):
        nonlocal active
        active = slot['metadata']['slot']
        owner.save(f'attempt-{active:02}.json', slot['metadata'])
        owner.save(f'request-{active:02}.json', {'metadata': slot['metadata'], 'payload': slot['payload']})

    def persist(number, job):
        counters[number] = counters.get(number, 0) + 1
        owner.save(f'checkpoint-{number:02}-{counters[number]:03}.json', job)

    def record(result):
        owner.save(f'result-{result["slot"]:02}.json', result)
        results.append(copy.deepcopy(result))

    def finish(completed):
        require(len(completed) == 11, 'A live owned scope must attempt the entire frozen cohort')
        owner.save('summary.json', {'mode': 'authorized_operation_one_shot',
            'results': [{k: r[k] for k in ('slot', 'job_id', 'disposition')} for r in completed],
            'failure': None, 'unattempted': [], 'retries': False})
        final = compiled['database_audit']()
        final['artifacts'] = dict(before['artifacts'])
        verify_prefix(before, final, owner.rows, allowance=allowance, ceiling=ceiling)
        owner.save('final-integrity.json', final)

    try:
        for lease in leases:
            require(lease.acquire(), 'A worker lease is held')
            acquired.append(lease)
        barrier()
        unused_job_ids(database, [r['job_id'] for r in source['requests']])
        identity(force=True)
        barrier()
        owner.save('authorization.json', authorization)
        owner.save('started.json', {'one_shot': True, 'prepared_manifest_sha256': anchor})
        barrier()
        execute_cases(provider, packets, manifest=source, read=read, fast=fast,
            critical=critical, history=history, identity=identity, claim=claim, reserve=reserve,
            reservation_observed=lambda job_id, cost: any(r == {'job_id': job_id, 'cost': cost} for r in binding.rows),
            persist=persist, retain_terminal=lambda n, event: owner.save(f'terminal-{n:02}.json', event),
            retain_telemetry=lambda n, value: owner.save(f'diagnostics-{n:02}.json', value),
            record=record, cancelled=cancelled, finish=finish, opener_factory=opener_factory, clock=clock)
        barrier()
        verify_prefix(before, load(out/'final-integrity.json'), owner.rows, allowance=allowance, ceiling=ceiling)
        owner.stage_seal()
        barrier()
        receipt = owner.publish_seal()  # Last success write; no fallible receipt read after promotion.
    except BaseException as exc:
        primary = exc
        try:
            require(leases[0] in acquired, 'Failure evidence requires the owned output lease')
            held_leases((leases[0],))
            owner.save('failure.json', {'diagnostic': failure_projection(exc), 'stopped_slot': active,
                'sealed': False, 'retries': False,
                'unattempted': [n for n in range(1, 12) if not (out/f'attempt-{n:02}.json').exists()]})
        except BaseException:
            pass
        raise
    finally:
        cleanup_error = None
        for lease in reversed(acquired):
            try:
                lease.release()
            except BaseException as exc:
                if cleanup_error is None: cleanup_error = exc
        if cleanup_error is not None and primary is None:
            # A cleanup failure never returns a success digest. Retire a staged
            # success filename when storage permits; no independent success
            # anchor is issued even if that failure rename cannot be persisted.
            try:
                (out/'owned-artifacts.json').rename(out/'owned-artifacts.rejected.json')
                owner.save('failure.json', {'diagnostic': failure_projection(cleanup_error),
                    'stopped_slot': active, 'sealed': False, 'retries': False, 'unattempted': []})
            except BaseException:
                pass
            raise cleanup_error
    return {'results': results, 'receipt_manifest_sha256': receipt, 'retain_outside_output_directory': True}
