"""Optional local browser regression tests. All Missing Link evidence is a fixture.

These tests do not call GitHub, an AI provider or the account application server.
Install Playwright and a Chromium browser to run them; otherwise they skip.
REPOTRACTION_BROWSER_EXECUTABLE may point to an existing Chrome/Chromium binary.
"""

from __future__ import annotations

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import copy
import os
from pathlib import Path
from threading import Thread
import unittest

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None


STATIC = Path(__file__).resolve().parents[1] / "static"


class QuietStaticHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


def source_fixture():
    """Deliberately fictional cases; never presented as live product evidence."""
    return {
        "account": "fixture-user",
        "provider": {"configured": False},
        "repositories": [{
            "id": 7,
            "full_name": "fixture-user/public-repo",
            "revision": "a" * 40,
            "coverage": {"summary": "Synthetic UI test coverage only"},
            "capabilities": [{
                "id": "cap-fixture", "name": "Synthetic fixture capability",
                "summary": "<img src=x onerror=alert(1)>",
                "outcome": "Synthetic transformation", "standalone": False,
                "search_terms": ["bounded transformation"],
                "test_coverage": "Source reference only; not executed",
                "evidence": [{"path": "source.py", "line": 10,
                              "url": "javascript:alert(1)",
                              "quote": "<script>alert(1)</script>"}],
            }],
        }],
        "jobs": [{"id": "job-fixture", "status": "completed",
                  "stage": "Synthetic fixture collected", "requests_used": 5,
                  "input": {"repo": "fixture-user/public-repo", "max_requests": 80}}],
        "matches": [{
            "repo_id": 7,
            "id": "match-fixture", "repo": "fixture-user/public-repo",
            "revision": "a" * 40, "capability_id": "cap-fixture",
            "classification": "investigate",
            "request": {"title": "Synthetic request: fixture test only",
                        "url": "javascript:alert(1)", "context_complete": False,
                        "requirements": [{"id": "r1", "text": "Must isolate code",
                                          "mandatory": True, "explicit": True}]},
            "checks": [{"requirement_id": "r1", "status": "undetermined"}],
            "bridge": {"verification": {"status": "not_executed",
                                         "reason": "No isolated runner"}},
        }],
        "extension_groups": [],
    }


