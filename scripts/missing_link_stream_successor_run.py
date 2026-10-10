"""Separate stream-successor prepare/verify/run; frozen predecessors stay unchanged. Import performs no IO.

Run requires an independently retained prepared-manifest digest and separately
authorized command. Preparation is credential-free; neither prepare nor merge
authorizes calls. No production module imports these experimental adapters.
"""
import argparse
import copy
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from github_cli import verify_cli_account
from missing_link.config import provider_environment
from missing_link.lease import WorkerLease
from missing_link.provider import Provider
from missing_link.store import Store
from scripts.missing_link_repository_only_evaluator import ReservationBinding, require, verify_prefix, EvaluationStopped
from scripts.missing_link_repository_only_run import snapshot, sha, git, knobs, load, save, inventory
from scripts.missing_link_triage_transport import IdentityCheck
from scripts.missing_link_stream_successor_executor import verify_requests, execute_cases, STREAM_SETTINGS, same_slot_structure
from scripts.missing_link_stream_successor_receipts import failure_projection
from scripts.missing_link_demand_operation_policy_v3_executor import digest
from scripts import missing_link_demand_operation_policy_v3_run as predecessor

PREP = ROOT / 'data/missing-link-demand-operation-policy-v3-stream-preparation-2026-10-09'
PREP_SHA = 'dd7d0f975d70f2f3fc2a5110a9111b881fea0053f2d493c0ad02f76bee38b1f7'
PROTOCOL = ROOT / 'docs/missing-link-policy-v3-stream-successor-protocol-2026-10-09.md'
PROTOCOL_SHA = 'c73a88721b9bab36f2a715012a202df1f22583c4ecaa6661e22f599d0d045fbe'
DB = ROOT / 'data/repotraction-daniele-cangi.sqlite3'
ACCOUNT = 'Daniele-Cangi'
ALLOWANCE = 'missing-link-verification-2026-09-30'
CEILING = 8.23614
BASE_RESERVATIONS, BASE_RESERVED, EXISTING_CODE = 578, 8.13614, 53
HISTORY_ARTIFACTS = 1687
ADAPTERS = ('scripts/missing_link_stream_successor_receipts.py',
            'scripts/missing_link_stream_successor_executor.py',
            'scripts/missing_link_stream_successor_run.py',
            'tests/test_missing_link_stream_successor_receipts.py',
            'tests/test_missing_link_stream_successor_execution.py')
LOCK = 'run.missing-link.lock'
OWNED_RELATIVE = 'data/missing-link-demand-operation-policy-v3-stream-owned-run-2026-10-09'
CONTRACT_MAIN = '55f4a6d676fccc4a204322e0080667c2ee154dd7'
CONTRACT_REVIEWED = 'a3adfc1ace7163027eaaddb45f327f83a247a627'
HISTORIES = predecessor.HISTORIES + (
    ('data/missing-link-demand-operation-policy-v3-owned-run-2026-10-09',
     'v3_prepared_manifest_sha256', 'v3_receipt_manifest_sha256'),
    ('data/missing-link-demand-operation-policy-v3-owned-assessment-2026-10-09',
     'v3_assessment_prepared_sha256', 'v3_assessment_receipt_sha256'))


def settings():
    env = knobs()
    env.update(REPOTRACTION_AI_MAX_CALLS='1', REPOTRACTION_AI_MAX_COST_USD='0.02')
    return env


def owned_path(out):
    target = (ROOT/OWNED_RELATIVE).resolve()
    require(out.resolve() == target and target.is_relative_to(ROOT.resolve()),
            'Only the separately named owned directory may prepare, verify or run')


def historical_evidence(source, baseline):
    """Static predecessor seals only; never their stale live-prefix verifier."""
    original = predecessor.preparation()
    require(source['source_preparation_sha256'] == predecessor.PREP_SHA,
            'Original v3 source anchor changed')
    for name in ('inputs.json','references.json'):
        require((PREP/name).read_bytes() == (predecessor.PREP/name).read_bytes(), 'Original inputs/references changed')
    old_requests = original['requests']
    expected_requests = copy.deepcopy(old_requests)
    for number, row in enumerate(expected_requests,1):
        row['job_id'] = f'demand-operation-policy-v3-stream-owned-2026-10-09-{number:02}'
        for key in ('policy_envelope','native_body'):
            require((PREP/row[key]).read_bytes() == (predecessor.PREP/row[key]).read_bytes(), 'Original envelope/body changed')
    require(same_slot_structure(source['requests'],expected_requests), 'Successor changed more than accounting IDs')
    for relative, prepared_key, receipt_key in HISTORIES:
        folder = ROOT/relative
        if prepared_key:
            require(sha(folder/'prepared.json') == source['historical_anchors'][prepared_key], 'Historical prepared anchor changed')
        require(sha(folder/'owned-artifacts.json') == source['historical_anchors'][receipt_key], 'Historical receipt anchor changed')
        files = load(folder/'owned-artifacts.json')
        require(inventory(folder) == set(files) | {'owned-artifacts.json'}
                and all(sha(folder/name) == value for name,value in files.items()), 'Historical sealed inventory changed')
        for name in set(files) | {'owned-artifacts.json'}:
            require(baseline['artifacts'].get(relative+'/'+name) == sha(folder/name), 'Historical baseline binding changed')


