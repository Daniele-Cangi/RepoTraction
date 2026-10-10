"""Compile independent consumed anchors once for offline cadence integration.

No writer or paid-run entry point. Historical preparation graphs are checked at
compilation; subsequent audits hash immutable pin inventories and the exact DB.
"""
import copy
from pathlib import Path

from scripts import missing_link_stream_successor_run as consumed
from scripts.missing_link_checkpoint_cadence import FilePin, PinnedFiles
from scripts.missing_link_cadence_checks import HistoryAudit
from scripts.missing_link_database_audit import ContentVerifiedSnapshot
from scripts.missing_link_repository_only_evaluator import require, verify_prefix
from scripts.missing_link_repository_only_run import load, sha, inventory, git

OWNED = 'data/missing-link-demand-operation-policy-v3-stream-owned-run-2026-10-09'
ASSESSMENT = 'data/missing-link-demand-operation-policy-v3-stream-owned-assessment-2026-10-10'
# Independently retained native and assessment anchors, never regenerated.
OWNED_PREPARED = 'e9f3b1ee61c97e944a3ba4fe6e9ef5c55db8f70d37a72f8b2bc830ac5a862394'
OWNED_RECEIPT = '30441938e0974e6ed44c95aa094af267a946aa873beed143a26e44fae4e741c1'
ASSESSMENT_PREPARED = 'e5344edf26891c54eb05ed3f6fc786cac112c659636e1975cc9db0871d86662c'
ASSESSMENT_RECEIPT = '3d5f594ff23bcfae2452da57b3a4e387e849e38bac493ff2c90125bfeb8094b8'
MERGED_CADENCE = '65a066b35385b912491bb10e791b4807f710c725'
REVIEWED_CADENCE = 'd997c25a4dc22bd277b9c3308478889fcdf4e7a6'
ADAPTERS = tuple('scripts/missing_link_cadence_' + name + '.py'
                 for name in ('checks', 'reader', 'executor', 'owned', 'history', 'benchmark')) + (
    'scripts/missing_link_checkpoint_cadence.py', 'tests/test_missing_link_cadence_integration.py',
    'scripts/missing_link_database_audit.py', 'tests/test_missing_link_database_audit.py')


def safe_path(root, relative):
    path = Path(relative)
    require(not path.is_absolute() and '..' not in path.parts and (root/path).resolve().is_relative_to(root.resolve()),
            'Invalid protected relative path')
    return root/path


def compile_history(*, tree, additional_code=()):
    """Bind actual private history without reading keys or running old writers."""
    root = consumed.ROOT
    source = consumed.preparation()  # Recursive graph verification happens ONCE.
    git('merge-base', '--is-ancestor', MERGED_CADENCE, 'origin/main')
    require(git('rev-parse', MERGED_CADENCE+'^{tree}') == git('rev-parse', REVIEWED_CADENCE+'^{tree}'),
            'Merged cadence tree differs from reviewed content')
    old = root/OWNED
    require(sha(old/'prepared.json') == OWNED_PREPARED, 'Consumed owned anchor changed')
    manifest = load(old/'prepared.json')
    require(sha(old/'baseline.json') == manifest['baseline_sha256']
            and manifest['preparation_sha256'] == consumed.PREP_SHA
            and manifest['protocol_sha256_lf'] == consumed.PROTOCOL_SHA, 'Consumed preparation binding changed')
    expected = load(consumed.PREP/'baseline.json')
    expected['artifacts'].update({p.relative_to(root).as_posix(): sha(p) for p in consumed.PREP.iterdir()})
    before = load(old/'baseline.json')
    require(before == expected and len(before['artifacts']) == 1714, 'Consumed historical baseline changed')
    code = manifest['code_sha256_canonical_lf']
    require(set(code) == set(source['code_sha256_canonical_lf']) | set(consumed.ADAPTERS)
            and len(code) == 58, 'Consumed executable inventory changed')
    protected, inventories = dict(before['artifacts']), []
    for relative, prepared_anchor, receipt_anchor in (
            (OWNED, OWNED_PREPARED, OWNED_RECEIPT),
            (ASSESSMENT, ASSESSMENT_PREPARED, ASSESSMENT_RECEIPT)):
        folder = root/relative
        require(sha(folder/'prepared.json') == prepared_anchor
                and sha(folder/'owned-artifacts.json') == receipt_anchor, 'Consumed independent seal changed')
        files = load(folder/'owned-artifacts.json')
        require(inventory(folder) == set(files) | {'owned-artifacts.json'}, 'Consumed seal inventory changed')
        for name, value in dict(files, **{'owned-artifacts.json': receipt_anchor}).items():
            path = safe_path(folder, name)
            protected[path.relative_to(root).as_posix()] = value
        inventories.append((folder, set(files) | {'owned-artifacts.json'}))
    assessment = load(root/ASSESSMENT/'prepared.json')
    require(assessment['native_prepared_manifest_sha256'] == OWNED_PREPARED
            and assessment['native_receipt_manifest_sha256'] == OWNED_RECEIPT
            and assessment['source_preparation_sha256'] == consumed.PREP_SHA,
            'Assessment points to different native evidence')
    final = load(old/'final-integrity.json')
    verify_prefix(before, final, consumed.journal(old), allowance=consumed.ALLOWANCE, ceiling=consumed.CEILING)
    require(final['reservations'] == 579 and abs(final['reserved_usd']-8.1408513) < 1e-10
            and len(protected) == 1740, 'Consumed accounting or evidence count changed')
    baseline = copy.deepcopy(final)
    baseline['artifacts'] = protected
    # Preserve explicit inventories of predecessor sealed runs/preparations.
    # Other old baseline entries remain file pins, as in the frozen contract.
    folders = {root/relative for relative, _, _ in consumed.HISTORIES}
    folders.update((consumed.PREP, consumed.predecessor.PREP,
                    root/consumed.predecessor.LEGACY_PREP, root/consumed.predecessor.OLDER_PREP))
    for folder in sorted(folders):
        names = {Path(name).relative_to(folder.relative_to(root)).as_posix()
                 for name in protected if (root/name).parent == folder}
        require(inventory(folder) == names, 'Frozen predecessor inventory changed')
        inventories.append((folder, names))
    pins = (tuple(FilePin(safe_path(root, name), value, True) for name, value in code.items())
            + tuple(FilePin(root/name, sha(root/name, canonical=True), True) for name in ADAPTERS)
            + tuple(additional_code))
    PinnedFiles(pins).verify()
    database_audit = ContentVerifiedSnapshot(consumed.DB, consumed.ALLOWANCE)
    audit = HistoryAudit(root=root, database=consumed.DB, baseline=baseline,
        allowance=consumed.ALLOWANCE, ceiling=8.1408513, rows=lambda: [], tree=tree, inventories=inventories,
        database_audit=database_audit)
    audit()
    return {'source': source, 'baseline': baseline, 'code_pins': pins, 'audit': audit,
            'database_audit': database_audit}
