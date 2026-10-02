"""Machine-readable interpretation schemas, distinct from human examples."""
from .non_demands import NON_DEMAND_STATUS
from .contributions import CONTRIBUTION_KINDS, PARTIAL_BASES

MAX_SCOPED_IDS = 400
MAX_REQUEST_REQUIREMENTS = 30


def obj(**properties):
    return {"type": "object", "properties": properties, "required": list(properties), "additionalProperties": False}


def string(*choices):
    return {"type": "string", **({"enum": list(choices)} if choices else {})}


def array(items=None, *, minimum=None, maximum=None):
    bounds = {}
    if minimum is not None:
        bounds["minItems"] = minimum
    if maximum is not None:
        bounds["maxItems"] = maximum
    return {"type": "array", "items": items or string(), **bounds}


def validate_requirement_count(requirements, *, minimum=1):
    """Enforce local demand bounds; callers allow zero only for typed non-demands."""
    if not isinstance(requirements, list):
        raise ValueError("Request requirements must be a list.")
    if len(requirements) < minimum:
        raise ValueError("Extract at least one source-grounded requirement.")
    if len(requirements) > MAX_REQUEST_REQUIREMENTS:
        raise ValueError(f"Request requirements exceed maximum {MAX_REQUEST_REQUIREMENTS} (received {len(requirements)}).")


def schema_for(phase, *, source_ids=None, capability_ids=None, requirement_ids=None, citation_ids=None, optional_field_ids=None):
    requirement = obj(text=string(), mandatory={"type": "boolean"}, explicit={"type": "boolean"},
        source_id=string(), quote=string(), inference=string())
    field_disposition = obj(hint_id=string(), disposition=string("not_requested", "needs_review"), reason=string())
    request = obj(outcome=string(), status=string("unresolved", "resolved", "duplicate", "unclear", "automated", NON_DEMAND_STATUS),
        status_source_ids=array(), status_reason=string(),
        # Zero is legal only for the typed non-demand disposition. Cross-field
        # consistency is checked locally; normal demands still require 1..30.
        requirements=array(requirement, minimum=0, maximum=MAX_REQUEST_REQUIREMENTS),
        optional_field_dispositions=array(field_disposition),
        environment=array(), prior_attempts=array(), missing_information=array())
    capability = obj(id=string(), name=string(), summary=string(), outcome=string(), inputs=array(), outputs=array(),
        preconditions=array(), dependencies=array(), limitations=array(), standalone=string("yes", "no", "unknown"),
        search_terms=array(), source_ids=array())
    bridge = obj(kind=string("command", "example", "adapter", "extraction", "investigation"), summary=string(),
        steps=array(), existing_contribution=string(), new_logic=string(), assumptions=array(),
        dependencies=array(), runtime=string(), permissions=array(), coupling=string(), input=string(),
        expected_output=string(), ablation=string(), files=array(obj(path=string(), content=string())))
    partial = obj(requirement_id=string(), basis=string(*PARTIAL_BASES), operation=string(),
        requirement_part=string(), remaining_work=string(), source_ids=array())
    match = obj(capability_id=string(), classification=string("direct", "adapter", "extraction", "rejected", "investigate"),
        summary=string(), checks=array(obj(requirement_id=string(), status=string("satisfied", "incompatible", "undetermined"),
            contribution=string(*CONTRIBUTION_KINDS),
            reason=string(), source_ids=array())), partial_support=array(partial, maximum=MAX_REQUEST_REQUIREMENTS),
        obstacles=array(), bridge=bridge)
    schema = {"request": request, "capabilities": obj(capabilities=array(capability)),
              "matches": obj(matches=array(match))}[phase]

    def choices(values):
        # Bound dynamic enum growth before provider transport/reservation. Imports
        # and human examples retain the general schema when no scope is provided.
        ids = list(values)
        if not ids or any(not isinstance(value, str) or not value for value in ids):
            raise ValueError("Analysis citation scope is empty or exceeds contract bounds.")
        ids = list(dict.fromkeys(ids))
        if len(ids) > MAX_SCOPED_IDS:
            raise ValueError("Analysis citation scope is empty or exceeds contract bounds.")
        if len(ids) > 250 and sum(len(value) for value in ids) > 15000:
            raise ValueError("Analysis citation enum exceeds structured-output character bounds; narrow the context.")
        return string(*ids)

    if source_ids is not None:
        references = choices(source_ids)
        if phase == "request":
            if citation_ids is None:
                requirement["properties"]["source_id"] = references
            request["properties"]["status_source_ids"] = array(references)
        elif phase == "capabilities":
            capability["properties"]["source_ids"] = array(references)
        else:
            match["properties"]["checks"]["items"]["properties"]["source_ids"] = array(references)
            partial["properties"]["source_ids"] = array(references)
    if capability_ids is not None:
        if phase == "capabilities":
            capability["properties"]["id"] = choices(capability_ids)
        elif phase == "matches":
            match["properties"]["capability_id"] = choices(capability_ids)
    if requirement_ids is not None and phase == "matches":
        match["properties"]["checks"]["items"]["properties"]["requirement_id"] = choices(requirement_ids)
        partial["properties"]["requirement_id"] = choices(requirement_ids)
    if citation_ids is not None:
        if phase != "request":
            raise ValueError("Demand spans are only valid in the request contract.")
        # At most 400 span IDs + 400 status source IDs + 30 optional-field IDs:
        # below the structured-output limit of 1,000 values across the schema.
        request["properties"]["requirements"] = array(obj(text=string(), mandatory={"type": "boolean"},
            explicit={"type": "boolean"}, citation_id=choices(citation_ids), inference=string()),
            minimum=0, maximum=MAX_REQUEST_REQUIREMENTS)
    if optional_field_ids is not None:
        if phase != "request":
            raise ValueError("Optional-field decisions are only valid in the request contract.")
        ids = list(optional_field_ids)
        if ids:
            references = choices(ids)
            if len(references["enum"]) > 30:
                raise ValueError("Optional-field citation scope exceeds contract bounds.")
            field_disposition["properties"]["hint_id"] = references
        # With no offered hints the provider must return []; local scope checking
        # also rejects every nonempty decision rather than using an empty enum.
    return schema


def validate_shape(value, schema, location="output"):
    """Also enforce shape for compatible servers that only offer JSON mode."""
    kind = schema["type"]
    valid = {"object": isinstance(value, dict), "array": isinstance(value, list),
        "string": isinstance(value, str), "boolean": isinstance(value, bool)}[kind]
    if not valid or ("enum" in schema and value not in schema["enum"]):
        raise ValueError(f"AI output violates the {location} contract.")
    if kind == "object":
        if set(value) != set(schema["properties"]):
            raise ValueError(f"AI output has missing or unexpected {location} fields.")
        for key, child in schema["properties"].items():
            validate_shape(value[key], child, location + "." + key)
    elif kind == "array":
        if len(value) < schema.get("minItems", 0):
            raise ValueError(f"AI output {location} requires at least {schema['minItems']} item(s).")
        if len(value) > schema.get("maxItems", 100):
            raise ValueError(f"AI output {location} exceeds maximum {schema.get('maxItems', 100)} items.")
        if len(value) > 100:
            raise ValueError("AI output list exceeds contract bounds.")
        for child in value:
            validate_shape(child, schema["items"], location + "[]")
    elif kind == "string" and len(value) > 40000:
        raise ValueError("AI output text exceeds contract bounds.")
