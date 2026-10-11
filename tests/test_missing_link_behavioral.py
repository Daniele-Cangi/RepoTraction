"""Behavioral discovery regressions; acquired fixture code is never host-executed."""
import copy
import io
import json
import subprocess
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
import tempfile
import unittest

from missing_link.behavioral import extract_callables, prepare_behavior_search, assess_behavior_search, prepare_behavior_bridge
from missing_link.behavior_examples import observe, run
from missing_link.wasi_runner import MAX_OUTPUT


def snapshot(code):
    return {"full_name": "example/engine", "revision": "a" * 40, "public": True,
            "files": [{"path": "engine.py", "text": code}]}


def case(args, expected):
    return {"args": args, "expected": expected}


def mask_contract(runtime="python"):
    return {"id": "signal", "kind": "synthetic_control", "input_kind": "boolean_mask",
            "runtime": runtime, "examples": [case([[True, False, True]], [[0, 1], [2, 3]])],
            "checks": [case([[False, True, True]], [[1, 3]]), case([[False]], [])]}


# Authored test implementation. This code, unlike downloaded snapshots, can be
# evaluated as ordinary unit-test code on either CI operating system.
OWN_CODE = '''def hidden(records, selected):
    chosen = set(selected)
    result = []
    active = []
    for record in records:
        if record in chosen:
            active.append(record)
        elif active:
            result.append((active[0], active[-1]))
            active = []
    if active:
        result.append((active[0], active[-1]))
    return result
'''

OWN_GENERATOR = '''def generated(value):
    yield value + 1
'''

OWN_NOISY = '''def noisy(value, initial=print("loaded")):
    print("x" * 50000)
    print("stderr message", file=__import__("sys").stderr)
    yield value + 1
'''


def execute_authored_fixture(plan):
    """Exercise the guest evaluator using ONLY authored fixtures, never acquired source."""
    if any(c["evidence"]["quote"] not in (OWN_CODE, OWN_GENERATOR, OWN_NOISY) for c in plan["candidates"]):
        raise AssertionError("Host evaluation is restricted to the authored unit fixture.")
    with tempfile.TemporaryDirectory() as directory:
        candidates = []
        for i, candidate in enumerate(plan["candidates"]):
            path = Path(directory) / f"fixture{i}.py"
            path.write_text(candidate["code"], encoding="utf-8")
            candidates.append({**candidate, "file": str(path)})
        output = io.StringIO()
        with redirect_stdout(output):
            run({"candidates": candidates, "contracts": plan["contracts"], "output_limit": MAX_OUTPUT})
    return {"status": "exited_successfully", "context": "isolated_wasi_example",
            "artifact_sha256": plan["artifact_sha256"], "stdout": output.getvalue()}


