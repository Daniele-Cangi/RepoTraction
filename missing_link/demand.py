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
