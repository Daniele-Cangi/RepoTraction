"""Separate reviewed-main freeze and explicitly authorized operation one-shot CLI.

Prepare/verify use public knobs and read-only history without credentials/network
provider activity. Run requires an independent manifest digest and exact human
authorization. Neither merge nor preparation grants that authorization.
"""
import argparse
from pathlib import Path
import re
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from github_cli import verify_cli_account
from missing_link.config import provider_environment
from missing_link.provider import Provider, NoRedirect
from scripts import missing_link_stream_successor_run as consumed
from scripts.missing_link_cadence_history import compile_history
from scripts.missing_link_checkpoint_cadence import FilePin
from scripts.missing_link_operation_executor import successor_manifest, bind_requests
from scripts.missing_link_operation_owned import run_bound_owned, unused_job_ids, authorization_scope
from scripts.missing_link_demand_operation_policy_v3_executor import same_slot_structure
from scripts.missing_link_repository_only_evaluator import require
from scripts.missing_link_repository_only_run import git, load, save, sha, inventory
from scripts.missing_link_triage_transport import IdentityCheck

ACCOUNT, ALLOWANCE, DB = consumed.ACCOUNT, consumed.ALLOWANCE, consumed.DB
BASE_RESERVED, CEILING = 8.1408513, 8.2408513
OWNED_RELATIVE = 'data/missing-link-demand-operation-policy-v3-operation-owned-run-2026-10-10'
ADAPTERS = ('scripts/missing_link_operation_owned.py', 'scripts/missing_link_operation_run.py',
            'tests/test_missing_link_operation_run.py', 'docs/missing-link-operation-live-contract-2026-10-10.md')


def owned_path(out):
    target = (ROOT/OWNED_RELATIVE).resolve()
    require(target.is_relative_to(ROOT.resolve()) and out.resolve() == target and not out.is_symlink(),
            'Only the separately named owned directory may prepare, verify or run')


def execution_tree(head, tree):
    require(git('rev-parse', 'HEAD', 'HEAD^{tree}', 'origin/main').splitlines() == [head, tree, head]
            and git('branch', '--show-current') == 'main' and not git('status', '--porcelain'),
            'Run requires the exact clean frozen reviewed/merged main')


def compiled_history(head, tree):
    result = compile_history(tree=lambda: execution_tree(head, tree), additional_code=tuple(
        FilePin(ROOT/name, sha(ROOT/name, canonical=True), True) for name in ADAPTERS))
    result['root'] = ROOT
    return result


def operation_source(source):
    result = successor_manifest(source)
    result['atomic_cumulative_ceiling_usd'] = CEILING
    return result


def freeze_values(compiled, *, head, tree, reviewed_head, baseline_sha):
    source = operation_source(compiled['source'])
    return {'required_main': head, 'reviewed_head': reviewed_head, 'reviewed_tree': tree,
        'baseline_sha256': baseline_sha, 'source_preparation_sha256': consumed.PREP_SHA,
        'owned_output': OWNED_RELATIVE,
        'code_sha256_canonical_lf': {p.path.relative_to(ROOT).as_posix(): p.sha256 for p in compiled['code_pins']},
        'account': ACCOUNT, 'allowance': ALLOWANCE, 'configured_total_usd': 10,
        'segment_cap_usd': .10, 'atomic_cumulative_ceiling_usd': CEILING,
        'new_calls': 0, 'new_reservations': 0, 'call_authorization_granted': False, 'source': source}


def public_bind(source):
    provider = Provider(dict(consumed.settings(), REPOTRACTION_AI_KEY='offline-public-binding'))
    bind_requests(provider, load(consumed.PREP/'inputs.json')['cases'], source,
                  lambda name: (consumed.PREP/name).read_bytes())


def prepare(out, reviewed_head):
    owned_path(out)
    require(not out.exists(), 'Owned output already exists; never replace it')
    require(type(reviewed_head) is str and re.fullmatch(r'[a-f0-9]{40}', reviewed_head),
            'Reviewed full head required')
    git('fetch', 'origin', 'main')
    head, tree = git('rev-parse', 'HEAD'), git('rev-parse', 'HEAD^{tree}')
    execution_tree(head, tree)
    require(git('rev-parse', reviewed_head+'^{tree}') == tree, 'Merged tree differs from reviewed content')
    compiled = compiled_history(head, tree)
    require(compiled['baseline']['reservations'] == 579
            and abs(compiled['baseline']['reserved_usd']-BASE_RESERVED) < 1e-10, 'Original accounting changed')
    source = operation_source(compiled['source'])
    public_bind(source)
    unused_job_ids(DB, [r['job_id'] for r in source['requests']])
    out.mkdir()  # Exclusive; a partial freeze cannot be reused or replaced.
    save(out, 'baseline.json', compiled['baseline'])
    save(out, 'prepared.json', freeze_values(compiled, head=head, tree=tree,
        reviewed_head=reviewed_head, baseline_sha=sha(out/'baseline.json')))
    return {'prepared_manifest_sha256': sha(out/'prepared.json'), 'new_calls': 0,
            'new_reservations': 0, 'retain_outside_output_directory': True}


