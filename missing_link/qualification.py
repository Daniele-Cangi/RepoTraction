"""Derived discovery qualification, independent of model compatibility labels.

Name/reference hints are conservative review signals, not adoption evidence.
Absence of a hint never establishes novelty or author awareness.
"""
import re

from .sources import parse_issue_url
from .discussion import authorship


MAX_REFERENCE_EXCERPTS = 8


def _references(repository, catalog):
    name = repository["full_name"].split("/")[-1]
    # A repository link establishes a reference; package-name spellings only
    # suggest one. Do not confuse ordinary 'click' prose with the Click package.
    patterns = [("repository_link", re.compile(r"https://github\.com/" + re.escape(repository["full_name"])
                  + r"(?:\.git)?(?=$|[\s/#?,)\]>])", re.I)),
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
    relationship = ("same_project" if same_project else "already_referenced" if linked else
                    "reference_hint" if reference_count else "external" if target else "unknown")
    supported = sum(check["status"] == "satisfied" for check in checks)
    contribution = "conflict" if classification == "rejected" else "supported" if supported else "not_demonstrated"
    hard_ids = {r["id"] for r in request["requirements"] if r["mandatory"]}
    verdicts = {check["requirement_id"]: check["status"] for check in checks}
    complete_hard = (bool(hard_ids) and all(verdicts.get(rid) == "satisfied" for rid in hard_ids)
                     and all(r["explicit"] for r in request["requirements"] if r["mandatory"]))
    reasons = []
    if same_project:
        status = "same_project"
        reasons.append("The request belongs to the source project; this is internal work, not a new external connection.")
    elif not (issue.get("body") or "").strip():
        status = "reference_only"
        reasons.append("The empty issue body does not establish actionable demand; it may be a reference note.")
    elif reference_count:
        status = "known_reference" if linked else "reference_review"
        reasons.append("The source is already referenced or its package name appears in acquired discussion. Verify identity, intent and prior use; a mention is not adoption or endorsement.")
    elif (request["status"] in {"resolved", "duplicate", "automated"} or issue.get("repo_archived")
          or authorship(issue, original=True)["generated_hint"]):
        status = "not_actionable"
        reasons.append("An unresolved independent human demand in an active target is not established.")
    elif classification == "rejected":
        status = "not_a_fit"
        reasons.append("Compatibility assessment rejected this contribution; lexical resemblance is not a usable connection.")
    elif not supported:
        status = "similarity_only"
        reasons.append("No requirement has a supported existing contribution. Retrieval or all-undetermined checks are not a discovered solution.")
    elif (relationship == "unknown" or request["status"] != "unresolved" or not request.get("context_complete")
          or request.get("constraint_review", {}).get("qualification_blockers") or not complete_hard
          or classification not in {"direct", "adapter", "extraction"}):
        status = "needs_review"
        reasons.append("Some contribution is supported, but demand, context or mandatory compatibility still needs review.")
    else:
        status = "external_lead"
        reasons.append("Potential external connection with supported requirements; novelty, execution, target integration and adoption remain unverified.")
    reasons.append("No reference found in a bounded discussion is not proof that this connection is new or unknown to the author.")
    return {"status": status, "relationship": relationship, "contribution": contribution,
        "novelty": "unverified", "eligible_for_followup": status == "external_lead",
        "references": references, "reference_count": reference_count,
        "reference_coverage_complete": reference_count <= len(references),
        "reasons": reasons, "method": "source-derived conservative hints, not a novelty classifier"}
