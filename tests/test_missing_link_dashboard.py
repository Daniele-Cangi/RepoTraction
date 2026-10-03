"""Opt-in scoped polling preserves full evidence and legacy/account contracts."""
import copy
from contextlib import ExitStack
import hashlib
import http.client
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest import mock

import app
from github_cli import ActiveAccountChangedError, GitHubAccountVerificationError
from missing_link.dashboard_state import dashboard_selection, project_dashboard
from missing_link.job_errors import job_failure
from missing_link.service import Service
import test_missing_link as fixtures


def state_fixture():
    quote = 'complete source evidence ' * 1000
    return {'account': 'alice', 'provider': {'configured': False}, 'isolation': {'host_execution': False},
        'repositories': [
            {'id': 7, 'full_name': 'alice/source', 'revision': 'a' * 40,
                'capabilities': [{'id': 'a', 'evidence': [{'quote': quote}]}], 'coverage': {'complete': False}},
            {'id': 8, 'full_name': 'bob/other', 'revision': 'b' * 40,
                'capabilities': [{'id': 'b', 'evidence': [{'quote': quote}]}]}],
        'matches': [
            {'id': 'current', 'repo_id': 7, 'repo': 'alice/source', 'request': {'body': quote}},
            {'id': 'renamed', 'repo_id': '7', 'repo': 'alice/old-name', 'stale': True,
                'superseded': True, 'checks': [{'evidence': [{'quote': quote}]}]},
            {'id': 'different-id', 'repo_id': 8, 'repo': 'alice/source', 'bridge': {'files': [{'content': quote}]}},
            {'id': 'missing-id', 'repo': 'alice/source'}],
        'jobs': [{'id': 'job', 'status': 'paused', 'input': {'repo': 'alice/source', 'max_requests': 80},
            'requests_used': 80, 'ai_calls_used': 2, 'cost_reserved_usd': .1,
            'ai_trace': [{'source_context': quote}], 'reported_usage': [{'input_tokens': 5}],
            'result': {'partial': True, 'candidate_errors': [{'error': 'Invalid quote'}],
                'non_demands': [{'status_evidence': [{'quote': quote}]}]}}],
        'extension_groups': [{'requirement': 'fixture', 'match_ids': ['current', 'different-id']}],
        'safety': {'publication': False}, 'limits': {'source_files': 24}}


class DashboardProjectionTests(unittest.TestCase):
    def test_full_contract_remains_default_and_unknown_legacy_queries_stay_ignored(self):
        for query in (None, {}, {'repo': ['alice/source']}, {'legacy': ['value']}):
            self.assertIsNone(dashboard_selection(query))
        self.assertEqual(dashboard_selection({'view': ['dashboard']}), '')
        self.assertEqual(dashboard_selection({'view': ['dashboard'], 'repo': ['Alice/source']}), 'Alice/source')

    def test_invalid_view_repository_and_duplicate_selection_fail_before_state_access(self):
        for query in ({'view': ['other']}, {'view': ['dashboard', 'dashboard']},
                {'view': ['dashboard'], 'repo': ['a/b', 'a/c']},
                {'view': ['dashboard'], 'repo': ['https://github.com/a/b']},
                {'view': ['dashboard'], 'repo': ['a/b?token=fixture']},
                {'view': ['dashboard'], 'repo': ['a/b#fragment']},
                {'view': ['dashboard'], 'repo': [' a/b']},
                {'view': ['dashboard'], 'repo': ['a/' + 'x' * 101]}):
            with self.subTest(query=query), self.assertRaises(ValueError):
                dashboard_selection(query)

    def test_selected_evidence_is_lossless_without_mutating_the_full_state(self):
        state = state_fixture()
        before = copy.deepcopy(state)
        projected = project_dashboard(state, 'ALICE/SOURCE')
        self.assertEqual(projected['repositories'][0], state['repositories'][0])
        self.assertEqual(projected['matches'], state['matches'][:2])
        self.assertEqual(projected['jobs'][0]['result'], state['jobs'][0]['result'])
        self.assertEqual(projected['jobs'][0]['reported_usage'], state['jobs'][0]['reported_usage'])
        self.assertEqual(projected['jobs'][0]['cost_reserved_usd'], .1)
        self.assertNotIn('ai_trace', projected['jobs'][0])
        self.assertIn('ai_trace', state['jobs'][0])
        for field in ('account', 'provider', 'isolation', 'extension_groups', 'safety', 'limits'):
            self.assertEqual(projected[field], state[field])
        self.assertEqual(state, before)

    def test_unselected_evidence_is_explicitly_unloaded_not_certified_empty(self):
        state = state_fixture()
        projected = project_dashboard(state, 'alice/source')
        other = projected['repositories'][1]
        self.assertFalse(other['evidence_loaded'])
        self.assertEqual(other['capability_count'], 1)
        self.assertNotIn('capabilities', other)
        self.assertEqual(projected['dashboard']['total_matches'], 4)
        self.assertEqual(projected['dashboard']['full_state_url'], '/api/missing-link')
        selected_other = project_dashboard(state, 'bob/other')
        self.assertEqual(selected_other['repositories'][1], state['repositories'][1])
        self.assertEqual(selected_other['matches'], [state['matches'][2]])

    def test_empty_and_unknown_selection_have_an_explicit_index_without_name_inference(self):
        for name in ('', 'alice/not-analyzed'):
            with self.subTest(name=name):
                state = state_fixture()
                projected = project_dashboard(state, name)
                self.assertEqual(projected['dashboard']['selected_repo'], name)
                self.assertIsNone(projected['dashboard']['selected_repo_id'])
                self.assertEqual(projected['matches'], [])
                self.assertTrue(all(repo['evidence_loaded'] is False for repo in projected['repositories']))

    def test_restricted_identity_view_is_never_broadened(self):
        restricted = {'account': 'alice', 'diagnostic_only': True, 'identity_verified': False, 'jobs': []}
        self.assertEqual(project_dashboard(restricted, 'alice/source'), restricted)
        self.assertNotIn('dashboard', project_dashboard(restricted, 'alice/source'))


