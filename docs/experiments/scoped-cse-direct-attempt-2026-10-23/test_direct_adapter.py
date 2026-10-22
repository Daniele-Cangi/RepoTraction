"""Run the unchanged frozen contract through the experiment-local compiler."""

import importlib.util
from pathlib import Path
import unittest

import sympy as sy

from scoped_lambdify import scoped_lambdify


fixture_path = Path(__file__).parent.parent / "scoped-cse-obstacle-2026-10-23/test_scope_contract.py"
spec = importlib.util.spec_from_file_location("frozen_scope_contract", fixture_path)
frozen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(frozen)


class _SymPyWithDirectCompiler:
    lambdify = staticmethod(scoped_lambdify)

    def __getattr__(self, name):
        return getattr(sy, name)


frozen.sy = _SymPyWithDirectCompiler()


class DirectScopeContract(frozen.ScopeContract):
    """Inherit the frozen assertions and samples without changing the fixture."""


class AdapterRegressions(unittest.TestCase):
    def test_helper_name_collision(self):
        i, n, value = sy.symbols("i n _scope_sum_0", integer=True)
        expr = sy.Sum(sy.sin(i) + value, (i, 1, n))
        function = scoped_lambdify([n, value], expr, modules="math", cse=True)
        self.assertAlmostEqual(function(2, 3), 6 + sy.sin(1).evalf() + sy.sin(2).evalf())

    def test_disabled_cse_delegates(self):
        i, n = sy.symbols("i n", integer=True)
        function = scoped_lambdify(n, sy.Sum(i, (i, 1, n)), modules="math", cse=False)
        self.assertEqual(function(4), 10)

    def test_reversed_bounds_are_explicitly_unsupported(self):
        i, n = sy.symbols("i n", integer=True)
        function = scoped_lambdify(n, sy.Sum(sy.sin(i), (i, 1, n)), modules="math", cse=True)
        with self.assertRaisesRegex(ValueError, "ascending"):
            function(-2)

    def test_other_backends_are_explicitly_unsupported(self):
        i, n = sy.symbols("i n", integer=True)
        with self.assertRaisesRegex(NotImplementedError, "math backend"):
            scoped_lambdify(n, sy.Sum(i, (i, 1, n)), modules="numpy", cse=True)


if __name__ == "__main__":
    unittest.main()
