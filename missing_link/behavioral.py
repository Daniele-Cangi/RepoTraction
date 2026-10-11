"""Opt-in discovery by executable examples, using the existing isolated runner.

This is a functional prototype, not a semantic oracle or a qualification path.
The host parses source as data. Only an explicitly supplied WASI runner executes
extracted functions. A witness describes finite observations of an extracted
slice, not the behavior of an imported package or fulfillment of a whole issue.
"""
from __future__ import annotations

import ast
import builtins
import hashlib
import json
import re
import symtable
from urllib.parse import quote

from .sources import _redact, source_role, validate_repository


_STDLIB = {"collections", "datetime", "functools", "itertools", "math", "operator", "re", "typing"}
_PREFIX = "from __future__ import annotations\n"
_RECIPES = ("identity", "mask_zero_closed", "mask_zero_halfopen",
            "mask_one_closed", "mask_one_halfopen")


def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _plan_sha256(plan):
    return _sha(json.dumps(plan, sort_keys=True, ensure_ascii=True, allow_nan=False))


def _references(code):
    table = symtable.symtable(_PREFIX + code, "<source-slice>", "exec")

    def walk(scope):
        names = {s.get_name() for s in scope.get_symbols() if s.is_referenced() and s.is_global()}
        for child in scope.get_children():
            names.update(walk(child))
        return names

    return walk(table)


def extract_callables(repository, *, limit=40):
    """Find callable slices without using names/docstrings to infer behavior.

    Top-level synchronous functions only. Resolve same-file functions, literal
    constants and selected stdlib imports. Report unresolved coupling instead of
    replacing it with stubs. Module initialization and package imports are not
    reproduced. Decorators/default expressions remain part of the slice.
    """
    name = validate_repository(repository["full_name"])
    revision = repository.get("revision", "")
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("Behavior search requires a pinned repository revision.")
    if repository.get("public") is not True:
        raise ValueError("Behavior search requires an explicitly public snapshot.")
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 40:
        raise ValueError("Callable limit must be between 1 and 40.")
    candidates, omissions = [], []
    for file in repository.get("files", []):
        path, original = file["path"], file["text"]
        if not path.endswith(".py") or source_role(path) != "implementation":
            continue
        cleaned, redacted, truncated = _redact(original)
        if redacted or truncated or cleaned != original or file.get("truncated"):
            omissions.append({"path": path, "reason": "Source was redacted/truncated; do not execute altered code."})
            continue
        try:
            module = ast.parse(original)
        except (SyntaxError, ValueError):
            omissions.append({"path": path, "reason": "Source is not parsable by the local Python AST."})
            continue
        lines = original.splitlines(keepends=True)
        bindings = {}
        for node in module.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                bound = [node.name]
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                bound = [a.asname or (a.name.split(".")[0] if isinstance(node, ast.Import) else a.name)
                         for a in node.names]
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                bound = [n.id for target in targets for n in ast.walk(target) if isinstance(n, ast.Name)]
            else:
                # Conditional module bindings make an extracted environment
                # ambiguous. Record the binding so builtin fallback cannot hide it.
                bound = [n.id for n in ast.walk(node) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)]
            for key in bound:
                bindings.setdefault(key, []).append(node)

        def segment(node):
            start = min([node.lineno] + [d.lineno for d in getattr(node, "decorator_list", [])])
            return "".join(lines[start - 1:node.end_lineno]), start

        def closure(root):
            ordered, active, done = [], set(), set()

            def add(key):
                if key in active:
                    return  # recursive function bindings exist at call time
                if key in done:
                    return
                nodes = bindings.get(key, [])
                if not nodes and key in vars(builtins):
                    return
                if len(nodes) != 1:
                    raise ValueError("Unresolved or ambiguous global: " + key)
                node = nodes[0]
                if isinstance(node, ast.FunctionDef):
                    pass
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    imports = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ""]
                    if getattr(node, "level", 0) or any(n.split(".")[0] not in _STDLIB for n in imports):
                        raise ValueError("Dependency outside the extracted stdlib slice: " + key)
                elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                    try:
                        ast.literal_eval(node.value)
                    except (ValueError, TypeError):
                        raise ValueError("Computed module state: " + key) from None
                else:
                    raise ValueError("Unsupported module binding: " + key)
                active.add(key)
                code, _ = segment(node)
                for dependency in sorted(_references(code)):
                    if dependency != key:
                        add(dependency)
                active.remove(key)
                done.add(key)
                if node not in ordered:
                    ordered.append(node)

            add(root.name)
            return ordered

        for node in module.body:
            if not isinstance(node, ast.FunctionDef):
                continue
            identity = f"{name}@{revision}:{path}:{node.name}"
            if len(candidates) >= limit:
                omissions.append({"path": path, "symbol": node.name, "reason": "Callable limit reached."})
                continue
            try:
                dependencies = closure(node)
            except (ValueError, SyntaxError) as exc:
                omissions.append({"path": path, "symbol": node.name, "reason": str(exc)})
                continue
            code, start = segment(node)
            artifacts = [_PREFIX] + [segment(dep)[0] + "\n" for dep in dependencies]
            args = node.args
            positional = len(args.posonlyargs) + len(args.args)
            candidates.append({"id": _sha(identity)[:20], "name": node.name,
                "entrypoint": path + ":" + node.name, "private_name": node.name.startswith("_"),
                "summary": (ast.get_docstring(node) or "").split("\n")[0],
                "required_args": positional - len(args.defaults), "positional_args": positional,
                "required_keywords": any(d is None for d in args.kw_defaults),
                "variadic": bool(args.vararg), "code": "".join(artifacts),
                "evidence": {"url": f"https://github.com/{name}/blob/{revision}/{quote(path, safe='/')}#L{start}-L{node.end_lineno}",
                    "path": path, "line": start, "end_line": node.end_lineno,
                    "quote": code, "file_sha256": _sha(original), "slice_sha256": _sha(code)},
                "dependencies": [{"line": segment(dep)[1], "end_line": dep.end_lineno}
                                 for dep in dependencies if dep is not node],
                "runtime": "python", "scope": "extracted_function_with_resolved_same_file_bindings"})
    return candidates, omissions


