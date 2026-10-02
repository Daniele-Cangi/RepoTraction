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


def _jsx_open(text, start):
    """Recognize a simple JSX name/fragment, not TS type argument grammar."""
    index = start + 1
    if text.startswith("<>", start):
        return index + 1, ""
    if index == len(text) or not (text[index].isalpha() or text[index] in "_$"):
        return None
    index += 1
    while index < len(text) and (text[index].isalnum() or text[index] in "_$.-:"):
        index += 1
    if index < len(text) and not (text[index].isspace() or text[index] in "/><"):
        return None  # E.g. TSX's unambiguous generic arrow prefix <T,>.
    # A following '<' may introduce JSX component type arguments. Tag mode
    # treats that unsupported syntax as incomplete, never as rendered code.
    return index, text[start + 1:index]


def _jsx_close(text, start, name):
    index = start + 2
    if not text.startswith(name, index):
        return None
    index += len(name)
    while index < len(text) and text[index].isspace():
        index += 1
    return index + 1 if index < len(text) and text[index] == ">" else None


def export_view(text, *, jsx=False):
    """Preserve offsets/module literals while hiding comments and templates.

    Code-position flags exclude declaration keywords inside quoted strings.
    Template interpolation is also hidden, including nested templates, strings,
    comments and expression braces. Unterminated/depth-limited regions do not
    expose their tail as code. No repository source is changed or executed.
    JSX mode hides entire named elements/fragments, including attributes and
    embedded expressions. Unsupported/ambiguous markup cannot certify coverage.
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

    def nest(frame, first, last):
        nonlocal complete
        if len(stack) >= MAX_LEXICAL_NESTING:
            hide(first, len(text))
            complete = False
            return False
        hide(first, last)
        stack.append(frame)
        return True

    while index < len(text):
        frame, char = stack[-1], text[index]
        if frame["mode"] in {"jsx_tag", "jsx_text"}:
            if char == "{":
                if not nest({"mode": "code", "depth": 1, "operand": True, "previous": ""}, index, index + 1):
                    break
                index += 1
            elif frame["mode"] == "jsx_tag":
                if char in "'\"":
                    # Quoted JSX attributes are raw text, not JS escape strings.
                    closing = text.find(char, index + 1)
                    if closing < 0:
                        hide(index, len(text))
                        complete = False
                        break
                    hide(index, closing + 1)
                    index = closing + 1
                elif text.startswith("/>", index):
                    hide(index, index + 2)
                    stack.pop()
                    index += 2
                elif char == ">":
                    hide(index, index + 1)
                    frame["mode"] = "jsx_text"
                    index += 1
                elif char in "<`,}":
                    hide(index, len(text))
                    complete = False
                    break
                else:
                    hide(index, index + 1)
                    index += 1
            elif text.startswith("</", index):
                end = _jsx_close(text, index, frame["name"])
                if end is None:
                    hide(index, len(text))
                    complete = False
                    break
                hide(index, end)
                stack.pop()
                index = end
            elif char == "<":
                opening = _jsx_open(text, index)
                if opening is None:
                    hide(index, len(text))
                    complete = False
                    break
                end, name = opening
                if not nest({"mode": "jsx_text" if not name else "jsx_tag", "name": name}, index, end):
                    break
                index = end
            else:
                hide(index, index + 1)
                index += 1
            continue
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
        if jsx and char == "<" and (frame["operand"] or frame["previous"] == "}"):
            opening = _jsx_open(text, index)
            if opening is not None:
                end, name = opening
                # A block-ending statement and an object comparison need grammar
                # to distinguish. Hide balanced JSX, but expose the ambiguity.
                complete &= frame["operand"]
                frame.update(operand=False, previous="literal")
                if not nest({"mode": "jsx_text" if not name else "jsx_tag", "name": name}, index, end):
                    break
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


def top_level_code(text, code):
    """Bound delimiter scopes using the lexical mask, not JS/TS grammar.

    Only code delimiters affect nesting; strings, comments, templates and regexp
    candidates stay excluded. Malformed/depth-limited scopes hide their tail and
    cannot certify a complete hint scan. This pass is linear in the supplied text.
    """
    visible = bytearray(len(text))
    stack = []
    closing = {")": "(", "]": "[", "}": "{"}
    for offset, char in enumerate(text):
        if not code[offset]:
            continue
        if not stack:
            visible[offset] = 1
        if char in "([{":
            if len(stack) == MAX_LEXICAL_NESTING:
                return visible, False
            stack.append(char)
        elif char in closing:
            if not stack or stack[-1] != closing[char]:
                return visible, False
            stack.pop()
    return visible, not stack
