"""Bounded, phase-specific source context with explicit omissions and stable IDs."""
import json
import re
from collections import Counter

from .analysis import evidence_catalog, resolve_evidence, quoted_span
from .discussion import constraint_hints
from .demand import optional_field_hints
from .contracts import MAX_SCOPED_IDS
from .sources import source_role


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


def capability_path(capability):
    path = (capability.get("entrypoint") or "").split(":", 1)[0]
    return path or next((e["path"] for e in capability.get("evidence", []) if e.get("path")), "unknown")


def select_capabilities(capabilities, limit=30):
    """Prefer product implementation with bounded per-file diversity, not export proof."""
    ranked = sorted(capabilities, key=lambda cap: (
        {"implementation": 0, "support": 1, "test": 2, "infrastructure": 3}[source_role(capability_path(cap))],
        cap.get("level") != "mechanism", cap.get("name", "").startswith("_"), cap.get("standalone") != "yes"))
    selected = []
    for role in ("implementation", "support", "test", "infrastructure"):
        groups = {}
        for cap in ranked:
            path = capability_path(cap)
            if source_role(path) == role:
                groups.setdefault(path, []).append(cap)
        # One definition from each file before a second one from a large module.
        for offset in range(max((len(group) for group in groups.values()), default=0)):
            for group in groups.values():
                if offset < len(group):
                    selected.append(group[offset])
                    if len(selected) == limit:
                        return selected
    return selected


def interleave_regions(regions):
    """First source chunk of each region before later chunks from a long definition."""
    chunks = [[(path, first, min(end, first + 59)) for first in range(start, end + 1, 60)]
              for path, start, end in regions]
    for offset in range(max((len(group) for group in chunks), default=0)):
        for group in chunks:
            if offset < len(group):
                yield group[offset]