def _validate_contracts(contracts):
    if not isinstance(contracts, list) or not 1 <= len(contracts) <= 16:
        raise ValueError("Use 1–16 example contracts.")
    seen = set()
    for contract in contracts:
        identity = contract.get("id")
        if not isinstance(identity, str) or not identity or identity in seen:
            raise ValueError("Example contract IDs must be distinct nonempty strings.")
        seen.add(identity)
        if contract.get("input_kind") not in {"arguments", "boolean_mask"}:
            raise ValueError("Unsupported example input representation.")
        for phase in ("examples", "checks"):
            cases = contract.get(phase)
            if not isinstance(cases, list) or not 1 <= len(cases) <= 256:
                raise ValueError("Each contract needs 1–256 examples and separate checks.")
            for case in cases:
                if set(case) != {"args", "expected"} or not isinstance(case["args"], list):
                    raise ValueError("A case needs positional args and an expected JSON value.")
                if contract["input_kind"] == "boolean_mask" and (len(case["args"]) != 1
                        or not isinstance(case["args"][0], list)
                        or any(type(v) is not bool for v in case["args"][0])):
                    raise ValueError("Boolean masks must contain actual booleans.")
        # Incomplete target context remains explicit. Contract evidence describes
        # which suboperation was translated; it cannot certify the whole issue.
        if contract.get("kind") not in {"probe", "public_demand", "synthetic_control"}:
            raise ValueError("Declare probe, public demand, or synthetic control provenance.")
        if contract["kind"] == "public_demand":
            evidence = contract.get("evidence", {})
            if (not evidence.get("quote") or evidence["quote"] not in evidence.get("body", "")
                    or not str(evidence.get("url", "")).startswith("https://github.com/")):
                raise ValueError("Public demand contracts need a verbatim acquired quote and URL.")
        if contract.get("runtime") not in {"python", "javascript", "rust", "unknown"}:
            raise ValueError("Declare the target runtime, including unknown when unestablished.")
    wire = json.dumps(contracts, ensure_ascii=False, allow_nan=False)
    if len(wire.encode()) > 128000:
        raise ValueError("Example contracts exceed the bounded experiment size.")


def prepare_behavior_search(repository, contracts, *, limit=40):
    """Prepare inspectable WASI artifacts. No imports or execution of source."""
    _validate_contracts(contracts)
    from .wasi_runner import MAX_OUTPUT
    candidates, omissions = extract_callables(repository, limit=limit)
    files = {f"project/candidate_{i}.py": c["code"] for i, c in enumerate(candidates)}
    payload = {"candidates": [{"id": c["id"], "name": c["name"],
        "file": f"/sandbox/work/project/candidate_{i}.py", "required_args": c["required_args"],
        "positional_args": c["positional_args"], "required_keywords": c["required_keywords"],
        "variadic": c["variadic"]} for i, c in enumerate(candidates)],
        "contracts": [{k: c[k] for k in ("id", "input_kind", "examples", "checks")} for c in contracts],
        "output_limit": MAX_OUTPUT}
    # Keep the guest driver in one ordinary module, shared by tests and the
    # generated artifact. No new process runner, transport, store or scheduler.
    from . import behavior_examples
    from pathlib import Path
    driver = Path(behavior_examples.__file__).read_text(encoding="utf-8")
    files["reviewed_tests/search.py"] = driver + "\nrun(" + repr(payload) + ")\n"
    return {"version": 1, "repository": repository["full_name"], "revision": repository["revision"],
        "candidates": candidates, "omissions": omissions, "contracts": json.loads(json.dumps(contracts)),
        "files": files, "entrypoint": "reviewed_tests/search.py",
        "artifact_sha256": {path: _sha(content) for path, content in files.items()},
        "limitations": ["Top-level Python functions in supplied files; not whole-repository coverage.",
            "Examples are specifications supplied by an operator/model, not autonomously understood prose.",
            "Finite behavioral observations do not prove equivalence, performance or target integration.",
            "Module initialization is omitted; annotations are deferred; only extracted-slice behavior is observed."]}


