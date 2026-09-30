"""Derived discovery qualification, independent of model compatibility labels.

Name/reference hints are conservative review signals, not adoption evidence.
Absence of a hint never establishes novelty or author awareness.
"""
import re
from datetime import datetime

from .sources import parse_issue_url
from .discussion import authorship


MAX_REFERENCE_EXCERPTS = 8
STALE_DEMAND_DAYS = 365


def _reference_body(body):
    """High-precision link-note hint; short real requests remain eligible."""
    without_urls = re.sub(r"https?://[^\s<>]+", " ", body or "", flags=re.I)
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
    name = repository["full_name"].split("/")[-1]
    # A repository link establishes a reference; package-name spellings only
    # suggest one. Do not confuse ordinary 'click' prose with the Click package.
    # Quotes/Markdown delimit URLs. Dots may also belong to a repository
    # name, so accept them only as terminal sentence punctuation, not .extra.
    url_end = r"(?=$|[\s/#?,;:!)}\]>\"'`*]|\.+(?=$|[\s,;:!)}\]>\"'`*]))"
    patterns = [("repository_link", re.compile(r"https://github\.com/" + re.escape(repository["full_name"])
                  + r"(?:\.git)?" + url_end, re.I)),
                ("package_name_hint", re.compile(r"[`'\"]" + re.escape(name) + r"[`'\"]", re.I)),
                ("package_name_hint", re.compile(r"\b(?:from|import)\s+" + re.escape(name)
                  + r"(?=$|[\s.;])", re.I))]
    if "-" in name and len(name) >= 5:
        patterns.append(("package_name_hint", re.compile(r"(?<![\w-])" + re.escape(name) + r"(?![\w-])", re.I)))
    references, found, repository_link_found = [], 0, False
    for source_id, source in catalog.items():
        if not re.fullmatch(r"q\d+", source_id):
            continue
        value = source.get("quote") or ""
        seen = set()
        for kind, pattern in patterns:
            for match in pattern.finditer(value):
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
    relationship = ("same_project" if same_project else "already_referenced" if linked else
                    "reference_hint" if reference_count else "external" if target else "unknown")
    supported_ids = [check["requirement_id"] for check in checks if check["status"] == "satisfied"]
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
        reasons.append("The source is already referenced or its package name appears in acquired discussion. Verify identity, intent and prior use; a mention is not adoption or endorsement.")
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
          or request.get("constraint_review", {}).get("qualification_blockers") or not complete_hard
          or review["qualification_blockers"]
          or classification not in {"direct", "adapter", "extraction"}):
        status = "needs_review"
        reasons.append("Some contribution is supported, but demand, context or mandatory compatibility still needs review.")
    else:
        status = "external_lead"
        reasons.append("Potential external connection with supported requirements; novelty, execution, target integration and adoption remain unverified.")
    reasons.append("No reference found in a bounded discussion is not proof that this connection is new or unknown to the author.")
    reasons.extend(review["qualification_blockers"])
    return {"status": status, "relationship": relationship, "contribution": contribution,
        "supported_requirement_ids": supported_ids, "conflicting_requirement_ids": conflict_ids,
        "undetermined_requirement_ids": unknown_ids,
        "opportunity_review": review,
        "novelty": "unverified", "eligible_for_followup": status == "external_lead",
        "references": references, "reference_count": reference_count,
        "reference_coverage_complete": reference_count <= len(references),
        "reasons": reasons, "method": "source-derived conservative hints, not a novelty classifier"}
