"""Typed non-demand fixtures; provenance, persistence and zero comparison spend."""
import copy
import json
import unittest
from unittest import mock

from missing_link.analysis import validate_matches, validate_request
from missing_link.contracts import schema_for, validate_shape
from missing_link.provider import CandidateValidationError, Provider
from missing_link.store import Store
from missing_link.lease import WorkerLease
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


class NonDemandImportTests(unittest.TestCase):
    setUp = fixtures.ServiceTests.setUp
    fake_sources = fixtures.ServiceTests.fake_sources

    def acquired_job(self):
        source = self.fake_sources()
        source.fetch_issue.return_value = article()
        with mock.patch("missing_link.service.PublicGitHub", return_value=source), \
             mock.patch("missing_link.service.extract_structure", return_value=fixtures.repository()["capabilities"]):
            started = self.service.start({"repo": "example/words", "issue_url": article()["url"]}, background=False)
        return self.service.store.get("jobs", started["job_id"])

    def import_non_demand(self, job, raw=None, **options):
        return self.service.import_analysis({"job_id": job["id"], **options,
            "analysis": {"request": raw or non_demand_raw(), "matches": []}})

    def test_import_is_persisted_attributed_and_visible_without_provider_or_charge(self):
        job = self.acquired_job()
        before_matches = self.service.store.list("matches")
        with mock.patch.object(self.service.provider, "complete") as paid:
            response = self.import_non_demand(job)
        paid.assert_not_called()
        self.assertEqual(response["match_ids"], [])
        stored = Store(self.path, "alice").get("jobs", job["id"])
        record = stored["result"]["non_demands"][0]
        self.assertEqual(record, response["non_demands"][0])
        self.assertEqual(record, stored["checkpoint"]["non_demands"]["0"])
        self.assertEqual(stored["checkpoint"]["requests"]["0"]["status"], "not_a_request")
        self.assertEqual(record["analysis_source"], "coding_agent_import")
        self.assertIn("Coding-agent interpretation", record["note"])
        self.assertFalse(record["compatibility_evaluated"])
        self.assertEqual(record["ai_calls_used"], 0)
        self.assertEqual(record["cost_reserved_usd"], 0)
        for key in ("ai_calls_used", "cost_reserved_usd", "requests_used", "status"):
            self.assertEqual(stored[key], job[key])
        self.assertEqual(len(self.service.store.list("matches")), len(before_matches))
        self.assertTrue(all(item["superseded"] for item in self.service.store.list("matches")))
        public = next(item for item in self.service.state()["jobs"] if item["id"] == job["id"])
        self.assertEqual(public["result"]["non_demands"], [record])
        self.assertNotIn("checkpoint", public)

    def test_reimport_updates_one_outcome_preserves_other_discussions_and_redacts(self):
        job = self.acquired_job()
        other = dict(article(), id=77, url="https://github.com/example/site/issues/77", fingerprint="other-discussion")
        job["checkpoint"]["discussions"]["1"] = other
        self.service.store.put("jobs", job["id"], job)
        self.import_non_demand(job, discussion_index=1)
        self.import_non_demand(job)
        raw = dict(non_demand_raw(), status_reason="Updated agent review. ghp_" + "A" * 36)
        response = self.import_non_demand(job, raw)
        stored = self.service.store.get("jobs", job["id"])
        self.assertEqual(len(stored["result"]["non_demands"]), 2)
        self.assertEqual(set(stored["checkpoint"]["non_demands"]), {"0", "1"})
        self.assertEqual(stored["checkpoint"]["non_demands"]["1"]["url"], other["url"])
        self.assertIn("[REDACTED]", stored["checkpoint"]["non_demands"]["0"]["reason"])
        self.assertNotIn("ghp_", json.dumps(stored))
        self.assertNotIn("ghp_", json.dumps(response))

    def test_import_preserves_prior_charged_outputs_and_resume_does_not_retry(self):
        job = self.acquired_job()
        job.update(status="paused", ai_calls_used=1, cost_reserved_usd=.10,
            ai_trace=[{"phase": "request", "call_number": 1}], reported_usage=[{"input_tokens": 10, "output_tokens": 20}])
        job["checkpoint"]["ai_outputs"] = [{"phase": "request", "output": {"requirements": []}}]
        # Force a resume to rely on the typed checkpoint, not an old evaluated flag.
        job["checkpoint"].pop("evaluated", None)
        self.service.store.put("jobs", job["id"], job)
        self.import_non_demand(job)
        stored = self.service.store.get("jobs", job["id"])
        for key in ("ai_calls_used", "cost_reserved_usd", "ai_trace", "reported_usage"):
            self.assertEqual(stored[key], job[key])
        self.assertEqual(stored["checkpoint"]["ai_outputs"], job["checkpoint"]["ai_outputs"])
        source = self.fake_sources()
        source.fetch_issue.side_effect = AssertionError("No refetch")
        source.search_issues.side_effect = AssertionError("No refill")
        with mock.patch("missing_link.service.PublicGitHub", return_value=source), \
             mock.patch.object(self.service.provider, "complete", side_effect=AssertionError("No paid retry")):
            self.service.resume({"job_id": job["id"]}, background=False)
        resumed = self.service.store.get("jobs", job["id"])
        self.assertEqual(resumed["result"]["non_demands"], stored["result"]["non_demands"])
        self.assertEqual(resumed["cost_reserved_usd"], .10)
        self.assertEqual(resumed["status"], "completed")

    def test_actual_request_reimport_removes_non_demand_and_cannot_resurrect_on_resume(self):
        job = self.acquired_job()
        self.import_non_demand(job)
        # An explicit agent review establishes an actual request in the same supplied text.
        raw = dict(fixtures.request_raw(), requirements=[{"text": "Explain Promise chaining", "mandatory": True,
            "explicit": False, "source_id": "q0", "quote": "This article demonstrates callbacks and chaining.", "inference": "Agent hypothesis"}])
        response = self.service.import_analysis({"job_id": job["id"], "analysis": {"request": raw, "matches": []}})
        self.assertEqual(response["match_ids"], [])
        stored = self.service.store.get("jobs", job["id"])
        self.assertEqual(stored["result"]["non_demands"], [])
        self.assertNotIn("0", stored["checkpoint"]["non_demands"])
        self.assertEqual(stored["checkpoint"]["requests"]["0"]["status"], "unresolved")
        self.assertIn("0", stored["checkpoint"]["evaluated"])

    def test_invalid_import_leaves_existing_outcome_and_matches_unchanged(self):
        job = self.acquired_job()
        self.import_non_demand(job)
        before = self.service.store.get("jobs", job["id"])
        matches = self.service.store.list("matches")
        for raw in (dict(non_demand_raw(), status_source_ids=["missing"]), dict(non_demand_raw(), status="unclear")):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                self.import_non_demand(job, raw)
        self.assertEqual(self.service.store.get("jobs", job["id"]), before)
        self.assertEqual(self.service.store.list("matches"), matches)
        self.assertIsNone(self.service.lease.file)

    def test_structural_supersession_is_limited_to_the_exact_pinned_discussion(self):
        job = self.acquired_job()
        original = self.service.store.list("matches")[0]
        variations = ({"repo_id": 99}, {"revision": "b" * 40}, {"source_fingerprint": "other-snapshot"},
            {"request": dict(original["request"], id=99)}, {"analysis_source": "model"})
        for index, changes in enumerate(variations):
            peer = dict(copy.deepcopy(original), id="peer-" + str(index), **changes)
            self.service.store.put("matches", peer["id"], peer)
        self.import_non_demand(job)
        self.assertTrue(self.service.store.get("matches", original["id"])["superseded"])
        for index in range(len(variations)):
            self.assertFalse(self.service.store.get("matches", "peer-" + str(index)).get("superseded", False))

    def test_import_cannot_race_another_process_worker_or_resume(self):
        job = self.acquired_job()
        lease = WorkerLease(self.path)
        self.assertTrue(lease.acquire())
        try:
            with self.assertRaisesRegex(ValueError, "active investigation"):
                self.import_non_demand(job)
            self.assertEqual(self.service.store.get("jobs", job["id"]), job)
        finally:
            lease.release()
        self.import_non_demand(job)

    def test_job_outcome_and_structural_supersession_rollback_together(self):
        job = self.acquired_job()
        matches = self.service.store.list("matches")
        # A fixture trigger fails the final job write, after peer updates.
        with self.service.store.connection() as db:
            db.execute("CREATE TRIGGER fail_outcome BEFORE UPDATE ON ml_jobs BEGIN SELECT RAISE(ABORT, 'Fixture write failure'); END")
        with self.assertRaisesRegex(Exception, "Fixture write failure"):
            self.import_non_demand(job)
        self.assertEqual(self.service.store.get("jobs", job["id"]), job)
        self.assertEqual(self.service.store.list("matches"), matches)
        self.assertIsNone(self.service.lease.file)
