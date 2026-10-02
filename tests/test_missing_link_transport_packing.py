"""Oversized final prompts repack offline, without truncating extracted demands."""
import copy
import json
import unittest
from unittest import mock

from missing_link.context import build_context
from missing_link.contracts import schema_for
from missing_link.provider import Provider
from test_missing_link import repository, issue


class TransportPackingTests(unittest.TestCase):
    def case(self):
        repo, demand = repository(), issue()
        demand.update(body="Implement the requested operation.", comments=[])
        # A bounded stand-in for the acquired Zod shape: many source excerpts,
        # 27 independently extracted requirements and a large review ledger.
        for index in range(35):
            repo["files"].append({"path": f"src/module_{index}.py", "kind": "source",
                "text": '\\"é\t' * 30 + "\n" + ("fixture = " + '\\"é' * 25 + "\n") * 59,
                "url": "https://github.com/example/words/blob/" + "a" * 40 + f"/src/module_{index}.py"})
        request = {"requirements": [{"id": f"r{i}", "text": "Requested operation " + "x" * 700,
            "source": {"source_id": "q0", "quote": "Implement the requested operation."}} for i in range(27)],
            "constraint_review": {"items": ["review " + "y" * 8900]}}
        return repo, demand, request

    def provider(self, api="responses", format="json_schema"):
        return Provider({"REPOTRACTION_AI_URL": "http://localhost/v1", "REPOTRACTION_AI_MODEL": "fixture",
            "REPOTRACTION_AI_API_KIND": api, "REPOTRACTION_AI_RESPONSE_FORMAT": format,
            "REPOTRACTION_AI_STREAMING": "1", "REPOTRACTION_AI_MAX_PROMPT_BYTES": "180000"})

    def test_full_transport_repacking_preserves_request_and_rebuilds_scope(self):
        repo, demand, request = self.case()
        original = copy.deepcopy((repo, demand, request))
        for api in ("chat", "responses"):
            for format in ("json_object", "json_schema"):
                with self.subTest(api=api, format=format):
                    provider = self.provider(api, format)
                    first, _ = build_context(repo, demand, "matches", provider.max_bytes)
                    first["request"] = request
                    first["schema"] = schema_for("matches", source_ids=first["sources"],
                        capability_ids=["trim"], requirement_ids=[r["id"] for r in request["requirements"]])
                    self.assertGreater(len(provider._encode_prompt("Assess", first, first["schema"], "matches")[2]),
                                       provider.max_bytes)
                    with mock.patch("urllib.request.build_opener") as network:
                        data, report = provider._bounded_context(repo, demand, "matches", "Assess", request)
                    network.assert_not_called()
                    self.assertLessEqual(len(provider._encode_prompt("Assess", data, data["schema"], "matches")[2]),
                                         provider.max_bytes)
                    self.assertEqual(data["request"], request)
                    self.assertEqual(len(data["request"]["requirements"]), 27)
                    self.assertFalse(report["implementation_context_missing"])
                    self.assertIn("file:words.py#L1-L3", data["sources"])
                    self.assertGreater(report["omitted_source_count"], 0)
                    references = data["schema"]["properties"]["matches"]["items"]["properties"]["checks"]["items"]["properties"]["source_ids"]["items"]["enum"]
                    self.assertEqual(set(references), set(data["sources"]))
        self.assertEqual((repo, demand, request), original)

    def test_unsatisfiable_fixed_request_fails_before_reservation_or_http(self):
        repo, demand, request = self.case()
        request["constraint_review"] = {"items": ["z" * 200000]}
        budget = mock.Mock()
        with mock.patch("urllib.request.build_opener") as network, self.assertRaises(ValueError):
            self.provider().evaluate(repo, demand, request, budget)
        network.assert_not_called()
        budget.reserve_ai.assert_not_called()

    def test_complete_sends_the_same_encoding_used_by_preflight(self):
        provider = self.provider()
        data = {"sources": {}, "example": '\\"é\n'}
        endpoint, payload, body = provider._encode_prompt("Inspect", data, None, "analysis")
        opener, response = mock.Mock(), mock.MagicMock()
        opener.open.return_value = response
        # Streaming is enabled: provide a terminal local fixture, not a model.
        result = {"type": "response.completed", "response": {"status": "completed", "output": [
            {"type": "message", "content": [{"type": "output_text", "text": "{}"}]}]}}
        response.__enter__.return_value.readline.side_effect = [("data: " + json.dumps(result) + "\n").encode(), b""]
        with mock.patch("urllib.request.build_opener", return_value=opener):
            provider.complete("Inspect", data, mock.Mock())
        sent = opener.open.call_args.args[0]
        self.assertEqual(sent.data, body)
        self.assertEqual(sent.full_url, provider.url + endpoint)
        self.assertEqual(json.loads(body), payload)


if __name__ == "__main__":
    unittest.main()
