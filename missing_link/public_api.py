"""Bounded literal Python API declaration hints, not runtime export verification."""
import ast
import json
from pathlib import PurePosixPath

MAX_PUBLIC_API_HINTS = 64
MAX_INITIALIZERS = 32
MAX_INITIALIZER_CHARS = 32768
MAX_PUBLIC_API_REPORT_BYTES = 8192


def public_api_report(hints):
    """Bound displayed hints in bytes without changing the full ranking input."""
    entries = hints["entrypoints"]
    report = dict(hints, entrypoints=[], omitted_entrypoint_count=len(entries), entrypoint_list_complete=not entries)
    for entry in entries:
        report["entrypoints"].append(entry)
        report["omitted_entrypoint_count"] = len(entries) - len(report["entrypoints"])
        report["entrypoint_list_complete"] = not report["omitted_entrypoint_count"]
        if len(json.dumps(report, ensure_ascii=False).encode("utf-8")) > MAX_PUBLIC_API_REPORT_BYTES:
            report["entrypoints"].pop()
            report["omitted_entrypoint_count"] += 1
            report["entrypoint_list_complete"] = False
            break
    return report


def public_api_hints(files):
    """Read acquired initializers only; no imports, execution or recursive resolver."""
    acquired = {file["path"] for file in files}
    initializers = sorted((file for file in files if PurePosixPath(file["path"]).name == "__init__.py"),
                          key=lambda file: file["path"])
    entries, complete = [], len(initializers) <= MAX_INITIALIZERS
    for file in initializers[:MAX_INITIALIZERS]:
        path, text = PurePosixPath(file["path"]), file.get("text", "")
        if (path.is_absolute() or ".." in path.parts or "\\" in str(path)
                or len(text) > MAX_INITIALIZER_CHARS or file.get("truncated") or file.get("reference_truncated")):
            complete = False
            continue
        try:
            module = ast.parse(text)
        except (SyntaxError, ValueError, RecursionError):
            complete = False
            continue
        writes = [node for node in ast.walk(module) if
                  (isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets))
                  or (isinstance(node, (ast.AnnAssign, ast.AugAssign)) and isinstance(node.target, ast.Name)
                      and node.target.id == "__all__")]
        if not writes:
            continue  # No literal declaration; do not infer a public API.
        if (len(writes) != 1 or writes[0] not in module.body or isinstance(writes[0], ast.AugAssign)
                or any(isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
                       and node.value.id == "__all__" for node in ast.walk(module))):
            complete = False
            continue
        value = writes[0].value
        if (not isinstance(value, (ast.List, ast.Tuple))
                or any(not isinstance(item, ast.Constant) or not isinstance(item.value, str)
                       or not item.value.isidentifier() for item in value.elts)):
            complete = False
            continue
        names = [item.value for item in value.elts]
        if len(names) > MAX_PUBLIC_API_HINTS:
            complete = False
        bindings = {}
        for node in module.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                bindings[node.name] = str(path) + ":" + node.name
            elif isinstance(node, ast.ImportFrom) and node.level == 1 and node.module:
                base = path.parent.joinpath(*node.module.split("."))
                target = next((str(option) for option in (base.with_suffix(".py"), base / "__init__.py")
                               if str(option) in acquired), None)
                for alias in node.names:
                    if target and alias.name != "*":
                        bindings[alias.asname or alias.name] = target + ":" + alias.name
            elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for target in targets:
                    if isinstance(target, ast.Name):
                        bindings.pop(target.id, None)  # Literal imports later rebound are not API hints.
        for name in names[:MAX_PUBLIC_API_HINTS]:
            entry = bindings.get(name)
            if entry and entry not in entries:
                if len(entries) == MAX_PUBLIC_API_HINTS:
                    complete = False
                    break
                entries.append(entry)
    return {"entrypoints": entries, "scan_complete": complete,
            "method": "literal __all__ and direct acquired relative imports; ranking hints, not verified exports"}
