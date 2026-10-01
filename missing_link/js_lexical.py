"""Lexical exclusions for bounded export hints, not a JS/TS syntax validator."""

MAX_LEXICAL_NESTING = 64
_EXPRESSION_PREFIXES = {"return", "throw", "case", "delete", "void", "typeof", "new", "yield", "await", "in", "instanceof"}


def _quoted_end(text, start):
    delimiter, index = text[start], start + 1
    while index < len(text):
        if text[index] == "\\":
            index += 2  # Includes escaped quotes and line continuations.
        elif text[index] == delimiter:
            return index + 1, True
        else:
            index += 1
    return len(text), False


def _regexp_end(text, start, work):
    """A same-line regexp candidate; slash/statement ambiguity stays explicit."""
    index, character_class = start + 1, False
    while index < len(text) and text[index] not in "\r\n":
        work[0] -= 1
        if work[0] < 0:
            return 0  # Shared lookahead bound, not an unclosed-expression guess.
        char = text[index]
        if char == "\\":
            if index + 1 == len(text) or text[index + 1] in "\r\n":
                return None
            index += 2
        elif char == "[":
            character_class = True
            index += 1
        elif char == "]":
            character_class = False
            index += 1
        elif char == "/" and not character_class:
            index += 1
            while index < len(text) and text[index].isalpha():
                index += 1
            return index
        else:
            index += 1
    return None


def export_view(text):
    """Preserve offsets/module literals while hiding comments and templates.

    Code-position flags exclude declaration keywords inside quoted strings.
    Template interpolation is also hidden, including nested templates, strings,
    comments and expression braces. Unterminated/depth-limited regions do not
    expose their tail as code. No repository source is changed or executed.
    """
    visible = list(text)
    code = bytearray(len(text))
    literals = {}
    regexp_work = [len(text) * 4]  # Prevent repeated failed slash probes from quadratic scans.
    stack = [{"mode": "code", "depth": None, "operand": True, "previous": ""}]
    index, complete = 0, True

    def hide(first, last):
        for offset in range(first, last):
            if text[offset] not in "\r\n":
                visible[offset] = " "

    def mark(first, last):
        if len(stack) == 1:
            code[first:last] = b"\1" * (last - first)
        else:
            hide(first, last)

    while index < len(text):
        frame, char = stack[-1], text[index]
        if frame["mode"] == "template":
            end = min(len(text), index + (2 if char == "\\" else 1))
            if char == "`":
                stack.pop()
            elif text.startswith("${", index):
                end = index + 2
                if len(stack) >= MAX_LEXICAL_NESTING:
                    hide(index, len(text))
                    complete = False
                    break
                stack.append({"mode": "code", "depth": 1, "operand": True, "previous": ""})
            hide(index, end)
            index = end
            continue
        if text.startswith("//", index):
            end = index + 2
            while end < len(text) and text[end] not in "\r\n":
                end += 1
            hide(index, end)
            index = end
            continue
        if text.startswith("/*", index):
            closing = text.find("*/", index + 2)
            end = len(text) if closing < 0 else closing + 2
            hide(index, end)
            complete &= closing >= 0
            index = end
            continue
        if char in "'\"":
            end, closed = _quoted_end(text, index)
            complete &= closed
            if len(stack) == 1 and closed:
                literals[index] = end
            elif len(stack) > 1:
                hide(index, end)
            frame.update(operand=False, previous="literal")
            index = end
            continue
        if char == "`":
            hide(index, index + 1)
            frame.update(operand=False, previous="literal")
            if len(stack) >= MAX_LEXICAL_NESTING:
                hide(index, len(text))
                complete = False
                break
            stack.append({"mode": "template"})
            index += 1
            continue
        if char == "/":
            end = _regexp_end(text, index, regexp_work) if frame["operand"] or frame["previous"] in {")", "}"} else None
            if end == 0:
                hide(index, len(text))
                complete = False
                break
            if end is not None:
                # After a closing group/block, distinguishing a regexp from
                # division needs a full parser. Hide the same-line candidate,
                # but never certify that ambiguous lexical scan as complete.
                complete &= frame["operand"]
                hide(index, end)
                frame.update(operand=False, previous="literal")
                index = end
                continue
            if frame["operand"]:
                hide(index, len(text))
                complete = False
                break
        if char.isalnum() or char in "_$":
            end = index + 1
            while end < len(text) and (text[end].isalnum() or text[end] in "_$"):
                end += 1
            word = text[index:end]
            mark(index, end)
            frame.update(operand=word in _EXPRESSION_PREFIXES, previous=word)
            index = end
            continue
        mark(index, index + 1)
        if not char.isspace():
            if frame["depth"] is not None:
                if char == "{":
                    frame["depth"] += 1
                elif char == "}":
                    frame["depth"] -= 1
                    if not frame["depth"]:
                        stack.pop()
            if text[index:index + 2] in {"++", "--"}:
                mark(index + 1, index + 2)
                index += 2
                continue  # Preserve operand state for prefix/postfix forms.
            frame.update(operand=char in "=([{,:;!?&|+-*%^~<>/", previous=char)
        index += 1
    return "".join(visible), code, literals, bool(complete and len(stack) == 1)
