"""Source-blind, cited model hypotheses for the existing behavioral prototype."""
import json

from .analysis import digest
from .behavioral import _validate_contracts
from .contracts import array, obj, string, validate_shape
from .sources import _redact
from .store import redact_payload


VERSION = "behavioral-demand-v1"
INSTRUCTION = """Translate this public discussion into small executable example contracts.
You have no candidate implementation: do not guess one, name a source function,
choose an adapter, or tailor expected values to a prospective solution.
Read later comments and distinguish requested behavior from examples, context,
resolved work and conflicting requirements. Return undetermined with no contracts
when a defensible operation cannot be specified. Never force a positive result.
Propose at most three independently testable suboperations. Preserve prohibitions,
runtime limits, preconditions and uncovered requirements. Unknown runtime stays
unknown; non-unknown runtime needs a supporting demand citation.
Select citation IDs only from demand_spans. Citations establish textual provenance,
not semantic correctness. Label each example as an explicit_example only if its
input AND expected output appear in the cited discussion; otherwise use inferred.
Record representation choices and uncertain assumptions explicitly.
args_json encodes a JSON array of positional arguments; expected_json encodes the
expected JSON value. No code, expressions, non-finite numbers or custom types.
Use boolean_mask only for one argument containing a list of actual booleans.
Examples and checks must have different inputs. Include boundary/counterexample
checks, but these checks come from the same interpretation, not an independent
oracle. Do not invent missing coordinate, ordering, runtime or error semantics.
All proposed contracts require independent technical review before qualification.
"""


def proposal_schema():
    citations = array(string(), minimum=1, maximum=4)
    case = obj(args_json=string(), expected_json=string(), citation_ids=citations,
               basis=string("explicit_example", "inferred"))
    contract = obj(operation=string(), citation_ids=citations,
        input_kind=string("arguments", "boolean_mask"),
        runtime=string("python", "javascript", "rust", "unknown"),
        runtime_citation_ids=array(string(), maximum=4),
        preconditions=array(string(), maximum=8), assumptions=array(string(), maximum=8),
        uncovered_requirements=array(string(), maximum=12),
        examples=array(case, minimum=1, maximum=4), checks=array(case, minimum=1, maximum=4))
    return obj(status=string("proposed", "undetermined"), reason=string(),
               contracts=array(contract, maximum=3), unknowns=array(string(), maximum=12))


def _json_value(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate example JSON key.")
            result[key] = value
        return result

    def invalid_constant(value):
        raise ValueError("Example JSON contains a non-finite number.")

    return json.loads(text, object_pairs_hook=pairs, parse_constant=invalid_constant)


def resolve_proposal(raw, data, report, issue, provider_identity):
    """Validate shape/provenance and decode data only; never certify semantics."""
    validate_shape(raw, proposal_schema())
    serialized = json.dumps(raw, ensure_ascii=False, allow_nan=False)
    cleaned, redacted, truncated = _redact(serialized)
    if redacted or truncated or cleaned != serialized or len(serialized.encode()) > 48000:
        raise ValueError("Behavior proposal exceeds public text bounds or needs redaction.")
    if (raw["status"] == "proposed") != bool(raw["contracts"]):
        raise ValueError("Proposed status requires contracts; undetermined requires none.")
    if not raw["reason"].strip():
        raise ValueError("Behavior proposal requires a disposition reason.")

    def citations(ids):
        if len(set(ids)) != len(ids) or any(ref not in data["demand_spans"] for ref in ids):
            raise ValueError("Behavior proposal cites unavailable or duplicate demand spans.")
        result = []
        for ref in ids:
            span = data["demand_spans"][ref]
            source = data["sources"][span["source_id"]]
            result.append({"citation_id": ref, "source_id": span["source_id"],
                           "url": source["url"], "quote": span["quote"]})
        return result

    contracts = []
    for item in raw["contracts"]:
        evidence = citations(item["citation_ids"])
        runtime_evidence = citations(item["runtime_citation_ids"])
        if item["runtime"] != "unknown" and not runtime_evidence:
            raise ValueError("A proposed runtime needs demand evidence; otherwise use unknown.")
        if not item["operation"].strip():
            raise ValueError("Behavior proposal needs an operation.")
        phases, case_evidence, inputs = {}, {}, set()
        for phase in ("examples", "checks"):
            phases[phase], case_evidence[phase] = [], []
            for case in item[phase]:
                refs = citations(case["citation_ids"])
                args, expected = _json_value(case["args_json"]), _json_value(case["expected_json"])
                if not isinstance(args, list):
                    raise ValueError("Behavior example arguments must be a JSON array.")
                identity = json.dumps(args, sort_keys=True, allow_nan=False)
                if identity in inputs:
                    raise ValueError("Behavior examples/checks must have distinct inputs.")
                inputs.add(identity)
                phases[phase].append({"args": args, "expected": expected})
                case_evidence[phase].append({"citations": refs, "basis": case["basis"],
                                            "semantic_status": "model_proposed_unreviewed"})
        first = evidence[0]
        source = data["sources"][first["source_id"]]
        contract = {"id": "demand-" + digest({"issue": issue["url"], "proposal": item})[:20],
            "kind": "public_demand", "operation": item["operation"],
            "input_kind": item["input_kind"], "runtime": item["runtime"], **phases,
            "evidence": {"url": first["url"], "quote": first["quote"], "body": source["quote"]},
            "citations": evidence, "runtime_evidence": runtime_evidence, "case_evidence": case_evidence,
            "preconditions": item["preconditions"], "assumptions": item["assumptions"],
            "uncovered_requirements": item["uncovered_requirements"],
            "interpretation_origin": "model_proposed_unreviewed",
            "check_origin": "same_model_response_not_independent_oracle", "qualified": False}
        contracts.append(contract)
    if contracts:
        _validate_contracts(contracts)
        # Escapes in args_json/expected_json can hide patterns until decoding.
        # Store must never silently change executable example values or keys.
        if redact_payload(contracts) != contracts:
            raise ValueError("Decoded examples need redaction; no altered contract is accepted.")
    unknowns = list(raw["unknowns"])
    if not report["discussion_complete"]:
        unknowns.append("Discussion context is incomplete; omitted requirements may change the operation.")
    return {"version": VERSION, "status": raw["status"], "reason": raw["reason"],
        "contracts": contracts, "unknowns": unknowns, "analysis_context": report,
        "issue_url": issue["url"], "issue_fingerprint": issue["fingerprint"],
        "provider_identity": provider_identity, "qualified": False,
        "semantic_status": "model_proposed_unreviewed", "execution_status": "not_requested"}
