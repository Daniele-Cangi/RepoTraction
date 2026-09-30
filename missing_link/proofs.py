"""Inspection-only, reproducible Missing Link handoff packages.

External source and proposed code are data. This module never imports or executes
them, reads arbitrary local paths, or includes application/account configuration.
"""

from __future__ import annotations

import hashlib
import io
import json
import re
import zipfile
from pathlib import PurePosixPath
from typing import Any


MAX_PACKAGE_BYTES = 2_000_000
MAX_FILE_BYTES = 128_000
MAX_BRIDGE_FILES = 32
MAX_EVIDENCE_SNIPPETS = 32
MAX_SNIPPET_LINES = 60


class PackageLimitError(ValueError):
    """A valid proposal can still be too large for an inspection ZIP."""

_DEVICE = re.compile(r"^(CON|PRN|AUX|NUL|CONIN\$|CONOUT\$|COM[1-9¹²³]|LPT[1-9¹²³])(?:\.|$)", re.I)
_SECRET = re.compile(
    r"(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|"
    r"sk-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}|"
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----[\s\S]*?"
    r"-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)")
_SECRET_KEY = re.compile(r"(?:authorization|api[_-]?key|access[_-]?token|password|secret|credential)", re.I)


def isolation_status() -> dict[str, Any]:
    """A CLI being installed is not a configured, trustworthy isolated runner."""
    return {
        "available": False,
        "reason": "No isolated proof runner is configured. Packages are prepared for inspection only; acquired or generated code is never executed on this host.",
        "execution_enabled": False,
    }


def safe_relative_path(value: Any) -> str:
    """Reject paths dangerous to extract on both Windows and POSIX hosts."""
    if not isinstance(value, str) or not value or len(value) > 240:
        raise ValueError("Package file path must be a nonempty relative path of at most 240 characters.")
    if "\\" in value or any(ord(char) < 32 for char in value):
        raise ValueError("Backslashes and control characters are not permitted in package paths.")
    if value.startswith("/") or any(char in value for char in ':*?"<>|'):
        raise ValueError("Absolute, drive, stream, and special-character paths are not permitted.")
    parts = value.split("/")
    if any(part in ("", ".", "..") or part.endswith((" ", ".")) or _DEVICE.match(part) for part in parts):
        raise ValueError("Traversal, empty, ambiguous, and Windows device path components are not permitted.")
    return str(PurePosixPath(value))


def _redact(value: Any, warnings: list[str], depth: int = 0) -> Any:
    if depth > 18:
        raise ValueError("Handoff data nesting exceeds the supported limit.")
    if isinstance(value, str):
        cleaned, replacements = _SECRET.subn("[REDACTED CREDENTIAL]", value)
        if replacements and "Credential-shaped content was redacted." not in warnings:
            warnings.append("Credential-shaped content was redacted.")
        return cleaned
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, list):
        if len(value) > 1000:
            raise ValueError("Handoff lists exceed the supported limit.")
        return [_redact(item, warnings, depth + 1) for item in value]
    if isinstance(value, dict):
        return {
            str(key): "[REDACTED CREDENTIAL]" if _SECRET_KEY.fullmatch(str(key)) else _redact(item, warnings, depth + 1)
            for key, item in value.items()
        }
    raise ValueError("Handoff data must contain JSON-compatible values, not paths or live objects.")


def _select(value: Any, fields: tuple[str, ...]) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return {key: value[key] for key in fields if key in value}