def assess_behavior_search(plan, execution):
    """Attach observations and incompatibilities; never create qualified leads."""
    if execution.get("status") != "exited_successfully":
        return {"status": "not_evaluated", "execution_status": execution.get("status"),
                "matches": [], "qualified_leads": 0, "limitations": plan["limitations"]}
    if execution.get("context") != "isolated_wasi_example" or execution.get("artifact_sha256") != plan["artifact_sha256"]:
        raise ValueError("Observations must refer to these exact isolated artifacts.")
    try:
        observed = json.loads(execution["stdout"])
    except (KeyError, ValueError):
        raise ValueError("Guest did not return the bounded observation document.") from None
    candidates = {c["id"]: c for c in plan["candidates"]}
    contracts = {c["id"]: c for c in plan["contracts"]}
    bindings = observed.get("bindings") if isinstance(observed, dict) else None
    if not isinstance(bindings, list) or len(bindings) > len(candidates) * len(contracts) * len(_RECIPES):
        raise ValueError("Unexpected behavioral observation count.")
    fields = ("candidate_id", "contract_id", "recipe", "examples_passed", "checks_passed",
              "mutated_input", "ablation_passed", "first_failure")
    if any(not isinstance(row, list) or len(row) != len(fields) for row in bindings):
        raise ValueError("Invalid behavioral observation record.")
    rows = [dict(zip(fields, row)) for row in bindings]
    omitted = observed.get("omitted_bindings", 0)
    if type(omitted) is not int or not 0 <= omitted <= len(candidates) * len(contracts) * len(_RECIPES) - len(rows):
        raise ValueError("Invalid omitted observation count.")
    load_errors = observed.get("load_errors", [])
    if not isinstance(load_errors, list) or any(not isinstance(row, dict) or row.get("candidate_id") not in candidates for row in load_errors):
        raise ValueError("Invalid candidate load-error record.")
    expected_bindings = set()
    for cid, candidate in candidates.items():
        for pid, contract in contracts.items():
            recipes = _RECIPES if contract["input_kind"] == "boolean_mask" else ("identity",)
            for recipe in recipes:
                arity = len(contract["examples"][0]["args"]) if recipe == "identity" else 2
                if (not candidate["required_keywords"] and arity >= candidate["required_args"]
                        and (candidate["variadic"] or arity <= candidate["positional_args"])):
                    expected_bindings.add((cid, pid, recipe))
    matches, counterexamples, seen = [], [], set()
    plan_sha256 = _plan_sha256(plan)
    for row in rows:
        cid, pid, recipe = row.get("candidate_id"), row.get("contract_id"), row.get("recipe")
        key = (cid, pid, recipe)
        if key not in expected_bindings or key in seen:
            raise ValueError("Unknown or duplicate behavioral observation.")
        seen.add(key)
        candidate, contract = candidates[cid], contracts[pid]
        for phase in ("examples", "checks"):
            total = len(contract[phase])
            if type(row.get(phase + "_passed")) is not int or not 0 <= row[phase + "_passed"] <= total:
                raise ValueError("Invalid behavioral observation count.")
        if row.get("examples_passed") != len(contract["examples"]) or row.get("checks_passed") != len(contract["checks"]):
            if row.get("first_failure"):
                counterexamples.append({"candidate_id": cid, "contract_id": pid, "recipe": recipe,
                    "first_failure": row["first_failure"]})
            continue
        if row.get("mutated_input") is not False:
            continue
        if (type(row.get("ablation_passed")) is not int
                or not 0 <= row["ablation_passed"] < len(contract["examples"]) + len(contract["checks"])):
            # Adapter alone passing everything establishes no source contribution.
            continue
        runtime = contract["runtime"]
        status = "behavioral_witness" if runtime == "python" else "runtime_blocked" if runtime != "unknown" else "runtime_unknown"
        matches.append({"candidate_id": cid, "entrypoint": candidate["entrypoint"], "contract_id": pid,
            "plan_sha256": plan_sha256,
            "disposition": status, "recipe": recipe, "evidence": candidate["evidence"],
            "source_scope": candidate["scope"], "private_name": candidate["private_name"],
            "examples_passed": row["examples_passed"], "checks_passed": row["checks_passed"],
            "ablation_passed": row["ablation_passed"], "input_mutation_observed": False,
            "requested_operation": contract.get("operation", ""),
            "interpretation_origin": contract.get("interpretation_origin", "operator_supplied"),
            "uncovered_requirements": contract.get("uncovered_requirements", []),
            "reuse_mode": "extraction_requires_review",
            "qualified": False, "target_integrated": False, "complete_fit": "unestablished"})
    return {"status": "observed", "matches": matches, "counterexamples": counterexamples,
        "candidate_count": len(candidates), "contract_count": len(contracts),
        "attempted_bindings": len(rows) + omitted, "reported_bindings": len(rows),
        "omitted_bindings": omitted, "load_errors": load_errors, "qualified_leads": 0,
        "unobserved_bindings": [{"candidate_id": c, "contract_id": p, "recipe": r}
                                for c, p, r in sorted(expected_bindings - seen)],
        "omissions": plan["omissions"], "limitations": plan["limitations"],
        "observation_trust": "Guest observations from inspected source; not adversarial execution attestation."}


