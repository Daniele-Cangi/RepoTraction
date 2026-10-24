"""Independent small-graph oracle for the actual NetworkX arborescence API.

These controls preserve documented spanning/optimality/API behavior. They do not
prescribe a faster algorithm or count as evidence of agent assistance.
"""
from copy import deepcopy
from itertools import product
import random
import unittest

import networkx as nx


def edge_records(graph, attr="weight", default=1):
    if graph.is_multigraph():
        return [(u, v, key, data.get(attr, default), data)
                for u, v, key, data in graph.edges(keys=True, data=True)]
    return [(u, v, None, data.get(attr, default), data)
            for u, v, data in graph.edges(data=True)]


def enumerated_optimum(graph, attr="weight", default=1, partition=None):
    """Enumerate parent choices, using no branching solver or greedy rule."""
    nodes = list(graph)
    edges = edge_records(graph, attr, default)
    included = {(u, v, key) for u, v, key, _, data in edges
                if partition and data.get(partition) == nx.EdgePartition.INCLUDED}
    eligible = [(u, v, key, weight) for u, v, key, weight, data in edges
                if u != v and not (partition and data.get(partition) == nx.EdgePartition.EXCLUDED)]
    best = None
    for root in nodes:
        others = [node for node in nodes if node != root]
        choices = [[edge for edge in eligible if edge[1] == node] for node in others]
        for selected in product(*choices):
            if not included.issubset({edge[:3] for edge in selected}):
                continue
            parent = {v: u for u, v, _, _ in selected}
            valid = True
            for node in others:
                seen = set()
                while node != root:
                    if node in seen or node not in parent:
                        valid = False
                        break
                    seen.add(node)
                    node = parent[node]
                if not valid:
                    break
            if valid:
                weight = sum(edge[3] for edge in selected)
                best = weight if best is None else min(best, weight)
    return best


class NativeArborescenceAcceptance(unittest.TestCase):
    def check_optimum(self, graph, *, allow_default_fill=False, **kwargs):
        before = deepcopy((dict(graph.nodes(data=True)), edge_records(graph), graph.graph))
        expected = enumerated_optimum(graph, kwargs.get("attr", "weight"), kwargs.get("default", 1), kwargs.get("partition"))
        if expected is None:
            with self.assertRaises(nx.NetworkXException):
                nx.minimum_spanning_arborescence(graph, **kwargs)
        else:
            answer = nx.minimum_spanning_arborescence(graph, **kwargs)
            self.assertEqual(set(answer), set(graph))
            self.assertTrue(nx.is_arborescence(answer))
            self.assertEqual(answer.number_of_edges(), len(graph) - 1)
            self.assertEqual(nx.tree.branching_weight(answer, kwargs.get("attr", "weight"), kwargs.get("default", 1)), expected)
            original = edge_records(graph, kwargs.get("attr", "weight"), kwargs.get("default", 1))
            for u, v, _, weight, data in edge_records(answer, kwargs.get("attr", "weight"), kwargs.get("default", 1)):
                sources = [edge for edge in original if edge[:2] == (u, v) and edge[3] == weight]
                self.assertTrue(sources)
                if kwargs.get("preserve_attrs"):
                    self.assertTrue(any(all(data.get(k) == val for k, val in edge[4].items()) for edge in sources))
        after = deepcopy((dict(graph.nodes(data=True)), edge_records(graph), graph.graph))
        if allow_default_fill:
            # The existing API fills absent weight attributes with the default.
            # Do not add an unrelated no-mutation requirement to this experiment.
            # Either absent or explicitly default-valued is semantically equivalent;
            # all other edge/node/graph attributes must remain unchanged.
            for snapshot in (before, after):
                for _, _, _, _, data in snapshot[1]:
                    data.setdefault(kwargs["attr"], kwargs["default"])
        self.assertEqual(after, before)

    def test_nested_cycle_choices(self):
        graph = nx.DiGraph()
        graph.add_weighted_edges_from([
            ("root", "a", 10), ("root", "c", 11),
            ("a", "b", 1), ("b", "a", 1), ("c", "d", 1), ("d", "c", 1),
            ("b", "c", 2), ("d", "a", 2), ("a", "a", -100),
        ])
        self.check_optimum(graph)

    def test_seeded_small_graphs(self):
        for seed in range(12):
            with self.subTest(seed=seed):
                rng = random.Random(4000 + seed)
                n = 4 + seed % 2
                graph = nx.DiGraph()
                graph.add_nodes_from(range(n))
                for u in range(n):
                    for v in range(n):
                        if u != v and (v == (u + 1) % n or rng.random() < 0.6):
                            graph.add_edge(u, v, weight=rng.randrange(-7, 15))
                self.check_optimum(graph)

    def test_parallel_edges_and_mixed_labels(self):
        graph = nx.MultiDiGraph()
        a, b, c = 0, "b", (2, "c")
        graph.add_edge(a, b, weight=9, label="expensive")
        graph.add_edge(a, b, weight=-3, label="cheap")
        graph.add_edge(b, c, weight=2, label="tail")
        graph.add_edge(c, b, weight=-2, label="cycle")
        graph.add_edge(a, c, weight=4, label="alternative")
        graph.add_edge(c, c, weight=-100, label="self")
        self.check_optimum(graph, preserve_attrs=True)

    def test_custom_weight_and_missing_default(self):
        graph = nx.DiGraph()
        graph.add_edge(0, 1, label="default")
        graph.add_edge(0, 2, cost=2, label="explicit")
        graph.add_edge(1, 2, cost=8, label="alternative")
        self.check_optimum(graph, attr="cost", default=3, preserve_attrs=True, allow_default_fill=True)

    def test_partition_constraints(self):
        graph = nx.DiGraph()
        graph.add_edge(0, 1, weight=1)
        graph.add_edge(0, 2, weight=2)
        graph.add_edge(2, 1, weight=7, state=nx.EdgePartition.INCLUDED)
        graph.add_edge(1, 2, weight=-8, state=nx.EdgePartition.EXCLUDED)
        self.check_optimum(graph, partition="state", preserve_attrs=True)

    def test_no_spanning_solution(self):
        graph = nx.DiGraph()
        graph.add_weighted_edges_from([(0, 1, 1), (2, 3, 1)])
        self.check_optimum(graph)

    def test_tied_weights_and_singleton(self):
        graph = nx.DiGraph()
        graph.add_weighted_edges_from([(0, 1, 0), (1, 0, 0), (0, 2, 0), (1, 2, 0)])
        self.check_optimum(graph)
        graph = nx.DiGraph()
        graph.add_node("only")
        self.check_optimum(graph)


if __name__ == "__main__":
    unittest.main(verbosity=2)