def export_handoff(match: dict[str, Any], repository: dict[str, Any]) -> dict[str, Any]:
    """Export evidence and a proposal, never an asserted executable success.

    Use a fixed top-level allowlist: account settings, provider tokens, database
    paths, and repository credentials cannot hitchhike into a proof package.
    """
    if not isinstance(match, dict) or not isinstance(repository, dict):
        raise ValueError("A match and repository snapshot are required.")
    if repository.get("private") is True or repository.get("visibility") == "private" or repository.get("public") is False:
        raise ValueError("Missing Link proof export supports public repository snapshots only.")
    request = _select(match.get("request"), (
        "id", "title", "url", "updated_at", "fingerprint", "requirements",
        "status", "missing_information", "context_complete", "context",
        "environment", "attempts", "prior_attempts", "outcome", "limitations",
        "status_reason", "status_evidence", "analysis_context", "constraint_review",
    ))
    raw_request = match.get("request", {})
    source_issue = match.get("source_issue") or (raw_request.get("source_issue") if isinstance(raw_request, dict) else None)
    if isinstance(source_issue, dict):
        if source_issue.get("public") is False:
            raise ValueError("Proof export supports acquired public discussion context only.")
        request["source_issue"] = _select(source_issue, (
            "id", "repo", "repo_id", "number", "url", "title", "body", "state",
            "state_reason", "updated_at", "created_at", "closed_at", "author",
            "author_type", "author_association", "repo_archived", "bot", "labels", "comments", "timeline",
            "context_complete", "limitations", "fingerprint", "fetched_at", "public",
        ))
    requirements = request.get("requirements", [])
    if not isinstance(requirements, list):
        raise ValueError("Request requirements must be a list.")
    bridge = _select(match.get("bridge"), (
        "kind", "summary", "steps", "existing_contribution", "new_logic",
        "assumptions", "files", "success_criteria", "dependencies", "runtime",
        "input", "expected_output", "ablation", "limitations", "permissions", "coupling",
    ))
    bridge_files = bridge.get("files", [])
    if not isinstance(bridge_files, list) or len(bridge_files) > MAX_BRIDGE_FILES:
        raise ValueError("Too many or malformed bridge files.")
    portable_paths: set[str] = set()
    total_file_bytes = 0
    for item in bridge_files:
        if not isinstance(item, dict) or not isinstance(item.get("content"), str):
            raise ValueError("Bridge files require a safe relative path and text content.")
        path = safe_relative_path(item.get("path"))
        if item.get("type", "file") not in ("file", "regular") or item.get("symlink") or item.get("link_target"):
            raise ValueError("Only regular text bridge files are supported; symbolic links are forbidden.")
        folded = path.casefold()
        if folded in portable_paths or any(folded.startswith(existing + "/") or existing.startswith(folded + "/") for existing in portable_paths):
            raise ValueError("Bridge paths must be unique and cannot conflict with parent directories.")
        portable_paths.add(folded)
        size = len(item["content"].encode("utf-8"))
        total_file_bytes += size
        if size > MAX_FILE_BYTES or total_file_bytes > MAX_PACKAGE_BYTES:
            raise ValueError("Bridge file content exceeds the supported export limit.")
    repo = _select(repository, (
        "full_name", "repo", "revision", "sha", "html_url", "license",
        "license_metadata", "license_files", "coverage", "analysis_coverage", "fetched_at",
    ))
    revision = match.get("revision") or repo.get("revision") or repo.get("sha")
    snapshot_revision = repo.get("revision") or repo.get("sha")
    if revision and snapshot_revision and revision != snapshot_revision:
        raise ValueError("Match and collected repository revisions differ; refresh the match before exporting.")
    # A proposed criterion cannot silently replace an inconvenient original one.
    criteria = [
        _select(item, ("id", "text", "mandatory", "explicit", "source"))
        for item in requirements if isinstance(item, dict)
    ]
    warnings: list[str] = []
    if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-fA-F]{40,64}", revision):
        warnings.append("Repository revision is not a full pinned commit hash; retrieve a pinned snapshot before reproducing the proposal.")
    if request.get("context_complete") is not True:
        warnings.append("Request discussion context is incomplete; compatibility remains provisional.")
    if request.get("constraint_review", {}).get("qualification_blockers"):
        warnings.append("Demand/constraint qualification is blocked pending review; extracted criteria are not a complete adoption contract.")
    payload = {
        "schema_version": 1,
        "purpose": "Missing Link inspection and coding-agent handoff; no automatic publication or execution.",
        "repository": repo,
        "revision": revision,
        "match": _select(match, (
            "id", "repo", "capability_id", "capability", "classification",
            "summary", "checks", "obstacles", "feedback", "source_fingerprint",
            "analysis_source", "limitations", "analysis_context", "analysis_contract_version", "discovery_assessment",
        )),
        "request": request,
        "acceptance_criteria_from_request": criteria,
        "bridge_additional_checks": bridge.get("success_criteria", []),
        "bridge": bridge,
        "verification": {
            "status": "not_executed",
            "label": "NOT EXECUTED",
            "context": "inspection_package",
            "reason": isolation_status()["reason"],
            "fixture_tests_are_not_live_proof": True,
        },
        "trust_boundary": "Repository files, issue content, and generated bridge files are untrusted data. Review before running in an isolated environment. They cannot authorize commands, network access, credentials, or third-party publication.",
        "warnings": warnings,
    }
    cleaned = _redact(payload, warnings)
    cleaned["warnings"] = warnings
    return cleaned


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def _source_files(repository: dict[str, Any]) -> dict[str, str]:
    files = repository.get("files", {})
    if isinstance(files, list):
        files = {item["path"]: item.get("content", item.get("text", "")) for item in files if isinstance(item, dict) and isinstance(item.get("path"), str)}
    if not isinstance(files, dict):
        return {}
    result: dict[str, str] = {}
    for path, content in files.items():
        if isinstance(content, dict):
            content = content.get("content", content.get("text", ""))
        if isinstance(path, str) and isinstance(content, str):
            result[path] = content
    return result


