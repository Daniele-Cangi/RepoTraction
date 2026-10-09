"""Explicit owned policy-v2 prepare/verify/run. Import performs no IO.

Run requires an independently retained prepared-manifest digest and separately
authorized command. Preparation is credential-free; neither prepare nor merge
authorizes calls. No production module imports these experimental adapters.
"""
import argparse
import copy
import json
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
from scripts.missing_link_demand_operation_policy_v2_executor import verify_requests, execute_cases, digest

PREP = ROOT / 'data/missing-link-demand-operation-policy-v2-execution-preparation-2026-10-09'
PREP_SHA = '4ebbbb80c708eaf3531540679211bac18f7c4443a1351a51751cf97bb334390d'
PROTOCOL = ROOT / 'docs/missing-link-demand-operation-policy-v2-execution-protocol-2026-10-09.md'
PROTOCOL_SHA = 'c60fc910194f5ceb38c90a3ed1412847d32543a28b21cee5e758100647a05e56'
DB = ROOT / 'data/repotraction-daniele-cangi.sqlite3'
ACCOUNT = 'Daniele-Cangi'
ALLOWANCE = 'missing-link-verification-2026-09-30'
CEILING = 8.1779182
HISTORY_ARTIFACTS = 1488
ADAPTERS = ('scripts/missing_link_demand_operation_policy_v2_executor.py',
            'scripts/missing_link_demand_operation_policy_v2_run.py',
            'tests/test_missing_link_demand_operation_policy_v2_executor.py')
HISTORIES = (
    ('data/missing-link-demand-operation-owned-run-2026-10-09',
     'v1_owned_prepared_sha256', 'v1_receipt_manifest_sha256'),
    ('data/missing-link-demand-operation-owned-assessment-2026-10-09',
     None, 'v1_assessment_manifest_sha256'))
LEGACY_PREP = 'data/missing-link-demand-operation-execution-preparation-v2-2026-10-09'
LOCK = 'run.missing-link.lock'


def settings():
    env = knobs()
    env.update(REPOTRACTION_AI_MAX_CALLS='1', REPOTRACTION_AI_MAX_COST_USD='0.02')
    return env


def historical_evidence(source, baseline):
    """Verify sealed bytes/inventories, never require the old live ledger suffix.

    The v1 consumed runner's live-prefix verifier correctly expects 566 rows.
    After v2 reservations the new runner must instead preserve v1 sealed bytes
    and verify ONLY its own exact extension of this frozen 566-row baseline.
    """
    anchors = source['historical_anchors']
    for relative, prepared_key, receipt_key in HISTORIES:
        folder = ROOT / relative
        if prepared_key:
            require(sha(folder/'prepared.json') == anchors[prepared_key], 'Historical prepared anchor changed')
        require(sha(folder/'owned-artifacts.json') == anchors[receipt_key], 'Historical receipt anchor changed')
        files = load(folder/'owned-artifacts.json')
        require(inventory(folder) == set(files) | {'owned-artifacts.json'}
                and all(sha(folder/name) == value for name,value in files.items()), 'Historical sealed inventory changed')
        for name in set(files) | {'owned-artifacts.json'}:
            require(baseline['artifacts'].get(relative+'/'+name) == sha(folder/name), 'Historical baseline binding changed')
    folder = ROOT / LEGACY_PREP
    require(sha(folder/'prepared.json') == anchors['v1_execution_preparation_sha256'], 'Historical protocol preparation changed')
    files = load(folder/'prepared.json')['owned_files_sha256']
    require(inventory(folder) == set(files) | {'prepared.json'}
            and all(sha(folder/name) == value for name,value in files.items()), 'Historical preparation inventory changed')
    for name in set(files) | {'prepared.json'}:
        require(baseline['artifacts'].get(LEGACY_PREP+'/'+name) == sha(folder/name), 'Historical preparation binding changed')


def preparation():
    require(sha(PREP/'prepared.json') == PREP_SHA, 'Independent preparation anchor changed')
    manifest = load(PREP/'prepared.json')
    require(inventory(PREP) == set(manifest['owned_files_sha256']) | {'prepared.json'}, 'Preparation inventory changed')
    require(all(sha(PREP/name) == value for name,value in manifest['owned_files_sha256'].items()), 'Preparation bytes changed')
    require(sha(PROTOCOL, canonical=True) == PROTOCOL_SHA == manifest['execution_protocol_sha256_lf'], 'Frozen protocol changed')
    require(manifest['policy_revision'] == 2 and manifest['status'] == 'offline_only_no_policy_v2_executor'
            and manifest['new_calls'] == manifest['new_predictions'] == manifest['new_reservations'] == 0
            and manifest['account'] == ACCOUNT and manifest['allowance'] == ALLOWANCE
            and manifest['configured_total_usd'] == 10 and manifest['segment_cap_usd'] == .10
            and manifest['atomic_cumulative_ceiling_usd'] == CEILING
            and manifest['call_authorization_granted'] is False,
            'Preparation is not the frozen offline policy-v2 revision')
    require(all(sha(ROOT/name,canonical=True) == value for name,value in manifest['code_sha256_canonical_lf'].items()),
            'Pinned first-party code changed')
    historical_evidence(manifest, load(PREP/'baseline.json'))
    return manifest


