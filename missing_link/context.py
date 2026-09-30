"""Bounded, phase-specific source context with explicit omissions and stable IDs."""
import json
import re

from .analysis import evidence_catalog, resolve_evidence


def size(value):
    return len(json.dumps(value, ensure_ascii=False).encode("utf-8"))


def supplied_reference(reference, sources, catalog):
    """A precise sub-span is valid only when every cited line was supplied."""
    if reference in sources:
        return True
    try:
        evidence = resolve_evidence(reference, catalog)
    except ValueError:
        return False
    if not evidence.get("path"):
        return False
    needed = set(range(evidence["line"], evidence["end_line"] + 1))
    visible = set()
    for source in sources.values():
        if source.get("path") == evidence["path"]:
            visible.update(range(source["line"], source["end_line"] + 1))
    return needed <= visible


def normalize_references(references, sources, catalog):
    normalized = []
    for reference in references:
        span = re.fullmatch(r"(file:[^#]+)#L([1-9][0-9]*)-L([1-9][0-9]*)", reference)
        if span and int(span[3]) - int(span[2]) >= 60:
            first, last = int(span[2]), int(span[3])
            if last - first >= 240:
                raise ValueError("AI evidence span is too broad to substantiate a precise claim.")
            parts = [f"{span[1]}#L{start}-L{min(last, start + 59)}" for start in range(first, last + 1, 60)]
        else:
            parts = [reference]
        if any(not supplied_reference(part, sources, catalog) for part in parts):
            raise ValueError("AI analysis cites lines not actually provided in its source context.")
        normalized.extend(parts)
    return list(dict.fromkeys(normalized))


def build_context(repository, issue, phase, byte_limit):
    # Leave room for instructions, the JSON schema and protocol framing.
    # Reserve for the coverage ledger, interpreted requirements and the schema
    # appearing both in JSON-mode instructions and structured transport framing.
    target = int(byte_limit * 0.60)
    if target < 12000:
        raise ValueError("AI prompt bound is too small for grounded investigation.")
    catalog = evidence_catalog(repository or {"files": [], "capabilities": []}, issue or {"url": ""})
    sources, omitted, shortened = {}, [], []
    data = {"sources": sources}
    if issue:
        data["issue"] = {key: issue.get(key) for key in ("id", "url", "title", "state", "updated_at", "created_at",
            "labels", "author_type", "bot", "context_complete", "limitations")}
    candidates = []
    if repository:
        candidates = sorted(repository.get("capabilities", []), key=lambda c: (
            c.get("level") != "mechanism", c.get("name", "").startswith("_"), c.get("standalone") != "yes"))[:30]
        data["repository"] = {key: repository.get(key) for key in ("id", "full_name", "revision", "license", "coverage")}
        # Do not duplicate source snippets, raw files, snapshots or account data.
        data["repository"]["capabilities"] = [{key: cap.get(key) for key in ("id", "name", "level", "entrypoint",
            "summary", "outcome", "inputs", "outputs", "preconditions", "dependencies", "standalone", "limitations")}
            for cap in candidates]
    if size(data) > target // 2:
        raise ValueError("Capability descriptors exceed context bound; narrow the selected repository.")

    def add(reference, entry, discussion=False):
        if reference in sources:
            return
        entry = dict(entry)
        if discussion and len(entry.get("quote", "")) > 16000:
            entry["quote"] = entry["quote"][:8000] + "\n[OMITTED MIDDLE]\n" + entry["quote"][-8000:]
            shortened.append(reference)
        sources[reference] = entry
        if size(data) > target:
            sources.pop(reference)
            omitted.append(reference)

    # Request first and recent discussion before old comments: later resolution
    # cannot be silently dropped by a prefix-only character cut.
    discussion_ids = [key for key in catalog if key.startswith(("q", "t"))] if issue else []
    order = (["q0"] + [key for key in reversed(discussion_ids) if key != "q0"]) if issue else []
    for reference in order:
        add(reference, catalog[reference], discussion=True)

    if repository:
        by_path = {file["path"]: file for file in repository.get("files", [])}
        # Include implementation spans around selected entry points, then imports,
        # manifests, documentation and the remaining acquired text as space permits.
        regions = []
        # Selected definitions must precede broad file prefixes: a large
        # manifest or unrelated early code can otherwise consume their budget.
        for cap in candidates:
            for evidence in cap.get("evidence", []):
                if evidence.get("path") in by_path:
                    start = max(1, evidence.get("line", 1))
                    end = max(start, cap.get("definition", {}).get("end_line", evidence.get("end_line", start))
                        if evidence.get("kind") == "declaration" else evidence.get("end_line", start))
                    regions.append((evidence["path"], start, min(end, start + 179)))
        for file in sorted(by_path.values(), key=lambda f: (
            0 if f.get("kind") == "manifest" else 1 if f.get("kind") == "source" and not f["path"].startswith("tools/")
            else 2 if f["path"].lower().startswith("readme") else 3 if f.get("kind") == "source" else 4)):
            if file.get("kind") in {"source", "manifest"} or file["path"].lower().startswith("readme"):
                regions.append((file["path"], 1, len(file["text"].splitlines())))
        for file in sorted(by_path.values(), key=lambda f: f.get("kind") not in {"manifest", "documentation"}):
            regions.append((file["path"], 1, len(file["text"].splitlines())))
        for path, start, end in regions:
            for first in range(start, end + 1, 60):
                last = min(end, first + 59)
                reference = f"file:{path}#L{first}-L{last}"
                add(reference, resolve_evidence(reference, catalog))

    report = {"phase": phase, "source_ids": list(sources), "omitted_source_ids": list(dict.fromkeys(omitted)),
        "shortened_discussion_ids": shortened,
        "discussion_complete": bool(issue and issue.get("context_complete") and not shortened and all(key in sources for key in discussion_ids)),
        "capability_ids": [cap["id"] for cap in candidates],
        "omitted_capability_ids": [cap["id"] for cap in (repository or {}).get("capabilities", []) if cap not in candidates],
        "source_coverage": (repository or {}).get("coverage", {}),
        "note": "Selected evidence is not the whole repository. Missing context remains unknown; omitted discussion prevents a qualified positive."}
    # Lists themselves are bounded; do not let reporting thousands of skipped
    # source chunks consume the context that it is supposed to protect.
    report["omitted_source_count"] = len(report["omitted_source_ids"])
    if not repository:
        for key in ("capability_ids", "omitted_capability_ids", "source_coverage"):
            report.pop(key)
    report["omitted_source_ids"] = report["omitted_source_ids"][:60]
    data["context_coverage"] = report
    report["payload_bytes"] = size(data)
    if size(data) > byte_limit - 16000:
        raise ValueError("Context report exceeds the configured prompt bound.")
    return data, report