def prepare_behavior_bridge(plan, match):
    """Export the observed binding as an inspectable partial-reuse proposal.

    No target application files are changed. The generated check uses the same
    examples and holdout; it checks export fidelity, not fresh generalization.
    """
    if match.get("disposition") != "behavioral_witness":
        raise ValueError("Resolve the runtime before preparing an executable extraction proposal.")
    if match.get("plan_sha256") != _plan_sha256(plan):
        raise ValueError("The observed match belongs to a different or unbound search plan.")
    candidate = next(c for c in plan["candidates"] if c["id"] == match["candidate_id"])
    contract = next(c for c in plan["contracts"] if c["id"] == match["contract_id"])
    recipe = match["recipe"]
    if recipe not in _RECIPES or (recipe != "identity" and contract["input_kind"] != "boolean_mask"):
        raise ValueError("The observed representation binding is unavailable.")
    adapter = f"from extracted import {candidate['name']} as operation\n\n"
    if recipe == "identity":
        adapter += "def apply(*args):\n    return operation(*args)\n"
    else:
        origin = 1 if "_one_" in recipe else 0
        delta = 1 if recipe.endswith("halfopen") else 0
        adapter += ("def apply(mask):\n"
            "    if not isinstance(mask, list) or any(type(v) is not bool for v in mask):\n"
            "        raise TypeError('The observed adapter accepts a list of booleans.')\n"
            f"    universe = list(range({origin}, len(mask) + {origin}))\n"
            f"    selected = [i + {origin} for i, value in enumerate(mask) if value]\n"
            f"    return [[start - {origin}, end - {origin} + {delta}]\n"
            "            for start, end in operation(universe, selected)]\n")
    cases = contract["examples"] + contract["checks"]
    check = ("import copy\nimport json\nfrom reuse import apply\n"
        "from behavior_examples import _normal, _equal\n"
        f"cases = {cases!r}\n"
        "for case in cases:\n"
        "    args = copy.deepcopy(case['args'])\n"
        "    actual = _normal(apply(*args))\n"
        "    assert _equal(actual, case['expected']), (case, actual)\n"
        "    assert _equal(args, case['args']), 'input mutation'\n"
        "print(json.dumps({'passed': len(cases), 'scope': 'exported partial adapter', 'target_integrated': False}))\n")
    from . import behavior_examples
    from pathlib import Path
    evaluator = Path(behavior_examples.__file__).read_text(encoding="utf-8")
    return {"kind": "extraction", "entrypoint": "reviewed_tests/verify.py",
        "files": {"project/extracted.py": candidate["code"], "bridge/reuse.py": adapter,
                  "reviewed_tests/verify.py": check, "reviewed_tests/behavior_examples.py": evaluator},
        "evidence": candidate["evidence"], "recipe": recipe,
        "existing_contribution": contract.get("operation", "Observed transformation"),
        "new_logic": "Input/output representation conversion; target-specific features remain unimplemented.",
        "uncovered_requirements": contract.get("uncovered_requirements", []),
        "assumptions": ["Review extraction and license/notice obligations at the pinned source revision.",
                        "The slice is an internal helper; package API stability is not established.",
                        "List-based examples do not establish NumPy or target-application compatibility."],
        "qualified": False, "target_integrated": False}