class ExtractionTests(unittest.TestCase):
    def test_search_artifacts_fit_runner_after_payload_and_slice_overhead(self):
        code = "def wide(value):\n    # " + "x" * 50000 + "\n    return value + 1\n"
        repo = snapshot(code)
        repo["files"] = [{"path": f"engine{i}.py", "text": code} for i in range(40)]
        plan = prepare_behavior_search(repo, [mask_contract()])
        self.assertLessEqual(sum(len(text.encode("utf-8")) for text in plan["files"].values()), 2000000)
        self.assertTrue(all(len(text.encode("utf-8")) <= 262144 for text in plan["files"].values()))
        self.assertLess(len(plan["candidates"]), 40)
        self.assertEqual(len(plan["candidates"]) + len(plan["omissions"]), 40)
        self.assertIn("artifact byte limit", plan["omissions"][-1]["reason"])

    def test_parsing_never_executes_module_initializers(self):
        repo = snapshot("raise RuntimeError('must not execute')\n" + OWN_CODE)
        candidates, _ = extract_callables(repo)
        self.assertEqual([c["name"] for c in candidates], ["hidden"])
        self.assertNotIn("must not execute", candidates[0]["code"])
        self.assertEqual(candidates[0]["evidence"]["line"], 2)
        self.assertEqual(candidates[0]["evidence"]["quote"], OWN_CODE)

    def test_resolves_transitive_same_file_dependencies_and_preserves_defaults(self):
        code = "SCALE = 2\ndef inner(x):\n    return x * SCALE\ndef outer(x, factor=3):\n    return inner(x) * factor\n"
        candidates, _ = extract_callables(snapshot(code))
        outer = next(c for c in candidates if c["name"] == "outer")
        self.assertIn("SCALE = 2", outer["code"])
        self.assertIn("def inner", outer["code"])
        self.assertEqual((outer["required_args"], outer["positional_args"]), (1, 2))

    def test_unknown_globals_and_computed_initializers_are_not_stubbed(self):
        code = "STATE = initialize()\ndef hidden(x):\n    return STATE + x\ndef other(x):\n    return unknown(x)\n"
        candidates, omissions = extract_callables(snapshot(code))
        self.assertEqual(candidates, [])
        self.assertEqual(len(omissions), 2)

    def test_global_shadowing_cannot_fall_back_to_builtins(self):
        code = "if configured:\n    sorted = replacement\ndef f(x):\n    return sorted(x)\n"
        candidates, omissions = extract_callables(snapshot(code))
        self.assertEqual(candidates, [])
        self.assertIn("Unsupported", omissions[0]["reason"])

    def test_decorator_is_preserved_not_silently_removed(self):
        code = "from functools import lru_cache\n@lru_cache()\ndef f(x):\n    return x + 1\n"
        candidate = extract_callables(snapshot(code))[0][0]
        self.assertIn("@lru_cache()", candidate["code"])
        self.assertEqual(candidate["evidence"]["line"], 2)

    def test_redacted_or_truncated_source_is_omitted(self):
        for text in (OWN_CODE + "\n# " + "x" * 70000, OWN_CODE + "\n# sk-" + "a" * 30):
            candidates, omissions = extract_callables(snapshot(text))
            self.assertEqual(candidates, [])
            self.assertIn("redacted/truncated", omissions[0]["reason"])

    def test_private_functions_are_scanned_without_readme_or_name_promotion(self):
        candidate = extract_callables(snapshot(OWN_CODE.replace("hidden", "_opaque")))[0][0]
        self.assertTrue(candidate["private_name"])
        self.assertEqual(candidate["name"], "_opaque")

    def test_public_pinned_snapshot_is_required(self):
        for key, value in (("revision", "main"), ("public", False)):
            repo = snapshot(OWN_CODE)
            repo[key] = value
            with self.assertRaises(ValueError):
                extract_callables(repo)

    def test_actual_coverage_fixture_is_parsed_but_never_host_executed(self):
        directory = Path(__file__).parent / "fixtures" / "behavioral_discovery"
        meta = json.loads((directory / "provenance.json").read_text(encoding="utf-8"))
        repo = {"full_name": meta["source"], "revision": meta["revision"], "public": True,
                "files": [{"path": f["path"], "text": (directory / f["fixture"]).read_text(encoding="utf-8")}
                          for f in meta["files"]]}
        candidates, omissions = extract_callables(repo)
        helper = next(c for c in candidates if c["name"] == "_line_ranges")
        self.assertEqual((helper["evidence"]["line"], helper["evidence"]["end_line"]), (422, 446))
        self.assertTrue(any(o.get("symbol") == "format_lines" for o in omissions))
        self.assertEqual(helper["dependencies"], [])


