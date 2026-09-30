"""Read-only live browser smoke test. No jobs/AI calls or third-party writes.

Optional dependency: Playwright plus Chromium. Screenshots are local artifacts,
not suitable for publishing if the sidebar shows a real account.
"""
import argparse
import ipaddress
import json
import os
from pathlib import Path
from urllib.parse import urlparse


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8765")
    parser.add_argument("--repo", default="un33k/python-slugify")
    parser.add_argument("--screenshot")
    args = parser.parse_args()
    parsed = urlparse(args.url)
    if parsed.scheme != "http" or parsed.username or parsed.password or parsed.query or parsed.fragment:
        parser.error("Use a plain local HTTP origin.")
    if parsed.hostname != "localhost" and not ipaddress.ip_address(parsed.hostname).is_loopback:
        parser.error("Only a loopback test server is allowed.")
    from playwright.sync_api import sync_playwright
    with sync_playwright() as runtime:
        executable = os.environ.get("REPOTRACTION_BROWSER_EXECUTABLE")
        if not executable and Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe").is_file():
            executable = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        browser = runtime.chromium.launch(headless=True, **({"executable_path": executable} if executable else {}))
        try:
            page = browser.new_page(viewport={"width": 1510, "height": 1000})
            errors = []
            mutations = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.on("request", lambda request: mutations.append(request.url) if request.method != "GET" else None)
            page.goto(args.url.rstrip("/") + "/?v=missing-link-live#missing-link")
            page.locator("#mlRepo").wait_for(timeout=30000)
            page.locator("#mlRepo").fill(args.repo)
            page.locator("#mlRepo").dispatch_event("input")
            page.locator(".ml-match").first.wait_for(timeout=30000)
            result = {"title": page.locator("#pageTitle").inner_text(),
                "cards": page.locator(".ml-match").count(),
                "verdicts": page.locator(".ml-match .ml-card-top > .ml-pill").all_text_contents(),
                "exports": page.locator('a[href^="/api/missing-link/package"]').count(),
                "javascript_errors": errors, "mutation_requests": mutations}
            if args.screenshot:
                page.screenshot(path=args.screenshot, full_page=False)
            page.set_viewport_size({"width": 390, "height": 844})
            result["mobile_overflow"] = page.evaluate("document.documentElement.scrollWidth > innerWidth")
            if result["mobile_overflow"]:
                result["overflow_nodes"] = page.evaluate("""[...document.querySelectorAll('#missingLinkRoot *')]
                    .filter(node => node.getBoundingClientRect().right > innerWidth + 1 && node.getBoundingClientRect().width)
                    .slice(0, 10).map(node => ({tag: node.tagName, class: node.className, text: node.textContent.slice(0, 80)}))""")
            print(json.dumps(result, indent=2))
            if errors or mutations or result["mobile_overflow"] or result["title"] != "Missing Link":
                raise SystemExit(1)
        finally:
            browser.close()


if __name__ == "__main__":
    main()
