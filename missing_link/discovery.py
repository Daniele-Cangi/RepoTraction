"""Deterministic retrieval hints, not semantic compatibility or novelty scores."""
import re
from collections import Counter
from itertools import groupby

from .sources import parse_issue_url, source_role


SELECTION_POLICY = "external/open first; balance projects and queries; title overlap then upstream rank"
_GENERIC = {"function", "functions", "return", "returns", "class", "unknown", "method", "methods",
            "the", "and", "with", "from", "for", "this", "that", "support", "supports",
            "constructor", "declaration", "declared", "candidate", "partial", "scan"}


def words(value):
    value = re.sub(r"([a-z])([A-Z])", r"\1 \2", value)
    return re.findall(r"[a-z0-9]+", value.casefold())


def project_words(repository):
    return words(repository["full_name"].split("/")[-1])


def _problem_terms(value, repository):
    tokens = words(value)
    name = project_words(repository)
    # Drop only the whole package name (p-limit / pLimit / p limit), not
    # individual words such as 'limit' that also describe a useful mechanism.
    result, index = [], 0
    while index < len(tokens):
        if name and tokens[index:index + len(name)] == name:
            index += len(name)
        elif name and tokens[index] == "".join(name):
            index += 1
        else:
            if tokens[index] not in _GENERIC:
                result.append(tokens[index])
            index += 1
    return list(dict.fromkeys(result))


def _path(capability):
    entrypoint = capability.get("entrypoint", "")
    if entrypoint:
        return entrypoint.split(":", 1)[0]
    return next((item["path"] for item in capability.get("evidence", []) if item.get("path")), "unknown")


def problem_queries(repository):
    """Prefer bounded mechanism phrases; automatic discovery excludes the source.

    These are lexical hints from reviewed capabilities, not inferred demands.
    An explicit query/issue remains available for closed or same-project work.
    """
    def quality(cap):
        return ({"implementation": 0, "support": 1, "test": 2, "infrastructure": 3}[source_role(_path(cap))],
                0 if cap.get("maintainer_correction") else 1 if cap.get("claim_source") == "model" else 2)
    candidates = sorted(repository.get("capabilities", []), key=lambda cap: (*quality(cap),
        cap.get("level") != "mechanism" or cap.get("name", "").startswith("_"),
        cap.get("summary", "").startswith(("Declared ", "Declaration candidate"))))
    phrases = []
    for cap in candidates:
        if (cap.get("summary", "").startswith(("Declared ", "Declaration candidate"))
                and not cap.get("maintainer_correction") and cap.get("claim_source") != "model"):
            # A scanner's description of itself is not a reusable mechanism.
            # Do not let file diversity promote test/build declaration filler.
            continue
        clean = [_problem_terms(term, repository) for term in cap.get("search_terms", []) if isinstance(term, str)]
        # A lone package name or generic helper cannot create a discovery query.
        phrase = next((term for term in clean if len(term) >= 2), None)
        if not phrase:
            combined = list(dict.fromkeys(token for term in clean for token in term))
            phrase = combined if len(combined) >= 2 else None
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