class DashboardHTTPTests(unittest.TestCase):
    def setUp(self):
        stack = ExitStack()
        self.addCleanup(stack.close)
        directory = stack.enter_context(tempfile.TemporaryDirectory())
        self.path = Path(directory) / 'fixture.sqlite3'
        self.verify = mock.Mock(return_value='alice')
        self.read = mock.Mock(side_effect=AssertionError('No GitHub acquisition'))
        self.provider = mock.Mock()
        self.provider.describe.return_value = {'configured': False}
        self.service = Service(self.path, 'alice', self.read, self.verify, self.provider)
        stack.enter_context(mock.patch.object(app, 'ACCOUNT_LOGIN', 'alice'))
        stack.enter_context(mock.patch.object(app, 'DB_PATH', self.path))
        stack.enter_context(mock.patch.object(app, 'verify_active_account', self.verify))
        stack.enter_context(mock.patch.object(app, '_MISSING_LINK_SERVICES', {
            ('alice', str(self.path.resolve())): self.service}))
        repo, issue = fixtures.repository(), fixtures.issue()
        from missing_link.analysis import validate_matches, validate_request
        match = validate_matches([fixtures.raw_match()], repo, issue,
            validate_request(fixtures.request_raw(), issue), 'model')[0]
        self.service.store.put('repositories', repo['id'], repo)
        self.service.store.save_matches([match], repo)
        self.match_id = match['id']
        self.service.store.put('jobs', 'a' * 32, {'id': 'a' * 32, 'status': 'completed',
            'ai_trace': [{'marker': 'retained trace'}], 'result': {'warning': 'Keep warning'},
            'input': {'repo': repo['full_name']}, 'checkpoint': {'repository': repo, 'discussions': {}}})
        self.server = app.ThreadingHTTPServer(('127.0.0.1', 0), app.DashboardHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop_server)
        self.origin = f'http://127.0.0.1:{self.server.server_port}'

    def stop_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)

    def request(self, path, headers=None):
        client = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=3)
        try:
            client.request('GET', path, headers=headers or {'Origin': self.origin})
            response = client.getresponse()
            raw = response.read()
            value = json.loads(raw) if response.getheader('Content-Type', '').startswith('application/json') else raw
            return response.status, value
        finally:
            client.close()

    def test_legacy_state_and_every_export_remain_equal_after_scoped_poll(self):
        full = self.request('/api/missing-link')[1]
        json_before = self.request('/api/missing-link/export?match_id=' + self.match_id)
        zip_before = self.request('/api/missing-link/package?match_id=' + self.match_id)
        context_before = self.request('/api/missing-link/context?job_id=' + 'a' * 32)
        before = hashlib.sha256(self.path.read_bytes()).hexdigest()
        status, scoped = self.request('/api/missing-link?view=dashboard&repo=example/words')
        self.assertEqual(status, 200)
        self.assertEqual(scoped, project_dashboard(full, 'example/words'))
        self.assertEqual(self.request('/api/missing-link')[1], full)
        self.assertEqual(self.request('/api/missing-link/export?match_id=' + self.match_id), json_before)
        self.assertEqual(self.request('/api/missing-link/package?match_id=' + self.match_id), zip_before)
        self.assertEqual(self.request('/api/missing-link/context?job_id=' + 'a' * 32), context_before)
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(), before)
        self.assertFalse(self.service.threads)
        self.read.assert_not_called()

    def test_scoped_outage_keeps_minimal_diagnostics_without_full_state_or_writes(self):
        self.service.store.put('jobs', 'b' * 32, {'id': 'b' * 32,
            **job_failure(GitHubAccountVerificationError('github_identity_cli_timeout'))})
        self.verify.side_effect = GitHubAccountVerificationError('github_identity_cli_timeout')
        before = hashlib.sha256(self.path.read_bytes()).hexdigest()
        with mock.patch.object(self.service, 'state', side_effect=AssertionError('No full state')):
            status, payload = self.request('/api/missing-link?view=dashboard&repo=example/words')
        self.assertEqual(status, 200)
        self.assertTrue(payload['diagnostic_only'])
        self.assertNotIn('dashboard', payload)
        self.assertNotIn('repositories', payload)
        self.assertNotIn('matches', payload)
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(), before)

    def test_switch_and_ambiguous_identity_deny_scoped_data(self):
        for error in (ActiveAccountChangedError(), GitHubAccountVerificationError('github_identity_ambiguous')):
            with self.subTest(error=type(error).__name__):
                self.verify.side_effect = error
                status, payload = self.request('/api/missing-link?view=dashboard&repo=example/words')
                self.assertEqual(status, 409)
                self.assertEqual(set(payload), {'error'})

    def test_scoped_view_has_the_same_origin_guard(self):
        with mock.patch.object(self.service, 'state', side_effect=AssertionError('No cross-site state')):
            self.assertEqual(self.request('/api/missing-link?view=dashboard', {'Origin': 'http://evil.example'})[0], 403)
        self.verify.assert_not_called()

    def test_invalid_selection_never_reaches_account_or_store(self):
        with mock.patch.object(self.service, 'state', side_effect=AssertionError('No state access')):
            status, payload = self.request('/api/missing-link?view=dashboard&repo=a/b&repo=c/d')
        self.assertEqual(status, 502)  # Existing handle_api validation-error status.
        self.assertIn('single public repository', payload['error'])
        self.verify.assert_not_called()


if __name__ == '__main__':
    unittest.main()
