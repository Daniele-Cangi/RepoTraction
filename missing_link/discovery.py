"""Deterministic retrieval hints, not semantic compatibility or novelty scores."""
import re
from collections import Counter
from itertools import groupby

from .sources import parse_issue_url, source_role, runtime_bin_entrypoints
from .qualification import reference_only_body
from .public_api import public_api_hints


SELECTION_POLICY = "external/open first; balance projects and queries; title overlap then upstream rank"
SCREENING_POLICY = "bounded code-dump/manual, reference-only and automated-author hints; explicit issue/query bypass; no replacement or compatibility verdict"
_GENERIC = {"function", "functions", "return", "returns", "class", "unknown", "method", "methods",
            "the", "and", "with", "from", "for", "this", "that", "support", "supports",
            "constructor", "declaration", "declared", "candidate", "partial", "scan"}
_GENERIC_SINGLETON = {"main", "run", "next", "result", "helper", "helpers", "util", "utils",
                      "get", "set", "call", "invoke", "execute", "init", "test", "check"}


def words(value):
    # Language identifiers are whole terms, unlike ordinary camelCase symbols.
    value = re.sub(r"\b(?:java\s*script|type\s*script)\b", lambda match: re.sub(r"\s+", "", match[0]).lower(), value, flags=re.I)
    value = re.sub(r"([a-z])([A-Z])", r"\1 \2", value)
    return re.findall(r"[a-z0-9]+", value.casefold())


def screen_candidate(issue):
    """High-precision retrieval hints, not proof of absent demand or a rejection.

    Discussion or human request prose keeps the candidate eligible. Bot author
    metadata remains a hint; words about generated content are not bot identity.
    These narrowly structural hints only apply to automatic exploration.
    """
    body, title = issue.get("body") or "", issue.get("title") or ""
    hint = {"skip": False, "code": "not_screened_out", "policy": SCREENING_POLICY,
            "discussion_complete": bool(issue.get("context_complete")), "proves_absence_of_demand": False}
    if any((comment.get("body") or "").strip() for comment in issue.get("comments", [])):
        return hint
    reference_only = reference_only_body(body)
    automated = bool(issue.get("bot") or issue.get("author_type") == "Bot")
    if reference_only or automated:
        hint.update(skip=True, code="reference_only_body_hint" if reference_only else "automated_author_hint",
            reason="No independently specified human demand in the acquired body; explicit selection remains available for review.")
        return hint
    # Keep even request-like prose inside code/comments: avoiding a false skip
    # matters more than filtering every dump, and no Markdown rewrite is needed.
    prose = body
    # Accept common PHP line/block comment prefixes, including inline comments.
    # This is only a retrieval hint; original body/quotes are never rewritten.
    prefix = r"(?:^[ \t]*(?:#+[ \t]*)?|//+[ \t]*|/\*+[ \t]*|^[ \t]*\*+[ \t]*)"
    request_prose = re.search(r"(?im)" + prefix + r"(?:please\s+(?:fix|add|support|change|help)|"
        r"(?:could|can|would)\s+(?:we|you)\b|i\s+(?:need|want|would like)\b|"
        r"(?:bug|feature)\s+request\b|expected\s+(?:behavior|result)\b|steps to reproduce\b)", prose)
    if request_prose:
        return hint
    code_dump = (re.fullmatch(r"[\w.-]+\.php", title.strip(), re.I)
                 and body.lstrip().startswith("<?php") and len(body) >= 2000)
    exam_manual = (re.fullmatch(r"(?:cloud\s+)?lab\s+(?:exam\s+)?preparation\s+manual", title.strip(), re.I)
                   and re.search(r"(?im)^#\s+[^\n]*exam preparation manual\b", body[:512])
                   and re.search(r"\b(?:problem sheets|syllabus)\b", body[:1024], re.I))
    if code_dump or exam_manual:
        hint.update(skip=True, code="source_file_dump_hint" if code_dump else "exam_manual_hint",
            reason="Automatic retrieval found a source-file-like body, not a separate request in acquired text."
                   if code_dump else "Automatic retrieval found an exam preparation document, not independently specified adoption demand.")
        hint["reason"] += " This bounded hint is not a compatibility rejection; select the issue explicitly to inspect it."
    return hint


