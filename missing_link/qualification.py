"""Derived discovery qualification, independent of model compatibility labels.

Name/reference hints are conservative review signals, not adoption evidence.
Absence of a hint never establishes novelty or author awareness.
"""
import re
import json
try:
    import tomllib
except ImportError:  # Python 3.10 keeps core analytics dependency-free.
    try:
        import tomli as tomllib  # Optional backport, never installed implicitly.
    except ImportError:
        tomllib = None
from datetime import datetime
from html.parser import HTMLParser

from .sources import parse_issue_url
from .discussion import authorship


MAX_REFERENCE_EXCERPTS = 8
STALE_DEMAND_DAYS = 365


def _manifest_metadata(path, value):
    if path == "package.json":
        data = json.loads(value)
        if not isinstance(data, dict):
            raise ValueError("Manifest is not an object")
        for key in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
            if key in data and (not isinstance(data[key], dict)
                                or any(not isinstance(version, str) for version in data[key].values())):
                raise ValueError("Invalid dependency fields")
        return data
    if tomllib is None:
        raise ValueError("TOML parser unavailable")
    data = tomllib.loads(value)
    project = data.get("project", {})
    poetry = data.get("tool", {}).get("poetry", {})
    if not isinstance(project, dict) or not isinstance(poetry, dict):
        raise ValueError("Invalid package metadata")
    dependencies = project.get("dependencies", [])
    optional = project.get("optional-dependencies", {})
    if (not isinstance(dependencies, list) or any(not isinstance(dep, str) for dep in dependencies)
            or not isinstance(optional, dict) or any(not isinstance(group, list)
                or any(not isinstance(dep, str) for dep in group) for group in optional.values())
            or not isinstance(poetry.get("dependencies", {}), dict)):
        raise ValueError("Invalid dependency fields")
    return data


def package_names(repository):
    """Declared distribution names and static package paths; identity hints only."""
    name = repository["full_name"].split("/")[-1]
    distributions, modules = {name}, {name} if name.isidentifier() else set()
    for file in repository.get("files", []):
        path, value = file.get("path", ""), file.get("text", "")
        try:
            if path == "pyproject.toml":
                data = _manifest_metadata(path, value)
                declared = data.get("project", {}).get("name") or data.get("tool", {}).get("poetry", {}).get("name")
            elif path == "package.json":
                declared = _manifest_metadata(path, value).get("name")
            else:
                declared = None
            if isinstance(declared, str) and re.fullmatch(r"(?:@[\w.-]+/)?[\w.-]{1,100}", declared):
                distributions.add(declared)
        except (ValueError, TypeError, AttributeError, RecursionError):
            pass  # Missing/malformed/truncated metadata is unknown, not an alias.
        parts = path.split("/")
        if parts[-1] == "__init__.py":
            package = parts[1] if len(parts) == 3 and parts[0] in {"src", "lib"} else parts[0] if len(parts) == 2 else ""
            if package.isidentifier():
                modules.add(package)
    return sorted(distributions), sorted(modules)


def _declared_dependencies(path, value):
    """Parse literal dependency fields only; never execute build metadata."""
    try:
        if path == "pyproject.toml":
            data = _manifest_metadata(path, value)
            project = data.get("project", {})
            deps = list(project.get("dependencies", []))
            for group in project.get("optional-dependencies", {}).values():
                deps.extend(group)
            deps.extend(data.get("tool", {}).get("poetry", {}).get("dependencies", {}).keys())
        elif path == "package.json":
            data = _manifest_metadata(path, value)
            deps = [name for key in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies")
                    for name in data.get(key, {}).keys()]
        elif path == "requirements.txt":
            deps = [line.strip() for line in value.splitlines() if not line.lstrip().startswith(("#", "-"))]
        else:
            return set()
        return {match[0].casefold().replace("_", "-").replace(".", "-") for dep in deps
                if isinstance(dep, str) and (match := re.match(r"(?:@[\w.-]+/)?[\w.-]+", dep))}
    except (ValueError, TypeError, AttributeError, RecursionError):
        return set()


