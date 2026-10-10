"""Same wire/ownership controls plus mutations across protected-unit boundaries."""
from unittest.mock import Mock, patch

from missing_link.store import Store
from scripts import missing_link_operation_executor as executor
from scripts import missing_link_cadence_executor as legacy
from scripts import missing_link_demand_operation_policy_v3_executor as policy
from scripts.missing_link_repository_only_evaluator import EvaluationStopped
from scripts.missing_link_repository_only_run import load
from test_missing_link_cadence_integration import CadenceIntegrationTests as _Base
from test_missing_link_stream_successor_receipts import Stream


class OperationIntegrationTests(_Base):
    operation_units = True
    executor_module = executor

    def usage_checkpoint(self, owner):
        files = sorted(owner.out.glob('checkpoint-01-*.json'))
        if not files: return False
        job = load(files[-1])
        return 'reported_usage' in job and 'ai_trace' not in job

    def test_single_attempt_has_21_full_audits_and_accepts_only_sealed_results(self):
        history = Mock()
        result = self.owned(history=history, case_limit=1)
        self.assertEqual(history.call_count, 21)
        self.assertEqual(len(result['results']), 1)
        self.assertTrue((self.workspace/'evidence/owned-artifacts.json').exists())

    def test_original_history_change_between_accounting_writes_blocks_acceptance(self):
        changed = False
        primary = EvaluationStopped('Authored original mutation inside account unit')
        def observe(stage, owner):
            nonlocal changed
            if stage == 'persist' and self.usage_checkpoint(owner): changed = True
        def history():
            if changed: raise primary
        with self.assertRaises(EvaluationStopped) as caught: self.owned(observe=observe, history=history)
        self.assertIs(caught.exception, primary)
        self.assertEqual(self.opens, 1)
        out = self.workspace/'evidence'
        self.assertFalse((out/'result-01.json').exists())
        self.assertFalse((out/'attempt-02.json').exists())
        self.assertFalse((out/'owned-artifacts.json').exists())

    def test_foreign_owned_reservation_stops_before_the_next_accounting_checkpoint(self):
        def observe(stage, owner):
            if stage == 'persist' and self.usage_checkpoint(owner):
                Store(owner.out.parent/'authored-ledger.sqlite3', self.fixture.source['account']).reserve_ai_allowance(
                    self.fixture.source['allowance'], 'foreign', .001, 10)
        with self.assertRaises(EvaluationStopped): self.owned(observe=observe)
        out = self.workspace/'evidence'
        self.assertFalse((out/'checkpoint-01-003.json').exists())
        self.assertFalse((out/'attempt-02.json').exists())
        self.assertFalse((out/'owned-artifacts.json').exists())

    def test_storage_failure_inside_account_unit_retains_charge_and_stops_all_later_writes(self):
        primary = OSError('Authored accounting checkpoint storage failure')
        def observe(stage, owner):
            if stage == 'persist' and self.usage_checkpoint(owner): raise primary
        with self.assertRaises(OSError) as caught: self.owned(observe=observe)
        self.assertIs(caught.exception, primary)
        out = self.workspace/'evidence'
        self.assertTrue((out/'reservation-01.json').exists())
        self.assertFalse((out/'checkpoint-01-003.json').exists())
        self.assertFalse((out/'attempt-02.json').exists())

    def test_cleanup_mutation_is_checked_before_accounting_unit_entry(self):
        changed = False
        close = Stream.__exit__
        def cleanup(stream, *args):
            nonlocal changed
            value = close(stream, *args)
            changed = True
            return value
        def history():
            if changed: raise EvaluationStopped('Authored history mutation during response cleanup')
        with patch.object(Stream, '__exit__', cleanup):
            with self.assertRaises(EvaluationStopped): self.owned(history=history)
        self.assertFalse((self.workspace/'evidence/checkpoint-01-002.json').exists())
        self.assertFalse((self.workspace/'evidence/owned-artifacts.json').exists())

    def test_history_mutation_cannot_be_hidden_by_a_local_normalizer_refusal(self):
        changed = False
        primary = EvaluationStopped('Authored original mutation during normalization')
        def normalize(*a, **k):
            nonlocal changed
            changed = True
            raise ValueError('Authored local refusal')
        def history():
            if changed: raise primary
        with patch.object(policy, 'normalize_prediction', side_effect=normalize):
            with self.assertRaises(EvaluationStopped) as caught: self.owned(history=history)
        self.assertIs(caught.exception, primary)
        self.assertFalse((self.workspace/'evidence/attempt-02.json').exists())
        self.assertFalse((self.workspace/'evidence/owned-artifacts.json').exists())

    def test_revision_and_unused_accounting_ids_cannot_mix_with_legacy_cadence(self):
        with self.assertRaises(EvaluationStopped):
            legacy.bind_requests(self.fixture.provider, self.fixture.packets, self.manifest,
                                 self.fixture.files.__getitem__)
        for value in (True, 0, 2):
            changed = dict(self.manifest, protected_operation_revision=value)
            with self.assertRaises(EvaluationStopped):
                executor.bind_requests(self.fixture.provider, self.fixture.packets, changed,
                                       self.fixture.files.__getitem__)


del _Base  # Avoid rediscovering the imported legacy test class in this module.