def preparation():
    git('merge-base','--is-ancestor',CONTRACT_MAIN,'origin/main')
    require(git('rev-parse',CONTRACT_MAIN+'^{tree}') == git('rev-parse',CONTRACT_REVIEWED+'^{tree}'),
            'Reviewed/merged stream contract trees differ')
    require(sha(PREP/'prepared.json') == PREP_SHA, 'Independent source preparation anchor changed')
    source = load(PREP/'prepared.json')
    require(inventory(PREP) == set(source['owned_files_sha256']) | {'prepared.json'}
            and all(sha(PREP/name) == value for name,value in source['owned_files_sha256'].items()), 'Source preparation bytes changed')
    require(sha(PROTOCOL,canonical=True) == source['protocol_sha256_lf'] == PROTOCOL_SHA
            and sha(PREP/'protocol.md',canonical=True) == PROTOCOL_SHA, 'Frozen stream protocol changed')
    require(sha(ROOT/'docs/missing-link-policy-v3-stream-diagnostics-2026-10-09.md',canonical=True)
            == source['diagnostic_report_sha256_lf'], 'Diagnostic report changed')
    require(sha(PREP/'baseline.json') == source['baseline_sha256']
            and sha(PREP/'inputs.json') == source['inputs_sha256']
            and sha(PREP/'references.json',canonical=True) == source['references_sha256_lf'], 'Source anchors changed')
    require(source['status'] == 'offline_only_no_stream_successor_executor'
            and source['new_calls'] == source['new_predictions'] == source['new_reservations'] == 0
            and source['call_authorization_granted'] is False
            and source['account'] == ACCOUNT and source['allowance'] == ALLOWANCE
            and source['configured_total_usd'] == 10 and source['segment_cap_usd'] == .10
            and source['atomic_cumulative_ceiling_usd'] == CEILING
            and len(source['code_sha256_canonical_lf']) == EXISTING_CODE,
            'Preparation is not the frozen offline stream successor')
    require(all(sha(ROOT/name,canonical=True) == value for name,value in source['code_sha256_canonical_lf'].items()),
            'Pinned predecessor code changed')
    historical_evidence(source,load(PREP/'baseline.json'))
    verify_requests(Provider(settings()),load(PREP/'inputs.json')['cases'],source,
                    lambda name:(PREP/name).read_bytes(),readiness=False)
    return source


def prepare(out, reviewed_head):
    owned_path(out)
    require(not out.exists(), 'Never replace an owned successor')
    git('fetch','origin','main')
    require(git('branch','--show-current') == 'main' and not git('status','--porcelain')
            and git('rev-parse','HEAD') == git('rev-parse','origin/main'), 'Prepare requires clean merged main')
    require(git('rev-parse','HEAD^{tree}') == git('rev-parse',reviewed_head+'^{tree}'), 'Reviewed and merged trees differ')
    source = preparation()
    baseline = load(PREP/'baseline.json')
    require(snapshot(baseline) == baseline, 'Original preparation baseline changed')
    require(len(baseline['artifacts']) == HISTORY_ARTIFACTS, 'Historical inventory changed')
    protected = dict(baseline['artifacts'])
    for path in PREP.iterdir():
        protected[path.relative_to(ROOT).as_posix()] = sha(path)
    baseline = snapshot({'artifacts':protected})
    require(baseline['reservations'] == BASE_RESERVATIONS and abs(baseline['reserved_usd']-BASE_RESERVED) < 1e-10
            and not baseline['active_jobs'], 'Original ledger/worker changed')
    ids = {r['job_id'] for r in source['requests']}
    require(not any(row[2] in ids for row in baseline['reservation_rows']), 'An owned accounting slot was already used')
    packets = load(PREP/'inputs.json')['cases']
    verify_requests(Provider(settings()), packets, source, lambda name:(PREP/name).read_bytes(), readiness=False)
    code = dict(source['code_sha256_canonical_lf'])
    code.update({name:sha(ROOT/name,canonical=True) for name in ADAPTERS})
    out.mkdir(parents=True)
    save(out,'baseline.json',baseline)
    save(out,'prepared.json',{'required_main':git('rev-parse','HEAD'), 'reviewed_head':reviewed_head,
        'owned_output':OWNED_RELATIVE,
        'reviewed_tree':git('rev-parse','HEAD^{tree}'), 'preparation_sha256':PREP_SHA,
        'protocol_sha256_lf':PROTOCOL_SHA, 'baseline_sha256':sha(out/'baseline.json'),
        'code_sha256_canonical_lf':code, 'new_calls':0,'new_reservations':0})
    require(snapshot(baseline) == baseline, 'Original ledger/history changed during freeze')
    print(json.dumps({'prepared_manifest_sha256':sha(out/'prepared.json'), 'retain_outside_output_directory':True}))


