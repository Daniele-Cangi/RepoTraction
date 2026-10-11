"""Behavior queries over pinned Python packages, without importing them on host.

Enumerate direct calls and one constructor/factory -> method/property composition.
Names and documentation locate code; they do not score compatibility. The existing
example evaluator and WASI runner decide which finite observations survive.
"""
from __future__ import annotations

import ast
import hashlib
import re
import sys
from pathlib import PurePosixPath
from urllib.parse import quote

from .proofs import safe_relative_path
from .sources import validate_repository
from .store import redact_payload
from .wasi_runner import MAX_ARTIFACT_BYTES, MAX_TOTAL_ARTIFACT_BYTES


def _sha(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _arity(node, implicit=0):
    if node is None:
        return 0, 0
    args = node.args
    if any(default is None for default in args.kw_defaults):
        return None  # This grammar supplies positional arguments only.
    total = len(args.posonlyargs) + len(args.args) - implicit
    return max(0, total - len(args.defaults)), (4 if args.vararg else total)


def _accepts(bounds, count):
    return bounds is not None and bounds[0] <= count <= bounds[1]


def _dotted(node):
    if isinstance(node, ast.Subscript):
        return _dotted(node.value)
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return _dotted(node.value) + "." + node.attr
    return ""


def package_candidates(repository, package_root, arities, *, limit=40):
    """Return API wrappers, omissions and complete supplied package artifacts.

    A caller supplies a reviewed snapshot, not an installed package name. Missing
    modules/native dependencies remain import failures in WASI. No download,
    pip install, filesystem traversal, model call or execution happens here.
    """
    name = validate_repository(repository["full_name"])
    revision = repository.get("revision", "")
    if repository.get("public") is not True or not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("API search needs an explicitly public pinned snapshot.")
    if type(limit) is not int or not 1 <= limit <= 40:
        raise ValueError("Callable limit must be between 1 and 40.")
    root = safe_relative_path(package_root)
    package = PurePosixPath(root).name
    if (not package.isidentifier() or package.startswith("_")
            or package in sys.stdlib_module_names
            or package in {"behavior_examples", "extracted", "reuse"}):
        raise ValueError("Use a distinct Python package name, not a runtime module.")
    if (not arities or any(type(n) is not int or not 0 <= n <= 4 for n in arities)):
        raise ValueError("API search supports zero to four positional inputs.")
    package_files, modules, classes, omissions = {}, {}, {}, []
    portable = set()
    for file in repository.get("files", []):
        path = safe_relative_path(file["path"])
        if not path.startswith(root + "/") or not path.endswith(".py"):
            continue
        relative = path[len(root) + 1:]
        parts = PurePosixPath(relative).with_suffix("").parts
        if any(not part.isidentifier() for part in parts):
            raise ValueError("Package modules must have literal Python identifiers.")
        content = file.get("text")
        if (not isinstance(content, str) or file.get("truncated") or file.get("reference_truncated")
                or file.get("mode") == "120000" or "\x00" in content
                or len(content.encode("utf-8")) > MAX_ARTIFACT_BYTES
                or redact_payload(content) != content):
            raise ValueError("Do not import altered, unsafe or oversized package source.")
        artifact = "project/" + package + "/" + relative
        if artifact.casefold() in portable:
            raise ValueError("Duplicate package module path.")
        portable.add(artifact.casefold())
        package_files[artifact] = content
        module = ".".join((package, *parts[:-1])) if parts[-1] == "__init__" else ".".join((package, *parts))
        if module in modules:
            raise ValueError("Ambiguous module and package with the same import name.")
        try:
            tree = ast.parse(content)
        except (SyntaxError, ValueError, RecursionError):
            raise ValueError("Supplied package source cannot be indexed by this Python AST.") from None
        modules[module] = (file, tree, parts[-1] == "__init__")
    if "project/" + package + "/__init__.py" not in package_files:
        raise ValueError("Supply the package initializer and its dependencies.")
    if len(package_files) > 62 or sum(len(v.encode()) for v in package_files.values()) > MAX_TOTAL_ARTIFACT_BYTES:
        raise ValueError("Package exceeds existing WASI artifact bounds.")

    aliases = {}
    for module, (file, tree, initializer) in modules.items():
        names = {}
        for node in tree.body:
            if isinstance(node, ast.ImportFrom):
                parent = module.split(".") if initializer else module.split(".")[:-1]
                prefix = (parent[:len(parent) - node.level + 1] if node.level else [])
                target = ".".join(prefix + (node.module or "").split(".")).strip(".")
                for item in node.names:
                    names[item.asname or item.name] = target + "." + item.name
            elif isinstance(node, ast.Import):
                for item in node.names:
                    names[item.asname or item.name.split(".")[0]] = item.name if item.asname else item.name.split(".")[0]
            elif isinstance(node, ast.ClassDef):
                identity = module + "." + node.name
                names[node.name] = identity
                classes[identity] = (module, file, node)
        aliases[module] = names

    def members(identity, active=()):
        if identity not in classes or identity in active:
            return {}
        module, file, cls = classes[identity]
        result = {}
        for base in reversed(cls.bases):
            dotted = _dotted(base).split(".")
            target = ".".join([aliases[module].get(dotted[0], module + "." + dotted[0]), *dotted[1:]])
            result.update(members(target, (*active, identity)))
        for node in cls.body:
            if isinstance(node, ast.FunctionDef):
                decorators = {_dotted(d) for d in node.decorator_list}
                if any(d.endswith((".setter", ".deleter")) for d in decorators):
                    continue
                # The implementation following overload declarations wins.
                result[node.name] = (file, node, decorators)
        return result

    candidates = []

    def add(module, label, expression, locations, arity, binding):
        primary_file, primary_node = locations[-1]
        def evidence(file, node):
            lines = file["text"].splitlines(keepends=True)
            start = min([node.lineno] + [d.lineno for d in getattr(node, "decorator_list", [])])
            code = "".join(lines[start - 1:node.end_lineno])
            return {"path": file["path"], "line": start, "end_line": node.end_lineno,
                "url": f"https://github.com/{name}/blob/{revision}/{quote(file['path'], safe='/')}#L{start}-L{node.end_lineno}",
                "quote": code, "file_sha256": _sha(file["text"]), "slice_sha256": _sha(code)}
        code = ("from importlib import import_module\n"
                "def _reuse(*args):\n"
                f"    module = import_module({module!r})\n"
                f"    if not module.__file__.replace('\\\\', '/').startswith('/sandbox/work/project/{package}/'):\n"
                "        raise ValueError('Callable module is not the supplied package')\n"
                f"    return {expression}\n")
        entry = module + ":" + label
        candidates.append({"id": _sha(name + revision + entry + str(arity))[:20],
            "name": "_reuse", "entrypoint": entry, "private_name": False, "summary": "",
            "required_args": arity, "positional_args": arity, "required_keywords": False,
            "variadic": False, "code": code, "evidence": evidence(primary_file, primary_node),
            "dependencies": [evidence(f, n) for f, n in locations[:-1]],
            "runtime": "python", "scope": "imported_pinned_package_api",
            "api_binding": binding, "package": package})

    for module, (file, tree, _) in sorted(modules.items()):
        if any(part.startswith("_") for part in module.split(".")[1:]):
            continue  # Imported dependencies stay in the bundle, not in the API catalog.
        # Overload declarations do not create additional runtime functions.
        definitions = {node.name: node for node in tree.body
                       if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
        for node in definitions.values():
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                for arity in sorted(arities):
                    if _accepts(_arity(node), arity):
                        add(module, node.name, f"module.{node.name}(*args)", [(file, node)], arity,
                            {"kind": "function", "function": node.name})
            if not isinstance(node, ast.ClassDef) or node.name.startswith("_"):
                continue
            available = members(module + "." + node.name)
            init = available.get("__init__")
            factories = [(None, init[1] if init else None, init[0] if init else file)]
            factories += [(key, method, origin) for key, (origin, method, decorators) in available.items()
                          if not key.startswith("_") and "classmethod" in decorators]
            for factory, constructor, constructor_file in factories:
                for key, (origin, method, decorators) in available.items():
                    if key.startswith("_") or decorators & {"classmethod", "staticmethod"}:
                        continue
                    prop = "property" in decorators
                    for arity in sorted(arities):
                        for split in range(arity + 1):
                            if not _accepts(_arity(constructor, 1 if constructor else 0), split):
                                continue
                            if not _accepts((0, 0) if prop else _arity(method, 1), arity - split):
                                continue
                            create = f"module.{node.name}" + ("." + factory if factory else "")
                            expression = f"{create}(*args[:{split}]).{key}" + ("" if prop else f"(*args[{split}:])")
                            locations = ([(constructor_file, constructor)] if constructor else [(file, node)]) + [(origin, method)]
                            binding = {"kind": "factory_property" if prop else "factory_method", "class": node.name,
                                "factory": factory, "member": key, "constructor_inputs": split}
                            add(module, f"{node.name}.{factory or '__init__'}[{split}].{key}", expression, locations, arity, binding)
    # Stable order, no names/docstrings/expected outputs used as relevance scores.
    candidates.sort(key=lambda c: (c["entrypoint"], c["required_args"]))
    bound = min(limit, 63 - len(package_files))
    for candidate in candidates[bound:]:
        omissions.append({"entrypoint": candidate["entrypoint"], "reason": "Existing callable/artifact count limit reached."})
    return candidates[:bound], omissions, package_files