def frozen(out, anchor, *, fetch=False):
    owned_path(out)
    require(type(anchor) is str and re.fullmatch(r'[a-f0-9]{64}', anchor)
            and sha(out/'prepared.json') == anchor, 'Independent prepared manifest anchor required')
    require(inventory(out) == {'prepared.json', 'baseline.json'}, 'Owned run is already consumed')
    manifest = load(out/'prepared.json')
    require(all(type(manifest.get(k)) is str and re.fullmatch(r'[a-f0-9]{40}', manifest[k])
                for k in ('required_main', 'reviewed_head', 'reviewed_tree')), 'Invalid frozen Git identity')
    if fetch: git('fetch', 'origin', 'main')
    execution_tree(manifest['required_main'], manifest['reviewed_tree'])
    require(git('rev-parse', manifest['reviewed_head']+'^{tree}') == manifest['reviewed_tree'],
            'Frozen reviewed tree changed')
    compiled = compiled_history(manifest['required_main'], manifest['reviewed_tree'])
    require(same_slot_structure(load(out/'baseline.json'), compiled['baseline'])
            and same_slot_structure(manifest, freeze_values(compiled, head=manifest['required_main'],
                tree=manifest['reviewed_tree'], reviewed_head=manifest['reviewed_head'],
                baseline_sha=sha(out/'baseline.json'))), 'Frozen operation scope changed')
    public_bind(manifest['source'])
    unused_job_ids(DB, [r['job_id'] for r in manifest['source']['requests']])
    return manifest, compiled


def run(out, anchor, authorization):
    manifest, compiled = frozen(out, anchor, fetch=True)
    require(authorization is not None and authorization.is_file() and not authorization.is_symlink(),
            'Separate exact-scope human call authorization record required')
    approved = load(authorization)
    require(same_slot_structure(approved, authorization_scope(anchor, manifest)),
            'Separate exact-scope human call authorization record required')
    # No credentials, opener construction or original reservation before this gate.
    env = provider_environment()
    env.update(REPOTRACTION_AI_MAX_CALLS='1', REPOTRACTION_AI_MAX_COST_USD='0.02',
               REPOTRACTION_AI_MAX_OUTPUT_TOKENS='6000')
    provider, source = Provider(env), manifest['source']
    packets = load(consumed.PREP/'inputs.json')['cases']
    read = lambda name: (consumed.PREP/name).read_bytes()
    bind_requests(provider, packets, source, read)
    identity = IdentityCheck(lambda: verify_cli_account(ACCOUNT, run=subprocess.run), time.monotonic)
    return run_bound_owned(out, manifest=manifest, anchor=anchor, source=source, authorization=approved,
        provider=provider, packets=packets, read=read, database=DB, account=ACCOUNT, allowance=ALLOWANCE,
        ceiling=CEILING, compiled=compiled,
        tree=lambda: execution_tree(manifest['required_main'], manifest['reviewed_tree']), identity=identity,
        opener_factory=lambda: urllib.request.build_opener(NoRedirect()),
        cancelled=lambda: (out.parent/(out.name+'.cancel')).exists())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'verify', 'run'))
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--reviewed-head')
    parser.add_argument('--prepared-manifest-sha256')
    parser.add_argument('--call-authorization', type=Path)
    args = parser.parse_args()
    out = args.output.resolve()
    if args.action == 'prepare': result = prepare(out, args.reviewed_head)
    elif args.action == 'verify':
        frozen(out, args.prepared_manifest_sha256, fetch=True)
        result = {'verified': True, 'new_calls': 0, 'new_reservations': 0}
    else: result = run(out, args.prepared_manifest_sha256, args.call_authorization)
    # Keep semantic/provider output in private evidence, not console diagnostics.
    import json
    print(json.dumps({k: v for k, v in result.items() if k != 'results'}))


if __name__ == '__main__':
    main()