def project_words(repository):
    return words(repository["full_name"].split("/")[-1])


def _strip_project_name(tokens, repository):
    name = project_words(repository)
    full_name = words(repository["full_name"])
    # Drop only the whole package name (p-limit / pLimit / p limit), not
    # individual words such as 'limit' that also describe a useful mechanism.
    result, index = [], 0
    while index < len(tokens):
        if full_name and tokens[index:index + len(full_name)] == full_name:
            index += len(full_name)
        elif name and tokens[index:index + len(name)] == name:
            index += len(name)
        elif name and tokens[index] == "".join(name):
            index += 1
        else:
            result.append(tokens[index])
            index += 1
    return result


def _problem_terms(value, repository):
    return list(dict.fromkeys(token for token in _strip_project_name(words(value), repository)
                             if token not in _GENERIC))


def _path(capability):
    entrypoint = capability.get("entrypoint", "")
    if entrypoint:
        return entrypoint.rsplit(":", 1)[0]
    return next((item["path"] for item in capability.get("evidence", []) if item.get("path")), "unknown")


def problem_queries(repository):
    """Prefer bounded mechanism phrases; automatic discovery excludes the source.

    These are lexical hints from reviewed capabilities, not inferred demands.
    An explicit query/issue remains available for closed or same-project work.
    """
    runtime_entrypoints = runtime_bin_entrypoints(repository.get("files", []))
    public_entrypoints = set(public_api_hints(repository.get("files", []))["entrypoints"])
    def quality(cap):
        return ({"implementation": 0, "support": 1, "test": 2, "infrastructure": 3}[source_role(_path(cap), runtime_entrypoints=runtime_entrypoints)],
                0 if cap.get("maintainer_correction") else 1,
                0 if cap.get("entrypoint") in public_entrypoints else 1,
                0 if cap.get("claim_source") == "model" else 1)
    candidates = sorted(repository.get("capabilities", []), key=lambda cap: (*quality(cap),
        cap.get("level") != "mechanism" or cap.get("name", "").startswith("_"),
        cap.get("summary", "").startswith(("Declared ", "Declaration candidate"))))
    phrases = []
    for cap in candidates:
        if (source_role(_path(cap), runtime_entrypoints=runtime_entrypoints) == "support" and cap.get("claim_source", "structural") == "structural"
                and not cap.get("maintainer_correction")):
            # Unreviewed README/manifest descriptions are retrieval filler,
            # not an independently established implementation mechanism.
            continue
        if (cap.get("summary", "").startswith(("Declared ", "Declaration candidate"))
                and not cap.get("maintainer_correction") and cap.get("claim_source") != "model"):
            # A scanner's description of itself is not a reusable mechanism.
            # Do not let file diversity promote test/build declaration filler.
            continue
        clean = []
        for term in cap.get("search_terms", []):
            if not isinstance(term, str):
                continue
            tokens = _problem_terms(term, repository)
            if len(tokens) == 1 and (tokens[0] in _GENERIC_SINGLETON or len(tokens[0]) < 2
                    or not tokens[0][0].isalpha() or "constructor" in words(term)):
                continue
            original = words(term)
            clean.append((tokens, _strip_project_name(original, repository) == original))
        # Prefer contextual phrases, but specific single-word mechanisms such
        # as pagination/backpressure need no invented second word to be searched.
        # Package names and generic helpers are filtered before this selection.
        # Stripping a compound package name can also erase domain/runtime words
        # (e.g. "Python dotenv parse to dictionary"). Prefer a supplied contextual
        # alternative that needs no source-name stripping; invent no replacement
        # terms. Preserve provider order and the stripped phrase as a fallback.
        phrase = next((term for term, source_free in clean if source_free and len(term) >= 2), None)
        if not phrase:
            phrase = next((term for term, _ in clean if len(term) >= 2), None)
        if not phrase and clean:
            # Filtering each atomic term alone cannot recognize a fragmented
            # package name. Re-clean the original joined terms before deduping.
            combined = _problem_terms(" ".join(term for term in cap.get("search_terms", [])
                if isinstance(term, str) and "constructor" not in words(term)), repository)
            combined = [token for token in combined if token not in _GENERIC_SINGLETON and len(token) >= 2 and token[0].isalpha()]
            phrase = combined or None
        if phrase:
            value = " ".join(phrase[:6])[:100]
            if value not in [item[2] for item in phrases]:
                phrases.append((quality(cap), _path(cap), value))
    # Diversity must not promote weak documentation/declarations over reviewed
    # implementation. Balance modules within each quality tier before moving on.
    selected, paths = [], set()
    for _, group in groupby(phrases, key=lambda item: item[0]):
        tier = list(group)
        for diverse in (True, False):
            for _, path, phrase in tier:
                if phrase in selected or (diverse and path in paths):
                    continue
                selected.append(phrase)
                paths.add(path)
                if len(selected) == 3:
                    break
            if len(selected) == 3:
                break
        if len(selected) == 3:
            break
    qualifiers = f"is:open in:title,body -repo:{repository['full_name']}"
    # PublicGitHub appends these mandatory scope qualifiers after this helper.
    available = 256 - len(qualifiers) - len(" is:issue is:public") - 1
    bounded = []
    for phrase in selected:
        tokens = phrase.split()
        while len(" ".join(tokens)) > available and len(tokens) > 2:
            tokens.pop()
        if len(" ".join(tokens)) <= available:
            bounded.append(" ".join(tokens))
    if not bounded:
        raise ValueError("No problem-oriented search terms established. Review a capability or supply a discovery query.")
    return [f"{phrase} {qualifiers}" for phrase in dict.fromkeys(bounded)]