@unittest.skipUnless(sync_playwright is not None, "Optional Playwright is not installed")
class MissingLinkFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        candidates = [os.environ.get("REPOTRACTION_BROWSER_EXECUTABLE")]
        windows_chrome = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
        if windows_chrome.is_file():
            candidates.append(str(windows_chrome))
        candidates.append(None)
        cls.browser = None
        for executable in candidates:
            if executable == "":
                continue
            try:
                kwargs = {"headless": True}
                if executable:
                    kwargs["executable_path"] = executable
                cls.browser = cls.playwright.chromium.launch(**kwargs)
                break
            except Exception:
                continue
        if cls.browser is None:
            cls.playwright.stop()
            raise unittest.SkipTest("Optional Chromium browser is unavailable")
        cls.server = ThreadingHTTPServer(
            ("127.0.0.1", 0), partial(QuietStaticHandler, directory=str(STATIC))
        )
        cls.thread = Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.origin = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def setUp(self):
        self.context = self.browser.new_context(viewport={"width": 1440, "height": 1000})
        self.page = self.context.new_page()
        self.errors = []
        self.page.on("pageerror", lambda error: self.errors.append(str(error)))
        # No external browser requests, even if a future UI adds a remote asset.
        self.page.route("**/*", lambda route: route.continue_()
                        if route.request.url.startswith(self.origin + "/") else route.abort())

    def tearDown(self):
        self.context.close()
        self.assertEqual(self.errors, [], "Frontend JavaScript error")

    def test_partial_job_exposes_candidate_error_without_executing_error_markup(self):
        fixture = source_fixture()
        fixture["jobs"][0]["result"] = {"partial": True, "candidate_errors": [{
            "url": "https://github.com/fixture/request/issues/1", "stage": "requirements",
            "error": "Invalid quote <img src=x onerror=alert(1)>"}]}
        self.fixture_page(fixture)
        warning = self.page.locator(".ml-job .ml-callout").filter(has_text="Partial investigation")
        warning.wait_for()
        self.assertIn("No automatic retry", warning.inner_text())
        self.assertIn("Invalid quote <img", warning.inner_text())
        self.assertEqual(warning.locator("img").count(), 0)

    def test_scope_compatibility_is_not_displayed_as_existing_behavior(self):
        fixture = source_fixture()
        match = fixture["matches"][0]
        match["checks"][0].update(status="satisfied", contribution="scope_compatible")
        match["discovery_assessment"] = {"status": "similarity_only", "supported_requirement_ids": [],
            "scope_compatible_requirement_ids": ["r1"], "conflicting_requirement_ids": [], "undetermined_requirement_ids": []}
        self.fixture_page(fixture)
        details = self.page.locator('[data-ml-detail="discovery-match-fixture"]')
        details.locator("summary").click()
        self.assertIn("Existing behavior: 0", details.inner_text())
        self.assertIn("Scope-compatible constraints: 1", details.inner_text())
        self.page.locator('[data-ml-detail="requirements-match-fixture"] summary').click()
        self.assertIn("Scope-compatible constraint only", self.page.locator(".ml-requirement").inner_text())

    def test_retrieval_skip_is_distinct_from_rejected_or_invalid_analysis(self):
        fixture = source_fixture()
        fixture["jobs"][0]["result"] = {"candidate_skips": [{"url": "https://github.com/fixture/request/issues/1",
            "code": "source_file_dump_hint", "reason": "Hint <img src=x onerror=alert(1)>"}]}
        self.fixture_page(fixture)
        warning = self.page.locator(".ml-job .ml-callout").filter(has_text="retrieval candidate(s) skipped")
        warning.wait_for()
        self.assertIn("not a rejection", warning.inner_text())
        self.assertEqual(warning.locator("img").count(), 0)

    def test_discovery_qualification_is_separate_and_reference_markup_is_escaped(self):
        fixture = source_fixture()
        fixture["matches"][0]["classification"] = "direct"
        fixture["matches"][0]["discovery_assessment"] = {"status": "known_reference", "reasons": [
            "Already mentioned <img src=x onerror=alert(1)>"], "references": [{
            "source_id": "q1", "url": "javascript:alert(1)", "kind": "repository_link",
            "quote": "<script>alert(1)</script>"}]}
        self.fixture_page(fixture)
        card = self.page.locator(".ml-match")
        card.wait_for()
        self.assertIn("Existing interface", card.inner_text())
        self.assertIn("Already referenced · not a new discovery", card.inner_text())
        detail = card.locator('details[data-ml-detail="discovery-match-fixture"]')
        detail.locator("summary").click()
        self.assertIn("not evidence of adoption", detail.inner_text())
        self.assertIn("<script>", detail.inner_text())
        self.assertEqual(card.locator("script, img, a[href^='javascript:']").count(), 0)

    def test_non_demand_is_not_a_failed_or_rejected_match_and_reason_is_escaped(self):
        fixture = source_fixture()
        fixture["matches"] = []
        fixture["jobs"][0]["result"] = {"non_demands": [{"status": "not_a_request",
            "url": "https://github.com/fixture/request/issues/1",
            "reason": "Article only <img src=x onerror=alert(1)>"}]}
        self.fixture_page(fixture)
        warning = self.page.locator(".ml-job .ml-callout").filter(has_text="no established actionable request")
        warning.wait_for()
        self.assertIn("not a compatibility rejection", warning.inner_text())
        self.assertIn("Article only <img", warning.inner_text())
        self.assertEqual(warning.locator("img").count(), 0)
        self.assertEqual(self.page.locator(".ml-match").count(), 0)

    def test_non_demand_body_and_later_comment_provenance_are_visible_and_attributed(self):
        fixture = source_fixture()
        fixture["matches"] = []
        url = "https://github.com/fixture/request/issues/1"
        fixture["jobs"][0]["result"] = {"non_demands": [
            {"url": url, "reason": "Body is reference material", "analysis_source": "model",
             "status_evidence": [{"url": url, "source_id": "q0"}]},
            {"url": url, "reason": "Later comment establishes reference intent", "analysis_source": "coding_agent_import",
             "status_evidence": [{"url": url + "#issuecomment-9", "source_id": "q1"}]}]}
        self.fixture_page(fixture)
        warning = self.page.locator(".ml-job .ml-callout").filter(has_text="no established actionable request")
        warning.wait_for()
        body_source = warning.get_by_role("link", name="q0", exact=False)
        comment_source = warning.get_by_role("link", name="q1", exact=False)
        self.assertEqual(body_source.get_attribute("href"), url)
        self.assertEqual(comment_source.get_attribute("href"), url + "#issuecomment-9")
        self.assertEqual(comment_source.get_attribute("target"), "_blank")
        self.assertEqual(comment_source.get_attribute("rel"), "noreferrer")
        self.assertIn("Provider interpretation", warning.inner_text())
        self.assertIn("Coding-agent import", warning.inner_text())
        self.assertEqual(self.page.locator(".ml-match").count(), 0)

    def test_non_demand_provenance_uses_safe_links_and_escapes_labels(self):
        fixture = source_fixture()
        fixture["matches"] = []
        fixture["jobs"][0]["result"] = {"non_demands": [{"url": "javascript:alert(1)", "reason": "Fixture review",
            "status_evidence": [{"url": "javascript:alert(1)", "source_id": "<img src=x onerror=alert(1)>"},
                {"url": "https://github.com@evil.example/issue", "source_id": "q_unsafe"},
                {"url": "https://user:secret@github.com/fixture/repo/issues/1", "source_id": "q_credentials"}]}]}
        self.fixture_page(fixture)
        warning = self.page.locator(".ml-job .ml-callout").filter(has_text="no established actionable request")
        warning.wait_for()
        self.assertIn("<img src=x", warning.inner_text())
        self.assertIn("q_unsafe", warning.inner_text())
        self.assertEqual(warning.locator("a, img, script").count(), 0)

    def test_historical_result_without_discovery_assessment_does_not_claim_novelty(self):
        self.fixture_page()
        card = self.page.locator(".ml-match")
        card.wait_for()
        self.assertIn("Discovery not assessed · novelty unverified", card.inner_text())

    def fixture_page(self, fixture=None, *, capability_name="Synthetic fixture capability", dashboard=None, scoped_responses=None):
        self.page.route("**/ui-fixture", lambda route: route.fulfill(
            content_type="text/html",
            body='<html><head><link rel="stylesheet" href="/styles.css"></head>'
                 '<body><main><div id="missingLinkRoot"></div></main></body></html>',
        ))
        self.page.goto(self.origin + "/ui-fixture")
        self.page.evaluate("""async ({fixture, dashboard, scopedResponses}) => {
          window.mlFixture = fixture;
          window.mlScopedResponses = scopedResponses;
          window.mlCalls = [];
          window.mlDashboard = dashboard || {repositories: [
            {full_name: 'fixture-user/private-repo', private: true},
            {full_name: 'fixture-user/public-repo', private: false}
          ]};
          const module = await import('/missing-link.js');
          window.mlModule = module;
          const escapeHtml = value => String(value ?? '').replaceAll('&', '&amp;')
            .replaceAll('<', '&lt;').replaceAll('>', '&gt;')
            .replaceAll('"', '&quot;').replaceAll("'", '&#039;');
          window.mlController = module.initMissingLink({
            api: async (path, options = {}) => {
              window.mlCalls.push({path, options});
              const repo = new URL(path, location.origin).searchParams.get('repo') || '';
              return options.method ? {} : window.mlScopedResponses?.[repo] || window.mlFixture;
            }, escapeHtml, demoMode: false, getDashboard: () => window.mlDashboard
          });
          window.mlController.setActive(true);
        }""", {'fixture': fixture or source_fixture(), 'dashboard': dashboard, 'scopedResponses': scoped_responses})
        if capability_name != "Synthetic fixture capability":
            self.page.locator("#mlRepo").fill(fixture["repositories"][0]["full_name"])
            self.page.locator("#mlRepo").dispatch_event("change")
        self.page.locator("#mlCapabilities").get_by_text(
            capability_name, exact=True
        ).wait_for()

    def wait_post(self, path):
        self.page.wait_for_function(
            "path => window.mlCalls.some(call => call.path === path && call.options.method === 'POST')",
            arg=path,
        )
        value = self.page.evaluate(
            "path => window.mlCalls.find(call => call.path === path && call.options.method === 'POST').options.body",
            path,
        )
        return json.loads(value)

    def test_demo_navigation_never_calls_missing_link_api(self):
        calls = []
        self.page.on("request", lambda request: calls.append(request.url)
                     if "/api/missing-link" in request.url else None)
        response = self.page.goto(self.origin + "/?demo=1#missing-link")
        self.page.get_by_text(
            "Missing Link works with real public source evidence", exact=True
        ).wait_for()
        self.assertEqual(response.status, 200)
        self.assertEqual(self.page.locator("#pageTitle").inner_text(), "Missing Link")
        self.page.locator('[data-view="network"]').click()
        self.page.locator("#networkView.active").wait_for()
        self.page.locator('[data-view="missing-link"]').click()
        self.page.locator("#missing-linkView.active").wait_for()
        self.assertEqual(calls, [])

    def test_runner_receipts_are_escaped_and_not_misrepresented_as_integration(self):
        fixture = source_fixture()
        fixture["matches"][0]["isolated_examples"] = [{"status": "exited_successfully", "applies_to_current_bridge": True,
            "entrypoint": "bridge/test.py", "stdout": "<script>alert(1)</script>", "revision": "a" * 40}]
        self.fixture_page(fixture)
        self.page.get_by_text("Isolated example ran", exact=True).wait_for()
        self.assertIn("target integration remain unverified", self.page.locator("#mlMatches").inner_text())
        self.page.locator('[data-ml-detail="examples-match-fixture"]').evaluate("node => node.open = true")
        self.assertEqual(self.page.locator("#mlMatches script").count(), 0)
        fixture["matches"][0]["isolated_examples"][0]["applies_to_current_bridge"] = False
        self.page.evaluate("fixture => {window.mlFixture = fixture;}", fixture)
        self.page.locator('[data-ml-action="refresh"]').click()
        self.page.get_by_text("historical artifact", exact=False).wait_for()
        self.assertEqual(self.page.get_by_text("Isolated example ran", exact=True).count(), 0)
        self.page.set_viewport_size({"width": 390, "height": 844})
        self.assertTrue(self.page.evaluate("document.documentElement.scrollWidth <= innerWidth"))

    def test_partial_contribution_does_not_hide_full_rejection(self):
        fixture = source_fixture()
        match = fixture["matches"][0]
        match["classification"] = "rejected"
        match["discovery_assessment"] = {"status": "partial_contribution", "eligible_for_followup": False,
            "supported_requirement_ids": ["r0"], "conflicting_requirement_ids": ["r1"],
            "undetermined_requirement_ids": [], "reasons": ["<script>not executable</script>"], "references": []}
        self.fixture_page(fixture)
        self.page.get_by_text("Partial code support · full request still rejected", exact=True).wait_for()
        self.assertIn("Not a fit", self.page.locator("#mlMatches").inner_text())
        self.page.locator('[data-ml-detail="discovery-match-fixture"]').evaluate("node => node.open = true")
        self.assertIn("Existing behavior: 1 requirements fully supported · Partial primitives: 0 · Scope-compatible constraints: 0 · Conflicts: 1", self.page.locator("#mlMatches").inner_text())
        self.assertEqual(self.page.locator("#mlMatches script").count(), 0)
        self.assertIn("Not executed", self.page.locator("#mlMatches").inner_text())

    def test_normalized_explicit_rejection_with_unknown_checks_uses_not_a_fit_filter(self):
        from missing_link.analysis import validate_matches
        import test_missing_link_rejection as rejection_fixtures
        repo, issue, request, raw = rejection_fixtures.ExplicitRejectionTests().case()
        match = validate_matches([raw], repo, issue, request, "model")[0]
        fixture = source_fixture()
        fixture["repositories"] = [repo]
        fixture["matches"] = [match]
        self.fixture_page(fixture, capability_name=repo["capabilities"][0]["name"])
        card = self.page.locator(".ml-match")
        card.wait_for()
        self.assertIn("Not a fit", card.inner_text())
        self.assertNotIn("Needs investigation", card.inner_text())
        self.assertIn("Not executed", card.inner_text())
        self.page.locator('[data-ml-filter="investigate"]').click()
        self.assertEqual(self.page.locator(".ml-match").count(), 0)
        self.page.locator('[data-ml-filter="rejected"]').click()
        self.assertEqual(self.page.locator(".ml-match").count(), 1)
        self.assertEqual(self.page.evaluate("window.mlCalls.filter(call => call.options.method === 'POST').length"), 0)

    def test_stale_lead_is_visibly_historical_not_silently_requalified(self):
        fixture = source_fixture()
        fixture["matches"][0].update(stale=True, discovery_assessment={"status": "external_lead", "reasons": []})
        self.fixture_page(fixture)
        self.page.get_by_text("Historical qualification · reevaluation required · Potential external connection · novelty unverified",
                              exact=True).wait_for()


    def test_review_opt_in_and_request_validation(self):
        self.fixture_page()
        self.assertTrue(self.page.locator("#mlDiscoverButton").is_disabled())
        self.assertTrue(self.page.locator("#mlUseAI").is_disabled())
        self.assertEqual(self.page.locator(
            '#mlPublicRepositories option[value="fixture-user/private-repo"]'
        ).count(), 0)
        # Regression: input fires before change; the review must remain checked.
        self.page.locator("#mlReviewed").check()
        self.assertTrue(self.page.locator("#mlDiscoverButton").is_enabled())
        self.page.locator("#mlIssue").fill("https://github.com/example/problem/issues/123")
        self.assertEqual(self.page.locator("#mlDiscoverButton").inner_text(), "Evaluate this request")
        self.page.locator("#mlDiscoverButton").click()
        payload = self.wait_post("/api/missing-link/jobs")
        self.assertFalse(payload["use_ai"])
        self.assertEqual(payload["max_requests"], 80)
        self.assertEqual(payload["max_candidates"], 5)
        self.assertEqual(payload["issue_url"], "https://github.com/example/problem/issues/123")
        self.page.locator("#mlIssue").fill("https://evil.test/issues/1")
        self.page.locator("#mlDiscoverButton").click()
        self.page.get_by_text(
            "Use a public GitHub issue URL: https://github.com/owner/repository/issues/123.", exact=True
        ).wait_for()
        self.assertEqual(self.page.evaluate(
            'window.mlCalls.filter(call => call.path === "/api/missing-link/jobs").length'
        ), 1)

    def test_partial_primitive_is_not_displayed_as_a_fulfilled_requirement(self):
        fixture = source_fixture()
        match = fixture["matches"][0]
        match["checks"][0].update(contribution="partial_behavior", reason="Reusable operation; wiring unverified.")
        match["discovery_assessment"] = {"status": "partial_contribution", "supported_requirement_ids": [],
            "partial_requirement_ids": ["r1"], "undetermined_requirement_ids": ["r1"], "eligible_for_followup": False}
        self.fixture_page(fixture)
        self.assertIn("Partial code support · full request not established", self.page.locator("#mlMatches").inner_text())
        self.page.locator('summary').filter(has_text="Discovery qualification").click()
        self.assertIn("0 requirements fully supported · Partial primitives: 1", self.page.locator("#mlMatches").inner_text())
        self.page.locator('summary').filter(has_text="Every requirement").click()
        self.assertIn("Reusable primitive only · integration unverified", self.page.locator("#mlMatches").inner_text())
        self.assertIn("mandatory requirement is not supported", self.page.locator("#mlMatches").inner_text())

    def test_untrusted_evidence_remains_text_and_mobile_fits(self):
        fixture = source_fixture()
        fixture["provider"] = {"configured": True, "limits": {"allowance_id": "a-very-long-allowance-identifier-" * 5}}
        self.fixture_page(fixture)
        self.assertEqual(self.page.locator(
            '#missingLinkRoot img, #missingLinkRoot script, a[href^="javascript:"]'
        ).count(), 0)
        self.assertIn("<img src=x onerror=alert(1)>", self.page.locator("#mlCapabilities").inner_text())
        self.assertIn("Not executed", self.page.locator("#mlMatches").inner_text())
        self.assertIn("mandatory requirement is not supported", self.page.locator("#mlMatches").inner_text())
        for url in ("javascript:alert(1)", "https://github.com.evil.test/x", "https://u:p@github.com/o/r", "https://github.com:444/o/r"):
            self.assertEqual(self.page.evaluate("url => window.mlModule.safeGithubUrl(url)", url), "")
        self.page.set_viewport_size({"width": 390, "height": 844})
        self.assertTrue(self.page.evaluate("document.documentElement.scrollWidth <= innerWidth"))

    def test_correction_resets_review_and_agent_import_sends_json(self):
        self.fixture_page()
        self.page.locator("#mlReviewed").check()
        self.page.locator("summary").filter(has_text="Correct this capability as maintainer").click()
        self.page.locator('.ml-correction-form input[name="name"]').fill("Reviewed fixture name")
        self.page.locator('.ml-correction-form button[type="submit"]').click()
        payload = self.wait_post("/api/missing-link/capability")
        self.assertEqual(payload["correction"]["name"], "Reviewed fixture name")
        self.assertTrue(self.page.locator("#mlDiscoverButton").is_disabled())
        self.page.locator("summary").filter(has_text="Use a coding agent without configuring a provider").click()
        self.page.locator("#mlImportJob").select_option("job-fixture")
        analysis = {"request": {"outcome": "Synthetic fixture only"}, "matches": []}
        self.page.locator("#mlImportFile").set_input_files({
            "name": "reviewed-analysis.json", "mimeType": "application/json",
            "buffer": json.dumps({"analysis": analysis}).encode(),
        })
        self.page.locator("#mlImportButton").click()
        payload = self.wait_post("/api/missing-link/analysis")
        self.assertEqual(payload, {"job_id": "job-fixture", "analysis": analysis})

    def test_superseded_results_are_not_current_opportunities(self):
        fixture = source_fixture()
        fixture["matches"][0]["superseded"] = True
        self.fixture_page(fixture)
        self.assertEqual(self.page.locator(".ml-match").count(), 0)
        self.page.locator("#mlIncludeSuperseded").check()
        self.assertEqual(self.page.locator(".ml-match").count(), 1)
        self.assertIn("Superseded result", self.page.locator("#mlMatches").inner_text())

    def test_repository_rename_keeps_same_identity_history(self):
        fixture = source_fixture()
        self.fixture_page(fixture)
        fixture["repositories"][0]["full_name"] = "fixture-user/renamed"
        self.page.evaluate("fixture => {window.mlFixture = fixture;}", fixture)
        self.page.locator("#mlRepo").fill("fixture-user/renamed")
        self.page.locator("#mlRepo").dispatch_event("input")
        self.page.locator('[data-ml-action="refresh"]').click()
        self.page.locator(".ml-match").wait_for()
        self.assertEqual(self.page.locator(".ml-match").count(), 1)
        self.assertIn("Synthetic request", self.page.locator("#mlMatches").inner_text())

    def test_reused_name_does_not_mix_distinct_repository_ids(self):
        fixture = source_fixture()
        fixture["repositories"][0]["full_name"] = "fixture-user/renamed"
        other = copy.deepcopy(fixture["repositories"][0])
        other.update(id=8, full_name="fixture-user/public-repo")
        fixture["repositories"].append(other)
        fixture["matches"][0]["request"]["title"] = "Historical repository need"
        other_match = copy.deepcopy(fixture["matches"][0])
        other_match.update(id="new-repository-match", repo_id=8)
        other_match["request"]["title"] = "New repository need"
        fixture["matches"].append(other_match)
        self.fixture_page(fixture)
        self.assertEqual(self.page.locator(".ml-match").count(), 1)
        self.assertIn("New repository need", self.page.locator("#mlMatches").inner_text())
        self.assertNotIn("Historical repository need", self.page.locator("#mlMatches").inner_text())
        self.page.locator("#mlRepo").fill("fixture-user/renamed")
        self.page.locator("#mlRepo").dispatch_event("input")
        self.assertEqual(self.page.locator(".ml-match").count(), 1)
        self.assertIn("Historical repository need", self.page.locator("#mlMatches").inner_text())
        self.assertNotIn("New repository need", self.page.locator("#mlMatches").inner_text())

    def test_exhausted_budget_requires_explicit_higher_limit(self):
        fixture = source_fixture()
        fixture["jobs"][0].update(status="paused", requests_used=80)
        self.fixture_page(fixture)
        resume = self.page.locator('[data-ml-action="resume"]')
        self.assertTrue(resume.is_disabled())
        self.page.locator("#mlMaxRequests").fill("100")
        self.assertTrue(resume.is_enabled())
        resume.click()
        payload = self.wait_post("/api/missing-link/resume")
        self.assertEqual(payload, {"job_id": "job-fixture", "max_requests": 100})

    def test_account_switch_clears_old_results_before_refresh(self):
        self.fixture_page()
        self.assertEqual(self.page.locator(".ml-match").count(), 1)
        self.page.evaluate("""() => {
            window.mlController.setActive(false);
            window.mlDashboard = {profile: {login: 'other-fixture-user'}, repositories: []};
            window.mlController.updateDashboard(window.mlDashboard);
        }""")
        self.assertEqual(self.page.locator(".ml-match").count(), 0)
        self.assertEqual(self.page.locator(".ml-capability").count(), 0)
        self.assertEqual(self.page.locator("#mlRepo").input_value(), "")

    def test_identity_outage_clears_full_evidence_even_with_focused_form_and_blocks_actions(self):
        self.fixture_page()
        self.page.locator('#mlReviewed').check()
        self.page.locator('details[data-ml-detail="feedback-match-fixture"] summary').click()
        self.page.locator('.ml-feedback-form textarea').focus()
        diagnostic = {"account": "fixture-user", "diagnostic_only": True,
            "identity_verified": False, "actions_available": False,
            "identity_error": "Current GitHub verification failed; no account change is confirmed.",
            "jobs": [{"id": "a" * 32, "status": "paused", "error": "Saved GitHub verification timed out.",
                "error_diagnostic": {"category": "github_identity", "code": "github_identity_cli_timeout"}}]}
        self.page.evaluate("fixture => {window.mlFixture = fixture;}", diagnostic)
        self.page.get_by_role("button", name="Refresh results", exact=True).click()
        self.page.get_by_text("Identity unverified · diagnostic-only view", exact=True).wait_for()
        self.assertEqual(self.page.locator('.ml-match, .ml-capability, .ml-feedback-form').count(), 0)
        self.assertIn('Saved stop code: github_identity_cli_timeout', self.page.locator('#mlJobs').inner_text())
        self.assertIn('Current GitHub verification failed', self.page.locator('#mlNotice').inner_text())
        self.assertEqual(self.page.locator('a[href^="/api/missing-link/"]').count(), 0)
        self.assertEqual(self.page.locator('[data-ml-action="resume"], [data-ml-action="cancel"]').count(), 0)
        self.page.locator('#mlRepo').fill('fixture-user/public-repo')
        self.assertTrue(self.page.locator('#mlAnalyzeButton').is_disabled())
        self.assertTrue(self.page.locator('#mlDiscoverButton').is_disabled())
        self.assertTrue(self.page.locator('#mlImportButton').is_disabled())
        self.page.locator('#mlStartForm').dispatch_event('submit')
        self.page.locator('#mlImportForm').dispatch_event('submit')
        self.assertFalse(self.page.evaluate("window.mlCalls.some(call => call.options.method === 'POST')"))

    def test_identity_diagnostic_keeps_polling_then_recovers_without_post_or_review_opt_in(self):
        self.fixture_page()
        self.page.locator('#mlReviewed').check()
        self.page.evaluate("""() => {
            window.mlTimers = [];
            window.setTimeout = (callback, delay) => {window.mlTimers.push({callback, delay}); return window.mlTimers.length;};
            window.clearTimeout = () => {};
            window.mlFixture = {account: 'fixture-user', diagnostic_only: true,
                identity_error: 'Identity unavailable', jobs: []};
        }""")
        self.page.get_by_role("button", name="Refresh results", exact=True).click()
        self.page.get_by_text("Identity unverified · diagnostic-only view", exact=True).wait_for()
        self.assertEqual(self.page.evaluate("window.mlTimers.at(-1).delay"), 15000)
        self.page.evaluate("fixture => {window.mlFixture = fixture; window.mlTimers.at(-1).callback();}", source_fixture())
        self.page.get_by_text("GitHub identity verified again.", exact=False).wait_for()
        self.assertEqual(self.page.locator('.ml-match').count(), 1)
        self.assertEqual(self.page.locator('.ml-capability').count(), 1)
        self.assertFalse(self.page.locator('#mlReviewed').is_checked())
        self.assertTrue(self.page.locator('#mlDiscoverButton').is_disabled())
        self.assertFalse(self.page.evaluate("window.mlCalls.some(call => call.options.method === 'POST')"))

    def test_results_precede_capabilities_and_expansion_survives_refresh(self):
        fixture = source_fixture()
        original = fixture["repositories"][0]["capabilities"][0]
        for index in range(1, 8):
            fixture["repositories"][0]["capabilities"].append({
                **original, "id": f"cap-fixture-{index}", "name": f"Additional fixture capability {index}",
            })
        self.fixture_page(fixture)
        self.assertTrue(self.page.evaluate("""() => {
            const matches = document.querySelector('#mlMatches');
            const capabilities = document.querySelector('#mlCapabilities');
            return Boolean(matches.compareDocumentPosition(capabilities) & Node.DOCUMENT_POSITION_FOLLOWING);
        }"""))
        self.assertEqual(self.page.locator(".ml-capability:visible").count(), 3)
        self.page.locator(".ml-more-capabilities > summary").click()
        self.assertEqual(self.page.locator(".ml-capability:visible").count(), 8)
        self.assertTrue(self.page.locator("#mlDiscoverButton").is_disabled(), "Expansion is not maintainer review")
        self.page.evaluate("window.mlFixture.repositories[0].coverage.summary = 'Updated fixture source coverage'")
        self.page.get_by_role("button", name="Refresh results", exact=True).click()
        self.page.get_by_text("Updated fixture source coverage", exact=True).wait_for()
        self.assertTrue(self.page.locator(".ml-more-capabilities").evaluate("node => node.open"))
        self.assertEqual(self.page.locator(".ml-capability:visible").count(), 8)

    def test_refresh_reads_new_external_results_without_discovery_or_review_opt_in(self):
        self.fixture_page()
        selected_repo = "fixture-source/new-repo"
        self.page.locator("#mlRepo").fill(selected_repo)
        self.assertEqual(self.page.locator(".ml-match").count(), 0)
        self.assertIn("0 results", self.page.locator("#mlMatchCount").inner_text())
        fixture = source_fixture()
        fixture["repositories"][0]["full_name"] = selected_repo
        fixture["matches"][0]["repo"] = selected_repo
        fixture["jobs"][0]["input"]["repo"] = selected_repo
        fixture["matches"][0]["request"]["title"] = "New externally completed fixture result"
        # Emulates a CLI job completing after the browser's first state response.
        self.page.evaluate("fixture => {window.mlFixture = fixture; window.mlCalls = [];}", fixture)
        self.page.get_by_role("button", name="Refresh results", exact=True).click()
        self.page.get_by_text("New externally completed fixture result", exact=True).wait_for()
        self.assertEqual(self.page.locator("#mlRepo").input_value(), selected_repo)
        self.assertEqual(self.page.locator(".ml-match").count(), 1)
        self.assertIn("1 results for selected repository", self.page.locator("#mlMatchCount").inner_text())
        self.assertFalse(self.page.locator("#mlReviewed").is_checked())
        self.assertFalse(self.page.locator("#mlUseAI").is_checked())
        self.assertTrue(self.page.locator("#mlDiscoverButton").is_disabled())
        calls = self.page.evaluate("window.mlCalls")
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["path"], "/api/missing-link?view=dashboard&repo=fixture-source%2Fnew-repo")
        self.assertNotIn("method", calls[0]["options"])

    def test_delayed_refresh_keeps_selected_repository_and_does_not_start_another_job(self):
        self.fixture_page()
        self.page.evaluate("""() => {
            window.mlDeferred = {};
            window.mlFixture = new Promise(resolve => {window.mlDeferred.resolve = resolve;});
            window.mlCalls = [];
        }""")
        refresh_button = self.page.get_by_role("button", name="Refresh results", exact=True)
        refresh_button.click()
        self.page.wait_for_function("window.mlCalls.length === 1")
        self.page.locator("#mlRepo").fill("fixture-source/new-repo")
        refresh_button.click()
        self.assertEqual(self.page.evaluate("window.mlCalls.length"), 1, "No overlapping state reads")
        fixture = source_fixture()
        fixture["repositories"][0]["full_name"] = "fixture-source/new-repo"
        fixture["matches"][0]["repo"] = "fixture-source/new-repo"
        fixture["matches"][0]["request"]["title"] = "Completed delayed fixture result"
        self.page.evaluate("fixture => {window.mlDeferred.resolve(fixture); window.mlFixture = fixture;}", fixture)
        self.page.get_by_text("Completed delayed fixture result", exact=True).wait_for()
        self.assertEqual(self.page.locator("#mlRepo").input_value(), "fixture-source/new-repo")
        self.assertFalse(self.page.locator("#mlReviewed").is_checked())
        self.assertFalse(self.page.locator("#mlUseAI").is_checked())
        self.assertFalse(self.page.evaluate("window.mlCalls.some(call => call.options.method === 'POST')"))

    def scoped_fixture_page(self):
        fixture = source_fixture()
        fixture['dashboard'] = {'version': 1, 'selected_repo': fixture['repositories'][0]['full_name'],
            'selected_repo_id': 7, 'total_matches': 1, 'full_state_url': '/api/missing-link'}
        self.fixture_page(fixture)
        return fixture

    def test_scoped_selection_loads_complete_evidence_and_keeps_export_links(self):
        self.scoped_fixture_page()
        self.page.evaluate("""() => {
          window.mlCalls = [];
          window.mlFixture = new Promise(resolve => {window.mlResolve = resolve;});
        }""")
        self.page.locator('#mlRepo').fill('fixture-source/other')
        self.page.get_by_text('Results not loaded', exact=True).wait_for()
        self.assertEqual(self.page.locator('.ml-match').count(), 0)
        self.assertFalse(self.page.locator('#mlReviewed').is_checked())
        self.page.wait_for_function('window.mlCalls.length === 1')
        next_fixture = source_fixture()
        next_fixture['repositories'][0]['full_name'] = 'fixture-source/other'
        next_fixture['matches'][0]['repo'] = 'fixture-source/other'
        next_fixture['matches'][0]['checks'][0]['evidence'] = [{'quote': 'Complete selected evidence marker'}]
        next_fixture['matches'][0]['bridge']['files'] = [{'path': 'bridge.py', 'content': 'Complete bridge marker'}]
        next_fixture['dashboard'] = {'version': 1, 'selected_repo': 'fixture-source/other', 'selected_repo_id': 7}
        self.page.evaluate('fixture => {window.mlResolve(fixture); window.mlFixture = fixture;}', next_fixture)
        self.page.get_by_text('1 results for selected repository', exact=True).wait_for()
        self.page.locator('[data-ml-detail="requirements-match-fixture"] summary').click()
        self.assertIn('Complete selected evidence marker', self.page.locator('#mlMatches').inner_text())
        self.assertEqual(self.page.locator('a[href="/api/missing-link/export?match_id=match-fixture"]').count(), 1)
        self.assertEqual(self.page.locator('a[href="/api/missing-link/package?match_id=match-fixture"]').count(), 1)
        self.assertEqual(self.page.locator('#mlFullStateLink').get_attribute('href'), '/api/missing-link')
        self.assertFalse(self.page.locator('#mlUseAI').is_checked())
        self.assertFalse(self.page.evaluate("window.mlCalls.some(call => call.options.method === 'POST')"))

    def test_scoped_selection_during_an_inflight_read_follows_only_the_latest_repository(self):
        self.scoped_fixture_page()
        self.page.evaluate("""() => {
          window.mlCalls = [];
          window.mlFixture = new Promise(resolve => {window.mlResolve = resolve;});
        }""")
        self.page.get_by_role('button', name='Refresh results', exact=True).click()
        self.page.wait_for_function('window.mlCalls.length === 1')
        self.page.locator('#mlRepo').fill('fixture-source/intermediate')
        self.page.locator('#mlRepo').fill('fixture-source/latest')
        fixture = source_fixture()
        fixture['dashboard'] = {'version': 1, 'selected_repo': 'fixture-user/public-repo', 'selected_repo_id': 7}
        self.page.evaluate('''fixture => {
            window.mlFixture = new Promise(resolve => {window.mlLatestResolve = resolve;});
            window.mlResolve(fixture);
        }''', fixture)
        self.page.wait_for_function('window.mlCalls.length === 2')
        calls = self.page.evaluate('window.mlCalls')
        self.assertTrue(calls[1]['path'].endswith('repo=fixture-source%2Flatest'))
        self.assertFalse(any('intermediate' in call['path'] for call in calls))
        self.assertEqual(self.page.locator('.ml-match').count(), 0, 'Old evidence must not reappear for the new selection')
        latest = copy.deepcopy(fixture)
        latest['dashboard']['selected_repo'] = 'fixture-source/latest'
        latest['repositories'][0]['full_name'] = 'fixture-source/latest'
        latest['matches'][0]['repo'] = 'fixture-source/latest'
        latest['matches'][0]['request']['title'] = 'Latest selected fixture'
        self.page.evaluate('fixture => {window.mlLatestResolve(fixture); window.mlFixture = fixture;}', latest)
        self.page.get_by_text('Latest selected fixture', exact=True).wait_for()
        self.assertEqual(self.page.evaluate('window.mlCalls.length'), 2)
        self.assertFalse(self.page.evaluate("window.mlCalls.some(call => call.options.method === 'POST')"))

    def test_scoped_fetch_failure_is_not_shown_as_zero_results_or_automatically_retried(self):
        self.scoped_fixture_page()
        self.page.evaluate("""() => {
          window.mlCalls = [];
          window.mlFixture = Promise.reject(new Error('Fixture state fetch failed'));
          window.mlFixture.catch(() => {});
        }""")
        self.page.locator('#mlRepo').fill('fixture-source/unloaded')
        self.page.get_by_text('Fixture state fetch failed', exact=True).wait_for()
        self.assertEqual(self.page.locator('#mlMatchCount').inner_text(), 'Results not loaded')
        self.assertEqual(self.page.locator('.ml-match').count(), 0)
        self.assertEqual(self.page.evaluate('window.mlCalls.length'), 1)
        self.assertTrue(self.page.locator('#mlDiscoverButton').is_disabled())

    def test_dashboard_account_change_discards_an_inflight_previous_account_response(self):
        fixture = self.scoped_fixture_page()
        self.page.evaluate("""() => {
          window.mlCalls = [];
          window.mlFixture = new Promise(resolve => {window.mlResolve = resolve;});
        }""")
        self.page.get_by_role('button', name='Refresh results', exact=True).click()
        self.page.wait_for_function('window.mlCalls.length === 1')
        self.page.evaluate("""() => {
          window.mlController.setActive(false);
          window.mlDashboard = {profile: {login: 'other-fixture-user'}, repositories: []};
          window.mlController.updateDashboard(window.mlDashboard);
        }""")
        self.page.evaluate('''async fixture => {
            window.mlResolve(fixture);
            await new Promise(resolve => setTimeout(resolve, 0));
        }''', fixture)
        self.assertEqual(self.page.locator('.ml-match').count(), 0)
        self.assertEqual(self.page.locator('.ml-capability').count(), 0)
        self.assertEqual(self.page.locator('#mlRepo').input_value(), '')
        self.assertFalse(self.page.locator('#mlUseAI').is_checked())

    def test_deactivation_cancels_a_debounced_repository_read(self):
        self.scoped_fixture_page()
        self.page.evaluate('window.mlCalls = []')
        self.page.locator('#mlRepo').fill('fixture-source/inactive')
        self.page.evaluate('window.mlController.setActive(false)')
        self.page.wait_for_timeout(350)  # Observe past the 250 ms selection debounce.
        self.assertFalse(self.page.evaluate("window.mlCalls.some(call => call.options.method === 'POST')"))
        self.assertEqual(self.page.evaluate('window.mlCalls.length'), 0)

    def test_active_account_change_follows_with_a_fresh_index_not_old_evidence(self):
        fixture = self.scoped_fixture_page()
        self.page.evaluate('''() => {
            window.mlCalls = [];
            window.mlFixture = new Promise(resolve => {window.mlResolve = resolve;});
        }''')
        self.page.get_by_role('button', name='Refresh results', exact=True).click()
        self.page.wait_for_function('window.mlCalls.length === 1')
        self.page.evaluate('''() => {
            window.mlDashboard = {profile: {login: 'other-fixture-user'}, repositories: []};
            window.mlController.updateDashboard(window.mlDashboard);
        }''')
        self.assertEqual(self.page.locator('.ml-match').count(), 0)
        self.assertEqual(self.page.locator('#mlRepo').input_value(), '')
        fresh = {'account': 'other-fixture-user', 'repositories': [], 'matches': [], 'jobs': [],
            'dashboard': {'version': 1, 'selected_repo': '', 'selected_repo_id': None}}
        self.page.evaluate('''values => {
            window.mlFixture = values.fresh;
            window.mlResolve(values.old);
        }''', {'fresh': fresh, 'old': fixture})
        self.page.wait_for_function('window.mlCalls.length === 2')
        self.page.wait_for_function("document.querySelector('#mlAccount').textContent === 'Local account: other-fixture-user'")
        self.assertEqual(self.page.evaluate('window.mlCalls[1].path'), '/api/missing-link?view=dashboard')
        self.assertEqual(self.page.locator('.ml-match').count(), 0)
        self.assertEqual(self.page.locator('.ml-capability').count(), 0)
        self.assertFalse(self.page.locator('#mlUseAI').is_checked())
        self.assertFalse(self.page.evaluate("window.mlCalls.some(call => call.options.method === 'POST')"))

    def test_scoped_index_loads_the_automatically_selected_source_without_opt_ins(self):
        complete = source_fixture()
        complete['dashboard'] = {'version': 1, 'selected_repo': 'fixture-user/public-repo', 'selected_repo_id': 7}
        index = copy.deepcopy(complete)
        index['repositories'][0].pop('capabilities')
        index['repositories'][0]['evidence_loaded'] = False
        index['matches'] = []
        index['dashboard']['selected_repo'] = ''
        index['dashboard']['selected_repo_id'] = None
        self.fixture_page(index, dashboard={'repositories': []},
            scoped_responses={'fixture-user/public-repo': complete})
        self.assertEqual(self.page.locator('.ml-match').count(), 1)
        calls = self.page.evaluate('window.mlCalls')
        self.assertEqual([call['path'] for call in calls], [
            '/api/missing-link?view=dashboard',
            '/api/missing-link?view=dashboard&repo=fixture-user%2Fpublic-repo'])
        self.assertFalse(self.page.locator('#mlReviewed').is_checked())
        self.assertFalse(self.page.locator('#mlUseAI').is_checked())

    def test_mismatched_scoped_response_is_rejected_without_a_read_loop(self):
        self.scoped_fixture_page()
        wrong = source_fixture()
        wrong['dashboard'] = {'version': 1, 'selected_repo': 'fixture-user/public-repo', 'selected_repo_id': 7}
        self.page.evaluate('fixture => {window.mlFixture = fixture; window.mlCalls = [];}', wrong)
        self.page.locator('#mlRepo').fill('fixture-source/other')
        self.page.get_by_text('Saved source response does not match the requested repository. Refresh results to try again.', exact=True).wait_for()
        self.page.wait_for_timeout(350)  # No automatic retry after a mismatched response.
        self.assertEqual(self.page.evaluate('window.mlCalls.length'), 1)
        self.assertEqual(self.page.locator('.ml-match').count(), 0)
        self.assertEqual(self.page.locator('#mlMatchCount').inner_text(), 'Results not loaded')


if __name__ == "__main__":
    unittest.main()