def frozen(out, anchor, provider=None, *, fetch=False):
    owned_path(out)
    require(bool(anchor and re.fullmatch(r'[a-f0-9]{64}',anchor)) and sha(out/'prepared.json') == anchor,
            'Independent owned preparation digest required')
    manifest = load(out/'prepared.json')
    require(manifest['owned_output'] == OWNED_RELATIVE, 'Owned directory binding changed')
    require(not git('status','--porcelain'), 'Tracked implementation is dirty')
    require(sha(out/'baseline.json') == manifest['baseline_sha256'], 'Owned baseline changed')
    require(all(sha(ROOT/name,canonical=True) == value for name,value in manifest['code_sha256_canonical_lf'].items()),
            'Owned executable fingerprint changed')
    source = preparation()
    expected_baseline = load(PREP/'baseline.json')
    expected_baseline['artifacts'].update({path.relative_to(ROOT).as_posix():sha(path) for path in PREP.iterdir()})
    require(load(out/'baseline.json') == expected_baseline, 'Owned baseline does not extend the frozen preparation')
    require(set(manifest['code_sha256_canonical_lf']) == set(source['code_sha256_canonical_lf']) | set(ADAPTERS),
            'Owned code inventory differs from required adapters')
    require(manifest['new_calls'] == manifest['new_reservations'] == 0
            and git('rev-parse',manifest['required_main']+'^{tree}') == manifest['reviewed_tree']
            and git('rev-parse',manifest['reviewed_head']+'^{tree}') == manifest['reviewed_tree'],
            'Owned reviewed/merged tree binding changed')
    require(manifest['preparation_sha256'] == PREP_SHA and manifest['protocol_sha256_lf'] == PROTOCOL_SHA,
            'Owned protocol/preparation binding changed')
    if fetch:
        git('fetch','origin','main')
    git('merge-base','--is-ancestor',manifest['required_main'],'origin/main')
    if provider is not None:
        verify_requests(provider,load(PREP/'inputs.json')['cases'],source,lambda name:(PREP/name).read_bytes())
    return manifest, source


def journal(out):
    paths = sorted(out.glob('reservation-*.json'))
    require([p.name for p in paths] == [f'reservation-{n:02}.json' for n in range(1,len(paths)+1)], 'Journal has gaps')
    return [load(p) for p in paths]


def verify(out, anchor, receipt_anchor=None):
    frozen(out,anchor)
    if (out/'owned-artifacts.json').exists():
        require(bool(receipt_anchor and re.fullmatch(r'[a-f0-9]{64}',receipt_anchor))
                and sha(out/'owned-artifacts.json') == receipt_anchor, 'Independent receipt anchor required')
        files = load(out/'owned-artifacts.json')
        require({'prepared.json','baseline.json','authorization.json','started.json','summary.json','final-integrity.json',LOCK} <= set(files),
                'Sealed receipt inventory is incomplete')
        require(inventory(out) == set(files) | {'owned-artifacts.json'}
                and all(sha(out/name) == value for name,value in files.items()), 'Owned receipts changed')
    else:
        require(inventory(out) <= {'prepared.json','baseline.json',LOCK}, 'Unsealed execution evidence exists')
        require(not journal(out), 'Unsealed reservation exists')
    before = load(out/'baseline.json')
    verify_prefix(before,snapshot(before),journal(out),allowance=ALLOWANCE,ceiling=CEILING)
    print('Frozen owned demand run and exact original reservation prefix reproduce.')


