"""Authored Git outputs; no Git subprocess, network or provider calls."""
from dataclasses import FrozenInstanceError
import unittest
from unittest.mock import Mock

from scripts.missing_link_cadence_git import GitTreeAudit
from scripts.missing_link_repository_only_evaluator import EvaluationStopped


class GitTreeAuditTests(unittest.TestCase):
    HEAD, TREE = 'a'*40, 'b'*40

    def test_every_audit_resolves_both_names_and_checks_fresh_status(self):
        run = Mock(side_effect=[self.HEAD+'\n'+self.TREE, '']*3)
        audit = GitTreeAudit(self.HEAD, self.TREE, run)
        for _ in range(3): audit()
        self.assertEqual(run.call_count, 6)
        self.assertEqual(run.call_args_list[::2], [unittest.mock.call('rev-parse', 'HEAD', 'HEAD^{tree}')]*3)
        self.assertEqual(run.call_args_list[1::2], [unittest.mock.call('status', '--porcelain')]*3)

    def test_head_tree_and_output_shape_changes_are_rejected(self):
        for output in ('c'*40+'\n'+self.TREE, self.HEAD+'\n'+'c'*40, self.HEAD,
                       self.HEAD+'\n'+self.TREE+'\n'+'c'*40, ''):
            with self.subTest(output=output):
                run = Mock(return_value=output)
                with self.assertRaises(EvaluationStopped): GitTreeAudit(self.HEAD, self.TREE, run)()
                self.assertEqual(run.call_count, 1)

    def test_clean_identity_does_not_hide_staged_unstaged_or_untracked_changes(self):
        for status in (' M authored.py', 'M  authored.py', '?? authored.py'):
            with self.subTest(status=status):
                run = Mock(side_effect=[self.HEAD+'\n'+self.TREE, status])
                with self.assertRaises(EvaluationStopped): GitTreeAudit(self.HEAD, self.TREE, run)()

    def test_command_failures_propagate_without_becoming_clean_outputs(self):
        for which in (1, 2):
            with self.subTest(command=which):
                primary = OSError('Authored Git command failure')
                run = Mock(side_effect=([self.HEAD+'\n'+self.TREE] if which == 2 else []) + [primary])
                with self.assertRaises(OSError) as caught: GitTreeAudit(self.HEAD, self.TREE, run)()
                self.assertIs(caught.exception, primary)

    def test_invalid_bindings_fail_before_any_git_command_and_valid_binding_is_immutable(self):
        run = Mock()
        for head, tree in (('', self.TREE), ('A'*40, self.TREE), (True, self.TREE), (self.HEAD, 'bad')):
            with self.subTest(head=head, tree=tree):
                with self.assertRaises(EvaluationStopped): GitTreeAudit(head, tree, run)
        run.assert_not_called()
        with self.assertRaises(FrozenInstanceError): GitTreeAudit(self.HEAD, self.TREE, run).head = 'c'*40


if __name__ == '__main__': unittest.main()
