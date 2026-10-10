"""Exact offline owned adapter, actual read-only history, authored transport.

No original ledger writes, CLI authentication, provider credentials or network.
The original repository/history must be present locally and remain unchanged.
Exit 1 when fixed performance gates fail; no result authorizes a paid attempt.
"""
import argparse
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from missing_link.provider import Provider
from scripts.missing_link_demand_operation_policy import FIELDS
from scripts.missing_link_cadence_history import compile_history
from scripts.missing_link_cadence_executor import successor_manifest
from scripts.missing_link_cadence_owned import run_offline_owned
from scripts.missing_link_repository_only_evaluator import require
from scripts.missing_link_repository_only_run import git, load
from scripts.missing_link_stream_successor_run import PREP, settings, ACCOUNT, ALLOWANCE
from scripts.missing_link_triage_transport import IdentityCheck


class Profile:
    """Fixed names, bounded samples, no paths or raw evidence in public output."""
    def __init__(self): self.values = {}

    def __call__(self, name, callback):
        start = time.perf_counter()
        try:
            return callback()
        finally:
            seconds = time.perf_counter() - start
            item = self.values.setdefault(name, {'count': 0, 'seconds': 0, 'max_seconds': 0, 'first_three_seconds': []})
            item['count'] += 1
            item['seconds'] += seconds
            item['max_seconds'] = max(item['max_seconds'], seconds)
            if len(item['first_three_seconds']) < 3:
                item['first_three_seconds'].append(seconds)


def authored_terminal():
    raw = {'request_kind': {'value': 'unknown', 'reason': 'Authored fixture.', 'citation_ids': []},
           'fields': {name: {'state': 'unknown', 'text': '', 'reason': 'Authored fixture.', 'citation_ids': []}
                      for name in FIELDS}, 'constraints': [],
           'query_relation': {'value': 'unclear', 'reason': 'Authored fixture.', 'citation_ids': []},
           'context_gaps': ['Authored offline stream; no model judgment.']}
    return {'type': 'response.completed', 'response': {'id': 'authored-offline', 'status': 'completed',
        'usage': {'input_tokens': 50, 'output_tokens': 25},
        'output': [{'type': 'message', 'content': [{'type': 'output_text', 'text': json.dumps(raw)}]}]}}


class AuthoredOpener:
    def __init__(self, lines): self.lines, self.opens = lines, 0

    def open(self, request, *, timeout):
        require(timeout == 55 and self.opens == 0, 'Offline transport attempted a retry')
        self.opens += 1
        return io.BytesIO(b': authored buffered stream\n' * self.lines
            + b'data: ' + json.dumps(authored_terminal()).encode() + b'\n')


def benchmark(*, temp_parent=None, workloads=(10000, 60000)):
    head, tree = git('rev-parse', 'HEAD'), git('rev-parse', 'HEAD^{tree}')
    require(not git('status', '--porcelain'), 'Offline measurement requires a clean committed implementation')

    def check_tree():
        require(git('rev-parse', 'HEAD') == head and git('rev-parse', 'HEAD^{tree}') == tree
                and not git('status', '--porcelain'), 'Measured implementation changed')

    def forbidden(*args, **kwargs): raise AssertionError('Offline integration forbids network and credentials')

    with patch('socket.socket', side_effect=forbidden), \
         patch('urllib.request.build_opener', side_effect=forbidden), \
         patch('missing_link.config.provider_environment', side_effect=forbidden), \
         patch('missing_link.provider.provider_environment', side_effect=forbidden):
        compilation_started = time.perf_counter()
        compiled = compile_history(tree=check_tree)
        compilation_seconds = time.perf_counter()-compilation_started
        source = successor_manifest(compiled['source'])
        packets = load(PREP/'inputs.json')['cases']
        # Dummy key permits the ordinary readiness checks, but cannot be sent:
        # the only injected opener returns the authored BytesIO above.
        provider = Provider(dict(settings(), REPOTRACTION_AI_KEY='authored-offline-not-a-credential'))
        runs = []
        for lines in workloads:
            profile = Profile()
            compiled['audit'].measure = profile
            before_counts = compiled['database_audit'].snapshot()
            with tempfile.TemporaryDirectory(prefix='repotraction-cadence-owned-', dir=temp_parent) as temporary:
                scratch = Path(temporary).resolve()
                identity_file = scratch/'authored-identity.txt'
                identity_file.write_text(ACCOUNT, encoding='utf-8')
                def account():
                    require(identity_file.read_text(encoding='utf-8') == ACCOUNT, 'Authored identity changed')
                identity = IdentityCheck(account, time.monotonic)
                opener = AuthoredOpener(lines)
                start = time.perf_counter()
                result = run_offline_owned(scratch/'run', provider=provider, packets=packets,
                    manifest=source, read=lambda name: (PREP/name).read_bytes(), code_pins=compiled['code_pins'],
                    historical_audit=compiled['audit'], identity=identity, opener_factory=lambda: opener,
                    allowance=ALLOWANCE, account=ACCOUNT, base_reserved=8.1408513, ceiling=8.2408513,
                    case_limit=1, measure=profile, cancelled=lambda: (scratch/'cancel').exists())
                elapsed = time.perf_counter()-start
                trace = load(scratch/'run/evidence/diagnostics-01.json')
                critical = profile.values['critical']['first_three_seconds']
                history = profile.values['history']['first_three_seconds']
                gates = {'critical_first_three_max_le_100ms': len(critical) == 3 and max(critical) <= .1,
                         'history_first_three_max_le_5s': len(history) == 3 and max(history) <= 5,
                         'whole_owned_probe_within_budget': elapsed <= (30 if lines == 10000 else 120)}
                runs.append({'nonterminal_lines': lines, 'attempted_authored_slots': 1,
                    'unattempted_slots': list(range(2, 12)), 'whole_owned_seconds': elapsed,
                    'stream_trace': trace, 'profile': copy.deepcopy(profile.values), 'gates': gates,
                    'gate_passed': all(gates.values()), 'authored_result_count': len(result['results']),
                    'database_audit_counts': {k: v-before_counts[k]
                        for k, v in compiled['database_audit'].snapshot().items()}})
        compiled['audit']()
    return {'scope': 'exact_offline_owned_adapter_original_read_only_history_authored_identity_and_transport',
        'implementation_head': head, 'implementation_tree': tree, 'historical_artifacts': 1740,
        'compilation_seconds_outside_owned_gates': compilation_seconds,
        'consumed_code_fingerprints': 58, 'runs': runs,
        'original_reservations': 579, 'original_reserved_usd': 8.1408513,
        'original_database_unchanged': True, 'provider_calls': 0, 'original_new_reservations': 0,
        'performance_gate_passed': all(r['gate_passed'] for r in runs),
        'paid_readiness': False, 'call_authorization_granted': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--temp-parent', type=Path)
    args = parser.parse_args()
    result = benchmark(temp_parent=args.temp_parent)
    print(json.dumps(result, indent=2))
    return 0 if result['performance_gate_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