class BehavioralTests(unittest.TestCase):
    def test_loading_and_lazy_callable_output_do_not_corrupt_search_json(self):
        contract = {"id": "noisy", "kind": "synthetic_control", "input_kind": "arguments",
                    "runtime": "python", "examples": [case([0], [1])], "checks": [case([1], [2])]}
        plan = prepare_behavior_search(snapshot(OWN_NOISY), [contract])
        errors = io.StringIO()
        with redirect_stderr(errors):
            execution = execute_authored_fixture(plan)
        result = assess_behavior_search(plan, execution)
        self.assertTrue(result["matches"])
        self.assertEqual(errors.getvalue(), "")
        self.assertLessEqual(len(execution["stdout"].encode("utf-8")), MAX_OUTPUT)
        self.assertGreater(result["discarded_output_chars"]["stdout"], MAX_OUTPUT)
        self.assertGreater(result["discarded_output_chars"]["stderr"], 0)

    def test_export_rejects_a_match_from_a_different_plan(self):
        plan = prepare_behavior_search(snapshot(OWN_CODE), [mask_contract()])
        match = assess_behavior_search(plan, execute_authored_fixture(plan))["matches"][0]
        alternatives = []
        altered = copy.deepcopy(plan)
        altered["contracts"][0]["checks"][0]["expected"] = [[0, 99]]
        alternatives.append(altered)
        altered = copy.deepcopy(plan)
        altered["candidates"][0]["code"] += "\n# different source\n"
        alternatives.append(altered)
        altered = copy.deepcopy(plan)
        altered["revision"] = "b" * 40
        alternatives.append(altered)
        for other in alternatives:
            with self.assertRaisesRegex(ValueError, "search plan"):
                prepare_behavior_bridge(other, match)
        del match["plan_sha256"]
        with self.assertRaisesRegex(ValueError, "search plan"):
            prepare_behavior_bridge(plan, match)

    def test_maximum_search_reports_omissions_within_existing_output_limit(self):
        repo = snapshot(OWN_CODE)
        repo["files"] = [{"path": f"engine{i}.py", "text": OWN_CODE} for i in range(40)]
        contracts = [{**mask_contract(), "id": f"mask{i}"} for i in range(16)]
        plan = prepare_behavior_search(repo, contracts)
        execution = execute_authored_fixture(plan)
        self.assertLessEqual(len(execution["stdout"].encode("utf-8")), MAX_OUTPUT)
        result = assess_behavior_search(plan, execution)
        self.assertEqual(result["attempted_bindings"], 40 * 16 * 4)
        self.assertGreater(result["omitted_bindings"], 0)
        self.assertEqual(len(result["unobserved_bindings"]), result["omitted_bindings"])
        self.assertTrue(result["matches"])

    def test_large_counterexample_keeps_case_reference_and_truncation(self):
        contract = {"id": "large", "kind": "synthetic_control", "input_kind": "arguments",
                    "runtime": "python", "examples": [case([0], "x" * 40000)],
                    "checks": [case([1], [2])]}
        plan = prepare_behavior_search(snapshot(OWN_GENERATOR), [contract])
        execution = execute_authored_fixture(plan)
        self.assertLessEqual(len(execution["stdout"].encode("utf-8")), MAX_OUTPUT)
        result = assess_behavior_search(plan, execution)
        self.assertEqual(result["matches"], [])
        failure = result["counterexamples"][0]["first_failure"]
        self.assertTrue(failure["detail_truncated"])
        self.assertEqual((failure["phase"], failure["case_index"]), ("examples", 0))

    def test_non_json_outputs_become_serializable_counterexamples(self):
        contract = {"examples": [case([1], {})], "checks": [case([2], {})]}
        for output in ({(1, 2): 3}, {1: "numeric key"}, float("inf"), float("nan")):
            row = observe(lambda value: output, contract, "identity")
            self.assertEqual(row["examples_passed"], 0)
            self.assertEqual(row["first_failure"]["error_type"], "ValueError")
            json.dumps(row, allow_nan=False)

    def test_finds_hidden_behavior_with_representation_adapter(self):
        plan = prepare_behavior_search(snapshot(OWN_CODE), [mask_contract()])
        result = assess_behavior_search(plan, execute_authored_fixture(plan))
        matches = result["matches"]
        self.assertTrue(matches)
        self.assertTrue(all(m["recipe"].endswith("halfopen") for m in matches))
        self.assertTrue(all(m["checks_passed"] == 2 for m in matches))
        self.assertTrue(all(m["ablation_passed"] < 3 for m in matches))
        self.assertTrue(all(not m["qualified"] and not m["target_integrated"] for m in matches))

    def test_runtime_conflict_and_unknown_survive_behavioral_success(self):
        for runtime, expected in (("javascript", "runtime_blocked"), ("unknown", "runtime_unknown")):
            plan = prepare_behavior_search(snapshot(OWN_CODE), [mask_contract(runtime)])
            result = assess_behavior_search(plan, execute_authored_fixture(plan))
            self.assertTrue(result["matches"])
            self.assertEqual({m["disposition"] for m in result["matches"]}, {expected})
            with self.assertRaises(ValueError):
                prepare_behavior_bridge(plan, result["matches"][0])

    def test_export_preserves_original_computation_and_exposes_new_conversion(self):
        plan = prepare_behavior_search(snapshot(OWN_CODE), [mask_contract()])
        result = assess_behavior_search(plan, execute_authored_fixture(plan))
        match = next(m for m in result["matches"] if m["recipe"] == "mask_one_halfopen")
        proposal = prepare_behavior_bridge(plan, match)
        self.assertIn(OWN_CODE, proposal["files"]["project/extracted.py"])
        self.assertIn("operation(universe, selected)", proposal["files"]["bridge/reuse.py"])
        self.assertNotIn("active", proposal["files"]["bridge/reuse.py"])
        self.assertFalse(proposal["target_integrated"])

    def test_heldout_counterexample_does_not_retrain_or_pass(self):
        contract = mask_contract()
        contract["checks"][0]["expected"] = [[0, 99]]
        plan = prepare_behavior_search(snapshot(OWN_CODE), [contract])
        result = assess_behavior_search(plan, execute_authored_fixture(plan))
        self.assertEqual(result["matches"], [])
        self.assertTrue(any(c["first_failure"]["phase"] == "checks" for c in result["counterexamples"]))

    def test_export_replays_noisy_generators_and_preserves_strict_example_types(self):
        contract = {"id": "iterator", "kind": "synthetic_control", "input_kind": "arguments",
                    "runtime": "python", "examples": [case([0], [1])], "checks": [case([1], [2])]}
        plan = prepare_behavior_search(snapshot(OWN_NOISY), [contract])
        result = assess_behavior_search(plan, execute_authored_fixture(plan))
        proposal = prepare_behavior_bridge(plan, result["matches"][0])
        # Only the explicitly authored generator and our exported adapter/check
        # execute on the host. Acquired source fixtures remain data.
        self.assertEqual(plan["candidates"][0]["evidence"]["quote"], OWN_NOISY)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for path, content in proposal["files"].items():
                destination = root / path
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(content, encoding="utf-8")
            launcher = ("import runpy,sys; from pathlib import Path; p=Path(sys.argv[1]); "
                        "sys.path[:0]=[str(p/'project'),str(p/'bridge'),str(p/'reviewed_tests')]; "
                        "runpy.run_path(str(p/'reviewed_tests'/'verify.py'),run_name='__main__')")
            replay = subprocess.run([sys.executable, "-I", "-c", launcher, str(root)],
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(replay.returncode, 0, replay.stderr)
            self.assertEqual(replay.stderr, "")
            self.assertLessEqual(len(replay.stdout.encode("utf-8")), MAX_OUTPUT)
            self.assertEqual(json.loads(replay.stdout)["passed"], 2)
            self.assertGreater(json.loads(replay.stdout)["discarded_output_chars"]["stdout"], MAX_OUTPUT)
            check_path = root / proposal["entrypoint"]
            check_path.write_text(check_path.read_text(encoding="utf-8").replace(
                "'expected': [1]", "'expected': [True]"), encoding="utf-8")
            replay = subprocess.run([sys.executable, "-I", "-c", launcher, str(root)],
                                    capture_output=True, text=True, timeout=10)
            self.assertNotEqual(replay.returncode, 0)
            self.assertIn("AssertionError", replay.stderr)

    def test_similar_range_words_do_not_make_interval_union_match(self):
        contract = {"id": "ranges", "input_kind": "arguments", "kind": "synthetic_control", "runtime": "python",
                    "examples": [case([[[1,5],[4,9]], [[1,5],[4,9]]], [[1,9]])],
                    "checks": [case([[[1,3]], [[1,3]]], [[1,3]])]}
        plan = prepare_behavior_search(snapshot(OWN_CODE), [contract])
        result = assess_behavior_search(plan, execute_authored_fixture(plan))
        self.assertEqual(result["matches"], [])
        self.assertTrue(result["counterexamples"])

    def test_mutation_fails_even_if_output_matches(self):
        def mutating(values):
            values.sort()
            return values
        contract = {"examples": [case([[2,1]], [1,2])], "checks": [case([[3,1]], [1,3])]}
        observed = observe(mutating, contract, "identity")
        self.assertEqual(observed["examples_passed"], 0)
        self.assertTrue(observed["mutated_input"])

    def test_json_boolean_and_number_are_not_equivalent(self):
        observed = observe(lambda x: 1, {"examples": [case([0], True)], "checks": [case([0], True)]}, "identity")
        self.assertEqual(observed["examples_passed"], 0)

    def test_identity_only_has_no_source_contribution(self):
        contract = mask_contract()
        contract.update(input_kind="arguments", examples=[case([[1]], [1])], checks=[case([[2]], [2])])
        row = observe(lambda x: x, contract, "identity")
        self.assertEqual(row["ablation_passed"], 2)

    def test_invalid_or_unavailable_isolation_cannot_create_results(self):
        plan = prepare_behavior_search(snapshot(OWN_CODE), [mask_contract()])
        self.assertEqual(assess_behavior_search(plan, {"status": "timeout"})["status"], "not_evaluated")
        result = execute_authored_fixture(plan)
        result["artifact_sha256"] = {}
        with self.assertRaises(ValueError):
            assess_behavior_search(plan, result)

    def test_missing_observations_remain_unobserved(self):
        plan = prepare_behavior_search(snapshot(OWN_CODE), [mask_contract()])
        execution = execute_authored_fixture(plan)
        document = json.loads(execution["stdout"])
        document["bindings"] = []
        execution["stdout"] = json.dumps(document)
        result = assess_behavior_search(plan, execution)
        self.assertEqual(result["matches"], [])
        self.assertTrue(result["unobserved_bindings"])

    def test_public_problem_quote_and_holdout_are_required(self):
        contract = mask_contract()
        contract.update(kind="public_demand", evidence={"url":"https://github.com/a/b/issues/1", "body":"actual", "quote":"invented"})
        with self.assertRaises(ValueError):
            prepare_behavior_search(snapshot(OWN_CODE), [contract])
        contract = mask_contract()
        contract["checks"] = []
        with self.assertRaises(ValueError):
            prepare_behavior_search(snapshot(OWN_CODE), [contract])

    def test_plan_does_not_mutate_snapshot_or_contracts(self):
        repo, contracts = snapshot(OWN_CODE), [mask_contract()]
        original = copy.deepcopy((repo, contracts))
        prepare_behavior_search(repo, contracts)
        self.assertEqual((repo, contracts), original)


if __name__ == "__main__":
    unittest.main()
