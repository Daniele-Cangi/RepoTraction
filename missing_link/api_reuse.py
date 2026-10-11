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


def _binding_events(body):
    """Conservative scope-local writes, including conditional rebinding."""
    class Writes(ast.NodeVisitor):
        def __init__(self):
            self.names = set()

        def visit_Name(self, node):
            if isinstance(node.ctx, (ast.Store, ast.Del)):
                self.names.add(node.id)

        def visit_Attribute(self, node):
            if isinstance(node.ctx, (ast.Store, ast.Del)):
                self.names.add(_dotted(node))

        def visit_FunctionDef(self, node):
            self.names.add(node.name)  # Do not descend into another scope.

        visit_AsyncFunctionDef = visit_FunctionDef
        visit_ClassDef = visit_FunctionDef

        def visit_Import(self, node):
            self.names.update(a.asname or a.name.split('.')[0] for a in node.names)

        def visit_ImportFrom(self, node):
            self.names.update(a.asname or a.name for a in node.names)

        def visit_ExceptHandler(self, node):
            if node.name:
                self.names.add(node.name)
            self.generic_visit(node)

        def visit_MatchAs(self, node):
            if node.name:
                self.names.add(node.name)
            self.generic_visit(node)

    result = {}
    for node in body:
        writes = Writes()
        writes.visit(node)
        for name in sorted(writes.names):
            result.setdefault(name, []).append(node)
    return result


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
        artifact = safe_relative_path("project/" + package + "/" + relative)
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
    # A fresh bridge needs four additional artifacts, not just a search driver.
    # Each of the four export artifacts is independently capped by the runner.
    if (len(package_files) > 60 or sum(len(v.encode()) for v in package_files.values())
            > MAX_TOTAL_ARTIFACT_BYTES - 4 * MAX_ARTIFACT_BYTES):
        raise ValueError("Package exceeds existing WASI artifact bounds.")

    aliases, declarations, module_bindings = {}, {}, {}
    for module, (file, tree, initializer) in modules.items():
        events = _binding_events(tree.body)
        module_bindings[module] = events
        definitions = {}
        for symbol, nodes in events.items():
            direct = [n for n in nodes if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name == symbol]
            if direct and len(direct) == len(nodes):
                definitions[symbol] = direct[-1]
            elif direct:
                omissions.append({"path": file["path"], "symbol": symbol, "reason": "Rebound module name; runtime source attribution is ambiguous."})
        declarations[module] = definitions
        names = {}
        for node in tree.body:
            if isinstance(node, ast.ImportFrom):
                parent = module.split(".") if initializer else module.split(".")[:-1]
                prefix = (parent[:len(parent) - node.level + 1] if node.level else [])
                target = ".".join(prefix + (node.module or "").split(".")).strip(".")
                for item in node.names:
                    alias = item.asname or item.name
                    if events.get(alias) == [node] and not any(k.startswith(alias + '.') for k in events):
                        names[alias] = target + "." + item.name
            elif isinstance(node, ast.Import):
                for item in node.names:
                    alias = item.asname or item.name.split(".")[0]
                    if events.get(alias) == [node] and not any(k.startswith(alias + '.') for k in events):
                        names[alias] = item.name if item.asname else item.name.split(".")[0]
            elif isinstance(node, ast.ClassDef) and definitions.get(node.name) is node:
                identity = module + "." + node.name
                names[node.name] = identity
                classes[identity] = (module, file, node)
        aliases[module] = names

    def members(identity, active=()):
        if identity in active:
            raise ValueError("Cyclic ancestry or re-export; omitted.")
        if identity not in classes:
            module, _, symbol = identity.rpartition('.')
            target = aliases.get(module, {}).get(symbol)
            if target and target != identity:
                return members(target, (*active, identity))
            # These standard bases provide object initialization, not an unseen
            # package constructor. Other unresolved ancestors are not guessed.
            if identity in {"builtins.object", "typing.Generic", "abc.ABC"}:
                return {}
            raise ValueError("Unresolved ancestor; construction provenance is unknown.")
        module, file, cls = classes[identity]
        if cls.decorator_list:
            raise ValueError("Decorated classes may replace construction; omitted.")
        if cls.keywords:
            raise ValueError("Custom metaclass or class keywords may replace construction; omitted.")
        if len(cls.bases) > 1:
            raise ValueError("Multiple inheritance requires runtime MRO attribution; omitted.")
        result = {}
        for base in cls.bases:
            dotted = _dotted(base).split(".")
            # A missing alias may have been rebound: do not silently fall back
            # to an earlier class declaration with the same name.
            target = ".".join([aliases[module].get(dotted[0], ""), *dotted[1:]])
            if dotted == ["object"] and "object" not in module_bindings[module]:
                target = "builtins.object"
            result.update(members(target, (*active, identity)))
        events = _binding_events(cls.body)
        rebound = {name for name, nodes in events.items()
                   if any(not isinstance(n, ast.FunctionDef) or n.name != name for n in nodes)}
        if "__init__" in rebound:
            raise ValueError("Rebound constructor; runtime source attribution is ambiguous.")
        for name in rebound:
            result.pop(name, None)
        for node in cls.body:
            if isinstance(node, ast.FunctionDef) and node.name not in rebound:
                decorators = {_dotted(d) for d in node.decorator_list}
                if any(d.endswith((".setter", ".deleter")) for d in decorators):
                    continue
                # The implementation following overload declarations wins.
                result[node.name] = (file, node, decorators)
        return result

    candidates = []

    def add(module, label, locations, arity, binding):
        primary_file, primary_node = locations[-1]
        def evidence(file, node):
            lines = file["text"].splitlines(keepends=True)
            start = min([node.lineno] + [d.lineno for d in getattr(node, "decorator_list", [])])
            code = "".join(lines[start - 1:node.end_lineno])
            return {"path": file["path"], "line": start, "end_line": node.end_lineno,
                "url": f"https://github.com/{name}/blob/{revision}/{quote(file['path'], safe='/')}#L{start}-L{node.end_lineno}",
                "quote": code, "file_sha256": _sha(file["text"]), "slice_sha256": _sha(code)}
        def checked(expression, location):
            file, node = location
            path = '/sandbox/work/project/' + package + '/' + file['path'][len(root) + 1:]
            line = min([node.lineno] + [d.lineno for d in node.decorator_list])
            return f"_checked({expression}, {path!r}, {line})"

        setup = ""
        if binding["kind"] == "function":
            expression = checked("module." + binding["function"], locations[-1]) + "(*args)"
        else:
            split, member = binding["constructor_inputs"], binding["member"]
            setup = (f"    cls = module.{binding['class']}\n"
                     "    if type(cls).__call__ is not type.__call__:\n"
                     "        raise ValueError('Custom metaclass construction is outside this grammar')\n")
            create = "cls"
            if binding["factory"]:
                setup += (f"    factory = cls.{binding['factory']}\n"
                          "    if getattr(factory, '__self__', None) is not cls:\n"
                          "        raise ValueError('Factory is bound to a different class')\n")
                create = checked("factory", locations[0])
            elif isinstance(locations[0][1], ast.FunctionDef):
                setup += "    " + checked("cls.__init__", locations[0]) + "\n"
            else:
                setup += ("    if cls.__init__ is not object.__init__:\n"
                          "        raise ValueError('Unindexed runtime initializer')\n")
            setup += (f"    instance = {create}(*args[:{split}])\n"
                      "    if type(instance) is not cls:\n"
                      "        raise ValueError('Factory returned a different runtime class')\n")
            if binding["kind"] == "factory_property":
                setup += (f"    descriptor = next(base.__dict__[{member!r}] for base in cls.__mro__ if {member!r} in base.__dict__)\n"
                          "    if type(descriptor) is not property or cls.__getattribute__ is not object.__getattribute__:\n"
                          "        raise ValueError('Property dispatch differs from the indexed declaration')\n")
                expression = checked("descriptor.fget", locations[-1]) + "(instance)"
            else:
                setup += (f"    method = getattr(instance, {member!r})\n"
                          "    if getattr(method, '__self__', None) is not instance:\n"
                          "        raise ValueError('Method is bound to a different instance')\n")
                expression = checked("method", locations[-1]) + f"(*args[{split}:])"
        code = ("from importlib import import_module\n"
                "from types import FunctionType, MethodType\n"
                "def _checked(function, path, line):\n"
                "    if type(function) not in (FunctionType, MethodType):\n"
                "        raise ValueError('Callable is not an indexed Python function or method')\n"
                "    code = (function.__func__ if type(function) is MethodType else function).__code__\n"
                "    if code.co_filename.replace('\\\\', '/') != path or code.co_firstlineno != line:\n"
                "        raise ValueError('Runtime callable differs from the indexed declaration')\n"
                "    return function\n"
                "def _reuse(*args):\n"
                f"    module = import_module({module!r})\n"
                f"    if not module.__file__.replace('\\\\', '/').startswith('/sandbox/work/project/{package}/'):\n"
                "        raise ValueError('Callable module is not the supplied package')\n"
                + setup +
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
        for node in declarations[module].values():
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                for arity in sorted(arities):
                    if _accepts(_arity(node), arity):
                        add(module, node.name, [(file, node)], arity,
                            {"kind": "function", "function": node.name})
            if not isinstance(node, ast.ClassDef) or node.name.startswith("_"):
                continue
            try:
                available = members(module + "." + node.name)
            except ValueError as exc:
                omissions.append({"path": file["path"], "symbol": node.name, "reason": str(exc)})
                continue
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
                            locations = ([(constructor_file, constructor)] if constructor else [(file, node)]) + [(origin, method)]
                            binding = {"kind": "factory_property" if prop else "factory_method", "class": node.name,
                                "factory": factory, "member": key, "constructor_inputs": split}
                            add(module, f"{node.name}.{factory or '__init__'}[{split}].{key}", locations, arity, binding)
    # Stable order, no names/docstrings/expected outputs used as relevance scores.
    candidates.sort(key=lambda c: (c["entrypoint"], c["required_args"]))
    bound = min(limit, 63 - len(package_files))
    for candidate in candidates[bound:]:
        omissions.append({"entrypoint": candidate["entrypoint"], "reason": "Existing callable/artifact count limit reached."})
    return candidates[:bound], omissions, package_files
