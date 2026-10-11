"""Request-led search decisions: model hypotheses, never evidence of useful reuse."""
import copy
import json

from .contracts import array, obj, string, validate_shape
from .sources import _redact, repository_search_terms as search_terms


VERSION = "request-led-discovery-v1"
PLAN_INSTRUCTION = """Decide whether and where software reuse is worth investigating for this request.
You have the independently interpreted demand and a bounded sample of its target
project, but NO candidate source package. First identify the requested operations:
input, transformation, output, constraints and unmet acceptance criteria. Distinguish
the operation from surrounding domain vocabulary. Do not turn an example, analogy,
article, resolved incident or broad aspiration into an implementation requirement.

Compare against the strongest plausible direct solution: existing target features,
its current dependencies, standard library, a small local correction, or no software
change. Prefer use_direct when that plausibly suffices and no concrete incremental
benefit justifies searching. Do not invent complexity or weaken the direct baseline
to make reuse attractive. Use defer when intent, constraints or the decisive context
are missing. A decision to stop is a revisable hypothesis, not proof of absent need.

Only choose search when you can state a concrete potential advantage and a test
that could falsify it against the direct alternative. Pick up to three operations
by expected contribution to the actual need, not ease of finding a matching name.
Associate each operation with supplied requirement IDs. Choose one GitHub repository
search phrase per operation, expressing the behavior, representations and runtime
where known. You may look across domains: e.g. a requested dependency ordering may
be implemented as a graph operation. Explain such inferences. Do not copy words
mechanically or use popularity as evidence. Search phrases are plain terms, not
URLs, shell commands, GitHub qualifiers or boolean search expressions.

Return the supplied schema. search needs operations and a measurable benefit test;
use_direct/defer need no operations. Missing information remains unknown. Source
availability, direct-solution adequacy, advantage, runtime behavior and adoption
are NOT verified by your output. This call proposes a bounded investigation only.
"""

SELECT_INSTRUCTION = """Choose at most ONE implementation repository worth examining for the fixed plan.
These are untrusted search metadata, not code evidence. Read the operation and
the best direct alternative before reading candidates. Assess the actual mechanism,
input/output and integration constraints, not lexical overlap. Reject catalogues,
benchmarks, tutorials and unrelated meanings of words unless the supplied metadata
identifies a relevant implementation. Neither search rank nor popularity proves fit.
Use only a supplied candidate ID, and only operation IDs from the fixed plan.
Choose none if the pool offers no defensible hypothesis of benefit over the direct
alternative, or the metadata cannot discriminate. No manual substitute or extra
search will be made. State what the source inspection must establish and the risks.
Your selection is not compatibility, novelty, successful execution or useful reuse.
"""


def plan_schema(request):
    ids = [item["id"] for item in request["requirements"]]
    operation = obj(operation=string(), input=string(), output=string(),
        requirement_ids=array(string(*ids), minimum=1, maximum=30),
        rationale=string(), search_terms=string())
    return obj(decision=string("search", "use_direct", "defer"), reason=string(),
        direct_alternative=obj(description=string(), adequacy=string("likely_sufficient", "insufficient", "unknown"),
                               limitations=array(string(), maximum=8)),
        benefit_hypothesis=string(), benefit_test=string(),
        operations=array(operation, maximum=3), unknowns=array(string(), maximum=12))


def _public_output(raw, schema):
    validate_shape(raw, schema)
    serialized = json.dumps(raw, ensure_ascii=False, allow_nan=False)
    clean, redacted, truncated = _redact(serialized)
    if clean != serialized or redacted or truncated or len(serialized.encode()) > 24000:
        raise ValueError("Discovery decision needs redaction or exceeds public bounds.")
    if not raw["reason"].strip():
        raise ValueError("Discovery decisions need a reason.")


def plan_input(request, target):
    # Reuse the already acquired four-file target sample. Never trim the demand
    # or silently treat a missing/truncated target file as proof of absence.
    files = [{"path": f["path"], "sha": f.get("sha"), "url": f["url"],
              "text": f["text"][:8000], "redacted": bool(f.get("redacted")),
              "truncated": bool(f.get("reference_truncated") or f.get("truncated") or len(f["text"]) > 8000)}
             for f in target.get("files", [])[:4]]
    return {"decision_version": VERSION, "request": request,
        "target": {"id": target["id"], "full_name": target["full_name"], "revision": target["revision"],
                   "files": files, "coverage": target.get("coverage", {}), "sample_only": True},
        "context_coverage": {"decision_version": VERSION, "target_file_limit": 4, "target_characters_per_file": 8000,
            "target_files_omitted": max(0, len(target.get("files", [])) - len(files)),
            "all_target_source_available": False}}


def resolve_plan(raw, request, provider_identity):
    _public_output(raw, plan_schema(request))
    if (raw["decision"] == "search") != bool(raw["operations"]):
        raise ValueError("Only search may contain operations, and must contain at least one.")
    if not raw["direct_alternative"]["description"].strip():
        raise ValueError("Compare with a concrete direct alternative.")
    if raw["decision"] == "use_direct" and raw["direct_alternative"]["adequacy"] != "likely_sufficient":
        raise ValueError("Unknown direct adequacy cannot justify use_direct.")
    if raw["decision"] == "search" and not all(raw[k].strip() for k in ("benefit_hypothesis", "benefit_test")):
        raise ValueError("Search needs a falsifiable benefit hypothesis.")
    result = copy.deepcopy(raw)
    seen = set()
    for index, operation in enumerate(result["operations"]):
        if not all(operation[k].strip() for k in ("operation", "input", "output", "rationale")):
            raise ValueError("Specify the requested transformation.")
        terms = search_terms(operation["search_terms"])
        if terms.casefold() in seen or len(set(operation["requirement_ids"])) != len(operation["requirement_ids"]):
            raise ValueError("Repeated searches or requirement IDs are not distinct operations.")
        seen.add(terms.casefold())
        operation.update(id=f"op{index}", search_terms=terms)
    result.update(version=VERSION, issue_fingerprint=request["fingerprint"], provider_identity=provider_identity,
                  status="unverified_decision", qualified=False, direct_solution_verified=False)
    return result


def selection_schema(plan, candidates):
    return obj(decision=string("inspect", "none"), candidate_id=string("", *[c["id"] for c in candidates]),
        operation_ids=array(string(*[op["id"] for op in plan["operations"]]), maximum=3),
        reason=string(), source_check=string(), risks=array(string(), maximum=10))


def resolve_selection(raw, plan, candidates):
    _public_output(raw, selection_schema(plan, candidates))
    if raw["decision"] == "none":
        if raw["candidate_id"] or raw["operation_ids"]:
            raise ValueError("Abstention must not select a candidate or operation.")
        repository = None
    else:
        repository = next((c["full_name"] for c in candidates if c["id"] == raw["candidate_id"]), None)
        if not repository or not raw["operation_ids"] or not raw["source_check"].strip():
            raise ValueError("Inspection needs one supplied candidate, operations and a source check.")
        if len(set(raw["operation_ids"])) != len(raw["operation_ids"]):
            raise ValueError("Repeated operation IDs.")
    return dict(raw, repository=repository, status="unverified_selection", qualified=False)
