"""Grounded interpretation contracts and conservative, non-AI investigation.

External text and model output are data, never instructions or execution authority.
Evidence existence validates provenance, not truth: model conclusions remain hypotheses.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from typing import Any
from .discussion import authorship, constraint_hints
from .qualification import assess_discovery
from .demand import optional_field_hints
from .sources import source_role, runtime_bin_entrypoints
from .contracts import validate_requirement_count
from .non_demands import NON_DEMAND_STATUS, is_non_demand, validate_non_demand
from .contributions import normalize_support, partial_reviews
from .operation_evidence import operation_regions

CLASSIFICATIONS = {"direct", "adapter", "extraction", "rejected", "investigate"}
REQUEST_STATUSES = {"unresolved", "resolved", "duplicate", "unclear", "automated", NON_DEMAND_STATUS}
ANALYSIS_CONTRACT_VERSION = 22


def passive_api_constraint(requirement: dict) -> bool:
    """Override only an unambiguously preservation-only extracted requirement.

    A compound functional requirement or a larger quotation is not passive just
    because it also preserves an API. Unrecognized wording remains model review.
    """
    value = " ".join(requirement["text"].split()).rstrip(".;:!?")
    # A bounded API noun phrase, not an arbitrary clause before the word API.
    name = r"(?!(?:and|or|then|while|but|without|to)\b)[\w'’/-]+"
    api = rf"(?:{name} ){{0,12}}(?:apis?|interfaces?)"
    modal = r"(?:(?:must|should|shall) )?"
    forms = (
        rf"{modal}(?:keep|leave|preserve|maintain) {api} unchanged",
        rf"{api} (?:{modal}(?:remain|stay|be) unchanged|(?:is|are) unchanged|unchanged|(?:requires?|needs?) no changes?)",
        rf"no changes? (?:(?:are )?(?:needed|required|necessary) )?to {api}",
        rf"(?:(?:must|should|shall) not|do not|don't) (?:change|modify) {api}",
        rf"without (?:changing|modifying) {api}",
        rf"(?:it (?:should|must) )?not (?:be )?necessary to (?:make changes to|change|modify) {api}",
    )
    return any(re.fullmatch(form, value, re.I) is not None for form in forms)


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def capability_fingerprint(capability: dict) -> str:
    # Audit timestamps/original values do not change the effective interpretation.
    return digest({key: value for key, value in capability.items()
                   if key not in {"original_interpretation", "maintainer_correction"}})


def text(value: Any, limit: int = 6000) -> str:
    if not isinstance(value, str):
        raise ValueError("Expected text in analysis.")
    if len(value) > limit:
        raise ValueError("Analysis field exceeds its size limit.")
    return value.strip()


def texts(value: Any, maximum: int = 30) -> list[str]:
    if not isinstance(value, list) or len(value) > maximum:
        raise ValueError("Expected a bounded list in analysis.")
    return [text(item) for item in value]


def quoted_span(quote: str, source: str) -> str | None:
    """Recover an original contiguous span; only whitespace may differ."""
    if not quote:
        return None
    if quote in source:
        return quote
    tokens = re.findall(r"\S+", quote)
    if not tokens:
        return None
    match = re.search(r"\s+".join(re.escape(token) for token in tokens), source)
    return match.group(0) if match else None


def evidence_catalog(repository: dict, issue: dict) -> dict[str, dict]:
    catalog = {"q0": {"url": issue["url"], "quote": issue.get("title", "") + "\n" + (issue.get("body") or ""),
                      "kind": "request", **authorship(issue, original=True)}}
    for index, comment in enumerate(issue.get("comments", []), 1):
        catalog[f"q{index}"] = {"url": comment["url"], "quote": comment.get("body", ""), "kind": "discussion",
                                **authorship(comment, issue.get("author"))}
    for index, event in enumerate(issue.get("timeline", [])):
        catalog[f"t{index}"] = {"url": issue["url"], "quote": json.dumps(event, ensure_ascii=False, sort_keys=True), "kind": "timeline"}
    for file in repository.get("files", []):
        catalog[f"file:{file['path']}"] = {"path": file["path"], "line": 1,
            "end_line": len(file["text"].splitlines()), "url": file["url"], "quote": file["text"], "kind": "source"}
    for index, capability in enumerate(repository.get("capabilities", [])):
        for offset, evidence in enumerate(capability.get("evidence", [])):
            catalog[f"c{index}:{offset}"] = dict(evidence)
    if repository.get("id"):
        # Target evidence cannot satisfy an existing SOURCE-code requirement.
        target = issue.get("target_context", {})
        for file in target.get("files", []):
            catalog[f"target:{file['path']}"] = {"target_path": file["path"],
                "url": file["url"], "quote": file["text"], "kind": "target_reference_context",
                "authority": "pinned_public_target_source", "reference_truncated": file.get("reference_truncated", False)}
    return catalog


def request_catalog(issue: dict) -> dict[str, dict]:
    return evidence_catalog({"files": [], "capabilities": []}, issue)


def review_constraints(issue: dict, requirements: list, optional_dispositions=()) -> dict:
    review = constraint_hints(issue)
    review["optional_field_review"] = optional_field_hints(request_catalog(issue), requirements, optional_dispositions)
    blockers = []
    for hint in review["items"]:
        represented = [r["id"] for r in requirements if r["source"]["source_id"] == hint["source_id"]
                       and r["mandatory"] and r["explicit"] and quoted_span(hint["quote"], r["source"]["quote"]) is not None]
        hint["represented_by"] = represented
        hint["needs_review"] = bool(hint.get("kind") != "current_gap" and
                                  (not represented or hint["quote_truncated"]
                                   or hint["authority"] in {"not_established", "automation_or_generated_text_needs_review"}))
        if hint["needs_review"]:
            blockers.append("Potential constraint needs extraction/authority review: " + hint["id"])
    if not review["complete"]:
        blockers.append("Constraint hint scan is bounded/incomplete.")
    if not (issue.get("body") or "").strip():
        blockers.append("Empty issue body: independent actionable demand is not established; discussion may be reference notes.")
    if issue.get("repo_archived"):
        blockers.append("Target repository is archived; current actionable adoption is not established.")
    for item in review["optional_field_review"]["items"]:
        if item["needs_review"]:
            blockers.append("Named optional field needs independent subrequirement extraction/authority review: " + item["field"])
    if not review["optional_field_review"]["complete"]:
        blockers.append("Optional-field hint scan is bounded/incomplete.")
    review["qualification_blockers"] = blockers
    return review


def resolve_evidence(reference: str, catalog: dict[str, dict]) -> dict:
    """Resolve validated line spans, so proof packages contain the relevant code."""
    if reference in catalog:
        return dict(catalog[reference])
    match = re.fullmatch(r"(file:[^#]+)#L([1-9][0-9]*)(?:-L([1-9][0-9]*))?", reference)
    if not match or match[1] not in catalog:
        raise ValueError("Unknown source reference in compatibility analysis.")
    source = dict(catalog[match[1]])
    lines = source["quote"].splitlines()
    start, end = int(match[2]), int(match[3] or match[2])
    if not start <= end <= len(lines) or end - start >= 60:
        raise ValueError("Source line range must exist and contain at most 60 lines.")
    source.update(line=start, end_line=end, quote="\n".join(lines[start - 1:end]),
        url=source["url"].split("#")[0] + f"#L{start}-L{end}")
    return source


def validate_request(raw: dict, issue: dict) -> dict:
    if not isinstance(raw, dict):
        raise ValueError("Request interpretation must be an object.")
    catalog = request_catalog(issue)
    status = raw.get("status", "unclear")
    if status not in REQUEST_STATUSES:
        raise ValueError("Unknown request disposition.")
    validate_non_demand(raw, issue, catalog)
    requirements = []
    raw_requirements = raw.get("requirements", [])
    validate_requirement_count(raw_requirements, minimum=0 if is_non_demand(raw) else 1)
    for index, item in enumerate(raw_requirements):
        if not isinstance(item, dict):
            raise ValueError("Each requirement must be an object.")
        source_id = item.get("source_id", "")
        quote = text(item.get("quote", ""))
        original = quoted_span(quote, catalog[source_id]["quote"]) if source_id in catalog else None
        if original is None:
            raise ValueError("Every requirement needs a verbatim quote from the fetched discussion.")
        for key in ("mandatory", "explicit"):
            if not isinstance(item.get(key), bool):
                raise ValueError("Requirement mandatory/explicit flags must be boolean.")
        requirements.append({"id": f"r{index}", "text": text(item["text"]),
            "mandatory": item["mandatory"], "explicit": item["explicit"],
            "source": {"url": catalog[source_id]["url"], "quote": original, "source_id": source_id,
                "quote_match": "exact" if original == quote else "whitespace_normalized"},
            "inference": text(item.get("inference", ""))})
    status_evidence = []
    for reference in raw.get("status_source_ids", []):
        if reference not in catalog:
            raise ValueError("Unknown discussion reference.")
        status_evidence.append({"url": catalog[reference]["url"], "source_id": reference})
    # Open/closed alone is NOT evidence that the need has been satisfied.
    if status in {"resolved", "duplicate", "automated"} and not status_evidence:
        status = "unclear"
    if not issue.get("context_complete", False) and status == "unresolved":
        status = "unclear"
    if issue.get("bot") and status != NON_DEMAND_STATUS:
        status = "automated"
    constraint_review = review_constraints(issue, requirements, raw.get("optional_field_dispositions", []))
    return {"id": issue["id"], "title": issue["title"], "url": issue["url"],
        "outcome": text(raw.get("outcome", issue["title"])), "status": status,
        "status_reason": text(raw.get("status_reason", "")), "status_evidence": status_evidence,
        "requirements": requirements, "environment": texts(raw.get("environment", [])),
        "prior_attempts": texts(raw.get("prior_attempts", [])),
        "missing_information": texts(raw.get("missing_information", [])),
        "optional_field_dispositions": constraint_review["optional_field_review"]["dispositions"],
        "constraint_review": constraint_review,
        "context_complete": bool(issue.get("context_complete")),
        "updated_at": issue.get("updated_at"), "fingerprint": issue.get("fingerprint", digest(issue))}


def conservative_request(issue: dict) -> dict:
    """Keep an unreviewed demand excerpt; do not pretend to infer all constraints."""
    body = issue.get("body") or issue["title"]
    excerpt = body[:1200]
    return validate_request({"outcome": issue["title"], "status": "automated" if issue.get("bot") else "unclear",
        "status_source_ids": ["q0"] if issue.get("bot") else [],
        "status_reason": "No interpretive provider or reviewed coding-agent analysis. Full requirements and resolution need review.",
        "requirements": [{"text": excerpt, "mandatory": True, "explicit": True,
            "source_id": "q0", "quote": excerpt}],
        "missing_information": ["Independently interpret requirements and later discussion before treating this as an opportunity."]}, issue)


def validate_matches(raw_matches: list, repository: dict, issue: dict, request: dict, source: str) -> list[dict]:
    if not isinstance(raw_matches, list) or len(raw_matches) > 12:
        raise ValueError("At most 12 evaluated capabilities per discussion.")
    if is_non_demand(request):
        if raw_matches:
            raise ValueError("A non-demand disposition cannot have compatibility matches.")
        return []
    validate_requirement_count(request["requirements"])
    # Recompute from acquired discussion even for imported/older request objects.
    request = dict(request, constraint_review=review_constraints(issue, request["requirements"],
                   request.get("optional_field_dispositions", [])))
    catalog = evidence_catalog(repository, issue)
    runtime_entrypoints = runtime_bin_entrypoints(repository.get("files", []))
    capabilities = {item["id"]: item for item in repository["capabilities"]}
    requirements = {item["id"]: item for item in request["requirements"]}
    matches = []
    used = set()
    operation_cache = {}
    for raw in raw_matches:
        if not isinstance(raw, dict):
            raise ValueError("Each compatibility assessment must be an object.")
        capability_id = raw.get("capability_id")
        if capability_id not in capabilities or capability_id in used:
            raise ValueError("Unknown or duplicate capability in compatibility analysis.")
        used.add(capability_id)
        capability = capabilities[capability_id]
        regions = operation_regions(capability, repository.get("files", []), cache=operation_cache)
        classification = raw.get("classification", "investigate")
        if classification not in CLASSIFICATIONS:
            raise ValueError("Unknown compatibility classification.")
        checks = []
        raw_checks = raw.get("checks", [])
        if not isinstance(raw_checks, list) or len(raw_checks) > 30 or any(not isinstance(item, dict) for item in raw_checks):
            raise ValueError("Compatibility checks must be a bounded list of objects.")
        supplied = {item.get("requirement_id"): item for item in raw_checks}
        if len(supplied) != len(raw_checks):
            raise ValueError("Duplicate requirement assessment.")
        if set(supplied) - set(requirements):
            raise ValueError("Unknown requirement in compatibility matrix.")
        partial = partial_reviews(raw.get("partial_support", []), requirements)
        for rid, requirement in requirements.items():
            item = supplied.get(rid, {})
            status = item.get("status", "undetermined")
            contribution = item.get("contribution", "not_demonstrated")
            evidence = []
            for reference in item.get("source_ids", []):
                entry = resolve_evidence(reference, catalog)
                entry["quote"] = entry["quote"][:1600]
                entry["source_id"] = reference
                evidence.append(entry)
            reason = text(item.get("reason", "No grounded assessment supplied."))
            review = partial.get(rid)
            # Every review citation is validated, even for an analogy or target
            # context. Candidate anchors must also occur in this check's evidence.
            if review:
                for reference in review["source_ids"]:
                    resolve_evidence(reference, catalog)
            status, contribution = normalize_support(status, contribution, evidence,
                capability=capability, passive=passive_api_constraint(requirement), reason=reason if "reason" in item else "",
                runtime_entrypoints=runtime_entrypoints, partial=review, operation_regions=regions)
            checks.append({"requirement_id": rid, "status": status, "contribution": contribution,
                "reason": reason, "evidence": evidence, **({"partial_support": review} if review else {})})
        hard = [item for item in checks if requirements[item["requirement_id"]]["mandatory"]]
        obstacles = texts(raw.get("obstacles", []))
        if any(item["status"] == "incompatible" for item in hard):
            classification = "rejected"
        elif any(item["status"] == "undetermined" for item in hard) or not hard:
            classification = "investigate"
        elif not any(item["contribution"] == "existing_behavior" for item in checks):
            classification = "investigate"
        if request["status"] in {"resolved", "duplicate", "automated"}:
            classification = "rejected"
            obstacles.append("The fetched discussion does not represent an unresolved independent request: " + request["status"])
        elif request["status"] == "unclear" or not request["context_complete"]:
            if classification != "rejected":
                classification = "investigate"
            obstacles.append("Request resolution or discussion completeness is not established.")
        blockers = request["constraint_review"]["qualification_blockers"]
        if blockers:
            if classification != "rejected":
                classification = "investigate"
            obstacles.extend(blockers)
        bridge = copy.deepcopy(raw.get("bridge", {}))
        if not isinstance(bridge, dict):
            raise ValueError("Bridge must be an object.")
        for key in ("summary", "existing_contribution", "new_logic", "runtime", "coupling", "input", "expected_output", "ablation"):
            bridge[key] = text(bridge.get(key, ""))
        for key in ("steps", "assumptions", "dependencies", "permissions"):
            bridge[key] = texts(bridge.get(key, []))
        bridge["kind"] = bridge.get("kind", "investigation")
        if bridge["kind"] not in {"command", "example", "adapter", "extraction", "investigation"}:
            raise ValueError("Unsupported bridge kind.")
        files = bridge.get("files", [])
        if not isinstance(files, list) or len(files) > 10:
            raise ValueError("Bridge file limit exceeded.")
        bridge["files"] = [{"path": text(file["path"], 200), "content": text(file["content"], 40000)} for file in files]
        # Criteria are frozen from demand, not a conveniently weak generated test.
        bridge["success_criteria"] = [item["text"] for item in request["requirements"] if item["mandatory"]]
        bridge["verification"] = {"status": "not_executed",
            "reason": "Source-grounded hypothesis; no isolated proof runner has executed this bridge."}
        if classification == "direct" and capability.get("standalone") != "yes":
            classification = "extraction" if capability.get("standalone") == "no" else "investigate"
            obstacles.append("Separately usable entry point is not established.")
        key = {"repo_id": repository["id"], "revision": repository["revision"],
            "target_context_fingerprint": issue.get("target_context", {}).get("fingerprint") or digest(issue.get("target_context", {})),
            "analysis_contract_version": ANALYSIS_CONTRACT_VERSION,
            "request": request["fingerprint"], "capability": capability_id, "source": source,
            "capability_fingerprint": capability_fingerprint(capability)}
        matches.append({"id": digest(key)[:32], "repo": repository["full_name"], "repo_id": repository["id"],
            "analysis_contract_version": ANALYSIS_CONTRACT_VERSION,
            "revision": repository["revision"], "request": request, "capability_id": capability_id,
            "target_context_fingerprint": key["target_context_fingerprint"],
            "capability": capability, "capability_fingerprint": key["capability_fingerprint"],
            "classification": classification, "summary": text(raw.get("summary", "Investigation required.")),
            "discovery_assessment": assess_discovery(repository, issue, request, classification, checks, catalog),
            "checks": checks, "bridge": bridge, "obstacles": list(dict.fromkeys(obstacles)),
            "analysis_source": source, "source_fingerprint": request["fingerprint"],
            "source_issue": issue,
            "limitations": ["Grounded interpretation is not an executed proof of compatibility."], "feedback": []})
    return matches


def conservative_matches(repository: dict, issue: dict, request: dict) -> list[dict]:
    words = set(re.findall(r"[a-z]{4,}", (issue["title"] + " " + issue.get("body", "")).lower()))
    def overlap(capability: dict) -> int:
        return len(words & set(re.findall(r"[a-z]{4,}", json.dumps([capability.get("name"), capability.get("summary"), capability.get("search_terms")]).lower())))
    candidates = sorted(repository["capabilities"], key=overlap, reverse=True)[:3]
    return validate_matches([{"capability_id": capability["id"], "classification": "investigate",
        "summary": "Lexical retrieval candidate only — no compatibility conclusion.",
        "obstacles": ["Needs independent requirement interpretation and code/context review."],
        "bridge": {"kind": "investigation", "summary": "Review the pinned entry point against every mandatory requirement.",
            "steps": ["Inspect source evidence and the full discussion.", "Provide grounded analysis through a configured model or a coding-agent handoff."],
            "existing_contribution": "Not yet established.", "new_logic": "Not yet established."}} for capability in candidates],
        repository, issue, request, "structural")


def extension_groups(matches: list[dict]) -> list[dict]:
    grouped: dict[str, dict] = {}
    for match in matches:
        if (match.get("stale") or match.get("superseded") or match["request"]["status"] != "unresolved"
                or match["request"].get("constraint_review", {}).get("qualification_blockers")):
            continue
        if not any(check.get("status") == "satisfied" and check.get("contribution") == "existing_behavior"
                   for check in match["checks"]):
            # A recurring gap with no reusable source behavior is not an
            # extension of an established contribution (nor a discovery lead).
            continue
        discovery = match.get("discovery_assessment", {})
        if (discovery.get("relationship", "external") != "external"
                or discovery.get("status") in {"reference_only", "not_actionable"}
                or discovery.get("opportunity_review", {}).get("qualification_blockers")):
            continue
        requirements = {item["id"]: item for item in match["request"]["requirements"]}
        for check in match["checks"]:
            if check["status"] != "incompatible":
                continue
            requirement = requirements[check["requirement_id"]]["text"]
            key = re.sub(r"\W+", " ", requirement.casefold()).strip()
            group = grouped.setdefault(key, {"requirement": requirement, "match_ids": [], "requests": set()})
            group["match_ids"].append(match["id"])
            group["requests"].add(match["request"]["url"])
    return [{"requirement": g["requirement"], "match_ids": g["match_ids"], "count": len(g["requests"]),
        "note": "Independent observed requests, not an adoption forecast."} for g in grouped.values() if len(g["requests"]) >= 2]


def analysis_contract() -> dict:
    return {"request": {"outcome": "Desired outcome independent of the candidate", "status": "unclear",
        "status_source_ids": ["q0"], "status_reason": "Read later comments, do not use issue state alone.",
        "requirements": [{"text": "Requirement", "mandatory": True, "explicit": True, "source_id": "q0", "quote": "verbatim source text", "inference": ""}],
        "environment": [], "prior_attempts": [], "missing_information": [], "optional_field_dispositions": []},
        "matches": [{"capability_id": "ID from repository", "classification": "investigate",
            "summary": "Problem to existing contribution", "checks": [{"requirement_id": "r0", "status": "undetermined",
                "contribution": "not_demonstrated", "reason": "Explain operating conditions", "source_ids": ["file:example.py#L1-L8"]}],
            "partial_support": [], "obstacles": [],
            "bridge": {"kind": "investigation", "summary": "Smallest useful connection",
                "steps": [], "existing_contribution": "Existing code", "new_logic": "Added code, if any", "assumptions": [], "files": [],
                "dependencies": [], "runtime": "", "permissions": [], "coupling": "", "input": "", "expected_output": "", "ablation": ""}}]}
