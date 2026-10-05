"""Offline experimental generation constraints; not production or semantic proof.

The frozen layer prompt/normalizer are reused unchanged. Nested anyOf branches
distinguish unknown, known and slice declarations. A typed outer projection keeps
the existing receipt reader's validate_shape compatible, but that generic reader
does NOT enforce anyOf/$ref/pattern. Call this module's normalizer afterward.
No IO, provider configuration, credentials, budget or execution on import.
"""
import copy

from missing_link.contracts import obj, string, validate_shape
from scripts import missing_link_triage_layer_prompt as frozen
from scripts.missing_link_triage_contract import FACETS
from scripts.missing_link_triage_explicit_scope import AXES, LAYERS, _enum_values

PROMPT = frozen.PROMPT
# Documented string pattern support; lengths/whitespace still use frozen guards.
NONEMPTY_PATTERN = r"[\s\S]"
SLICE_FIELDS = ("requested_part", "existing_behavior", "remaining_work")


def _ref(name):
    return {"$ref": f"#/$defs/{name}"}


def schema_for_context(context):
    """Emit closed, required objects; no root union or duplicated ID catalogs.

The outer facet shape is only a compatibility projection for the existing local
reader. Native generation constraints live in the nested branches; explicit local
branch validation and the frozen provenance/bounds guards remain mandatory.
    """
    original = frozen.schema_for_context(context)
    definitions = {"empty": string(""),
                   "nonempty": {"type": "string", "pattern": NONEMPTY_PATTERN}}
    demands, operations = context["demand_spans"], context["operation_evidence"]
    if demands:
        definitions["demand_id"] = string(*demands)
    if operations:
        definitions["operation_id"] = string(*operations)
    facets = {}
    for name in FACETS:
        prior = original["properties"]["facets"]["properties"][name]["properties"]
        projection = {key: string() for key in prior}
        projection["axis"] = string(AXES[name])
        projection["relation"] = copy.deepcopy(prior["relation"])
        unknown = {key: _ref("empty") for key in prior}
        unknown.update(axis=string(AXES[name]), relation=string("unknown"), reason=_ref("nonempty"))
        branches = [obj(**unknown)]
        # No empty enum or manufactured citation when only abstention is possible.
        if demands and operations:
            known = {key: _ref("empty") for key in prior}
            known.update(axis=string(AXES[name]), comparison_scope=string("requested_operation"),
                operation_layer=string(*LAYERS[1:]), demand_property=_ref("nonempty"),
                operation_property=_ref("nonempty"), relation=string("aligned", "different"),
                reason=_ref("nonempty"), demand_span_id=_ref("demand_id"), operation_id=_ref("operation_id"))
            branches.append(obj(**known))
            if name == "outcome":
                sliced = copy.deepcopy(known)
                sliced["relation"] = string("slice")
                for key in SLICE_FIELDS:
                    sliced[key] = _ref("nonempty")
                branches.append(obj(**sliced))
        facets[name] = obj(**projection) | {"anyOf": branches}
    schema = obj(demand_complete={"type": "boolean"}, facets=obj(**facets)) | {"$defs": definitions}
    if _enum_values(schema) > 1000:
        raise ValueError("Declaration schema exceeds structured-output enum bound")
    return schema


def validate_prediction_shape(raw, context):
    """Validate exactly our emitted branches, not a general JSON Schema engine.

The legacy generic validator ignores new keywords. Resolve this schema's flat
string refs and check its sole pattern explicitly, without modifying raw data.
Nonempty means at least one character, NOT non-whitespace, <=400, relevant or true.
    """
    schema = schema_for_context(context)
    validate_shape(raw, schema)
    for name in FACETS:
        facet = raw["facets"][name]
        branches = schema["properties"]["facets"]["properties"][name]["anyOf"]
        branch = next((item for item in branches
                       if facet["relation"] in item["properties"]["relation"]["enum"]), None)
        if branch is None:
            raise ValueError(f"{name}: known relation needs supplied citation catalogs")
        fields = {key: schema["$defs"][rule["$ref"].split("/")[-1]] if "$ref" in rule else rule
                  for key, rule in branch["properties"].items()}
        validate_shape(facet, obj(**fields), f"facets.{name}")
        for key, rule in fields.items():
            if rule.get("pattern") == NONEMPTY_PATTERN and not facet[key]:
                raise ValueError(f"facets.{name}.{key}: experimental schema requires a nonempty string")


def normalize_prediction(raw, context, *, demand_sources, operation_body, operation_spans):
    """Reject mechanically, then delegate all unchanged local/provenance guards."""
    validate_prediction_shape(raw, context)
    return frozen.normalize_prediction(raw, context, demand_sources=demand_sources,
        operation_body=operation_body, operation_spans=operation_spans)
