"""Browser -> actual HTTP handler -> service -> temporary SQLite acceptance test.

Public GitHub acquisition is a fixture; no provider calls, account DB writes or
third-party execution claims. The optional WASI step executes fixed test code.
"""
import copy
import os
from pathlib import Path
import tempfile
from threading import Thread
import unittest
from unittest import mock

import app
from missing_link.provider import Provider
from missing_link.service import Service
from missing_link.wasi_runner import WasiRunner
from test_missing_link import issue, repository
from test_missing_link_frontend import sync_playwright


class AcceptanceHandler(app.DashboardHandler):
    def log_message(self, *_args):
        pass

    def do_GET(self):
        if self.path == "/acceptance-fixture":
            body = b'<html><head><link rel="stylesheet" href="/styles.css"></head><body><main><h1>Synthetic acceptance test</h1><div id="missingLinkRoot"></div></main></body></html>'
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            super().do_GET()


@unittest.skipUnless(sync_playwright, "Optional Playwright unavailable")
class MissingLinkAcceptanceTests(unittest.TestCase):
    def test_browser_http_persistence_correction_reassessment_and_optional_wasi(self):
        with tempfile.TemporaryDirectory() as temp, sync_playwright() as runtime:
            executable = os.environ.get("REPOTRACTION_BROWSER_EXECUTABLE")
            chrome = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
            if not executable and chrome.is_file():
                executable = str(chrome)
            try:
                browser = runtime.chromium.launch(headless=True, **({"executable_path": executable} if executable else {}))
            except Exception:
                self.skipTest("Optional Chromium unavailable")
            database = Path(temp) / "fixture.sqlite3"
            service = Service(database, "fixture-account", lambda *_: {}, lambda: "fixture-account", Provider({}))
            source = mock.Mock()
            source.fetch_repository.side_effect = lambda *_: copy.deepcopy(repository())
            source.fetch_issue.side_effect = lambda *_: copy.deepcopy(issue())
            server = app.ThreadingHTTPServer(("127.0.0.1", 0), AcceptanceHandler)
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            origin = f"http://127.0.0.1:{server.server_port}"
            try:
                with mock.patch.object(app, "verify_active_account", return_value="fixture-account"), \
                     mock.patch.object(app, "missing_link_service", side_effect=lambda: service), \
                     mock.patch("missing_link.service.PublicGitHub", return_value=source), \
                     mock.patch("missing_link.service.extract_structure", side_effect=lambda *_: copy.deepcopy(repository()["capabilities"])):
                    page = browser.new_page(viewport={"width": 1440, "height": 1000})
                    errors, external = [], []
                    page.on("pageerror", lambda error: errors.append(str(error)))
                    def local_only(route):
                        if route.request.url.startswith(origin + "/"):
                            route.continue_()
                        else:
                            external.append(route.request.url)
                            route.abort()
                    page.route("**/*", local_only)
                    page.goto(origin + "/acceptance-fixture")
                    page.evaluate("""async () => {
                        const module = await import('/missing-link.js');
                        const escapeHtml = value => String(value ?? '').replaceAll('&', '&amp;')
                            .replaceAll('<', '&lt;').replaceAll('>', '&gt;')
                            .replaceAll('"', '&quot;').replaceAll("'", '&#039;');
                        window.acceptance = module.initMissingLink({demoMode: false, escapeHtml,
                            getDashboard: () => ({repositories: []}),
                            api: async (path, options = {}) => {
                                const response = await fetch(path, options);
                                const data = await response.json();
                                if (!response.ok) throw new Error(data.error || response.status);
                                return data;
                            }});
                        window.acceptance.setActive(true);
                    }""")
                    page.locator("#mlRepo").fill("example/words")
                    page.locator("#mlRepo").dispatch_event("input")
                    page.locator("#mlAnalyzeButton").click()
                    page.locator("#mlCapabilities h4").get_by_text("trim", exact=True).wait_for()
                    # The fixture finishes almost instantly; wait for its lease
                    # release before triggering the independent discovery job.
                    for worker in list(service.threads.values()):
                        worker.join(timeout=3)
                    page.locator("#mlReviewed").check()
                    page.locator("#mlIssue").fill(issue()["url"])
                    page.locator("#mlDiscoverButton").click()
                    try:
                        page.locator(".ml-match").first.wait_for(timeout=15000)
                    except Exception as error:
                        self.fail(f"Fixture discovery failed: {service.state()['jobs']}; notice={page.locator('#mlNotice').inner_text()}; {error}")
                    original = service.state()["matches"][0]
                    self.assertFalse(original["stale"])
                    page.locator('[data-ml-detail="correction-trim"] > summary').click()
                    form = page.locator('.ml-correction-form[data-capability-id="trim"]')
                    form.locator('[name="limitations"]').fill("Synthetic acceptance: requires host state")
                    form.locator('[name="standalone"]').select_option("no")
                    form.get_by_role("button", name="Save maintainer correction").click()
                    page.locator(".ml-match .ml-callout").first.wait_for()
                    self.assertTrue(service.state()["matches"][0]["stale"])
                    self.assertFalse(page.locator("#mlReviewed").is_checked())
                    blocked = page.request.post(origin + "/api/missing-link/example", headers={"Origin": origin},
                        data={"approved": True, "match_id": original["id"], "entrypoint": "reviewed_tests/probe.py",
                              "reviewed_tests": [{"path": "probe.py", "content": "print('FIXTURE ONLY')\n"}]})
                    self.assertEqual(blocked.status, 400)
                    self.assertIn("capability interpretation changed", blocked.json()["error"])
                    page.locator("#mlReviewed").check()
                    page.locator("#mlDiscoverButton").click()
                    page.wait_for_function("document.querySelectorAll('.ml-match').length === 2")
                    current = next(match for match in service.state()["matches"] if not match["stale"])
                    self.assertNotEqual(current["id"], original["id"])
                    if WasiRunner().describe()["available"]:
                        executed = page.request.post(origin + "/api/missing-link/example", headers={"Origin": origin},
                            data={"approved": True, "match_id": current["id"], "entrypoint": "reviewed_tests/probe.py",
                                  "reviewed_tests": [{"path": "probe.py", "content": "from words import trim\nassert trim('fixture') == 'fixture'\nprint('FIXTURE ONLY')\n"}]})
                        self.assertEqual(executed.status, 200, executed.text())
                        receipt = executed.json()["isolated_example"]
                        self.assertEqual(receipt["status"], "exited_successfully", receipt)
                        self.assertFalse(receipt["request_criteria_verified"])
                    service = Service(database, "fixture-account", lambda *_: {}, lambda: "fixture-account", Provider({}))
                    page.get_by_role("button", name="Refresh results").click()
                    self.assertEqual(len(service.state()["matches"]), 2)
                    self.assertTrue(next(match for match in service.state()["matches"] if match["id"] == original["id"])["stale"])
                    if WasiRunner().describe()["available"]:
                        page.get_by_text("Isolated example ran", exact=True).wait_for()
                        self.assertEqual(service.store.proofs(current["id"])[0]["id"], receipt["id"])
                    self.assertEqual(errors, [])
                    self.assertEqual(external, [])
                    page.close()
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)
                browser.close()
