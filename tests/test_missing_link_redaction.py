"""Key-safe private audit regression fixtures; no real keys or provider calls."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from missing_link.provider import Provider
from missing_link.sources import SECRET_TEXT
from missing_link.store import Store, redact_payload
import test_missing_link as fixtures


def credential_keys():
    return ["ghp_" + "A" * 36, "github_pat_" + "B" * 36, "sk-proj-" + "C" * 36, "AKIA" + "D" * 16]


class PayloadRedactionTests(unittest.TestCase):
    def test_ordinary_keys_and_json_values_are_unchanged(self):
        value = {"status": "unresolved", "requirements": [{"citation_id": "s0", "mandatory": True}],
            "counts": [0, 2.5, False, None], "unicode": {"café": "文章"}, "empty": {}}
        self.assertEqual(redact_payload(value), value)
        self.assertEqual(list(redact_payload(value)), list(value))

    def test_credential_patterns_are_redacted_in_keys_values_and_nested_lists(self):
        for key in credential_keys():
            with self.subTest(pattern=key.split("_", 1)[0][:8]):
                value = {"entries": [{"prefix " + key + " suffix": {key: key}}]}
                safe = redact_payload(value)
                self.assertFalse(SECRET_TEXT.search(json.dumps(safe)))
                self.assertEqual(safe, {"entries": [{"prefix [REDACTED] suffix": {"[REDACTED]": "[REDACTED]"}}]})

    def test_colliding_redactions_preserve_values_and_reserved_literal_fields(self):
        first, second = credential_keys()[:2]
        for literals_first in (False, True):
            secrets = {first: {"value": 1}, second: {"value": 2}}
            literals = {"[REDACTED]": "literal", "[REDACTED] [redacted-key 1]": "literal suffix"}
            value = dict(literals, **secrets) if literals_first else dict(secrets, **literals)
            safe = redact_payload(value)
            self.assertEqual(len(safe), len(value))
            self.assertEqual(safe["[REDACTED]"], "literal")
            self.assertEqual(safe["[REDACTED] [redacted-key 1]"], "literal suffix")
            self.assertEqual(safe["[REDACTED] [redacted-key 2]"], {"value": 1})
            self.assertEqual(safe["[REDACTED] [redacted-key 3]"], {"value": 2})
            self.assertFalse(SECRET_TEXT.search(json.dumps(safe)))

    def test_many_colliding_keys_keep_all_entries_without_repeated_suffix_search(self):
        value = {"ghp_" + f"{index:030d}": index for index in range(1000)}
        value["[REDACTED] [redacted-key 1]"] = "reserved"
        safe = redact_payload(value)
        self.assertEqual(len(safe), len(value))
        self.assertEqual({item for item in safe.values() if isinstance(item, int)}, set(range(1000)))
        self.assertEqual(safe["[REDACTED] [redacted-key 1]"], "reserved")
        self.assertFalse(SECRET_TEXT.search(json.dumps(safe)))

    def test_nested_collisions_have_independent_namespaces(self):
        first, second = credential_keys()[:2]
        value = {first: {first: 1, second: 2}, second: [{first: 3, "[REDACTED]": 4}]}
        safe = redact_payload(value)
        self.assertEqual(len(safe), 2)
        self.assertEqual(safe["[REDACTED]"], {"[REDACTED]": 1, "[REDACTED] [redacted-key 1]": 2})
        self.assertEqual(safe["[REDACTED] [redacted-key 1]"], [{"[REDACTED] [redacted-key 1]": 3, "[REDACTED]": 4}])

    def test_redaction_is_deterministic_idempotent_and_does_not_mutate_input(self):
        first, second = credential_keys()[:2]
        value = {first: {second: "fixture"}, second: [first], "[REDACTED]": "literal"}
        original = copy.deepcopy(value)
        safe = redact_payload(value)
        self.assertEqual(value, original)
        self.assertEqual(redact_payload(value), safe)
        self.assertEqual(redact_payload(safe), safe)
        self.assertEqual(redact_payload(json.loads(json.dumps(safe))), safe)

    def test_redacted_key_collisions_survive_repeated_storage_without_loss(self):
        first, second = credential_keys()[:2]
        output = {first: {second: "fixture"}, second: 2, "[REDACTED]": "literal"}
        with tempfile.TemporaryDirectory() as directory:
            store = Store(Path(directory) / "fixture.sqlite3", "fixture")
            record = {"id": "fixture", "checkpoint": {"ai_outputs": [{"output": output}]}}
            store.put("jobs", "fixture", record)
            saved = store.get("jobs", "fixture")
            self.assertEqual(saved["checkpoint"]["ai_outputs"][0]["output"], redact_payload(output))
            store.put("jobs", "fixture", saved)
            self.assertEqual(Store(store.path, "fixture").get("jobs", "fixture"), saved)
            with store.connection() as db:
                raw = db.execute("SELECT payload FROM ml_jobs").fetchone()[0]
            self.assertFalse(SECRET_TEXT.search(raw))
            self.assertEqual(record["checkpoint"]["ai_outputs"][0]["output"], output)


class AuditKeyPersistenceTests(unittest.TestCase):
    setUp = fixtures.ServiceTests.setUp
    fake_sources = fixtures.ServiceTests.fake_sources

    def test_shape_invalid_credential_keys_are_retained_redacted_and_still_rejected(self):
        first, second = credential_keys()[:2]
        output = {first: {second: "fixture"}, second: [first], "[REDACTED]": "literal"}
        provider = Provider({"REPOTRACTION_AI_URL": "http://localhost/v1", "REPOTRACTION_AI_MODEL": "fixture",
            "REPOTRACTION_AI_API_KIND": "responses", "REPOTRACTION_AI_INPUT_USD_PER_MILLION": "1",
            "REPOTRACTION_AI_OUTPUT_USD_PER_MILLION": "1"})
        self.service.provider = provider
        result = {"id": "resp_redaction_fixture", "status": "completed", "output": [{"type": "message", "content": [
            {"type": "output_text", "text": json.dumps(output)}]}], "usage": {"input_tokens": 10, "output_tokens": 20}}
        opener, response, source = mock.Mock(), mock.MagicMock(), self.fake_sources()
        response.__enter__.return_value.read.return_value = json.dumps(result).encode()
        opener.open.return_value = response
        with mock.patch("missing_link.service.PublicGitHub", return_value=source), \
             mock.patch("missing_link.service.extract_structure", return_value=fixtures.repository()["capabilities"]), \
             mock.patch.object(provider, "interpret_capabilities", return_value=fixtures.repository()["capabilities"]), \
             mock.patch("urllib.request.build_opener", return_value=opener), \
             mock.patch.object(provider, "evaluate") as evaluate:
            started = self.service.start({"repo": "example/words", "issue_url": fixtures.issue()["url"], "use_ai": True}, background=False)
        job = Store(self.path, "alice").get("jobs", started["job_id"])
        self.assertEqual(job["status"], "completed")
        self.assertTrue(job["result"]["partial"])
        self.assertEqual(job["result"]["match_ids"], [])
        self.assertEqual(job["checkpoint"]["ai_outputs"][0]["output"], redact_payload(output))
        self.assertEqual(len(job["checkpoint"]["ai_outputs"][0]["output"]), len(output))
        self.assertEqual(job["ai_calls_used"], 1)
        self.assertGreater(job["cost_reserved_usd"], 0)
        self.assertEqual(len(job["ai_trace"]), 1)
        self.assertEqual(len(job["reported_usage"]), 1)
        self.assertEqual(opener.open.call_count, 1)
        self.assertFalse(SECRET_TEXT.search(json.dumps(job)))
        evaluate.assert_not_called()
        source.fetch_reference_context.assert_not_called()