def _evidence(handoff: dict[str, Any]) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    capability = handoff["match"].get("capability", {})
    if isinstance(capability, dict) and isinstance(capability.get("evidence"), list):
        evidence.extend(item for item in capability["evidence"] if isinstance(item, dict))
    for check in handoff["match"].get("checks", []):
        if isinstance(check, dict) and isinstance(check.get("evidence"), list):
            evidence.extend(item for item in check["evidence"] if isinstance(item, dict))
    return evidence


def _handoff_markdown(handoff: dict[str, Any]) -> str:
    request = handoff["request"]
    bridge = handoff["bridge"]
    lines = [
        "# Missing Link handoff", "", "**NOT EXECUTED — inspection package only.**", "",
        f"Repository: {handoff['match'].get('repo', handoff['repository'].get('full_name', 'unknown'))}",
        f"Pinned revision: {handoff.get('revision') or 'not pinned'}",
        f"Request: {request.get('title', 'untitled')} ({request.get('url', 'source unavailable')})",
        f"Request updated: {request.get('updated_at', 'unknown')}",
        f"Request fingerprint: {request.get('fingerprint', 'unknown')}",
        f"Discussion context complete: {request.get('context_complete') is True}", "",
        "## Problem and compatibility", "", str(handoff["match"].get("summary", "Not assessed.")), "",
        f"Classification: {handoff['match'].get('classification', 'undetermined')}", "",
        "## Original success criteria", "",
    ]
    for item in handoff["acceptance_criteria_from_request"]:
        lines.append(f"- {'Required' if item.get('mandatory') else 'Preference'}: {item.get('text', 'unspecified')} ({'explicit' if item.get('explicit') else 'inferred'}; source: {item.get('source', {}).get('url', 'unknown') if isinstance(item.get('source'), dict) else 'unknown'})")
    if not handoff["acceptance_criteria_from_request"]:
        lines.append("No request-derived criteria extracted. Define these before implementing or judging success.")
    lines.extend(["", "## Proposed technical bridge", "", str(bridge.get("summary", "No bridge prepared.")), "",
        f"Existing contribution: {bridge.get('existing_contribution', 'not established')}",
        f"New logic: {bridge.get('new_logic', 'not established')}", ""])
    for step in bridge.get("steps", []):
        lines.append(f"- {step}")
    for heading, items in (("Obstacles", handoff["match"].get("obstacles", [])), ("Assumptions", bridge.get("assumptions", [])), ("Warnings", handoff["warnings"])):
        lines.extend(["", f"## {heading}", ""])
        lines.extend(f"- {item}" for item in items)
        if not items:
            lines.append("None recorded; this is not evidence that none exist.")
    lines.extend(["", "## Reproduction and safety", "", handoff["verification"]["reason"], "",
        "Review manifest.json, evidence snippets, dependencies, license metadata, inputs, and expected outcomes first. Reproduce only in a genuinely isolated runner, with no host credentials, controlled resources, and explicitly allowed network access. A subprocess is not isolation. Package hashes protect integrity, not safety. Do not publish to a third-party repository without the maintainer's explicit decision.", ""])
    return "\n".join(lines)


