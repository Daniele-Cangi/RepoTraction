"""Bounded review hints from public discussion, not executable instructions.

These English constraint markers are deliberately conservative and non-exhaustive.
They flag text needing review, not verified requirements or maintainer approval.
"""
import re

from .demand import sentence_spans

MAX_CONSTRAINT_HINTS = 16
MAX_HINT_QUOTE = 600
DEPENDENCY_PATTERN = (
    r"\b(?:no|without|avoid|exclude)\s+(?:(?:external|additional|new|heavy|third-party)\s+)*"
    r"(?:dependenc(?:y|ies)|packages?|libraries|Python|Node(?:\.js)?|Axios|`[^`\r\n]{1,80}`|[a-z][a-z0-9]*-[a-z][a-z0-9-]*)(?!\w)|"
    r"\bzero[- ]dependenc(?:y|ies)\b|\bNode(?:\.js)?\s*(?:>=|>|=|v)\s*\d+"
)
DEPENDENCY_MARKER = re.compile(DEPENDENCY_PATTERN, re.IGNORECASE)
CONSTRAINT_MARKER = re.compile(r"\b(?:must(?:\s+not)?|shall(?:\s+not)?|(?:do|does|should|can)\s+not)\b|" + DEPENDENCY_PATTERN, re.IGNORECASE)
# Explicit artifact labels/headings remain review hints. Merely requesting a
# parser for generated plans, an [automation] label or emoji is not such a label.
GENERATED_HINT = re.compile(
    r"^[ \t]*(?:#{1,6}[ \t]+)?(?:\[(?:orchestrator|orquestrador|automation|bot)\b[^\]\r\n]{0,80}\]|"
    r"(?:🤖[ \t]*)?(?:generated (?:master )?plan|plano mestre gerado)[ \t.:#-]*$|🤖[ \t]*$)",
    re.IGNORECASE | re.MULTILINE)


def authorship(item, original_author=None, original=False):
    bot_author = bool(item.get("bot") or item.get("author_type") == "Bot")
    generated = bool(bot_author or GENERATED_HINT.search(str(item.get("body") or "")[:1000]))
    association = item.get("author_association")
    if generated:
        authority = "automation_or_generated_text_needs_review"
    elif original or (original_author and item.get("author") == original_author):
        authority = "request_author"
    elif association in {"OWNER", "MEMBER", "COLLABORATOR"}:
        authority = "repository_member"
    else:
        authority = "not_established"
    return {"author": item.get("author"), "author_type": item.get("author_type"),
            "author_association": association, "bot_author_hint": bot_author,
            "generated_hint": generated, "authority": authority}


def constraint_hints(issue):
    """Inspect full acquired text before prompt shortening; retain exact spans."""
    items = []
    found = 0
    sources = [("q0", issue)] + [(f"q{index}", comment) for index, comment in enumerate(issue.get("comments", []), 1)]
    for source_index, (source_id, source) in enumerate(sources):
        author = authorship(source, issue.get("author"), source_id == "q0")
        source_text = str(source.get("body") or "")
        if source_id == "q0":
            # Match the request evidence catalog: titles are request evidence too.
            source_text = str(source.get("title") or "") + "\n" + source_text
        for line_number, line in enumerate(source_text.splitlines(), 1):
            line_hints = 0
            for sentence in sentence_spans(line):
                marker = CONSTRAINT_MARKER.search(sentence[0])
                if not marker:
                    continue
                # Match the citation catalog's sentence boundaries. Separate
                # constraints on one line remain independently reviewable;
                # neighboring explanations cannot stand in for a constraint.
                quote = sentence[0][marker.start():].strip()
                found += 1
                line_hints += 1
                hint_id = f"constraint:{source_id}:{line_number}"
                if line_hints > 1:
                    hint_id += f":{line_hints}"
                items.append({"id": hint_id, "source_id": source_id,
                              "quote": quote[:MAX_HINT_QUOTE], "quote_truncated": len(quote) > MAX_HINT_QUOTE,
                              **author, "_rank": (not bool(DEPENDENCY_MARKER.search(quote)),
                                                  -source_index, line_number, sentence.start())})
                # Keep the bounded ledger, but continue scanning so a late
                # dependency prohibition cannot disappear behind a checklist.
                items.sort(key=lambda item: item["_rank"])
                del items[MAX_CONSTRAINT_HINTS:]
    items.sort(key=lambda item: (-item["_rank"][1], item["_rank"][2:]))
    for item in items:
        item.pop("_rank")
    return {"items": items, "complete": found <= MAX_CONSTRAINT_HINTS,
            "markers_found": found,
            "note": "Non-exhaustive English constraint markers; no marker does not prove all requirements were extracted."}