def select_candidates(batches, queries, repository, limit):
    """Rank the bounded pool; preserve provenance and freeze decisions on resume."""
    pool = {}
    query_words = [set(words(re.sub(r"(?:^|\s)-?\w+:[^\s]+", " ", query))) - _GENERIC for query in queries]
    for query_index, batch in enumerate(batches):
        for rank, raw in enumerate(batch):
            url = raw.get("url") if str(raw.get("url", "")).startswith("https://github.com/") else raw.get("html_url") or ""
            try:
                repo, number = parse_issue_url(url)
            except (ValueError, TypeError):
                continue
            canonical = f"https://github.com/{repo}/issues/{number}"
            key = canonical.casefold()
            candidate = pool.setdefault(key, {"url": canonical, "repo": repo, "title": raw.get("title") or "",
                "state": raw.get("state"), "retrieval": []})
            candidate["retrieval"].append({"query_index": query_index, "upstream_rank": rank + 1})
    for candidate in pool.values():
        overlap = max((len(set(words(candidate["title"])) & query_words[item["query_index"]])
                       for item in candidate["retrieval"]), default=0)
        candidate["title_term_overlap"] = overlap
        candidate["same_project"] = candidate["repo"].casefold() == repository["full_name"].casefold()
    selected, repo_counts, query_counts = [], Counter(), Counter()
    while pool and len(selected) < limit:
        def priority(candidate):
            provenance = candidate["retrieval"]
            return (candidate["same_project"], {"open": 0, "closed": 2}.get(candidate["state"], 1),
                repo_counts[candidate["repo"].casefold()],
                min(query_counts[item["query_index"]] for item in provenance),
                -candidate["title_term_overlap"], min(item["upstream_rank"] for item in provenance),
                candidate["url"].casefold())
        candidate = min(pool.values(), key=priority)
        candidate["selection_order"] = len(selected) + 1
        selected.append(candidate)
        del pool[candidate["url"].casefold()]
        repo_counts[candidate["repo"].casefold()] += 1
        for item in candidate["retrieval"]:
            query_counts[item["query_index"]] += 1
    return selected, len(pool) + len(selected)
