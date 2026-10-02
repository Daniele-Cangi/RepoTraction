"""Typed non-demand fixtures; provenance, persistence and zero comparison spend."""
import copy
import json
import unittest
from unittest import mock

from missing_link.analysis import validate_matches, validate_request
from missing_link.contracts import schema_for, validate_shape
from missing_link.provider import CandidateValidationError, Provider
from missing_link.store import Store
import test_missing_link as fixtures


def article():
    return dict(fixtures.issue(), title="Understanding JavaScript Promises",
        body="A Promise represents an asynchronous result. This article demonstrates callbacks and chaining.",
        comments=[], timeline=[], context_complete=True)


def non_demand_raw():
    return dict(fixtures.request_raw(), status="not_a_request", requirements=[],
        status_source_ids=["q0"], status_reason="The body is an existing explanatory article, not a requested change.")


class NonDemandTests(unittest.TestCase):
    def test_typed_empty_result_is_source_bound_and_schema_valid(self):
        raw = non_demand_raw()
        original = copy.deepcopy(raw)
        validate_shape(raw, schema_for("request"))
        result = validate_request(raw, article())
        self.assertEqual(result["status"], "not_a_request")
        self.assertEqual(result["requirements"], [])
        self.assertEqual(result["status_evidence"], [{"url": article()["url"], "source_id": "q0"}])
        self.assertEqual(raw, original)

    def test_actual_demand_dispositions_cannot_have_zero_requirements(self):
        for status in ("unresolved", "unclear", "resolved", "duplicate", "automated"):
            with self.subTest(status=status):
                with self.assertRaisesRegex(ValueError, "at least one"):
                    validate_request(dict(non_demand_raw(), status=status), article())

    def test_non_demand_cannot_hide_requirements(self):
        with self.assertRaisesRegex(ValueError, "empty requirements"):
            validate_request(dict(non_demand_raw(), requirements=fixtures.request_raw()["requirements"]), fixtures.issue())

    def test_reason_and_known_discussion_evidence_are_required(self):
        for changes in ({"status_reason": " "}, {"status_reason": None}, {"status_source_ids": []},
                        {"status_source_ids": "q0"}, {"status_source_ids": ["missing"]},
                        {"status_source_ids": [False]}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                validate_request(dict(non_demand_raw(), **changes), article())

    def test_timeline_only_or_incomplete_discussion_cannot_certify_non_demand(self):
        demand = dict(article(), timeline=[{"event": "labeled"}])
        with self.assertRaisesRegex(ValueError, "Timeline state"):
            validate_request(dict(non_demand_raw(), status_source_ids=["t0"]), demand)
        with self.assertRaisesRegex(ValueError, "Incomplete discussion"):
            validate_request(non_demand_raw(), dict(article(), context_complete=False))

    def test_later_discussion_can_ground_disposition(self):
        demand = dict(article(), comments=[{"url": article()["url"] + "#issuecomment-1", "body": "Reference notes only."}])
        result = validate_request(dict(non_demand_raw(), status_source_ids=["q1"]), demand)
        self.assertEqual(result["status_evidence"][0]["source_id"], "q1")

    def test_bot_metadata_does_not_turn_empty_non_demand_into_actual_demand(self):
        self.assertEqual(validate_request(non_demand_raw(), dict(article(), bot=True))["status"], "not_a_request")

    def test_non_demand_and_empty_actual_request_cannot_generate_vacuous_matches(self):
        request = validate_request(non_demand_raw(), article())
        self.assertEqual(validate_matches([], fixtures.repository(), article(), request, "model"), [])
        with self.assertRaisesRegex(ValueError, "cannot have compatibility"):
            validate_matches([fixtures.raw_match()], fixtures.repository(), article(), request, "model")
        with self.assertRaisesRegex(ValueError, "at least one"):
            validate_matches([], fixtures.repository(), article(), dict(request, status="unresolved"), "model")

    def test_provider_accepts_non_demand_in_schema_and_json_modes_without_inventing_criteria(self):
        for mode in ("json_schema", "json_object"):
            provider = Provider({"REPOTRACTION_AI_URL": "http://localhost/v1", "REPOTRACTION_AI_MODEL": "fixture",
                "REPOTRACTION_AI_RESPONSE_FORMAT": mode})
            with self.subTest(mode=mode), mock.patch.object(provider, "complete", side_effect=fixtures.request_completion(non_demand_raw())) as complete:
                result = provider.interpret_request(article(), mock.Mock())
            self.assertEqual(result["status"], "not_a_request")
            self.assertEqual(result["requirements"], [])
            self.assertIn("Do not invent a mandatory article outline", complete.call_args.args[0])
            self.assertEqual(complete.call_count, 1)

    def test_incomplete_model_span_context_is_not_promoted_to_non_demand(self):
        provider = Provider({"REPOTRACTION_AI_URL": "http://localhost/v1", "REPOTRACTION_AI_MODEL": "fixture",
            "REPOTRACTION_AI_MAX_PROMPT_BYTES": "60000"})
        demand = dict(article(), body="Explanatory material.\n" * 4000)
        with mock.patch.object(provider, "complete", side_effect=fixtures.request_completion(non_demand_raw())):
            with self.assertRaisesRegex(CandidateValidationError, "Incomplete discussion"):
                provider.interpret_request(demand, mock.Mock())

    def test_provider_comparison_guard_runs_before_paid_transport(self):
        provider = Provider({"REPOTRACTION_AI_URL": "http://localhost/v1", "REPOTRACTION_AI_MODEL": "fixture"})
        budget = mock.Mock()
        with mock.patch.object(provider, "complete") as complete:
            with self.assertRaises(CandidateValidationError):
                provider.evaluate(fixtures.repository(), article(), validate_request(non_demand_raw(), article()), budget)
        complete.assert_not_called()
        budget.reserve_ai.assert_not_called()


class NonDemandServiceTests(unittest.TestCase):
    setUp = fixtures.ServiceTests.setUp
    fake_sources = fixtures.ServiceTests.fake_sources

    def run_disposition(self, demand=None, raw=None, **inputs):
        source = self.fake_sources()
        source.fetch_issue.return_value = demand or article()
        provider = Provider({"REPOTRACTION_AI_URL": "http://localhost/v1", "REPOTRACTION_AI_MODEL": "fixture"})
        self.service.provider = provider

        def completed(instruction, data, budget, schema, phase):
            budget.reserve_ai(.10, 8, 2)
            budget.record_usage(100, 200, .00011)
            budget.record_call({"phase": phase, "context_coverage": data["context_coverage"]})
            output = fixtures.wire_request(data, raw or non_demand_raw())
            budget.record_output(phase, output)
            return output

        with mock.patch("missing_link.service.PublicGitHub", return_value=source), \
             mock.patch("missing_link.service.extract_structure", return_value=fixtures.repository()["capabilities"]), \
             mock.patch.object(provider, "interpret_capabilities", return_value=fixtures.repository()["capabilities"]), \
             mock.patch.object(provider, "complete", side_effect=completed) as complete, \
             mock.patch.object(provider, "evaluate", return_value=[]) as evaluate:
            started = self.service.start({"repo": "example/words", "use_ai": True, **inputs}, background=False)
        return self.service.store.get("jobs", started["job_id"]), source, complete, evaluate

    def test_non_demand_is_completed_not_partial_rejected_or_retrieval_screened(self):
        job, source, complete, evaluate = self.run_disposition()
        self.assertEqual(job["status"], "completed")
        self.assertEqual(job["result"]["match_ids"], [])
        self.assertNotIn("partial", job["result"])
        self.assertNotIn("candidate_errors", job["result"])
        self.assertNotIn("candidate_skips", job["result"])
        record = job["result"]["non_demands"][0]
        self.assertEqual(record["status"], "not_a_request")
        self.assertFalse(record["compatibility_evaluated"])
        self.assertEqual(record["analysis_source"], "model")
        self.assertEqual(job["checkpoint"]["requests"]["0"]["requirements"], [])
        self.assertEqual(record, job["checkpoint"]["non_demands"]["0"])
        self.assertEqual(job["ai_calls_used"], 1)
        self.assertAlmostEqual(job["cost_reserved_usd"], .10)
        self.assertEqual(len(job["reported_usage"]), 1)
        self.assertEqual(len(job["ai_trace"]), 1)
        self.assertEqual(complete.call_count, 1)
        source.fetch_reference_context.assert_not_called()
        source.search_issues.assert_called()  # Frozen sample, no replacement.
        evaluate.assert_not_called()
        self.assertEqual(len(self.service.store.list("matches")), 0)
        public_job = next(item for item in self.service.state()["jobs"] if item["id"] == job["id"])
        self.assertNotIn("checkpoint", public_job)
        self.assertEqual(public_job["result"]["non_demands"], [record])

    def test_mixed_sample_keeps_actual_demand_and_never_refills_non_demand(self):
        reference = article()
        actual = dict(fixtures.issue(), id="issue-8", url="https://github.com/example/site/issues/8")
        source = self.fake_sources()
        issues = {item["url"]: item for item in (reference, actual)}
        source.fetch_issue.side_effect = lambda url: issues[url]
        source.search_issues.return_value = {"items": [{"url": url} for url in issues]}
        provider = Provider({"REPOTRACTION_AI_URL": "http://localhost/v1", "REPOTRACTION_AI_MODEL": "fixture"})
        self.service.provider = provider

        def interpret(demand, budget):
            budget.reserve_ai(.10, 8, 2)
            return validate_request(non_demand_raw() if demand["url"] == reference["url"] else fixtures.request_raw(), demand)

        def compare(repository, demand, request, budget):
            budget.reserve_ai(.10, 8, 2)
            return []

        with mock.patch("missing_link.service.PublicGitHub", return_value=source), \
             mock.patch("missing_link.service.extract_structure", return_value=fixtures.repository()["capabilities"]), \
             mock.patch.object(provider, "interpret_capabilities", return_value=fixtures.repository()["capabilities"]), \
             mock.patch.object(provider, "interpret_request", side_effect=interpret) as extract, \
             mock.patch.object(provider, "evaluate", side_effect=compare) as evaluate:
            started = self.service.start({"repo": "example/words", "use_ai": True,
                "query": "fixture demand", "max_candidates": 2}, background=False)
        job = self.service.store.get("jobs", started["job_id"])
        self.assertEqual(job["status"], "completed")
        self.assertNotIn("partial", job["result"])
        self.assertEqual({item["url"] for item in job["checkpoint"]["candidates"]}, set(issues))
        self.assertEqual(len(job["result"]["non_demands"]), 1)
        self.assertEqual(len(job["checkpoint"]["evaluated"]), 1)
        self.assertEqual(job["ai_calls_used"], 3)  # Two extractions; only the actual demand is compared.
        self.assertAlmostEqual(job["cost_reserved_usd"], .30)
        self.assertEqual(extract.call_count, 2)
        evaluate.assert_called_once()
        self.assertEqual(evaluate.call_args.args[1]["url"], actual["url"])
        source.fetch_reference_context.assert_called_once_with(actual)
        source.search_issues.assert_called_once()
        self.assertEqual(source.fetch_issue.call_count, 2)

    def test_explicit_issue_and_query_still_stop_after_grounded_non_demand(self):
        for inputs in ({"issue_url": article()["url"]}, {"query": "user selected article"}):
            with self.subTest(inputs=inputs):
                job, source, _, evaluate = self.run_disposition(**inputs)
                self.assertEqual(len(job["result"]["non_demands"]), 1)
                source.fetch_reference_context.assert_not_called()
                evaluate.assert_not_called()

    def test_zero_actual_demand_retains_charge_as_validation_failure(self):
        job, source, complete, evaluate = self.run_disposition(raw=dict(non_demand_raw(), status="unclear"))
        self.assertTrue(job["result"]["partial"])
        self.assertNotIn("non_demands", job["result"])
        self.assertEqual(len(job["checkpoint"]["ai_outputs"]), 1)
        self.assertAlmostEqual(job["cost_reserved_usd"], .10)
        source.fetch_reference_context.assert_not_called()
        evaluate.assert_not_called()
        self.assertEqual(complete.call_count, 1)

    def test_restart_and_resume_retain_non_demand_without_refetch_retry_or_refill(self):
        job, source, _, _ = self.run_disposition()
        other = Store(self.path, "alice")
        self.assertEqual(other.get("jobs", job["id"]), job)
        job.update(status="paused", error="Fixture pause")
        other.put("jobs", job["id"], job)
        source.fetch_issue.side_effect = AssertionError("No refetch")
        source.search_issues.side_effect = AssertionError("No refill")
        with mock.patch("missing_link.service.PublicGitHub", return_value=source), \
             mock.patch.object(self.service.provider, "interpret_request", side_effect=AssertionError("No retry")):
            self.service.resume({"job_id": job["id"]}, background=False)
        resumed = other.get("jobs", job["id"])
        self.assertEqual(resumed["status"], "completed")
        self.assertEqual(resumed["result"]["non_demands"], job["result"]["non_demands"])
        self.assertEqual(resumed["cost_reserved_usd"], job["cost_reserved_usd"])
        self.assertEqual(resumed["checkpoint"]["candidates"], job["checkpoint"]["candidates"])

    def test_reference_with_later_real_request_reaches_normal_analysis(self):
        demand = dict(article(), comments=[{"url": article()["url"] + "#issuecomment-9",
            "body": "Please add a callback adapter."}])
        raw = dict(fixtures.request_raw(), status_source_ids=["q1"], requirements=[{
            "text": "Add callback adapter", "mandatory": True, "explicit": True,
            "source_id": "q1", "quote": "Please add a callback adapter.", "inference": ""}])
        job, source, complete, evaluate = self.run_disposition(demand=demand, raw=raw)
        self.assertNotIn("non_demands", job["result"])
        source.fetch_reference_context.assert_called_once()
        evaluate.assert_called_once()
        self.assertEqual(job["checkpoint"]["evaluated"], ["0"])

    def test_non_demand_reason_is_redacted_in_persistence(self):
        raw = dict(non_demand_raw(), status_reason="Article only. ghp_" + "A" * 36)
        job, _, _, _ = self.run_disposition(raw=raw)
        self.assertIn("[REDACTED]", job["result"]["non_demands"][0]["reason"])
        self.assertNotIn("ghp_", json.dumps(job))
