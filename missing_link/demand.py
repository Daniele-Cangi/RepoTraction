"""Deterministic demand citations. Selecting a span is not interpreting it."""
import copy
import hashlib
import json
import re

from .contracts import MAX_SCOPED_IDS


def sentence_spans(line):
    """Conservative original sentence spans shared by citations and review hints."""
    # These abbreviation dots do not end a clause even before a capitalized
    # example. Keep original match offsets; this is not a semantic sentence parser.
    return re.finditer(r".+?(?:(?:(?<!\b[eE]\.[gG])(?<!\b[iI]\.[eE])\.|[!?])(?=\s+[A-Z]|$)|$)", line)


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
        pieces = [visible] if visible == original else re.split(
            r"\n\[(?:OMITTED MIDDLE|SELECTED CONSTRAINT EXCERPT)\]\n", visible)
        # Selected middle constraints precede long tail filler. Each piece must
        # itself be one original span; never join across a synthetic seam.
        pieces = pieces[:1] + pieces[2:] + pieces[1:2]
        for piece in pieces:
            base = original.find(piece)
            if base < 0:
                omitted += 1
                continue
            # Split sentences/lines from actually supplied pieces: a truncated
            # middle hint can be selected even if the original line is enormous.
            for match in re.finditer(r"[^\n]+", piece):
                for sentence in sentence_spans(match[0]):
                    start, end = match.start() + sentence.start(), match.start() + sentence.end()
                    for first in range(start, end, 1600):
                        quote = piece[first:min(end, first + 1600)].strip()
                        if not quote:
                            continue
                        offset = base + piece.find(quote, first, min(end, first + 1600))
                        key = "s" + hashlib.sha256(f"{source.get('url')}:{ref}:{offset}:{offset + len(quote)}:{quote}".encode()).hexdigest()[:16]
                        spans[key] = {"source_id": ref, "quote": quote}
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
    Identical lines by the same trusted author share one item with all retained
    source IDs; changed text and authority-uncertain sources remain independent.
    """
    items, groups, omitted, references = [], {}, 0, 0
    for ref, source in catalog.items():
        if not re.fullmatch(r"q\d+", ref):
            continue
        for line in source["quote"].splitlines():
            names = re.findall(r"\b([A-Za-z_]\w{0,79})\?\s*:", line)
            for name in dict.fromkeys(names):
                if len(line) > 1600:
                    omitted += 1
                    continue
                quote, authority = line.strip(), source.get("authority", "not_established")
                author = source.get("author")
                # Only identical declarations by the same identified, trusted
                # author share review across sources. Uncertain authorship stays
                # source-scoped; changed wording/types remain independent items.
                owner = ("author", author) if isinstance(author, str) and author and authority in {
                    "request_author", "repository_member"} else ("source", ref)
                key = (name, quote, authority, owner)
                item = groups.get(key)
                if item is not None and ref in item["source_ids"]:
                    continue
                # Preserve the original 30-occurrence provenance budget even
                # when several source references share one field-level item.
                if references == 30:
                    omitted += 1
                    continue
                references += 1
                if item is None:
                    item = {"field": name, "source_id": ref, "source_ids": [], "quote": quote,
                            "authority": authority}
                    groups[key] = item
                    items.append(item)
                item["source_ids"].append(ref)
    def identity(value):
        value = re.sub(r"([a-z])([A-Z])", r"\1 \2", value)
        return tuple(re.findall(r"[a-z0-9]+", value.casefold()))
    keys = sorted(filter(None, {identity(item["field"]) for item in items}),
                  key=lambda name: (-len(name), name))
    def mentions(value):
        # Consume the longest identifier at each position: colorMode is one
        # field, not also mode. A separate "and mode" still names a second
        # field and keeps a bundled requirement from clearing either hint.
        tokens, found, index = identity(value), set(), 0
        while index < len(tokens):
            name = next((key for key in keys if tokens[index:index + len(key)] == key), None)
            if name is None:
                index += 1
            else:
                found.add(name)
                index += len(name)
        return found
    interpreted = [(requirement, mentions(requirement["text"])) for requirement in requirements]
    for item in items:
        key = identity(item["field"])
        represented = []
        for requirement, named_fields in interpreted:
            quote = requirement["source"]["quote"]
            # A sentence can be shorter than its original line; legacy manual
            # citations can include surrounding lines. Both must actually cite
            # this declaration, not merely neighboring prose on the same line.
            cites_field = re.search(r"\b" + re.escape(item["field"]) + r"\?\s*:", quote)
            if (requirement["explicit"] and named_fields == {key}
                    and requirement["source"]["source_id"] in item["source_ids"]
                    and cites_field and (quote in item["quote"] or item["quote"] in quote)):
                represented.append(requirement["id"])
        item.update(represented_by=represented, needs_review=not represented or
                    item["authority"] not in {"request_author", "repository_member"})
    return {"items": items, "complete": not omitted, "omitted_fields": omitted,
            "method": "optional-field syntax is an extraction hint, not proof of optional demand or compatibility"}