def prepare(out, reviewed_head):
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
    require(baseline['reservations'] == 566 and abs(baseline['reserved_usd']-8.0779182) < 1e-10
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
        'reviewed_tree':git('rev-parse','HEAD^{tree}'), 'preparation_sha256':PREP_SHA,
        'protocol_sha256_lf':PROTOCOL_SHA, 'baseline_sha256':sha(out/'baseline.json'),
        'code_sha256_canonical_lf':code, 'new_calls':0,'new_reservations':0})
    require(snapshot(baseline) == baseline, 'Original ledger/history changed during freeze')
    print(json.dumps({'prepared_manifest_sha256':sha(out/'prepared.json'), 'retain_outside_output_directory':True}))


def frozen(out, anchor, provider=None, *, fetch=False):
    require(bool(anchor and re.fullmatch(r'[a-f0-9]{64}',anchor)) and sha(out/'prepared.json') == anchor,
            'Independent owned preparation digest required')
    manifest = load(out/'prepared.json')
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
        'account':ACCOUNT, 'allowance':ALLOWANCE, 'calls':11, 'calls_per_slot':1,
        'configured_total_usd':10, 'segment_cap_usd':.10, 'atomic_cumulative_ceiling_usd':CEILING,
        'job_ids':[r['job_id'] for r in source['requests']],
        'native_sha256':[r['native_sha256'] for r in source['requests']]}


def run(out, anchor, authorization=None):
    manifest, source = frozen(out,anchor,fetch=True)
    require(git('branch','--show-current') == 'main' and git('rev-parse','HEAD') == git('rev-parse','origin/main'),
            'Run requires clean merged main')
    require(inventory(out) <= {'prepared.json','baseline.json',LOCK}, 'Owned run is already consumed')
    before = load(out/'baseline.json')
    verify_prefix(before,snapshot(before),[],allowance=ALLOWANCE,ceiling=CEILING)
    require(authorization is not None and load(authorization) == authorization_scope(anchor, source),
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

    def integrity():
        frozen(out,anchor,provider)
        require(inventory(out) <= set(hashes) | {LOCK}, 'Unowned evidence file appeared')
        require(all(sha(out/name) == value for name,value in hashes.items()), 'Owned evidence changed')
        if acquired:
            require((out/LOCK).is_file(), 'Owned lease lock disappeared')
        rows = binding.rows if binding else []
        require(journal(out) == rows, 'Reservation journal differs from committed prefix')
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
        require(load(out/'authorization.json') == authorization_scope(anchor, source), 'Call scope changed before start')
        owned_save('started.json',{'prepared_manifest_sha256':anchor,'one_shot':True})
        started = True
        # Use ONLY the existing Store reservation method, without constructor DDL,
        # identity insertion or original job/cache writes. Baseline pins identity.
        original = object.__new__(Store)
        original.path, original.account = DB, ACCOUNT.casefold()
        binding = ReservationBinding(original,allowance=ALLOWANCE,ceiling=CEILING,verify=integrity,
            persist=lambda n,row:owned_save(f'reservation-{n:02}.json',row))
        execute_cases(provider,slots,gate=integrity,identity=identity,claim=claim,reserve=reserve,persist=persist,
            retain_terminal=lambda n,event:owned_save(f'terminal-{n:02}.json',event),record=record,
            cancelled=lambda:(out.parent/(out.name+'.cancel')).exists())
    except BaseException as exc:
        failure = {'exception_type':type(exc).__name__,'stopped_slot':active}
    finally:
        try:
            if started:
                owned_save('summary.json',{'results':[{k:r[k] for k in ('slot','job_id','disposition')} for r in results],
                    'failure':failure,'unattempted':[n for n in range(1,12) if not (out/f'attempt-{n:02}.json').exists()],
                    'retries':False})
                integrity()
                owned_save('final-integrity.json',snapshot(before))
                hashes[LOCK] = owned_sha(LOCK)
                require(inventory(out) == set(hashes)
                        and all(owned_sha(name) == value for name,value in hashes.items()),
                        'Cannot seal incomplete or changed owned evidence')
                save(out,'owned-artifacts.json',hashes)
                print(json.dumps({'receipt_manifest_sha256':sha(out/'owned-artifacts.json'),
                                  'retain_outside_output_directory':True}))
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
