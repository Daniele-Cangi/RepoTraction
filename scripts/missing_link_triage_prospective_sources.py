"""Offline pinned-source cohort construction, not Discover or a semantic scorer.

Explicit source records are data; never import or execute acquired Python.
Only whitelisted source fields enter model context. Reviewer judgments stay out.
"""
import ast
import hashlib
import re
from pathlib import PurePosixPath

from scripts.missing_link_triage_prompt import build_context
from scripts.missing_link_triage_contract import MAX_BODY_BYTES

SOURCE_FIELDS = {"repository", "revision", "path", "text", "blob_sha", "sha256"}
MAX_FILE_BYTES = 500_000
OPERATION_SPAN_CHARACTERS = 1200
LIMITATIONS = ["Upstream documented API contract, not an external unresolved issue",
    "Selected entrypoint text only; unseen delegates, execution and adoption remain unestablished"]


def validate_source(record):
    """Check a complete explicit UTF-8 file and Git blob identity without IO."""
    if not isinstance(record, dict) or not SOURCE_FIELDS <= record.keys():
        raise ValueError("Incomplete pinned source record")
    source = {name: record[name] for name in SOURCE_FIELDS}
    if any(not isinstance(value, str) or not value for value in source.values()):
        raise ValueError("Invalid pinned source field")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", source["repository"]):
        raise ValueError("Invalid source repository")
    if not re.fullmatch(r"[0-9a-f]{40}", source["revision"]):
        raise ValueError("Source must use a full pinned commit")
    path = source["path"]
    if ("\\" in path or PurePosixPath(path).is_absolute()
            or any(part in {"", ".", ".."} for part in path.split("/"))):
        raise ValueError("Invalid repository-relative source path")
    body = source["text"].encode("utf-8")
    if len(body) > MAX_FILE_BYTES:
        raise ValueError("Pinned source exceeds file bound")
    blob = hashlib.sha1(b"blob " + str(len(body)).encode() + b"\0" + body).hexdigest()
    if source["blob_sha"] != blob or source["sha256"] != hashlib.sha256(body).hexdigest():
        raise ValueError("Pinned source hash changed")
    return source


def function_source(record, name):
    """Select a unique top-level function with its complete decorators/body."""
    source = validate_source(record)
    tree = ast.parse(source["text"])
    nodes = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name]
    if len(nodes) != 1:
        raise ValueError("Selected function is missing or ambiguous")
    node = nodes[0]
    first = min([node.lineno] + [item.lineno for item in node.decorator_list])
    lines = source["text"].splitlines(keepends=True)
    # AST columns are UTF-8 byte offsets, not Python character offsets.
    last = lines[node.end_lineno - 1].encode("utf-8")[:node.end_col_offset].decode("utf-8")
    quote = "".join(lines[first - 1:node.end_lineno - 1]) + last
    return source, node, {"path": source["path"], "line": first, "end_line": node.end_lineno, "quote": quote}


def documented_case(number, operation_record, operation_name, *, demand_record, demand_function=None):
    """Keep full original doc literal/file, selected body and exact spans only.

This explicitly selected API-contract comparison is not autonomous discovery.
No expected relations, reviewer notes or prior predictions are forwarded.
"""
    if not isinstance(number, int) or isinstance(number, bool) or not 1 <= number <= 6:
        raise ValueError("Invalid prospective case number")
    source, _, evidence = function_source(operation_record, operation_name)
    demand = validate_source(demand_record)
    if demand["repository"] != source["repository"] or demand["revision"] != source["revision"]:
        raise ValueError("Contract and operation need the same pinned repository revision")
    demand_text = demand["text"]
    if demand_function is not None:
        _, node, _ = function_source(demand, demand_function)
        if (not node.body or not isinstance(node.body[0], ast.Expr)
                or not isinstance(node.body[0].value, ast.Constant)
                or not isinstance(node.body[0].value.value, str) or not node.body[0].value.value.strip()):
            raise ValueError("Selected contract has no nonempty docstring")
        # Preserve the exact original literal, including delimiters/indentation.
        demand_text = ast.get_source_segment(demand["text"], node.body[0].value)
    sources = {"q0": demand_text}
    body = evidence["quote"]
    if len(body.encode("utf-8")) > MAX_BODY_BYTES:
        raise ValueError("Selected operation exceeds body bound")
    catalog, spans = {}, {}
    for start in range(0, len(body), OPERATION_SPAN_CHARACTERS):
        end = min(start + OPERATION_SPAN_CHARACTERS, len(body))
        key, quote = "e" + str(len(spans)), body[start:end]
        first = evidence["line"] + body[:start].count("\n")
        last = evidence["line"] + body[:end].count("\n") - int(body[end - 1] == "\n")
        catalog[key] = {"path": evidence["path"], "line": first, "end_line": last, "quote": quote}
        spans[key] = {"start": start, "end": end, "quote": quote}
    context = build_context({"repository": source["repository"], "revision": source["revision"],
        "selected_entrypoint": source["path"] + ":" + operation_name, "demand_sources": sources,
        "operation_evidence": catalog, "acquisition_complete": False,
        "acquisition_limitations": list(LIMITATIONS)})
    url = "https://github.com/" + demand["repository"] + "/blob/" + demand["revision"] + "/" + demand["path"]
    if demand_function is not None:
        _, _, contract_evidence = function_source(demand, demand_function)
        url += "#L" + str(contract_evidence["line"])
    return {"case": number, "source_url": url, "data": context, "demand_sources": sources,
        "operation_body": body, "operation_spans": spans}
