"""Bounded static JS/TS entry/re-export sampling hints, never export verification."""
import json
import re
from pathlib import PurePosixPath

MAX_EXPORT_HINTS = 64


def export_hints(path, text, eligible):
    targets = []
    complete = True
    if PurePosixPath(path).name == "package.json":
        try:
            metadata = json.loads(text)
        except (ValueError, RecursionError):
            return [], False
        if not isinstance(metadata, dict):
            return [], False
        def leaves(value, depth=0):
            nonlocal complete
            if depth > 5:
                complete = False
                return []
            if isinstance(value, str):
                return [value]
            if isinstance(value, (dict, list)):
                children = list(value.values()) if isinstance(value, dict) else value
                if len(children) > 64:
                    complete = False
                result = [leaf for child in children[:64] for leaf in leaves(child, depth + 1)]
                if len(result) > 64:
                    complete = False
                return result[:64]
            return []
        specs = []
        for key in ("source", "main", "module", "exports"):
            specs.extend(leaves(metadata.get(key)))
    elif PurePosixPath(path).suffix in {".js", ".mjs", ".cjs", ".jsx", ".ts", ".tsx"}:
        # Named clauses can span lines. Stop at either brace so an unfinished
        # clause cannot consume another declaration; this remains a static hint.
        specs = re.findall(r"(?m)^[ \t]*export\s+(?:\*(?:\s+as\s+\w+)?|\{[^{}]*\})\s+from\s*['\"]([^'\"\n]{1,240})['\"]", text)
    else:
        return [], True
    if len(specs) > MAX_EXPORT_HINTS:
        complete = False
    for spec in specs[:MAX_EXPORT_HINTS]:
        if PurePosixPath(path).name == "package.json" and not spec.startswith(("/", "./", "../")):
            spec = "./" + spec  # npm main/source paths are relative without a './' prefix too.
        if not spec.startswith(("./", "../")) or any(char in spec for char in "\\*?#\x00"):
            continue
        parts = list(PurePosixPath(path).parent.parts)
        safe = True
        for part in spec.split("/"):
            if part == "..":
                if not parts:
                    safe = False
                    break
                parts.pop()
            elif part not in {"", "."}:
                parts.append(part)
        if not safe:
            continue
        base = "/".join(parts)
        options = [base]
        if base.endswith(".js"):
            options += [base[:-3] + ".ts", base[:-3] + ".tsx"]
        elif not PurePosixPath(base).suffix:
            options += [base + ext for ext in (".ts", ".js", "/index.ts", "/index.js")]
        selected = next((candidate for candidate in options if candidate in eligible
                         and not candidate.endswith(".d.ts")), None)
        if selected and selected not in targets:
            targets.append(selected)
        if len(targets) == MAX_EXPORT_HINTS:
            complete = False
            break
    return targets, complete
