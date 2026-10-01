"""Deterministic demand citations. Selecting a span is not interpreting it."""
import copy
import hashlib
import json
import re

from .contracts import MAX_SCOPED_IDS


def citation_spans(sources, catalog, byte_limit):
    """Bounded original lines/sentences, never the prompt's synthetic omission seams.

    IDs depend on original source offsets, not model spelling or packing order.
    Overflow is explicit: selected spans do not certify complete discussion.
    """
    spans, omitted = {}, 0
    for ref, source in sources.items():
        if not re.fullmatch(r"q\d+", ref):
            continue
        original = catalog[ref]["quote"]
        visible = source.get("quote", "")
        # Split at sentence boundaries as well as lines, keeping punctuation,
        # backticks and Markdown verbatim. Very long lines remain bounded.
        for match in re.finditer(r"[^\n]+", original):
            for sentence in re.finditer(r".+?(?:[.!?](?=\s+[A-Z]|$)|$)", match[0]):
                start, end = match.start() + sentence.start(), match.start() + sentence.end()
                for first in range(start, end, 1600):
                    quote = original[first:min(end, first + 1600)].strip()
                    if not quote or quote not in visible:
                        # Unsent discussion is already covered by context_coverage.
                        continue
                    offset = original.find(quote, first, min(end, first + 1600))
                    key = "s" + hashlib.sha256(f"{ref}:{offset}:{offset + len(quote)}".encode()).hexdigest()[:16]
                    entry = {"source_id": ref, "quote": quote}
                    spans[key] = entry
                    if len(spans) > MAX_SCOPED_IDS or len(json.dumps(spans, ensure_ascii=False).encode()) > byte_limit:
                        spans.pop(key)
                        omitted += 1
    return spans, {"span_count": len(spans), "omitted_visible_spans": omitted,
                   "complete": not omitted, "method": "exact original spans; selection is not semantic validation"}


def resolve_citations(raw, spans):
    """Normalize a schema-validated provider attempt without mutating its record."""
    normalized = copy.deepcopy(raw)
    for requirement in normalized["requirements"]:
        ref = requirement.pop("citation_id")
        if ref not in spans:
            raise ValueError("AI requirement cites an unavailable demand span.")
        requirement.update(spans[ref])
    return normalized


def optional_field_hints(catalog, requirements=()):
    """Review optional API fields independently; '?' is not an adoption verdict.

    A TypeScript optional argument does not prove that implementing the requested
    feature is optional. Only the independent interpretation assigns mandatory.
    The bounded syntactic scan can flag omissions, never add requirements/support.
    """
    items, omitted = [], 0
    for ref, source in catalog.items():
        if not re.fullmatch(r"q\d+", ref):
            continue
        for line in source["quote"].splitlines():
            names = re.findall(r"\b([A-Za-z_]\w{0,79})\?\s*:", line)
            for name in dict.fromkeys(names):
                if len(items) == 30 or len(line) > 1600:
                    omitted += 1
                    continue
                items.append({"field": name, "source_id": ref, "quote": line.strip()})
    def identity(value):
        value = re.sub(r"([a-z])([A-Z])", r"\1 \2", value)
        return tuple(re.findall(r"[a-z0-9]+", value.casefold()))
    def contains(tokens, key):
        return any(tokens[index:index + len(key)] == key for index in range(len(tokens) - len(key) + 1))
    keys = {identity(item["field"]) for item in items}
    for item in items:
        key = identity(item["field"])
        represented = []
        for requirement in requirements:
            prose = identity(requirement["text"])
            if (requirement["explicit"] and contains(prose, key) and sum(contains(prose, name) for name in keys) == 1
                    and requirement["source"]["source_id"] == item["source_id"]
                    and item["quote"] in requirement["source"]["quote"]):
                represented.append(requirement["id"])
        item.update(represented_by=represented, needs_review=not represented)
    return {"items": items, "complete": not omitted, "omitted_fields": omitted,
            "method": "optional-field syntax is an extraction hint, not proof of optional demand or compatibility"}
