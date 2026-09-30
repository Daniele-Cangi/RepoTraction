"""Bounded, read-only public GitHub acquisition and structural evidence.

Fetched content is untrusted data. This module never imports or executes a
repository's code and never turns a declaration/docstring into a verified claim.
The caller owns account isolation, persistent caching, request budgets and jobs.
"""
from __future__ import annotations

import ast
import base64
import binascii
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import PurePosixPath
from typing import Any, Callable
from urllib.parse import quote, urlsplit


MAX_FILE_BYTES = 256 * 1024
MAX_TOTAL_BYTES = 2 * 1024 * 1024
MAX_TEXT_CHARS = 64 * 1024
MAX_DISCUSSION_CHARS = 512 * 1024
MAX_CAPABILITIES = 100
REPO_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}/[A-Za-z0-9_.-]{1,100}\Z")
SHA_PATTERN = re.compile(r"(?:[a-fA-F0-9]{40}|[a-fA-F0-9]{64})\Z")
SUPPORTED_CODE = {".py": "Python", ".js": "JavaScript", ".mjs": "JavaScript",
                  ".cjs": "JavaScript", ".jsx": "JavaScript", ".ts": "TypeScript",
                  ".tsx": "TypeScript"}
MANIFESTS = {"pyproject.toml", "requirements.txt", "setup.cfg", "setup.py",
             "package.json", "cargo.toml", "go.mod", "pom.xml", "makefile"}
SECRET_PATH = re.compile(
    r"(?:^|/)(?:\.env(?:\..*)?|\.git|\.ssh|credentials?|secrets?|node_modules|"
    r"vendor|dist|build|venv|\.venv|__pycache__)(?:/|$)|"
    r"(?:^|/)(?:id_rsa|id_ed25519)(?:\.|$)|\.(?:pem|p12|pfx|key|sqlite3?|db)\Z",
    re.IGNORECASE,
)
SECRET_TEXT = re.compile(
    r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----[\s\S]*?"
    r"-----END (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----|"
    r"\bgh[pousr]_[A-Za-z0-9]{20,}\b|\bgithub_pat_[A-Za-z0-9_]{20,}\b|"
    r"\bAKIA[A-Z0-9]{16}\b|\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b|"
    r"(?P<assignment>(?:api[_-]?key|access[_-]?token|password|secret[_-]?key)"
    r"\s*[:=]\s*['\"])(?P<secret>[^'\"\r\n]{12,})(?=['\"])",
    re.IGNORECASE | re.MULTILINE,
)
PRIVATE_KEY_HEADER = re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def validate_repository(full_name: str) -> str:
    if not isinstance(full_name, str) or not REPO_PATTERN.fullmatch(full_name):
        raise ValueError("Use a GitHub repository in OWNER/REPO form.")
    if full_name.split("/", 1)[1] in {".", ".."}:
        raise ValueError("Invalid GitHub repository name.")
    return full_name


def parse_issue_url(url: str) -> tuple[str, int]:
    """Accept an exact public GitHub issue URL, not arbitrary fetch destinations."""
    if not isinstance(url, str):
        raise ValueError("Use https://github.com/OWNER/REPO/issues/NUMBER.")
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or parsed.netloc.casefold() != "github.com"
            or parsed.query or parsed.fragment or parsed.username or parsed.password):
        raise ValueError("Use https://github.com/OWNER/REPO/issues/NUMBER.")
    match = re.fullmatch(r"/([^/]+/[^/]+)/issues/([1-9][0-9]*)/?", parsed.path)
    if not match:
        raise ValueError("Use https://github.com/OWNER/REPO/issues/NUMBER.")
    full_name = validate_repository(match.group(1))
    number = int(match.group(2))
    if number > 2**31 - 1:
        raise ValueError("Invalid issue number.")
    return full_name, number