class _LinkProse(HTMLParser):
    """Keep prose outside HTML anchors; labels/attributes are not demand."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.anchors = []
        self.link_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            linked = any(name == "href" for name, _ in attrs)
            self.anchors.append(linked)
            self.link_depth += linked
        self.parts.append(" ")

    def handle_endtag(self, tag):
        if tag == "a" and self.anchors:
            self.link_depth -= self.anchors.pop()
        self.parts.append(" ")

    def handle_data(self, data):
        if not self.link_depth:
            self.parts.append(data)


def _balanced_end(value, start, opening, closing):
    """Exclusive end of a balanced Markdown label/destination, or None."""
    depth, index = 1, start + 1
    while index < len(value):
        char = value[index]
        if char == "\\":
            index += 2
            continue
        if char == opening:
            depth += 1
        elif char == closing:
            depth -= 1
            if not depth:
                return index + 1
        index += 1
    return None


def _without_markdown_links(value):
    # Remove definitions and recognize inline, full/collapsed/shortcut reference
    # links. A forward scan avoids backtracking through nested untrusted labels.
    references = set()
    def reference_key(label):
        return " ".join(label.split()).casefold()
    def definition(match):
        references.add(reference_key(match[1]))
        return " "
    value = re.sub(r"(?m)^[ \t]{0,3}\[([^\]\n]+)\]:[ \t]*\S+[^\n]*$", definition, value)
    parts, position = [], 0
    while position < len(value):
        start = value.find("[", position)
        if start < 0:
            parts.append(value[position:])
            break
        parts.append(value[position:start])
        escaped = start - 1
        while escaped >= 0 and value[escaped] == "\\":
            escaped -= 1
        if (start - escaped - 1) % 2:
            parts.append("[")
            position = start + 1
            continue
        end = _balanced_end(value, start, "[", "]")
        if end is None:
            parts.append(value[start:])
            break
        label = reference_key(value[start + 1:end - 1])
        link_end = None
        if value[end:end + 1] == "(":
            link_end = _balanced_end(value, end, "(", ")")
        elif value[end:end + 1] == "[":
            ref_end = _balanced_end(value, end, "[", "]")
            if ref_end is not None and (reference_key(value[end + 1:ref_end - 1]) or label) in references:
                link_end = ref_end
        elif label in references:
            link_end = end
        parts.append(" " if link_end is not None else value[start:end])
        position = link_end if link_end is not None else end
    return "".join(parts)


def _reference_body(body):
    """High-precision link-note hint; short real requests remain eligible."""
    parser = _LinkProse()
    parser.feed(body or "")
    parser.close()
    prose = _without_markdown_links("".join(parser.parts))
    without_urls = re.sub(r"https?://[^\s<>]+", " ", prose, flags=re.I)
    tokens = re.findall(r"[\w]+", without_urls.casefold())
    return not tokens or set(tokens) <= {"for", "ex", "example", "examples", "see", "reference",
                                        "references", "link", "links", "e", "g"}


def opportunity_review(issue):
    """Snapshot-relative review signals, never proof that old demand is gone."""
    blockers = []
    age = None
    try:
        collected = datetime.fromisoformat(issue["fetched_at"].replace("Z", "+00:00"))
        updated = datetime.fromisoformat(issue["updated_at"].replace("Z", "+00:00"))
        if collected.utcoffset() is None or updated.utcoffset() is None or updated > collected:
            raise ValueError("Invalid activity timestamps")
        age = (collected - updated).days
    except (KeyError, TypeError, AttributeError, ValueError, OverflowError):
        blockers.append("Demand recency is unknown: valid collection and issue-update timestamps are required before follow-up qualification.")
    if age is not None and age >= STALE_DEMAND_DAYS:
        blockers.append(f"Issue activity is {age} days old; confirm current demand before follow-up. Age alone does not prove resolution or inactivity.")
    reference_only = _reference_body(issue.get("body"))
    if reference_only:
        blockers.append("The body contains only references/example links, not an independently specified adoption request.")
    return {"activity_age_days": age, "stale_after_days": STALE_DEMAND_DAYS,
            "reference_body_hint": reference_only, "qualification_blockers": blockers,
            "method": "snapshot-relative conservative review hints; not a demand or runtime compatibility proof"}


def _references(repository, catalog):
    names, modules = package_names(repository)
    # A repository link establishes a reference; package-name spellings only
    # suggest one. Do not confuse ordinary 'click' prose with the Click package.
    # Quotes/Markdown delimit URLs. Dots may also belong to a repository
    # name, so accept them only as terminal sentence punctuation, not .extra.
    url_end = r"(?=$|[\s/#?,;:!)}\]>\"'`*]|\.+(?=$|[\s,;:!)}\]>\"'`*]))"
    patterns = [("repository_link", re.compile(r"https://github\.com/" + re.escape(repository["full_name"])
                  + r"(?:\.git)?" + url_end, re.I)),
                ]
    for name in names:
        bounded = r"(?<![\w./-])" + re.escape(name) + r"(?![\w./-])"
        patterns.append(("package_name_hint", re.compile(r"[`'\"]" + re.escape(name) + r"[`'\"]", re.I)))
        patterns.append(("package_name_hint", re.compile(bounded + r"(?=['’]s\b|\s+(?:package|library|dependency)\b)", re.I)))
        patterns.append(("package_name_hint", re.compile(r"\b(?:uses?|using|depends on)\s+" + bounded, re.I)))
        if "-" in name and len(name) >= 5:
            patterns.append(("package_name_hint", re.compile(bounded, re.I)))
    for module in modules:
        patterns.append(("package_name_hint", re.compile(r"\b(?:from|import)\s+" + re.escape(module)
            + r"(?=$|[\s.;])", re.I)))
    references, found, repository_link_found = [], 0, False
    for source_id, source in catalog.items():
        target = source_id.startswith("target:")
        if not re.fullmatch(r"q\d+", source_id) and not target:
            continue
        value = source.get("quote") or ""
        active_patterns = patterns
        if target:
            dependencies = _declared_dependencies(source.get("target_path"), value)
            declared = [name for name in names if name.casefold().replace("_", "-").replace(".", "-") in dependencies]
            active_patterns = [("dependency_declaration_hint", re.compile(r"(?<![\w.-])" + re.escape(name) + r"(?![\w.-])", re.I))
                               for name in declared]
            if source.get("target_path", "").endswith(".py"):
                # Static imports only, not string/docstring lookalikes.
                import ast
                try:
                    tree = ast.parse(value)
                    imports = {}
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            roots = {alias.name.split(".")[0] for alias in node.names}
                        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                            roots = {node.module.split(".")[0]}
                        else:
                            continue
                        imports.setdefault(node.lineno, set()).update(roots)
                except (SyntaxError, ValueError, RecursionError):
                    imports = {}
                active_patterns += [("target_import_hint", re.compile(
                    r"(?:\b(?:from|import)\s+|,\s*)(" + re.escape(module) + r")(?=$|[\s.,;])")) for module in modules]
        seen = set()
        for kind, pattern in active_patterns:
            for match in pattern.finditer(value):
                if kind == "target_import_hint":
                    line = value.count("\n", 0, match.start()) + 1
                    if match[1] not in imports.get(line, set()):
                        continue
                # Overlapping URL/name matches should not multiply evidence.
                if any(start <= match.start() < end for start, end in seen):
                    continue
                seen.add(match.span())
                found += 1
                repository_link_found |= kind == "repository_link"
                # Detection covers every acquired source; the excerpt cap only
                # limits presentation/export. Exact links displace weaker name
                # hints, preserving the first excerpts within each priority.
                if (len(references) < MAX_REFERENCE_EXCERPTS or
                        (kind == "repository_link" and any(ref["kind"] != kind for ref in references))):
                    start, end = max(0, match.start() - 80), min(len(value), match.end() + 160)
                    references.append({"source_id": source_id, "url": source.get("url"), "kind": kind,
                        "quote": value[start:end], "authority": source.get("authority", "not_established")})
                    references.sort(key=lambda ref: ref["kind"] != "repository_link")
                    del references[MAX_REFERENCE_EXCERPTS:]
    return references, found, repository_link_found


def assess_discovery(repository, issue, request, classification, checks, catalog):
    """Recompute from acquired sources; imported/model discovery claims are ignored."""
    try:
        target, _ = parse_issue_url(issue["url"])
    except (KeyError, ValueError, TypeError):
        target = ""
    same_id = (repository.get("id") is not None and issue.get("repo_id") is not None
               and repository["id"] == issue["repo_id"])
    same_project = same_id or target.casefold() == repository["full_name"].casefold()
    references, reference_count, linked = _references(repository, catalog)
    review = opportunity_review(issue)
    target_context = issue.get("target_context", {})
    manifest_review = []
    for role, context in (("source", repository), ("target", target_context)):
        for file in context.get("files", []):
            path = file.get("path")
            if path not in {"pyproject.toml", "package.json", "requirements.txt"}:
                continue
            try:
                if file.get("reference_truncated"):
                    raise ValueError("Truncated")
                if path != "requirements.txt":
                    _manifest_metadata(path, file.get("text", ""))
            except (ValueError, TypeError, AttributeError, RecursionError):
                manifest_review.append(f"{role} manifest {path} could not be fully reviewed (parser unavailable, malformed or truncated); prior package/dependency use remains unknown.")
    target_acquired = (target_context.get("public") is True and bool(target_context.get("files"))
                       and isinstance(target_context.get("revision"), str)
                       and bool(re.fullmatch(r"[a-fA-F0-9]{40}|[a-fA-F0-9]{64}", target_context["revision"])))
    relationship = ("same_project" if same_project else "already_referenced" if linked else
                    "reference_hint" if reference_count else "external" if target else "unknown")
    supported_ids = [check["requirement_id"] for check in checks
                     if check["status"] == "satisfied" and check.get("contribution") == "existing_behavior"]
    scope_ids = [check["requirement_id"] for check in checks
                 if check["status"] == "satisfied" and check.get("contribution") == "scope_compatible"]
    conflict_ids = [check["requirement_id"] for check in checks if check["status"] == "incompatible"]
    unknown_ids = [check["requirement_id"] for check in checks if check["status"] == "undetermined"]
    supported = bool(supported_ids)
    contribution = ("supported_with_conflicts" if supported and conflict_ids else
                    "supported" if supported else "conflict" if conflict_ids else "not_demonstrated")
    hard_ids = {r["id"] for r in request["requirements"] if r["mandatory"]}
    verdicts = {check["requirement_id"]: check["status"] for check in checks}
    complete_hard = (bool(hard_ids) and all(verdicts.get(rid) == "satisfied" for rid in hard_ids)
                     and all(r["explicit"] for r in request["requirements"] if r["mandatory"]))
    reasons = []
    if same_project:
        status = "same_project"
        reasons.append("The request belongs to the source project; this is internal work, not a new external connection.")
    elif review["reference_body_hint"]:
        status = "reference_only"
        reasons.append("An empty or reference-only issue body does not establish independently specified actionable demand.")
    elif reference_count:
        status = "known_reference" if linked else "reference_review"
        reasons.append("The source is referenced in acquired discussion or bounded target manifests/imports. Verify identity, intent and prior use; a mention is not adoption or endorsement.")
    elif (request["status"] in {"resolved", "duplicate", "automated"} or issue.get("repo_archived")
          or authorship(issue, original=True)["generated_hint"]):
        status = "not_actionable"
        reasons.append("An unresolved independent human demand in an active target is not established.")
    elif classification == "rejected":
        status = "partial_contribution" if supported else "not_a_fit"
        reasons.append("Some requirements have existing code support, but the complete request is rejected; supported parts do not remove mandatory conflicts or establish an actionable connection."
                       if supported else "Compatibility assessment rejected this contribution; lexical resemblance is not a usable connection.")
    elif not supported:
        status = "similarity_only"
        reasons.append("No requirement has a supported existing contribution. Retrieval or all-undetermined checks are not a discovered solution.")
    elif (relationship == "unknown" or request["status"] != "unresolved" or not request.get("context_complete")
          or not target_acquired
          or manifest_review
          or request.get("constraint_review", {}).get("qualification_blockers") or not complete_hard
          or review["qualification_blockers"]
          or classification not in {"direct", "adapter", "extraction"}):
        status = "needs_review"
        reasons.append("Some contribution is supported, but demand, context or mandatory compatibility still needs review.")
    else:
        status = "external_lead"
        reasons.append("Potential external connection with supported requirements; novelty, execution, target integration and adoption remain unverified.")
    if scope_ids:
        reasons.append("Scope-compatible constraints (such as leaving an API unchanged) are not reusable existing behavior and do not count as a useful contribution.")
    reasons.append("No reference found in bounded discussion/target samples is not proof that this connection is new or unknown to the author.")
    if not target_acquired:
        reasons.append("No pinned public target reference context was acquired; prior dependency/use remains unknown.")
    reasons.extend(review["qualification_blockers"])
    reasons.extend(manifest_review)
    return {"status": status, "relationship": relationship, "contribution": contribution,
        "supported_requirement_ids": supported_ids, "conflicting_requirement_ids": conflict_ids,
        "scope_compatible_requirement_ids": scope_ids,
        "undetermined_requirement_ids": unknown_ids,
        "opportunity_review": review,
        "novelty": "unverified", "eligible_for_followup": status == "external_lead",
        "references": references, "reference_count": reference_count,
        "reference_coverage_complete": reference_count <= len(references),
        "target_reference_context": {"acquired": target_acquired,
            "revision": issue.get("target_context", {}).get("revision"),
            "files_sampled": len(issue.get("target_context", {}).get("files", [])),
            "absence_proves_novelty": False},
        "manifest_review_blockers": manifest_review,
        "reasons": reasons, "method": "source-derived conservative hints, not a novelty classifier"}
