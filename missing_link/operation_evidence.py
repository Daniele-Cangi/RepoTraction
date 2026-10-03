"""Bound selected operation bodies in acquired text; never execute or prove semantics.

Python uses AST ranges. JS/TS recognizes named function bodies with the existing
lexical exclusions and balanced delimiters, not a grammar/type/export resolver.
Unsupported, ambiguous and incomplete shapes remain unestablished.
"""
import ast
from bisect import bisect_right
from pathlib import PurePosixPath
import re

from .js_lexical import export_view, MAX_LEXICAL_NESTING
from .sources import MAX_FILE_BYTES

_FUNCTION = re.compile(r"[ \t]*(?:export\s+(?:default\s+)?)?(?:async\s+)?function\s+[\w$]+\s*\(")
_BODY_OPEN = re.compile(r"\s*(?::[\w$.<>\[\]|,& \t\r\n]+)?\{")


def _scan(file):
    source, path = file.get("text"), file["path"]
    if not isinstance(source, str) or len(source.encode("utf-8")) > MAX_FILE_BYTES:
        return {}
    lines = source.splitlines()
    if PurePosixPath(path).suffix.casefold() == ".py":
        try:
            tree = ast.parse(source)
        except (SyntaxError, ValueError, RecursionError):
            return {}
        regions = {}
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            body = []
            for statement in ast.walk(node):
                if (not isinstance(statement, ast.stmt) or isinstance(statement,
                    (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Pass))):
                    continue
                if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Constant):
                    continue  # Docstrings and ellipsis stubs are not implementation.
                if (isinstance(statement, ast.AnnAssign) and statement.value is None
                        or isinstance(statement, ast.Return) and isinstance(statement.value, ast.Constant)
                        and statement.value.value is Ellipsis):
                    continue
                line = statement.lineno
                prefix = lines[line - 1].encode("utf-8")[:statement.col_offset].decode("utf-8")
                fragment = lines[line - 1][len(prefix):].strip()
                if fragment:
                    body.append((line, fragment, len(prefix)))
            regions[node.lineno] = {"path": path, "line": node.lineno,
                "end_line": node.end_lineno, "body": body, "lines": lines}
        return regions
    if PurePosixPath(path).suffix.casefold() not in {".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx"} or path.casefold().endswith(".d.ts"):
        return {}
    visible, code, _, complete = export_view(source, jsx=path.casefold().endswith((".jsx", ".tsx")))
    if not complete:
        return {}
    starts = [0] + [match.end() for match in re.finditer("\n", source)]
    regions = {}
    for line, start in enumerate(starts, 1):
        header = _FUNCTION.match(visible, start)
        if not header or not all(code[index] for index in range(header.start(), header.end()) if not visible[index].isspace()):
            continue
        params_end = _closing(visible, code, header.end() - 1)
        if params_end is None:
            continue
        # A deliberately narrow return annotation; object/function types and
        # overload declarations cannot borrow a later function's opening brace.
        tail = _BODY_OPEN.match(visible, params_end + 1)
        if not tail:
            continue
        opening = tail.end() - 1
        closing = _closing(visible, code, opening)
        if closing is None:
            continue
        end_line = bisect_right(starts, closing)
        line_end = starts[end_line] if end_line < len(starts) else len(source)
        if visible[closing + 1:line_end].strip(" \t\r\n;"):
            continue  # Line-only citations cannot separate a same-line sibling.
        body = []
        first_body_line = bisect_right(starts, opening)
        for body_line in range(first_body_line, end_line + 1):
            first = max(starts[body_line - 1], opening + 1)
            last = min(starts[body_line] if body_line < len(starts) else len(source), closing)
            offsets = [offset for offset in range(first, last) if code[offset] and not visible[offset].isspace()]
            if offsets and any(visible[offset].isalnum() or visible[offset] in "_$" for offset in offsets):
                body.append((body_line, source[offsets[0]:offsets[-1] + 1].strip(), offsets[0] - starts[body_line - 1]))
        regions[line] = {"path": path, "line": line, "end_line": end_line, "body": body, "lines": lines}
    return regions


def _closing(source, code, opening):
    stack = []
    closes = {")": "(", "]": "[", "}": "{"}
    for offset in range(opening, len(source)):
        if not code[offset]:
            continue
        char = source[offset]
        if char in "([{":
            if len(stack) == MAX_LEXICAL_NESTING:
                return None
            stack.append(char)
        elif char in closes:
            if not stack or stack.pop() != closes[char]:
                return None
            if not stack:
                return offset
    return None


def operation_regions(capability, files, *, cache=None):
    """Only pinned structural definition/declaration starts grant operation scope."""
    cache = {} if cache is None else cache
    by_path = {file["path"]: file for file in files if file.get("path")}
    anchors = [capability.get("definition", {})] + [entry for entry in capability.get("evidence", [])
        if entry.get("kind") == "declaration"]
    selected = []
    for anchor in anchors:
        path, first = anchor.get("path"), anchor.get("line")
        if path not in by_path or type(first) is not int or first < 1:
            continue
        if path not in cache:
            cache[path] = _scan(by_path[path])
        region = cache[path].get(first)
        if region and region not in selected:
            selected.append(region)
    return selected


def cites_operation_body(entry, regions):
    """Containment and cited body presence only, not behavior/relevance proof."""
    first, last = entry.get("line"), entry.get("end_line")
    if type(first) is not int or type(last) is not int or not 1 <= first <= last:
        return False
    for region in regions:
        if entry.get("path") == region["path"] and region["line"] <= first <= last <= region["end_line"]:
            # splitlines omits the final line terminator, including on a valid
            # whole-file citation. Normalize only that terminator, not content.
            quote = entry.get("quote", "").replace("\r\n", "\n").removesuffix("\n")
            actual = "\n".join(region["lines"][first - 1:last])
            if not actual.startswith(quote):
                return False
            quoted_lines = quote.splitlines()
            # A truncated excerpt cannot borrow matching words from a docstring
            # or default argument earlier than the actual body statement.
            return any(first <= line <= last and line - first < len(quoted_lines)
                and column + len(fragment) <= len(quoted_lines[line - first])
                for line, fragment, column in region["body"])
    return False


def in_operation(entry, regions):
    first, last = entry.get("line"), entry.get("end_line")
    return type(first) is int and type(last) is int and any(entry.get("path") == region["path"]
        and region["line"] <= first <= last <= region["end_line"] for region in regions)
