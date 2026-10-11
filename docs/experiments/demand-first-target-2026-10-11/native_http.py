"""One target-specific HTTP acceptance test; run only in the CI container.

This is an integration test, not a Missing Link discovery runner. Candidate
selection has already stopped without a qualified source. Only the unchanged
target and the independently specified direct correction are executed here.
"""
import html
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
from urllib.parse import urlencode
from urllib.request import urlopen


HERE = Path(__file__).resolve().parent
OLD_KEY = "auth_obj.sort_name or auth_obj.name for auth_obj in auth_objs"
NEW_KEY = "_author_order_key(auth_obj.sort_name or auth_obj.name) for auth_obj in auth_objs"
DIRECT_KEY = '''
def _author_order_key(value):
    normalized = "".join(
        char for char in unicodedata.normalize("NFD", value)
        if not unicodedata.combining(char)
    ).casefold()
    return normalized, value

'''


def direct_correction(source):
    if source.count(OLD_KEY) != 1 or source.count("def get_sorted_entries(") != 1:
        raise ValueError("Unexpected target source: do not apply a partial correction")
    return ("import unicodedata\n" + source).replace(OLD_KEY, NEW_KEY).replace(
        "def get_sorted_entries(", DIRECT_KEY + "def get_sorted_entries(")


class Entries(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "div" and "entry_row" in attrs.get("class", "").split():
            self.ids.append(int(attrs["id"]))


def exercise(variant):
    # Imports of third-party target code happen only inside the CI container.
    from datetime import datetime, timedelta, timezone
    from audio_feeder.config import Configuration
    from audio_feeder import database_handler as dh, object_handler as oh, pages
    from audio_feeder.app import create_app
    from werkzeug.serving import make_server, WSGIRequestHandler

    class QuietHandler(WSGIRequestHandler):
        def log(self, *args, **kwargs):
            pass

    config_dir = Path(os.environ["AF_CONFIG_DIR"])
    config_path = config_dir / "config.yml"
    Configuration(config_location=config_path, database_loc=config_dir / "database",
                  static_media_path=config_dir / "static",
                  disable_default_css=True).to_file(config_path)
    app = create_app(load_db=False, populate_qr_cache=False)
    server = make_server("127.0.0.1", 0, app, request_handler=QuietHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    results = []
    http_requests = 0
    try:
        for case in json.loads((HERE / "acceptance.json").read_text(encoding="utf-8")):
            database = {name: {} for name in ("entries", "books", "authors", "series")}
            displays = {}
            for i, name in enumerate(case["names"], 1):
                fallback = case.get("sort_names_absent", False)
                # Display and sort names deliberately differ, to test precedence.
                display = name if fallback else f"Shown {i:04d}: {name}"
                displays[i] = display
                database["authors"][i] = oh.Author(id=i, name=display,
                    sort_name=None if fallback else name, books=[i])
                database["books"][i] = oh.Book(id=i, title=f"Book {i:06d}",
                    authors=[display], author_ids=[i], description="Acceptance fixture")
                date = datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(days=i)
                database["entries"][i] = oh.Entry(id=i, path=Path(f"book-{i}"),
                    type="Book", table="books", data_id=i, date_added=date,
                    last_modified=date, files=[], file_metadata={}, file_hashes={})
            dh.save_database(database)
            dh.get_database(refresh=True)
            pages._clear_book_caches()
            expected_author = [case["names"].index(name) + 1 for name in case["expected"]]
            for order_by in ("author", "title", "date_added", "last_modified"):
                expected = expected_author if order_by == "author" else list(displays)
                for ascending in (True, False):
                    wanted = expected if ascending else list(reversed(expected))
                    per_page = case.get("per_page", 25)
                    for repeat in range(2):
                        actual, names_preserved = [], True
                        for page in range((len(wanted) + per_page - 1) // per_page):
                            query = urlencode(dict(orderBy=order_by, sortAscending=ascending,
                                                   perPage=per_page, page=page))
                            with urlopen(f"http://127.0.0.1:{server.server_port}/books?{query}", timeout=30) as response:
                                document = response.read().decode("utf-8")
                            http_requests += 1
                            parsed = Entries()
                            parsed.feed(document)
                            actual.extend(parsed.ids)
                            names_preserved &= all(displays[i] in html.unescape(document)
                                                   for i in parsed.ids)
                        results.append(dict(case=case["id"], order_by=order_by,
                            ascending=ascending, cached=bool(repeat), expected=wanted,
                            actual=actual, names_preserved=names_preserved,
                            passed=actual == wanted and names_preserved))
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
    return dict(variant=variant, http_requests=http_requests, checks=len(results),
                passed=sum(row["passed"] for row in results), results=results)


def main(output):
    output.mkdir(parents=True, exist_ok=True)
    for variant in ("original", "direct"):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree("/target/src", root / "src")
            target_file = root / "src/audio_feeder/pages.py"
            if variant == "direct":
                target_file.write_text(direct_correction(target_file.read_text(encoding="utf-8")), encoding="utf-8")
            (root / "config").mkdir()
            env = dict(os.environ, PYTHONPATH=str(root / "src"),
                       AF_CONFIG_DIR=str(root / "config"), AF_LOGGING_LEVEL="ERROR")
            subprocess.run([sys.executable, str(Path(__file__).resolve()), "--child", variant,
                            str(output / f"{variant}.json")], env=env, cwd=root, check=True, timeout=180)
            with (output / f"{variant}-upstream-tests.txt").open("w") as log:
                subprocess.run([sys.executable, "-m", "pytest", "/target/tests/test_pages.py",
                                "/target/tests/test_page_generator.py", "-q", "-p", "no:cacheprovider",
                                "--basetemp", str(root / "pytest")], env=env, cwd=root,
                               stdout=log, stderr=subprocess.STDOUT, check=True, timeout=120)
    direct = json.loads((output / "direct.json").read_text())
    original = json.loads((output / "original.json").read_text())
    print(json.dumps({"original_passed": original["passed"], "direct_passed": direct["passed"],
                      "checks_per_variant": direct["checks"]}))
    assert direct["passed"] == direct["checks"], "Direct baseline failed acceptance"
    assert original["passed"] < original["checks"], "Original bug was not reproduced"


if __name__ == "__main__":
    if sys.argv[1] == "--child":
        Path(sys.argv[3]).write_text(json.dumps(exercise(sys.argv[2]), ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        main(Path(sys.argv[1]).resolve())