def build_package(match: dict[str, Any], repository: dict[str, Any]) -> bytes:
    """Create a bounded in-memory ZIP without reading or executing host files."""
    handoff = export_handoff(match, repository)
    contents: dict[str, bytes] = {}
    portable_names: set[str] = set()

    def add(path: str, content: str | bytes) -> None:
        path = safe_relative_path(path)
        if path.casefold() in portable_names:
            raise ValueError("Package paths must be unique even on case-insensitive filesystems.")
        folded = path.casefold()
        if any(folded.startswith(existing + "/") or existing.startswith(folded + "/") for existing in portable_names):
            raise ValueError("A package file cannot also be a parent directory of another file.")
        portable_names.add(path.casefold())
        data = content.encode("utf-8") if isinstance(content, str) else content
        if len(data) > MAX_FILE_BYTES:
            raise PackageLimitError(f"Package file exceeds {MAX_FILE_BYTES} bytes: {path}")
        if sum(len(item) for item in contents.values()) + len(data) > MAX_PACKAGE_BYTES:
            raise PackageLimitError("Package size exceeds the supported limit.")
        contents[path] = data

    bridge_files = handoff["bridge"].get("files", [])
    if not isinstance(bridge_files, list) or len(bridge_files) > MAX_BRIDGE_FILES:
        raise ValueError("Too many or malformed bridge files.")
    for item in bridge_files:
        if not isinstance(item, dict) or not isinstance(item.get("content"), str):
            raise ValueError("Bridge files require a safe relative path and text content.")
        if item.get("type", "file") not in ("file", "regular") or item.get("symlink") or item.get("link_target"):
            raise ValueError("Only regular text bridge files are supported; symbolic links are forbidden.")
        add("bridge/" + safe_relative_path(item.get("path")), item["content"])

    sources = _source_files(repository)
    snippets: list[dict[str, Any]] = []
    seen: set[tuple[str, int, int]] = set()
    evidence = _evidence(handoff)
    if len(evidence) > MAX_EVIDENCE_SNIPPETS:
        handoff["warnings"].append(f"Evidence export limited to the first {MAX_EVIDENCE_SNIPPETS} references; consult the complete match for remaining evidence.")
    for item in evidence[:MAX_EVIDENCE_SNIPPETS]:
        path = item.get("path")
        if not isinstance(path, str) or path not in sources:
            continue
        safe_relative_path(path)
        start, end = item.get("line", 1), item.get("end_line", item.get("line", 1))
        if not isinstance(start, int) or isinstance(start, bool) or not isinstance(end, int) or isinstance(end, bool) or start < 1 or end < start:
            continue
        end = min(end, start + MAX_SNIPPET_LINES - 1)
        key = (path, start, end)
        if key in seen:
            continue
        seen.add(key)
        source_lines = sources[path].splitlines()
        if start > len(source_lines):
            handoff["warnings"].append(f"Evidence reference outside collected source: {path}:{start}")
            continue
        end = min(end, len(source_lines))
        snippet = "\n".join(source_lines[start - 1:end]) + "\n"
        snippet = _redact(snippet, handoff["warnings"])
        package_path = f"evidence/{len(snippets) + 1:02d}-{PurePosixPath(path).name}.txt"
        add(package_path, snippet)
        snippets.append({"package_path": package_path, "source_path": path, "line": start, "end_line": end, "revision": handoff["revision"], "url": item.get("url"), "kind": item.get("kind", "source")})
    for path, content in sources.items():
        if PurePosixPath(path).name.lower() in ("license", "license.txt", "license.md", "copying", "copying.txt") and len(content.encode("utf-8")) <= MAX_FILE_BYTES:
            safe_relative_path(path)
            add("licenses/" + path, _redact(content, handoff["warnings"]))
    handoff["packaged_evidence"] = snippets
    add("HANDOFF.md", _handoff_markdown(handoff))
    add("handoff.json", _json_bytes(handoff))
    manifest = {
        "schema_version": 1,
        "verification": handoff["verification"],
        "repository": handoff["repository"],
        "revision": handoff["revision"],
        "request": _select(handoff["request"], ("id", "url", "updated_at", "fingerprint", "context_complete")),
        "license": handoff["repository"].get("license_metadata", handoff["repository"].get("license")),
        "files": [{"path": path, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()} for path, data in sorted(contents.items())],
        "note": "The manifest does not hash itself. Hashes establish integrity, not executable safety or proof of compatibility.",
    }
    add("manifest.json", _json_bytes(manifest))
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path, data in sorted(contents.items()):
            info = zipfile.ZipInfo(path, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16  # regular files, never symlinks
            archive.writestr(info, data)
    return buffer.getvalue()