def _bounded_int(value: int, low: int, high: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        raise ValueError(f"{name} must be between {low} and {high}.")
    return value


def _safe_path(path: Any) -> bool:
    return (isinstance(path, str) and 0 < len(path) <= 1024 and "\\" not in path
            and not path.startswith("/") and not any(ord(c) < 32 for c in path)
            and all(part not in {"", ".", ".."} for part in path.split("/")))


def _redact(text: Any) -> tuple[str, bool, bool]:
    text = str(text or "")
    truncated = len(text) > MAX_TEXT_CHARS
    text = text[:MAX_TEXT_CHARS]

    def replace(match: re.Match[str]) -> str:
        return (match.group("assignment") or "") + "[REDACTED]"

    clean, count = SECRET_TEXT.subn(replace, text)
    return clean, bool(count), truncated


def redact_public_text(text: Any) -> str:
    """Bound and redact text before persisting feedback or generated artifacts.

    This is defense in depth, not a universal secret detector. Callers must never
    put runtime credentials into source context in the first place.
    """
    return _redact(text)[0]


def _fingerprint(value: Any) -> str:
    serialized = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _kind(path: str) -> str:
    name = PurePosixPath(path).name.casefold()
    if name in MANIFESTS:
        return "manifest"
    if name.startswith(("readme", "license", "copying")) or PurePosixPath(path).suffix.casefold() in {".md", ".rst"}:
        return "documentation"
    if PurePosixPath(path).suffix.casefold() in SUPPORTED_CODE:
        if re.search(r"(?:^|/)(?:tests?|__tests__)(?:/|$)|(?:^|/)test_|[._]test\.", path, re.I):
            return "test"
        return "source"
    return "unsupported"


def _priority(entry: dict[str, Any]) -> tuple[int, int, str]:
    path = entry["path"]
    name = PurePosixPath(path).name.casefold()
    preferred = name.startswith(("readme", "license", "copying")) or name in {
        "app.py", "main.py", "cli.py", "index.js", "index.ts", "core.py"}
    # Empty __init__ files should not crowd real implementations out of the budget.
    empty_init = name == "__init__.py" and entry.get("size", 0) < 100
    return (1 if empty_init else 0 if preferred else 1, path.count("/"), path.casefold())


def _select_files(entries: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    groups = {kind: sorted((e for e in entries if _kind(e["path"]) == kind), key=_priority)
              for kind in ("documentation", "manifest", "source", "test")}
    cycle = ("documentation", "manifest", "source", "source", "test", "source")
    selected: list[dict[str, Any]] = []
    while len(selected) < limit and any(groups.values()):
        for kind in cycle:
            if groups[kind] and len(selected) < limit:
                selected.append(groups[kind].pop(0))
    return selected


def _bot(user: Any) -> bool:
    return (isinstance(user, dict) and (user.get("type") == "Bot"
            or str(user.get("login", "")).casefold().endswith("[bot]")))


class PublicGitHub:
    """GitHub data reader with no token access and no mutation methods."""

    def __init__(self, read: Callable[..., Any], checkpoint: Callable[[], Any] | None = None):
        self.read = read
        self.checkpoint = checkpoint

    def _read(self, endpoint: str, params: dict[str, Any] | None = None) -> Any:
        if self.checkpoint:
            self.checkpoint()
        return self.read(endpoint, params=params) if params else self.read(endpoint)

    def _public_repo(self, full_name: str) -> dict[str, Any]:
        full_name = validate_repository(full_name)
        repo = self._read(f"repos/{full_name}")
        if not isinstance(repo, dict) or repo.get("private") is not False or repo.get("visibility", "public") != "public":
            raise ValueError("Missing Link currently analyzes public repositories only.")
        if isinstance(repo.get("id"), bool) or not isinstance(repo.get("id"), int) or repo["id"] <= 0:
            raise ValueError("GitHub did not provide an immutable repository identity.")
        # Repositories may have been renamed; use their public canonical identity.
        validate_repository(str(repo.get("full_name") or full_name))
        return repo

    def fetch_repository(self, full_name: str, max_files: int = 24) -> dict[str, Any]:
        max_files = _bounded_int(max_files, 1, 80, "max_files")
        repo = self._public_repo(full_name)
        full_name = str(repo.get("full_name") or full_name)
        branch = str(repo.get("default_branch") or "")
        if not branch or len(branch) > 256:
            raise ValueError("The repository has no analyzable default branch.")
        commit = self._read(f"repos/{full_name}/commits/{quote(branch, safe='')}")
        revision = str(commit.get("sha") or "")
        tree_sha = str(commit.get("commit", {}).get("tree", {}).get("sha") or "")
        if not SHA_PATTERN.fullmatch(revision) or not SHA_PATTERN.fullmatch(tree_sha):
            raise ValueError("GitHub did not provide a pinned repository revision/tree.")
        tree = self._read(f"repos/{full_name}/git/trees/{tree_sha}", {"recursive": 1})
        raw_entries = tree.get("tree")
        if not isinstance(raw_entries, list):
            raise ValueError("GitHub returned an invalid repository tree.")
        candidates: list[dict[str, Any]] = []
        excluded: Counter[str] = Counter()
        languages_in_tree: Counter[str] = Counter()
        seen: set[str] = set()
        for entry in raw_entries:
            if not isinstance(entry, dict) or entry.get("type") != "blob":
                continue
            path = entry.get("path")
            if not _safe_path(path) or path in seen:
                excluded["unsafe_or_duplicate_path"] += 1
                continue
            seen.add(path)
            languages_in_tree[SUPPORTED_CODE.get(PurePosixPath(path).suffix.casefold(), "Other")] += 1
            if SECRET_PATH.search(path):
                excluded["sensitive_or_generated_path"] += 1
            elif entry.get("mode") == "120000":
                excluded["symlink"] += 1
            elif _kind(path) == "unsupported":
                excluded["unsupported_file_type"] += 1
            elif not isinstance(entry.get("size"), int) or not 0 <= entry["size"] <= MAX_FILE_BYTES:
                excluded["file_size"] += 1
            elif not SHA_PATTERN.fullmatch(str(entry.get("sha") or "")):
                excluded["invalid_blob_sha"] += 1
            else:
                candidates.append(entry)
        files: list[dict[str, Any]] = []
        total_bytes = 0
        language_counts: Counter[str] = Counter()
        for entry in _select_files(candidates, max_files):
            if total_bytes + entry["size"] > MAX_TOTAL_BYTES:
                excluded["total_size_budget"] += 1
                continue
            blob = self._read(f"repos/{full_name}/git/blobs/{entry['sha']}")
            if blob.get("encoding") != "base64" or blob.get("sha") != entry["sha"]:
                excluded["invalid_blob_response"] += 1
                continue
            encoded = blob.get("content")
            if not isinstance(encoded, str) or len(encoded) > (MAX_FILE_BYTES * 4 // 3 + 4096):
                excluded["file_size"] += 1
                continue
            try:
                raw = base64.b64decode("".join(encoded.split()), validate=True)
                if len(raw) > MAX_FILE_BYTES or b"\x00" in raw:
                    excluded["binary_or_oversize"] += 1
                    continue
                text = raw.decode("utf-8-sig")
            except (ValueError, binascii.Error, UnicodeDecodeError):
                excluded["binary_or_invalid_encoding"] += 1
                continue
            # Never persist credential-looking source, including a partial private key.
            if SECRET_TEXT.search(text) or PRIVATE_KEY_HEADER.search(text):
                excluded["credential_looking_content"] += 1
                continue
            total_bytes += len(raw)
            path = entry["path"]
            language = SUPPORTED_CODE.get(PurePosixPath(path).suffix.casefold(), "Documentation/manifest")
            language_counts[language] += 1
            files.append({"path": path, "sha": entry["sha"], "text": text,
                          "url": f"https://github.com/{full_name}/blob/{revision}/{quote(path, safe='/')}",
                          "kind": _kind(path), "language": language, "bytes": len(raw)})
        limitations = ["Bounded source sample; declarations and test references are not execution proof."]
        if tree.get("truncated"):
            limitations.append("GitHub truncated the recursive tree; unseen paths were not analyzed.")
        if len(candidates) > max_files:
            limitations.append(f"File budget sampled {max_files} of {len(candidates)} eligible files.")
        if excluded:
            limitations.append("Some files were excluded for safety, size, encoding or unsupported type.")
        description, redacted, description_truncated = _redact(repo.get("description"))
        return {"id": repo.get("id"), "full_name": full_name, "revision": revision,
                "default_branch": branch, "description": description, "license": repo.get("license"),
                "files": files, "fetched_at": _now(), "public": True,
                "license_files": [{"path": f["path"], "sha": f["sha"], "url": f["url"]}
                                  for f in files if PurePosixPath(f["path"]).name.casefold().startswith(("license", "copying"))],
                "coverage": {"tree_truncated": bool(tree.get("truncated")),
                             "tree_entries": len(raw_entries), "eligible_files": len(candidates),
                             "files_scanned": len(files), "file_budget": max_files,
                             "bytes_scanned": total_bytes, "language_counts": dict(language_counts),
                             "tree_language_counts": dict(languages_in_tree), "excluded": dict(excluded),
                             "metadata_redacted": redacted, "metadata_truncated": description_truncated,
                             "complete": not tree.get("truncated") and len(files) == len(candidates) and not excluded,
                             "eligible_sample_complete": not tree.get("truncated") and len(files) == len(candidates),
                             "limitations": limitations}}

    def _pages(self, endpoint: str, maximum: int) -> tuple[list[dict[str, Any]], bool]:
        items: list[dict[str, Any]] = []
        page_size = min(100, maximum)
        page = 1
        while len(items) < maximum:
            batch = self._read(endpoint, {"per_page": page_size, "page": page})
            if not isinstance(batch, list):
                raise ValueError("GitHub returned an invalid discussion page.")
            room = maximum - len(items)
            items.extend(item for item in batch[:room] if isinstance(item, dict))
            if len(batch) < page_size:
                return items, True
            if len(batch) > room:
                return items, False
            page += 1
        # One bounded probe establishes whether an exact-size final page is complete.
        probe = self._read(endpoint, {"per_page": page_size, "page": page})
        if not isinstance(probe, list):
            raise ValueError("GitHub returned an invalid discussion page.")
        return items, not probe

    def fetch_issue(self, url: str, max_comments: int = 200) -> dict[str, Any]:
        max_comments = _bounded_int(max_comments, 1, 500, "max_comments")
        requested_name, number = parse_issue_url(url)
        repo = self._public_repo(requested_name)
        full_name = str(repo.get("full_name") or requested_name)
        prefix = f"repos/{full_name}/issues/{number}"
        issue = self._read(prefix)
        if not isinstance(issue, dict) or "pull_request" in issue:
            raise ValueError("Select an issue, not a pull request.")
        comments, comments_complete = self._pages(f"{prefix}/comments", max_comments)
        timeline, timeline_complete = self._pages(f"{prefix}/timeline", max_comments)
        limitations: list[str] = []
        if int(issue.get("comments") or 0) > len(comments):
            comments_complete = False
        if not comments_complete:
            limitations.append("Comment limit reached; later discussion may change the request.")
        if not timeline_complete:
            limitations.append("Timeline limit reached; resolution/duplicate context may be missing.")
        title, title_redacted, title_truncated = _redact(issue.get("title"))
        body, body_redacted, body_truncated = _redact(issue.get("body"))
        normalized_comments: list[dict[str, Any]] = []
        seen_comments: set[Any] = set()
        text_incomplete = title_truncated or body_truncated
        any_redaction = title_redacted or body_redacted
        discussion_remaining = MAX_DISCUSSION_CHARS - len(title) - len(body)
        for comment in comments:
            if comment.get("id") in seen_comments:
                continue
            seen_comments.add(comment.get("id"))
            text, redacted, truncated = _redact(comment.get("body"))
            if len(text) > discussion_remaining:
                text = text[:discussion_remaining]
                truncated = True
            discussion_remaining -= len(text)
            any_redaction |= redacted
            text_incomplete |= truncated
            normalized_comments.append({"id": comment.get("id"),
                                        "url": f"https://github.com/{full_name}/issues/{number}#issuecomment-{comment.get('id')}",
                                        "body": text, "author": (comment.get("user") or {}).get("login"),
                                        "author_association": comment.get("author_association"),
                                        "author_type": (comment.get("user") or {}).get("type"),
                                        "bot": _bot(comment.get("user")),
                                        "updated_at": comment.get("updated_at"),
                                        "created_at": comment.get("created_at"),
                                        "redacted": redacted, "truncated": truncated})
        normalized_timeline = []
        unresolved_cross_references = False
        for event in timeline:
            source_issue = (event.get("source") or {}).get("issue") or {}
            if event.get("event") == "cross-referenced":
                unresolved_cross_references = True
            # Never follow cross-references (possibly private); keep only event identity.
            normalized_timeline.append({"id": event.get("id"), "event": event.get("event"),
                                        "created_at": event.get("created_at"),
                                        "actor": (event.get("actor") or {}).get("login"),
                                        "state_reason": event.get("state_reason"),
                                        "commit_id": event.get("commit_id"),
                                        "source_issue_number": source_issue.get("number"),
                                        "label": (event.get("label") or {}).get("name")})
        if text_incomplete:
            limitations.append("Large discussion text was truncated; do not treat context as complete.")
        if any_redaction:
            limitations.append("Credential-looking text was redacted before storing or sending context.")
        if unresolved_cross_references:
            limitations.append("Cross-referenced discussions not fetched; resolution may need review.")
        if _bot(issue.get("user")):
            limitations.append("Automated issue author; not independent human demand without review.")
        labels = [str(label.get("name") or "") for label in issue.get("labels", []) if isinstance(label, dict)]
        result = {"id": issue.get("id"), "repo": full_name, "number": number,
                  "url": f"https://github.com/{full_name}/issues/{number}", "title": title, "body": body,
                  "state": issue.get("state"), "state_reason": issue.get("state_reason"),
                  "updated_at": issue.get("updated_at"), "created_at": issue.get("created_at"),
                  "closed_at": issue.get("closed_at"), "author": (issue.get("user") or {}).get("login"),
                  "author_type": (issue.get("user") or {}).get("type"), "bot": _bot(issue.get("user")),
                  "labels": labels, "comments": normalized_comments, "timeline": normalized_timeline,
                  "context_complete": comments_complete and timeline_complete and not text_incomplete and not any_redaction and not unresolved_cross_references,
                  "limitations": limitations, "fetched_at": _now(), "public": True}
        result["fingerprint"] = _fingerprint({key: value for key, value in result.items() if key != "fetched_at"})
        return result

    def search_issues(self, query: str, max_pages: int = 2, page_size: int = 20) -> dict[str, Any]:
        max_pages = _bounded_int(max_pages, 1, 10, "max_pages")
        page_size = _bounded_int(page_size, 1, 100, "page_size")
        if not isinstance(query, str) or not query.strip() or len(query) > 256 or any(ord(c) < 32 for c in query):
            raise ValueError("Use a non-empty search query of at most 256 characters.")
        # Reject contradictory scope so authenticated search cannot collect private bodies.
        if re.search(r"(?:^|\s)(?:is|type):(?:pr|pull-request|private)|(?:^|\s)visibility:private|(?:^|\s)-is:public", query, re.I):
            raise ValueError("Missing Link discovery searches public issues only.")
        enforced_query = f"{query.strip()} is:issue is:public"
        candidates: list[dict[str, Any]] = []
        seen: set[str] = set()
        total_count = 0
        incomplete_results = False
        raw_count = 0
        pages_read = 0
        excluded_bots = 0
        for page in range(1, max_pages + 1):
            payload = self._read("search/issues", {"q": enforced_query, "page": page, "per_page": page_size})
            if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
                raise ValueError("GitHub returned an invalid search response.")
            pages_read += 1
            total_count = max(total_count, int(payload.get("total_count") or 0))
            incomplete_results |= bool(payload.get("incomplete_results"))
            items = payload["items"]
            raw_count += len(items)
            for item in items:
                if not isinstance(item, dict) or "pull_request" in item:
                    continue
                if _bot(item.get("user")):
                    excluded_bots += 1
                    continue
                try:
                    full_name, number = parse_issue_url(str(item.get("html_url") or ""))
                except ValueError:
                    continue
                canonical = f"https://github.com/{full_name}/issues/{number}"
                if canonical.casefold() in seen:
                    continue
                seen.add(canonical.casefold())
                # Search is broad retrieval, not full-context analysis. Do not retain body.
                title, _, _ = _redact(item.get("title"))
                candidates.append({"id": item.get("id"), "repo": full_name, "number": number,
                                   "url": canonical, "title": title, "state": item.get("state"),
                                   "updated_at": item.get("updated_at"),
                                   "author": (item.get("user") or {}).get("login"),
                                   "context_complete": False, "requires_public_validation": True})
            if len(items) < page_size or raw_count >= min(total_count, 1000):
                break
        incomplete = incomplete_results or total_count > raw_count
        limitations = ["Search candidates are not matches; fetch public full discussion before compatibility analysis.",
                       "Empty search results do not establish that demand is absent."]
        if incomplete:
            limitations.append("Discovery is incomplete: API timeout, result cap or local page budget.")
        return {"items": candidates, "total_count": total_count, "incomplete_results": incomplete_results,
                "incomplete": incomplete, "queries": [enforced_query], "pages_read": pages_read,
                "raw_results": raw_count, "excluded_bots": excluded_bots, "limitations": limitations}


def _evidence(file: dict[str, Any], line: int, end_line: int, kind: str) -> dict[str, Any]:
    lines = file["text"].splitlines()
    line = max(1, line)
    end_line = max(line, end_line)
    snippet = "\n".join(lines[line - 1:min(end_line, line + 11)])[:1600]
    return {"path": file["path"], "line": line, "end_line": end_line,
            "url": f"{file['url']}#L{line}-L{end_line}", "kind": kind, "quote": snippet}


def _words(value: str) -> list[str]:
    value = re.sub(r"([a-z])([A-Z])", r"\1 \2", value)
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9]+", value.replace("_", " ").casefold())
    stop = {"the", "and", "this", "that", "with", "from", "return", "returns", "function", "class", "self"}
    return list(dict.fromkeys(token for token in tokens if token not in stop and len(token) > 2))[:12]


def _signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    # ast.unparse formats annotations/defaults without evaluating them.
    return f"{node.name}({ast.unparse(node.args)})" + (f" -> {ast.unparse(node.returns)}" if node.returns else "")


def extract_structure(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract declarations, pinned quotes and test references; no semantic proof.

    Python is AST parsed. JavaScript/TypeScript use a conservative, partial
    declaration scanner, not a parser/typechecker. Coverage is attached to the
    snapshot so consumers cannot present a bounded sample as whole-repo analysis.
    """
    capabilities: list[dict[str, Any]] = []
    analysis_files: list[dict[str, Any]] = []
    parsed: dict[str, ast.Module] = {}
    tests: dict[str, list[dict[str, Any]]] = {}
    files: list[dict[str, Any]] = []
    for file in snapshot.get("files", []):
        if not isinstance(file, dict) or not _safe_path(file.get("path")) or not isinstance(file.get("text"), str):
            continue
        if SECRET_PATH.search(file["path"]) or SECRET_TEXT.search(file["text"]) or PRIVATE_KEY_HEADER.search(file["text"]):
            analysis_files.append({"path": file["path"], "status": "safety_excluded", "language": "unknown"})
            continue
        if len(file["text"].encode("utf-8")) > MAX_FILE_BYTES:
            analysis_files.append({"path": file["path"], "status": "size_excluded", "language": "unknown"})
            continue
        files.append(file)
    for file in files:
        if PurePosixPath(file["path"]).suffix.casefold() == ".py":
            try:
                module = ast.parse(file["text"], filename=file["path"])
                parsed[file["path"]] = module
            except (SyntaxError, ValueError, RecursionError):
                analysis_files.append({"path": file["path"], "status": "parse_failed", "language": "Python"})
                continue
            analysis_files.append({"path": file["path"], "status": "ast", "language": "Python"})
            if file.get("kind") == "test" or _kind(file["path"]) == "test":
                for node in ast.walk(module):
                    if isinstance(node, ast.Call):
                        name = node.func.id if isinstance(node.func, ast.Name) else node.func.attr if isinstance(node.func, ast.Attribute) else ""
                        if name:
                            tests.setdefault(name, []).append(_evidence(file, node.lineno, node.end_lineno or node.lineno, "test_reference"))
        elif PurePosixPath(file["path"]).suffix.casefold() in SUPPORTED_CODE:
            analysis_files.append({"path": file["path"], "status": "partial_declaration_scan",
                                   "language": SUPPORTED_CODE[PurePosixPath(file["path"]).suffix.casefold()]})
        else:
            analysis_files.append({"path": file["path"], "status": "quoted_only", "language": "Documentation/manifest"})

    def append(file: dict[str, Any], name: str, level: str, summary: str,
               line: int, end_line: int, **extra: Any) -> None:
        if len(capabilities) >= MAX_CAPABILITIES:
            return
        references = tests.get(name.rsplit(".", 1)[-1], [])[:3]
        # Keep maintainer corrections attached across commits/line movements;
        # exact evidence remains pinned separately to the snapshot revision.
        repository_id = snapshot.get("id") or str(snapshot.get("full_name") or "").casefold()
        identity = f"{repository_id}:{file['path']}:{name}"
        capabilities.append({"id": hashlib.sha256(identity.encode()).hexdigest()[:20], "name": name,
                             "level": level, "summary": summary, "outcome": "Not verified; requires request-specific analysis.",
                             "inputs": [], "outputs": [], "entrypoint": f"{file['path']}:{name}",
                             "dependencies": [], "preconditions": ["Execution and adoption context have not been verified."],
                             "limitations": ["Source presence is not standalone usability or satisfied requirements."],
                             "standalone": "unknown", "test_coverage": "referenced" if references else "none",
                             "evidence": [_evidence(file, line, end_line, "documentation" if level == "product" else "declaration")] + references,
                             "search_terms": _words(f"{name} {summary}"), "claim_source": "structural",
                             "requirements_supported": [], "verification": "not_executed", **extra})

    for file in files:
        path = file["path"]
        kind = file.get("kind") or _kind(path)
        if kind == "test":
            continue
        if kind == "documentation" and PurePosixPath(path).name.casefold().startswith("readme"):
            lines = file["text"].splitlines()
            selected = next((i for i, text in enumerate(lines[:80])
                             if text.strip() and not text.lstrip().startswith(("#", "[", "!", "<", "|", "```"))), 0)
            summary = "Documentation states: " + " ".join(lines[selected:selected + 3])[:600]
            append(file, snapshot.get("full_name", "Repository"), "product", summary,
                   selected + 1, min(selected + 3, len(lines)) or 1,
                   limitations=["Documentation claim only; implementation and outcomes are not verified."])
        module = parsed.get(path)
        if module is not None:
            imports = sorted({node.module or "" for node in ast.walk(module) if isinstance(node, ast.ImportFrom)}
                             | {alias.name for node in ast.walk(module) if isinstance(node, ast.Import) for alias in node.names})

            def visit(body: list[ast.stmt], parent: str = "", depth: int = 0) -> None:
                if depth > 10:
                    return
                for node in body:
                    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        continue
                    name = f"{parent}.{node.name}" if parent else node.name
                    doc = ast.get_docstring(node) or ""
                    line = node.lineno
                    end_line = node.end_lineno or line
                    signature = _signature(node) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) else f"class {name}"
                    calls = sorted({ast.unparse(call.func) for call in ast.walk(node) if isinstance(call, ast.Call)})[:20]
                    summary = doc.splitlines()[0][:600] if doc else f"Declared {'class' if isinstance(node, ast.ClassDef) else 'function'} {name}."
                    if isinstance(node, ast.ClassDef):
                        append(file, name, "subsystem", summary, line, min(end_line, line + 12),
                               definition={"path": path, "line": line, "end_line": end_line},
                               signature=signature, dependencies=imports, calls=calls,
                               preconditions=["Class construction, coupling and runtime requirements are not verified."],
                               standalone="no" if parent else "unknown")
                        visit(node.body, name, depth + 1)
                    else:
                        inputs = [argument.arg + (f": {ast.unparse(argument.annotation)}" if argument.annotation else "")
                                  for argument in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs)
                                  if argument.arg not in {"self", "cls"}]
                        outputs = [ast.unparse(node.returns)] if node.returns else ["Return contract not declared."]
                        append(file, name, "mechanism", summary, line, min(end_line, line + 12),
                               definition={"path": path, "line": line, "end_line": end_line},
                               signature=signature, inputs=inputs, outputs=outputs,
                               dependencies=imports, calls=calls, standalone="no" if parent else "unknown")
                        # Nested implementation mechanisms are useful, but explicitly coupled.
                        visit(node.body, name, depth + 1)

            visit(module.body)
        elif PurePosixPath(path).suffix.casefold() in SUPPORTED_CODE:
            # Anchored line declarations only; deliberately avoids claiming complete JS semantics.
            declaration = re.compile(r"^\s*(?:export\s+(?:default\s+)?)?(?:(?:async\s+)?function\s+(\w+)\s*\(([^\n]*)|class\s+(\w+)\b|(?:const|let)\s+(\w+)\s*=\s*(?:async\s*)?\([^\n]*\)\s*=>)")
            for line, text in enumerate(file["text"].splitlines(), 1):
                match = declaration.match(text)
                if match:
                    name = match.group(1) or match.group(3) or match.group(4)
                    append(file, name, "subsystem" if match.group(3) else "mechanism",
                           f"Declaration candidate {name}; JavaScript/TypeScript partial scan.", line, line,
                           signature=text.strip()[:400],
                           limitations=["Partial declaration scan, not a JS/TS parser, typecheck or execution proof."])
    coverage = snapshot.setdefault("coverage", {})
    coverage["analysis"] = {"files": analysis_files, "capabilities": len(capabilities),
                             "capability_limit": MAX_CAPABILITIES,
                             "capability_limit_reached": len(capabilities) == MAX_CAPABILITIES,
                             "supported_languages": {"Python": "AST", "JavaScript": "partial", "TypeScript": "partial"},
                             "execution": "none", "test_evidence": "name-matched call references; not verified coverage",
                             "limitations": ["Direct and nested declarations only; declarations inside control-flow blocks may be omitted.",
                                             "JS/TS scan may miss declarations or identify comment/string lookalikes."]}
    return capabilities