def build_context(repository, issue, phase, byte_limit):
    # Leave room for instructions, the JSON schema and protocol framing.
    # Reserve for the coverage ledger, interpreted requirements and the schema
    # appearing both in JSON-mode instructions and structured transport framing.
    target = int(byte_limit * 0.60)
    if target < 12000:
        raise ValueError("AI prompt bound is too small for grounded investigation.")
    catalog = evidence_catalog(repository or {"files": [], "capabilities": []}, issue or {"url": ""})
    sources, omitted, shortened, id_limited = {}, [], [], set()
    data = {"sources": sources}
    hints = constraint_hints(issue) if issue else {"items": [], "complete": True}
    if issue:
        data["issue"] = {key: issue.get(key) for key in ("id", "url", "title", "state", "updated_at", "created_at",
            "labels", "author_type", "bot", "context_complete", "limitations")}
        data["potential_constraints"] = hints
        if phase == "request":
            data["potential_subrequirements"] = optional_field_hints({})
    candidates = []
    if repository:
        candidates = select_capabilities(repository.get("capabilities", []))
        data["repository"] = {key: repository.get(key) for key in ("id", "full_name", "revision", "license", "coverage")}
        # Do not duplicate source snippets, raw files, snapshots or account data.
        data["repository"]["capabilities"] = [{key: cap.get(key) for key in ("id", "name", "level", "entrypoint",
            "summary", "outcome", "inputs", "outputs", "preconditions", "dependencies", "standalone", "limitations")}
            for cap in candidates]
    if size(data) > target // 2:
        raise ValueError("Analysis metadata exceeds context bound; narrow the selected context.")

    # Match the schema's ID bound, independently of the byte bound. Leave some
    # slots for selected definitions/support files when comparing a discussion
    # to a repository, rather than filling the entire scope with discussion IDs.
    repository_slots = min(MAX_SCOPED_IDS // 4, len(candidates) * 3 + len((repository or {}).get("files", [])))
    discussion_id_limit = MAX_SCOPED_IDS - repository_slots
    discussion_count = 0

    def add(reference, entry, discussion=False):
        nonlocal discussion_count
        if reference in sources:
            return
        if len(sources) >= MAX_SCOPED_IDS or (discussion and discussion_count >= discussion_id_limit):
            omitted.append(reference)
            id_limited.add(reference)
            return
        entry = dict(entry)
        if discussion and len(entry.get("quote", "")) > 16000:
            original = entry["quote"]
            entry["quote"] = original[:8000] + "\n[OMITTED MIDDLE]\n" + original[-8000:]
            # Preserve bounded middle constraint spans, but never claim that
            # selected excerpts restore the full discussion or author approval.
            for hint in hints["items"]:
                if hint["source_id"] == reference and quoted_span(hint["quote"], entry["quote"]) is None:
                    entry["quote"] += "\n[SELECTED CONSTRAINT EXCERPT]\n" + hint["quote"]
            shortened.append(reference)
        sources[reference] = entry
        previous_subrequirements = data.get("potential_subrequirements")
        if previous_subrequirements is not None:
            # Review hints must only repeat supplied excerpts, and their bytes
            # share the same packing budget. Never restore omitted comments
            # through a post-packing scan of the full acquired discussion.
            data["potential_subrequirements"] = optional_field_hints(sources)
        if size(data) > target:
            sources.pop(reference)
            if previous_subrequirements is not None:
                data["potential_subrequirements"] = previous_subrequirements
            omitted.append(reference)
        elif discussion:
            # Count only retained discussion IDs. Definitions already inserted
            # have their own slots; byte-rejected entries do not spend ID quota.
            discussion_count += 1

    # Request first and recent discussion before old comments: later resolution
    # cannot be silently dropped by a prefix-only character cut.
    discussion_ids = [key for key in catalog if re.fullmatch(r"[qt]\d+", key)] if issue else []
    constraint_sources = list(dict.fromkeys(hint["source_id"] for hint in reversed(hints["items"]) if hint["source_id"] != "q0"))
    order = list(dict.fromkeys(["q0"] + constraint_sources + [key for key in reversed(discussion_ids) if key != "q0"])) if issue else []
    # Preserve the root request, then spend actual bytes on implementation
    # before filling them with comments. Reserving only ID slots is insufficient.
    for reference in (order[:1] if repository else order):
        add(reference, catalog[reference], discussion=True)
    if repository:
        by_path = {file["path"]: file for file in repository.get("files", [])}
        # Include implementation spans around selected entry points, then imports,
        # manifests, documentation and the remaining acquired text as space permits.
        definition_regions = []
        # Selected definitions must precede broad file prefixes: a large
        # manifest or unrelated early code can otherwise consume their budget.
        for cap in candidates:
            for evidence in cap.get("evidence", []):
                if evidence.get("path") in by_path:
                    start = max(1, evidence.get("line", 1))
                    end = max(start, cap.get("definition", {}).get("end_line", evidence.get("end_line", start))
                        if evidence.get("kind") == "declaration" else evidence.get("end_line", start))
                    definition_regions.append((evidence["path"], start, min(end, start + 179)))
        # Do not allow test references attached to a product capability to consume
        # the implementation's budget before other product entry points.
        ordered_definitions = []
        for role in ("implementation", "support", "test", "infrastructure"):
            ordered_definitions.extend(interleave_regions([region for region in definition_regions
                                                          if source_role(region[0]) == role]))
        regions = []
        for file in sorted(by_path.values(), key=lambda f: (
            0 if f.get("kind") == "source" and source_role(f["path"]) == "implementation"
            else 1 if f.get("kind") == "manifest" else 2 if f["path"].lower().startswith("readme") else 3)):
            if file.get("kind") in {"source", "manifest"} or file["path"].lower().startswith("readme"):
                regions.append((file["path"], 1, len(file["text"].splitlines())))
        for file in sorted(by_path.values(), key=lambda f: f.get("kind") not in {"manifest", "documentation"}):
            regions.append((file["path"], 1, len(file["text"].splitlines())))
        for path, first, last in ordered_definitions:
            reference = f"file:{path}#L{first}-L{last}"
            add(reference, resolve_evidence(reference, catalog))
        # Definitions are now already present and cannot be evicted by a long
        # discussion. Later constraints/resolution retain their existing order;
        # any omission makes the comparison explicitly incomplete.
        for reference in order[1:]:
            add(reference, catalog[reference], discussion=True)
        # Reference-only target files follow actual discussion and selected
        # implementation spans. They neither consume reserved source IDs first
        # nor inherit comment shortening/completeness semantics.
        if issue:
            for reference, entry in catalog.items():
                if reference.startswith("target:"):
                    add(reference, entry)
        for path, first, last in interleave_regions(regions):
            reference = f"file:{path}#L{first}-L{last}"
            add(reference, resolve_evidence(reference, catalog))

    report = {"phase": phase, "source_ids": list(sources), "omitted_source_ids": list(dict.fromkeys(omitted)),
        "source_id_limit": MAX_SCOPED_IDS, "source_id_limit_omissions": len(id_limited),
        "shortened_discussion_ids": shortened,
        "discussion_complete": bool(issue and issue.get("context_complete") and not shortened and all(key in sources for key in discussion_ids)),
        "capability_ids": [cap["id"] for cap in candidates],
        "omitted_capability_ids": [cap["id"] for cap in (repository or {}).get("capabilities", []) if cap not in candidates],
        "source_coverage": (repository or {}).get("coverage", {}),
        "note": "Selected evidence is not the whole repository. Missing context remains unknown; omitted discussion prevents a qualified positive."}
    if issue:
        if phase == "request":
            report["optional_field_hint_scan_complete"] = data["potential_subrequirements"]["complete"]
            report["discussion_complete"] &= report["optional_field_hint_scan_complete"]
        target_context = issue.get("target_context", {})
        report["target_reference_context"] = {"revision": target_context.get("revision"),
            "source_ids": [ref for ref in sources if ref.startswith("target:")],
            "omitted_source_ids": [ref for ref in omitted if ref.startswith("target:")],
            "reference_only": True, "absence_proves_novelty": False}
        report["omitted_constraint_ids"] = [hint["id"] for hint in hints["items"]
            if hint["source_id"] not in sources or quoted_span(hint["quote"], sources[hint["source_id"]]["quote"]) is None]
        report["constraint_hint_scan_complete"] = hints["complete"]
    if repository:
        supplied_paths = list(dict.fromkeys(entry["path"] for entry in sources.values() if entry.get("path")))
        report["selection_policy"] = "Request root, then implementation definitions before later discussion; per-file diversity and interleaved spans. Path heuristic, not verified exports."
        report["selected_capability_roles"] = dict(Counter(source_role(capability_path(cap)) for cap in candidates))
        report["supplied_source_roles"] = dict(Counter(source_role(path) for path in supplied_paths))
        report["implementation_source_paths"] = [path for path in supplied_paths if source_role(path) == "implementation"]
        report["implementation_context_missing"] = not report["implementation_source_paths"]
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
