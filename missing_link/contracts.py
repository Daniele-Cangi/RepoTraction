"""Machine-readable interpretation schemas, distinct from human examples."""


def obj(**properties):
    return {"type": "object", "properties": properties, "required": list(properties), "additionalProperties": False}


def string(*choices):
    return {"type": "string", **({"enum": list(choices)} if choices else {})}


def array(items=None):
    return {"type": "array", "items": items or string()}


def schema_for(phase, *, source_ids=None, capability_ids=None, requirement_ids=None):
    requirement = obj(text=string(), mandatory={"type": "boolean"}, explicit={"type": "boolean"},
        source_id=string(), quote=string(), inference=string())
    request = obj(outcome=string(), status=string("unresolved", "resolved", "duplicate", "unclear", "automated"),
        status_source_ids=array(), status_reason=string(), requirements=array(requirement),
        environment=array(), prior_attempts=array(), missing_information=array())
    capability = obj(id=string(), name=string(), summary=string(), outcome=string(), inputs=array(), outputs=array(),
        preconditions=array(), dependencies=array(), limitations=array(), standalone=string("yes", "no", "unknown"),
        search_terms=array(), source_ids=array())
    bridge = obj(kind=string("command", "example", "adapter", "extraction", "investigation"), summary=string(),
        steps=array(), existing_contribution=string(), new_logic=string(), assumptions=array(),
        dependencies=array(), runtime=string(), permissions=array(), coupling=string(), input=string(),
        expected_output=string(), ablation=string(), files=array(obj(path=string(), content=string())))
    match = obj(capability_id=string(), classification=string("direct", "adapter", "extraction", "rejected", "investigate"),
        summary=string(), checks=array(obj(requirement_id=string(), status=string("satisfied", "incompatible", "undetermined"),
            reason=string(), source_ids=array())), obstacles=array(), bridge=bridge)
    schema = {"request": request, "capabilities": obj(capabilities=array(capability)),
              "matches": obj(matches=array(match))}[phase]

    def choices(values):
        # Bound dynamic enum growth before provider transport/reservation. Imports
        # and human examples retain the general schema when no scope is provided.
        ids = list(values)
        if not ids or any(not isinstance(value, str) or not value for value in ids):
            raise ValueError("Analysis citation scope is empty or exceeds contract bounds.")
        ids = list(dict.fromkeys(ids))
        if len(ids) > 400:
            raise ValueError("Analysis citation scope is empty or exceeds contract bounds.")
        return string(*ids)

    if source_ids is not None:
        references = choices(source_ids)
        if phase == "request":
            requirement["properties"]["source_id"] = references
            request["properties"]["status_source_ids"] = array(references)
        elif phase == "capabilities":
            capability["properties"]["source_ids"] = array(references)
        else:
            match["properties"]["checks"]["items"]["properties"]["source_ids"] = array(references)
    if capability_ids is not None:
        if phase == "capabilities":
            capability["properties"]["id"] = choices(capability_ids)
        elif phase == "matches":
            match["properties"]["capability_id"] = choices(capability_ids)
    if requirement_ids is not None and phase == "matches":
        match["properties"]["checks"]["items"]["properties"]["requirement_id"] = choices(requirement_ids)
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
        if len(value) > 100:
            raise ValueError("AI output list exceeds contract bounds.")
        for child in value:
            validate_shape(child, schema["items"], location + "[]")
    elif kind == "string" and len(value) > 40000:
        raise ValueError("AI output text exceeds contract bounds.")
