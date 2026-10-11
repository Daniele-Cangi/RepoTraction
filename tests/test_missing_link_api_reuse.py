"""Only locally authored packages execute on the host; downloaded code is data."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from missing_link.behavioral import prepare_behavior_search, assess_behavior_search, prepare_behavior_bridge


OWN_PACKAGE = {
    "labpkg/__init__.py": "# Authored fixture, not acquired source.\n",
    "labpkg/base.py": '''class Base:
    def __init__(self, values):
        self.values = values

    def pick(self, index):
        return self.values[index]

    def mutate(self, index):
        return self.values.pop(index)

    @property
    def size(self):
        return len(self.values)
''',
    "labpkg/api.py": '''from .base import Base

HISTORY = []

class Opaque(Base):
    @classmethod
    def build(cls, values):
        return cls(values)

def stateful(value):
    HISTORY.append(value)
    return len(HISTORY)

def boolean(value):
    return True
''',
}


def snapshot(files=None):
    return {"full_name": "example/fixture", "revision": "a" * 40, "public": True,
            "files": [{"path": path, "text": text} for path, text in (files or OWN_PACKAGE).items()]}


def contract(identity="pick"):
    return {"id": identity, "kind": "synthetic_control", "input_kind": "arguments", "runtime": "python",
            "examples": [{"args": [["a", "b"], 1], "expected": "b"}],
            "checks": [{"args": [["z", "y", "x"], 0], "expected": "z"},
                       {"args": [["z", "y", "x"], -1], "expected": "x"}]}


def execute_authored(plan):
    if plan.get("package_files") != {"project/" + p: v for p, v in OWN_PACKAGE.items()}:
        raise AssertionError("Only the exact authored fixture may execute on the host.")
    return execute_authored_files(plan["files"], plan["entrypoint"], plan["artifact_sha256"])


def execute_authored_files(files, entrypoint, hashes=None):
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        for path, text in files.items():
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text.replace("/sandbox/work/", root.as_posix() + "/"), encoding="utf-8")
        launcher = ("import sys,runpy; from pathlib import Path; root=Path(sys.argv[1]); "
                    "sys.path[:0]=[str(root/'project'),str(root/'bridge'),str(root/'reviewed_tests')]; "
                    "runpy.run_path(str(root/sys.argv[2]),run_name='__main__')")
        process = subprocess.run([sys.executable, "-I", "-c", launcher, directory, entrypoint],
                                 capture_output=True, text=True, timeout=10)
        if process.returncode:
            raise AssertionError(process.stderr)
        return {"status": "exited_successfully", "context": "isolated_wasi_example",
                "artifact_sha256": hashes, "stdout": process.stdout}


class PackageReuseTests(unittest.TestCase):
    def test_finds_constructor_and_factory_inherited_method_without_name_scoring(self):
        plan = prepare_behavior_search(snapshot(), [contract()], package_root="labpkg")
        result = assess_behavior_search(plan, execute_authored(plan))
        found = {match["entrypoint"] for match in result["matches"]}
        self.assertIn("labpkg.api:Opaque.build[1].pick", found)
        self.assertIn("labpkg.api:Opaque.__init__[1].pick", found)
        self.assertFalse(any("mutate" in name for name in found))
        self.assertEqual(result["unobserved_bindings"], [])
        self.assertTrue(all(m["source_scope"] == "imported_pinned_package_api" for m in result["matches"]))
        self.assertTrue(all(not m["qualified"] and not m["target_integrated"] for m in result["matches"]))
        candidate = next(c for c in plan["candidates"] if c["entrypoint"] == "labpkg.api:Opaque.build[1].pick")
        self.assertEqual(candidate["evidence"]["path"], "labpkg/base.py")
        self.assertEqual(candidate["dependencies"][0]["path"], "labpkg/api.py")

    def test_complete_package_export_replays_the_observed_binding(self):
        plan = prepare_behavior_search(snapshot(), [contract()], package_root="labpkg")
        match = next(m for m in assess_behavior_search(plan, execute_authored(plan))["matches"]
                     if m["entrypoint"] == "labpkg.api:Opaque.build[1].pick")
        bridge = prepare_behavior_bridge(plan, match)
        self.assertEqual(bridge["kind"], "package_api")
        self.assertEqual(bridge["api_binding"]["factory"], "build")
        self.assertEqual(bridge["files"]["project/labpkg/base.py"], OWN_PACKAGE["labpkg/base.py"])
        output = execute_authored_files(bridge["files"], bridge["entrypoint"])
        self.assertEqual(json.loads(output["stdout"])["passed"], 3)
        self.assertFalse(bridge["qualified"])

    def test_property_binding_and_strict_bool_negative(self):
        spec = {**contract(), "examples": [{"args": [[8, 9]], "expected": 2}],
                "checks": [{"args": [[]], "expected": 0}]}
        plan = prepare_behavior_search(snapshot(), [spec], package_root="labpkg")
        result = assess_behavior_search(plan, execute_authored(plan))
        self.assertTrue(any(m["entrypoint"].endswith(".size") for m in result["matches"]))
        spec.update(examples=[{"args": [9], "expected": 1}], checks=[{"args": [8], "expected": 1}])
        plan = prepare_behavior_search(snapshot(), [spec], package_root="labpkg")
        result = assess_behavior_search(plan, execute_authored(plan))
        self.assertFalse(any(m["entrypoint"].endswith(":boolean") for m in result["matches"]))

    def test_shared_import_state_is_explicit_and_fresh_export_can_reject_warm_match(self):
        cold = {**contract("cold"), "examples": [{"args": [0], "expected": 1}],
                "checks": [{"args": [0], "expected": 2}]}
        warm = {**cold, "id": "warm", "examples": [{"args": [0], "expected": 3}],
                "checks": [{"args": [0], "expected": 4}]}
        plan = prepare_behavior_search(snapshot(), [cold, warm], package_root="labpkg")
        result = assess_behavior_search(plan, execute_authored(plan))
        warm_match = next(m for m in result["matches"]
                          if m["entrypoint"] == "labpkg.api:stateful" and m["contract_id"] == "warm")
        self.assertTrue(warm_match["independent_replay_required"])
        self.assertFalse(warm_match["qualified"])
        self.assertTrue(any("share package state" in text for text in plan["limitations"]))
        bridge = prepare_behavior_bridge(plan, warm_match)
        with self.assertRaisesRegex(AssertionError, "AssertionError"):
            execute_authored_files(bridge["files"], bridge["entrypoint"])

    def test_counterexample_and_runtime_block_are_not_promoted(self):
        spec = contract()
        spec["checks"][0]["expected"] = "not the requested index"
        plan = prepare_behavior_search(snapshot(), [spec], package_root="labpkg")
        self.assertEqual(assess_behavior_search(plan, execute_authored(plan))["matches"], [])
        spec = {**contract(), "runtime": "javascript"}
        plan = prepare_behavior_search(snapshot(), [spec], package_root="labpkg")
        matches = assess_behavior_search(plan, execute_authored(plan))["matches"]
        self.assertTrue(matches)
        self.assertEqual({m["disposition"] for m in matches}, {"runtime_blocked"})
        with self.assertRaises(ValueError):
            prepare_behavior_bridge(plan, matches[0])

    def test_default_extraction_remains_opt_in_and_inputs_unchanged(self):
        repo, specs = snapshot(), [contract()]
        before = copy.deepcopy((repo, specs))
        legacy = prepare_behavior_search(repo, specs)
        self.assertNotIn("package_files", legacy)
        self.assertFalse(any("Opaque" in c["entrypoint"] for c in legacy["candidates"]))
        prepare_behavior_search(repo, specs, package_root="labpkg")
        self.assertEqual((repo, specs), before)

    def test_indexing_initializer_does_not_execute_and_overloads_are_not_duplicates(self):
        files = {"labpkg/__init__.py": "raise AssertionError('host must not execute')\n",
                 "labpkg/api.py": "from typing import overload\n@overload\ndef f(x): ...\ndef f(x): return x+1\n"}
        spec = {**contract(), "examples": [{"args": [0], "expected": 1}],
                "checks": [{"args": [1], "expected": 2}]}
        plan = prepare_behavior_search(snapshot(files), [spec], package_root="labpkg")
        self.assertEqual(len(plan["candidates"]), 1)
        self.assertEqual(plan["candidates"][0]["evidence"]["line"], 4)

    def test_rejects_incomplete_unsafe_or_changed_code_instead_of_silently_truncating(self):
        for field, value in (("truncated", True), ("reference_truncated", True), ("mode", "120000"),
                             ("text", "# " + "x" * 262145), ("text", "# sk-" + "a" * 32),
                             ("text", "\x00")):
            repo = snapshot()
            repo["files"][1][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                prepare_behavior_search(repo, [contract()], package_root="labpkg")
        for field, value in (("public", False), ("revision", "main")):
            repo = snapshot()
            repo[field] = value
            with self.assertRaises(ValueError):
                prepare_behavior_search(repo, [contract()], package_root="labpkg")
        with self.assertRaises(ValueError):
            prepare_behavior_search(snapshot({"labpkg/api.py": ""}), [contract()], package_root="labpkg")

    def test_paths_cannot_shadow_runtime_or_collide_portably(self):
        for root in ("json", "behavior_examples", "../labpkg", "lab-pkg"):
            with self.assertRaises(ValueError):
                prepare_behavior_search(snapshot(), [contract()], package_root=root)
        for path in ("labpkg/API.py", "labpkg/api/__init__.py"):
            repo = snapshot({**OWN_PACKAGE, path: ""})
            with self.assertRaises(ValueError):
                prepare_behavior_search(repo, [contract()], package_root="labpkg")

    def test_package_and_wrappers_share_existing_artifact_limits(self):
        files = {**OWN_PACKAGE, **{f"labpkg/helper{i}.py": "" for i in range(57)}}
        plan = prepare_behavior_search(snapshot(files), [contract()], package_root="labpkg")
        self.assertLessEqual(len(plan["files"]), 64)
        self.assertEqual(len(plan["candidates"]), 3)
        self.assertTrue(plan["omissions"])
        self.assertLessEqual(sum(len(v.encode()) for v in plan["files"].values()), 2000000)
        for extra in (1, 2):
            oversized = {**files, **{f"labpkg/extra{i}.py": "" for i in range(extra)}}
            with self.assertRaisesRegex(ValueError, "artifact bounds"):
                prepare_behavior_search(snapshot(oversized), [contract()], package_root="labpkg")

    def test_ambiguous_diamond_and_its_descendants_are_omitted(self):
        source = '''class A:
    def f(self, x, y): return "A"
class B(A): pass
class C(A):
    def f(self, x, y): return "C"
class D(B, C): pass
class E(D): pass
'''
        plan = prepare_behavior_search(snapshot({"labpkg/__init__.py": source}), [contract()], package_root="labpkg")
        self.assertTrue(any(":C." in c["entrypoint"] for c in plan["candidates"]))
        self.assertFalse(any(":D." in c["entrypoint"] or ":E." in c["entrypoint"] for c in plan["candidates"]))
        self.assertEqual({o["symbol"] for o in plan["omissions"]}, {"D", "E"})

    def test_module_and_member_rebinding_cannot_cite_an_earlier_definition(self):
        source = '''class Claimed:
    def f(self, x, y): return "claimed"
class Actual:
    def f(self, x, y): return "actual"
Claimed = Actual
def f(x, y): return "first"
from elsewhere import f
class Member:
    def f(self, x, y): return "first"
    f = Actual.f
class Conditional:
    def f(self, x, y): return "first"
if True:
    Conditional = Actual
class Child(Claimed): pass
'''
        plan = prepare_behavior_search(snapshot({"labpkg/__init__.py": source}), [contract()], package_root="labpkg")
        entries = [c["entrypoint"] for c in plan["candidates"]]
        self.assertEqual(entries, ["labpkg:Actual.__init__[0].f"])
        self.assertEqual({o["symbol"] for o in plan["omissions"]}, {"Claimed", "f", "Conditional", "Child"})

    def test_runtime_replacements_cannot_claim_the_original_function_or_member(self):
        source = '''def replace(fn):
    return lambda *args: args[0][args[1]]
@replace
def claimed(values, index):
    return "never executed"
class Actual:
    def pick(self, values, index): return values[index]
class Claimed:
    @classmethod
    def build(cls): return Actual()
    def pick(self, values, index): return "never executed"
class Dynamic:
    def __init__(self): self.pick = Actual().pick
    def pick(self, values, index): return "never executed"
'''
        plan = prepare_behavior_search(snapshot({"labpkg/__init__.py": source}), [contract()], package_root="labpkg")
        execution = execute_authored_files(plan["files"], plan["entrypoint"], plan["artifact_sha256"])
        result = assess_behavior_search(plan, execution)
        self.assertEqual([m["entrypoint"] for m in result["matches"]], ["labpkg:Actual.__init__[0].pick"])
        self.assertTrue(any(c["first_failure"].get("error_type") == "ValueError" for c in result["counterexamples"]))

    def test_provenance_preserving_decorator_keeps_the_original_code_location(self):
        source = '''def annotate(fn):
    fn.documented = True
    return fn
@annotate
def original(values, index): return values[index]
'''
        plan = prepare_behavior_search(snapshot({"labpkg/__init__.py": source}), [contract()], package_root="labpkg")
        execution = execute_authored_files(plan["files"], plan["entrypoint"], plan["artifact_sha256"])
        self.assertEqual([m["entrypoint"] for m in assess_behavior_search(plan, execution)["matches"]], ["labpkg:original"])

    def test_replay_byte_budget_is_reserved_before_search(self):
        files = {"labpkg/__init__.py": "def f(x, y): return x+y\n"}
        files.update({f"labpkg/large{i}.py": "#" + "x" * 198900 + "\n" for i in range(10)})
        with self.assertRaisesRegex(ValueError, "artifact bounds"):
            prepare_behavior_search(snapshot(files), [contract()], package_root="labpkg")

    def test_package_directory_and_same_stem_wrapper_file_can_coexist(self):
        source = {"candidate_0/__init__.py": "def pick(values, index): return values[index]\n"}
        plan = prepare_behavior_search(snapshot(source), [contract()], package_root="candidate_0")
        self.assertIn("project/candidate_0.py", plan["files"])
        self.assertIn("project/candidate_0/__init__.py", plan["files"])
        # These are different basenames, not a file/directory prefix collision.
        paths = list(plan["files"])
        self.assertFalse(any(a.startswith(b + "/") for a in paths for b in paths if a != b))
        execution = execute_authored_files(plan["files"], plan["entrypoint"], plan["artifact_sha256"])
        self.assertEqual(len(assess_behavior_search(plan, execution)["matches"]), 1)

    def test_decorated_classes_and_descendants_abstain_before_construction(self):
        source = '''def replace(cls):
    class Different(cls):
        def __new__(kind):
            value = object.__new__(kind)
            value.values = ["replacement"]
            return value
    return Different
@replace
class Claimed:
    def pick(self, values, index): return self.values[index]
class Child(Claimed): pass
'''
        plan = prepare_behavior_search(snapshot({"labpkg/__init__.py": source}), [contract()], package_root="labpkg")
        self.assertEqual(plan["candidates"], [])
        self.assertEqual({o["symbol"] for o in plan["omissions"]}, {"Claimed", "Child"})

    def test_same_class_delegation_is_outside_this_instance_composition_grammar(self):
        source = '''class Engine:
    def __init__(self, values):
        self.values = ["not the requested values"]
        other = object.__new__(type(self))
        other.values = values
        self.pick = other.pick
    def pick(self, index): return self.values[index]
'''
        plan = prepare_behavior_search(snapshot({"labpkg/__init__.py": source}), [contract()], package_root="labpkg")
        execution = execute_authored_files(plan["files"], plan["entrypoint"], plan["artifact_sha256"])
        result = assess_behavior_search(plan, execution)
        self.assertEqual(result["matches"], [])
        self.assertTrue(any(c["first_failure"].get("error_type") == "ValueError" for c in result["counterexamples"]))
        factory = '''class Engine:
    @classmethod
    def build(cls, values):
        result = Engine()
        result.values = values
        return result
    def pick(self, index): return self.values[index]
class Other(Engine): pass
Engine.build = Other.build
'''
        plan = prepare_behavior_search(snapshot({"labpkg/__init__.py": factory}), [contract()], package_root="labpkg")
        execution = execute_authored_files(plan["files"], plan["entrypoint"], plan["artifact_sha256"])
        self.assertEqual(assess_behavior_search(plan, execution)["matches"], [])

    def test_reexported_decorated_ancestor_and_unknown_base_abstain(self):
        files = {"labpkg/__init__.py": "",
                 "labpkg/base.py": "def decorate(cls): return cls\n@decorate\nclass Base: pass\n",
                 "labpkg/alias.py": "from .base import Base as Export\n",
                 "labpkg/api.py": "from .alias import Export\nclass Child(Export):\n    def pick(self, x, y): return x[y]\n"}
        plan = prepare_behavior_search(snapshot(files), [contract()], package_root="labpkg")
        self.assertFalse(any(":Child." in c["entrypoint"] for c in plan["candidates"]))
        self.assertTrue(any(o.get("symbol") == "Child" and "Decorated" in o["reason"] for o in plan["omissions"]))
        files["labpkg/api.py"] = "from external import Unknown\nclass Child(Unknown):\n    def pick(self, x, y): return x[y]\n"
        plan = prepare_behavior_search(snapshot(files), [contract()], package_root="labpkg")
        self.assertFalse(any(":Child." in c["entrypoint"] for c in plan["candidates"]))
        self.assertTrue(any(o.get("symbol") == "Child" and "Unresolved" in o["reason"] for o in plan["omissions"]))

    def test_known_reexports_and_unshadowed_standard_generic_base_are_resolved(self):
        files = {"labpkg/__init__.py": "",
                 "labpkg/base.py": "class Base(object):\n    def pick(self, values, index): return values[index]\n",
                 "labpkg/alias.py": "from .base import Base as Export\n",
                 "labpkg/api.py": "from .alias import Export\nclass Child(Export): pass\n"}
        plan = prepare_behavior_search(snapshot(files), [contract()], package_root="labpkg")
        child = next(c for c in plan["candidates"] if ":Child." in c["entrypoint"])
        self.assertEqual(child["evidence"]["path"], "labpkg/base.py")
        files["labpkg/api.py"] = "from typing import Generic, TypeVar\nT = TypeVar('T')\nclass Child(Generic[T]):\n    def pick(self, values, index): return values[index]\n"
        plan = prepare_behavior_search(snapshot(files), [contract()], package_root="labpkg")
        self.assertTrue(any(":Child." in c["entrypoint"] for c in plan["candidates"]))
        files["labpkg/api.py"] = "object = external()\nclass Child(object):\n    def pick(self, values, index): return values[index]\n"
        plan = prepare_behavior_search(snapshot(files), [contract()], package_root="labpkg")
        self.assertFalse(any(":Child." in c["entrypoint"] for c in plan["candidates"]))


if __name__ == "__main__":
    unittest.main()