def authorization_scope(anchor, source):
    """A bounded scope record; human authorization is still required separately."""
    return {'authorized':True, 'prepared_manifest_sha256':anchor, 'preparation_sha256':PREP_SHA,
        'owned_output':OWNED_RELATIVE,
        'account':ACCOUNT, 'allowance':ALLOWANCE, 'calls':11, 'calls_per_slot':1,
        'configured_total_usd':10, 'segment_cap_usd':.10, 'atomic_cumulative_ceiling_usd':CEILING,
        'stream_settings':{key:source[key] for key in STREAM_SETTINGS},
        'job_ids':[r['job_id'] for r in source['requests']],
        'native_sha256':[r['native_sha256'] for r in source['requests']]}


def execution_tree(manifest):
    """Only the frozen merged commit/tree may execute; later main is not approval."""
    require(git('branch','--show-current') == 'main'
            and git('rev-parse','HEAD') == git('rev-parse','origin/main') == manifest['required_main']
            and git('rev-parse','HEAD^{tree}') == manifest['reviewed_tree'],
            'Run requires the exact frozen reviewed/merged tree')


def run(out, anchor, authorization=None):
    manifest, source = frozen(out,anchor,fetch=True)
    execution_tree(manifest)
    require(inventory(out) <= {'prepared.json','baseline.json',LOCK}, 'Owned run is already consumed')
    before = load(out/'baseline.json')
    verify_prefix(before,snapshot(before),[],allowance=ALLOWANCE,ceiling=CEILING)
    require(authorization is not None and same_slot_structure(load(authorization), authorization_scope(anchor, source)),
            'Separate exact-scope call authorization record required')
    env = provider_environment()
    env.update(REPOTRACTION_AI_MAX_CALLS='1',REPOTRACTION_AI_MAX_COST_USD='0.02',REPOTRACTION_AI_MAX_OUTPUT_TOKENS='6000')
    provider = Provider(env)
    frozen(out,anchor,provider)
    slots = verify_requests(provider,load(PREP/'inputs.json')['cases'],source,lambda name:(PREP/name).read_bytes())
    identity = IdentityCheck(lambda:verify_cli_account(ACCOUNT,run=subprocess.run),time.monotonic)
    leases = [WorkerLease(out/'run'),WorkerLease(DB)]
    acquired, hashes, binding = [], {name:sha(out/name) for name in ('prepared.json','baseline.json')}, None
    counters, results, active = {}, [], None
    started, failure = False, None
    pinned_manifest, pinned_source = copy.deepcopy(manifest), copy.deepcopy(source)

    def owned_save(name,value):
        save(out,name,value)
        hashes[name] = sha(out/name)

    def owned_sha(name):
        if name == LOCK and leases[0].file is not None:
            # Windows denies a second handle reading the locked byte. Keep the
            # lease held through sealing and hash through its existing handle.
            stream = leases[0].file
            stream.seek(0)
            value = digest(stream.read())
            stream.seek(0)
            return value
        return sha(out/name)

    def critical():
        require(same_slot_structure(manifest,pinned_manifest) and same_slot_structure(source,pinned_source),
                'In-memory owned bindings changed')
        require(sha(out/'prepared.json') == anchor and sha(PREP/'prepared.json') == PREP_SHA
                and sha(out/'baseline.json') == manifest['baseline_sha256'], 'Critical owned anchors changed')
        require(all(sha(ROOT/name,canonical=True) == value for name,value in manifest['code_sha256_canonical_lf'].items()),
                'Executable fingerprints changed during stream')
        for lease in acquired:
            require(lease.file is not None and not lease.file.closed and lease.path.is_file(), 'Held lease disappeared')
            held, path = os.fstat(lease.file.fileno()), lease.path.stat()
            require((held.st_dev,held.st_ino) == (path.st_dev,path.st_ino), 'Held lease file replaced')
        require(inventory(out) <= set(hashes) | {LOCK}, 'Unowned evidence file appeared')
        require(all(owned_sha(name) == value for name,value in hashes.items()), 'Owned evidence changed')
        require(journal(out) == (binding.rows if binding else []), 'Reservation journal changed')

    def integrity():
        critical()
        frozen(out,anchor,provider)
        execution_tree(manifest)
        rows = binding.rows if binding else []
        verify_prefix(before,snapshot(before),rows,allowance=ALLOWANCE,ceiling=CEILING)

    def claim(slot):
        nonlocal active
        active = slot['metadata']['slot']
        owned_save(f'attempt-{active:02}.json',slot['metadata'])
        owned_save(f'request-{active:02}.json',{'metadata':slot['metadata'],'payload':slot['payload']})

    def persist(number,job):
        counters[number] = counters.get(number,0)+1
        owned_save(f'checkpoint-{number:02}-{counters[number]:03}.json',job)

    def reserve(job_id,cost):
        binding.expect(job_id,cost)
        binding(ALLOWANCE,job_id,cost,10)

    def record(result):
        owned_save(f'result-{result["slot"]:02}.json',result)
        results.append(copy.deepcopy(result))

    try:
        for lease in leases:
            require(lease.acquire(), 'A worker lease is held')
            acquired.append(lease)
        integrity()
        identity(force=True)
        integrity()
        owned_save('authorization.json',load(authorization))
        require(same_slot_structure(load(out/'authorization.json'), authorization_scope(anchor, source)), 'Call scope changed before start')
        owned_save('started.json',{'prepared_manifest_sha256':anchor,'one_shot':True})
        started = True
        # Use ONLY the existing Store reservation method, without constructor DDL,
        # identity insertion or original job/cache writes. Baseline pins identity.
        original = object.__new__(Store)
        original.path, original.account = DB, ACCOUNT.casefold()
        binding = ReservationBinding(original,allowance=ALLOWANCE,ceiling=CEILING,verify=integrity,
            persist=lambda n,row:owned_save(f'reservation-{n:02}.json',row))
        execute_cases(provider,slots,manifest=source,read=lambda name:(PREP/name).read_bytes(),
            gate=integrity,light_gate=critical,identity=identity,claim=claim,reserve=reserve,persist=persist,
            reservation_observed=lambda job_id,cost:any(row == {"job_id":job_id,"cost":cost} for row in binding.rows),
            retain_terminal=lambda n,event:owned_save(f'terminal-{n:02}.json',event),
            retain_telemetry=lambda n,value:owned_save(f'diagnostics-{n:02}.json',value),record=record,clock=time.monotonic,
            cancelled=lambda:(out.parent/(out.name+'.cancel')).exists())
    except BaseException as exc:
        failure = {'diagnostic':failure_projection(exc),'stopped_slot':active}
    finally:
        try:
            if started:
                owned_save('summary.json',{'results':[{k:r[k] for k in ('slot','job_id','disposition')} for r in results],
                    'failure':failure,'unattempted':[n for n in range(1,12) if not (out/f'attempt-{n:02}.json').exists()],
                    'retries':False})
                require(failure is None or failure['diagnostic']['category'] != 'telemetry_persistence',
                        'Cannot seal a run with failed telemetry retention')
                integrity()
                owned_save('final-integrity.json',snapshot(before))
                hashes[LOCK] = owned_sha(LOCK)
                require(inventory(out) == set(hashes)
                        and all(owned_sha(name) == value for name,value in hashes.items()),
                        'Cannot seal incomplete or changed owned evidence')
                # Validate both current accounting and the actual retained final
                # snapshot immediately before issuing a receipt digest.
                integrity()
                verify_prefix(before,load(out/'final-integrity.json'),journal(out),
                    allowance=ALLOWANCE,ceiling=CEILING)
                save(out,'owned-artifacts.json',hashes)
                print(json.dumps({'receipt_manifest_sha256':sha(out/'owned-artifacts.json'),
                                  'retain_outside_output_directory':True}))
        except BaseException as exc:
            bounded = {'diagnostic':failure_projection(exc), 'primary_failure':failure, 'sealed':False}
            try:
                owned_save('finalization-failure.json',bounded)
            except BaseException:
                pass  # Existing evidence remains; no complete seal or retry claim.
            raise EvaluationStopped('Owned finalization failed; retained run is not resumable.') from None
        finally:
            for lease in reversed(acquired):
                lease.release()
    require(failure is None, 'Owned run stopped; preserved attempts must not be resumed')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('prepare','verify','run'))
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--reviewed-head')
    parser.add_argument('--prepared-manifest-sha256')
    parser.add_argument('--receipt-manifest-sha256')
    parser.add_argument('--call-authorization',type=Path)
    args = parser.parse_args()
    out = args.output.resolve()
    if args.action == 'prepare':
        require(bool(args.reviewed_head and re.fullmatch(r'[a-f0-9]{40}',args.reviewed_head)), 'Reviewed full head required')
        prepare(out,args.reviewed_head)
    elif args.action == 'verify':
        verify(out,args.prepared_manifest_sha256,args.receipt_manifest_sha256)
    else:
        run(out,args.prepared_manifest_sha256,args.call_authorization)


if __name__ == '__main__':
    main()
