"""Finite example evaluation copied into the existing WASI guest, not a runner.

Adapters convert representations only. They contain no grouping, interval union
or source-function choice. Discovery and holdout cases are evaluated separately.
"""
import copy
import json
import math
import types
from contextlib import redirect_stderr, redirect_stdout


class _DiscardedOutput:
    """Discard ordinary guest prints without retaining unbounded log text."""
    def __init__(self):
        self.characters = 0

    def write(self, text):
        self.characters += len(text)
        return len(text)

    def flush(self):
        pass


def _normal(value, depth=0):
    if depth > 8:
        raise ValueError("Output nesting exceeded")
    if type(value) is float and not math.isfinite(value):
        raise ValueError("Non-finite output is outside the JSON example domain")
    if value is None or type(value) in (bool, int, float, str):
        return value
    if isinstance(value, (list, tuple, types.GeneratorType)):
        result = []
        for item in value:
            if len(result) >= 2048:
                raise ValueError("Output length exceeded")
            result.append(_normal(item, depth + 1))
        return result
    if isinstance(value, dict):
        if len(value) > 2048 or any(type(key) is not str for key in value):
            raise ValueError("Expected a bounded mapping with JSON string keys")
        return {key: _normal(item, depth + 1) for key, item in value.items()}
    raise ValueError("Output is outside the JSON example domain")


def _adapt(args, recipe):
    if recipe == "identity":
        return args
    mask = args[0]
    origin = 1 if "_one_" in recipe else 0
    return [list(range(origin, len(mask) + origin)),
            [i + origin for i, present in enumerate(mask) if present]]


def _output(value, recipe):
    value = _normal(value)
    if recipe == "identity":
        return value
    origin = 1 if "_one_" in recipe else 0
    end_delta = 1 if recipe.endswith("halfopen") else 0
    if not isinstance(value, list) or any(not isinstance(p, list) or len(p) != 2
                                        or any(type(n) is not int for n in p) for p in value):
        raise ValueError("Expected integer endpoint pairs")
    return [[a - origin, b - origin + end_delta] for a, b in value]


def _equal(left, right):
    # Python's True == 1 must not establish a representation match.
    if type(left) is not type(right):
        return False
    if isinstance(left, list):
        return len(left) == len(right) and all(_equal(a, b) for a, b in zip(left, right))
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(_equal(left[k], right[k]) for k in left)
    return left == right


def observe(function, contract, recipe):
    row = {"examples_passed": 0, "checks_passed": 0, "mutated_input": False,
           "ablation_passed": 0, "first_failure": None}
    for phase in ("examples", "checks"):
        # Holdout does not change the adapter selected on discovery examples.
        if phase == "checks" and row["examples_passed"] != len(contract["examples"]):
            break
        for index, case in enumerate(contract[phase]):
            args = _adapt(copy.deepcopy(case["args"]), recipe)
            original = copy.deepcopy(args)
            try:
                observed = _output(function(*args), recipe)
                passed = _equal(observed, case["expected"])
                failure = {"observed": observed}
            except Exception as exc:
                passed, failure = False, {"error_type": type(exc).__name__[:128]}
            mutated = not _equal(args, original)
            row["mutated_input"] |= mutated
            row[phase + "_passed"] += int(passed and not mutated)
            if not passed or mutated:
                if row["first_failure"] is None:
                    row["first_failure"] = {"phase": phase, "case_index": index,
                        "args": case["args"], "expected": case["expected"],
                        "mutated_input": mutated, **failure}
            # Remove the existing source computation but keep representation
            # conversions: an identity substitute cannot group separated runs.
            try:
                ablated = _output(original[0], recipe)
                row["ablation_passed"] += int(_equal(ablated, case["expected"]))
            except Exception:
                pass
    return row


def _search(payload):
    records, load_errors = [], []
    # Reserve the result envelope and count fields up front. Records
    # that do not fit remain explicitly unobserved in the host assessment.
    budget = payload["output_limit"] - 256
    used, omitted = 0, 0
    fields = ("candidate_id", "contract_id", "recipe", "examples_passed", "checks_passed",
              "mutated_input", "ablation_passed", "first_failure")
    def wire(value):
        return json.dumps(value, ensure_ascii=True, allow_nan=False, separators=(",", ":"))

    for candidate in payload["candidates"]:
        try:
            namespace = {"__name__": "behavior_slice", "__file__": candidate["file"]}
            with open(candidate["file"], encoding="utf-8") as stream:
                code = stream.read()
            exec(compile(code, candidate["file"], "exec"), namespace)
            function = namespace[candidate["name"]]
        except Exception as exc:
            load_errors.append({"candidate_id": candidate["id"], "error_type": type(exc).__name__[:64]})
            continue
        for contract in payload["contracts"]:
            recipes = ["identity"]
            if contract["input_kind"] == "boolean_mask":
                recipes += ["mask_zero_closed", "mask_zero_halfopen", "mask_one_closed", "mask_one_halfopen"]
            for recipe in recipes:
                arity = len(contract["examples"][0]["args"]) if recipe == "identity" else 2
                if (candidate["required_keywords"] or arity < candidate["required_args"]
                        or (arity > candidate["positional_args"] and not candidate["variadic"])):
                    continue
                row = observe(function, contract, recipe)
                # Keep one counterexample per binding. Suppress redundant null
                # fields so an ordinary experiment fits the existing output cap.
                if row["first_failure"] is None:
                    del row["first_failure"]
                observation = {"candidate_id": candidate["id"], "contract_id": contract["id"],
                               "recipe": recipe, **row}
                record = wire([observation.get(k) for k in fields])
                if len(record) > 2048 and row.get("first_failure"):
                    # The case remains addressable in the frozen plan. Preserve
                    # its index/reason when duplicating full values would overflow.
                    failure = row["first_failure"]
                    observation["first_failure"] = {k: failure[k] for k in
                        ("phase", "case_index", "mutated_input", "error_type") if k in failure}
                    observation["first_failure"]["detail_truncated"] = True
                    record = wire([observation.get(k) for k in fields])
                if used + len(record) + 1 <= budget:
                    records.append(record)
                    used += len(record) + 1
                else:
                    omitted += 1
    # Fixed positional records avoid repeating field names across failed bindings
    # within the existing runner's 32-KiB stdout limit.
    while records and used + len(wire(load_errors)) > budget:
        used -= len(records.pop()) + 1
        omitted += 1
    return ('{"bindings":[' + ','.join(records) + '],"load_errors":' + wire(load_errors)
            + ',"omitted_bindings":' + str(omitted))


def run(payload):
    output, errors = _DiscardedOutput(), _DiscardedOutput()
    # Covers defaults/decorators during load, calls and lazy generator iteration.
    # This protects the result protocol from ordinary prints, not hostile code
    # that deliberately bypasses Python's streams inside the guest.
    with redirect_stdout(output), redirect_stderr(errors):
        document = _search(payload)
    print(document + ',"discarded_output_chars":{"stdout":' + str(output.characters)
          + ',"stderr":' + str(errors.characters) + '}}')
