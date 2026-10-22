"""Native SymPy contract fixture; run against the pinned target, not RepoTraction CI."""
import math
import unittest

import sympy as sy


class ScopeContract(unittest.TestCase):
    cse_policy = True

    def check(self, args, expr, samples):
        calls = []

        def counted_sin(value):
            calls.append(value)
            return math.sin(value)

        function = sy.lambdify(args, expr, modules=[{"sin": counted_sin}, "math"],
                              cse=type(self).cse_policy)
        for values, expected, maximum in samples:
            with self.subTest(values=values):
                calls.clear()
                actual = function(*values)
                if isinstance(expected, list):
                    self.assertIsInstance(actual, list)
                else:
                    self.assertNotIsInstance(actual, (list, tuple))
                actual = actual if isinstance(actual, (list, tuple)) else [actual]
                expected = expected if isinstance(expected, (list, tuple)) else [expected]
                self.assertEqual(len(actual), len(expected))
                for left, right in zip(actual, expected):
                    self.assertTrue(math.isclose(left, right, rel_tol=1e-12, abs_tol=1e-12),
                                    (actual, expected))
                if getattr(type(self), "check_work", True):
                    self.assertLessEqual(len(calls), maximum,
                                         "Correct value, but repeated sine work remains")

    def test_reported_sum(self):
        x, e, n, i, _, _ = symbols()
        expr = sy.Sum(term(sy.Indexed("x", i), e), (i, 1, n))
        samples = []
        for data, epsilon, length in (([5, 6, 7, 8, 9], .01, 4),
                                     ([.2, .7, 1.9, 3.1, 5.8, 7.6, 9.2], .07, 1),
                                     ([.2, .7, 1.9, 3.1, 5.8, 7.6, 9.2], .07, 6)):
            samples.append(((data, epsilon, length),
                            sum(numeric(v, epsilon) for v in data[1:length + 1]), length))
        self.check([x, e, n], expr, samples)

    def test_independent_sums_same_index_name(self):
        x, e, n, i, y, m = symbols()
        expr = sy.Sum(term(sy.Indexed("x", i), e), (i, 1, n)) + sy.Sum(
            term(sy.Indexed("y", i), e), (i, 1, m))
        a, b = [.2, .7, 1.9, 3.1, 5.8], [.3, .6, 1.3, 2.8, 4.9]
        samples = [((a, b, .03, k, length),
                    sum(numeric(v, .03) for v in a[1:k + 1]) +
                    sum(numeric(v, .03) for v in b[1:length + 1]), k + length)
                   for k, length in ((4, 2), (1, 4))]
        self.check([x, y, e, n, m], expr, samples)

    def test_nested_dependent_bounds(self):
        x, e, n, i, y, _ = symbols()
        j = sy.Symbol("j", integer=True)
        value = sy.Indexed("x", i) + sy.Indexed("y", j)
        expr = sy.Sum(term(value, e), (j, 1, i), (i, 1, n))
        a, b = [.2, .7, 1.9, 3.1, 5.8], [.3, .6, 1.3, 2.8, 4.9]
        samples = [((a, b, .02, length),
                    sum(numeric(a[k] + b[l], .02)
                        for k in range(1, length + 1) for l in range(1, k + 1)),
                    length * (length + 1) // 2) for length in (2, 4)]
        self.check([x, y, e, n], expr, samples)

    def test_loop_invariant_shared_work(self):
        x, e, n, i, _, _ = symbols()
        z = sy.Symbol("z", real=True)
        summed = sy.Sum(term(sy.Indexed("x", i), e), (i, 1, n))
        expr = [summed + sy.sin(z), sy.sin(z)**2]
        data = [.2, .7, 1.9, 3.1, 5.8]
        samples = [((data, .04, length, zvalue),
                    [sum(numeric(v, .04) for v in data[1:length + 1]) + math.sin(zvalue),
                     math.sin(zvalue)**2], length + 1)
                   for length, zvalue in ((2, .7), (4, 1.3))]
        self.check([x, e, n, z], expr, samples)

    def test_symbol_free_outside_and_bound_inside(self):
        _, _, n, i, _, _ = symbols()
        value = sy.sin(i) + sy.sin(i)**2
        expr = [value, sy.Sum(value, (i, 1, n))]
        samples = [((free_i, length),
                    [math.sin(free_i) + math.sin(free_i)**2,
                     sum(math.sin(k) + math.sin(k)**2 for k in range(1, length + 1))],
                    length + 1) for free_i, length in ((2, 4), (5, 2))]
        self.check([i, n], expr, samples)

    def test_existing_cse_without_sum(self):
        z = sy.Symbol("z", real=True)
        expr = [sy.sin(z) + z, sy.sin(z)**2 + 2*z]
        samples = [((v,), [math.sin(v) + v, math.sin(v)**2 + 2*v], 1)
                   for v in (.7, 1.3)]
        self.check([z], expr, samples)


def symbols():
    return (sy.Symbol("x", real=True), sy.Symbol("e", positive=True, real=True),
            sy.Symbol("n", positive=True, integer=True), sy.Symbol("i", integer=True),
            sy.Symbol("y", real=True), sy.Symbol("m", positive=True, integer=True))


def term(value, epsilon):
    return value + epsilon*sy.sin(value) + (epsilon*sy.sin(value))**2


def numeric(value, epsilon):
    return value + epsilon*math.sin(value) + (epsilon*math.sin(value))**2


if __name__ == "__main__":
    unittest.main()
