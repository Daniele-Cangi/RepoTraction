"""Frozen case-specific checks, not an experiment/agent/API runner.

Set ML_CYCLE_TARGET to an isolated pinned target directory. ML_CYCLE_MODE is
`candidate` (default) or `reference` (original enumeration plus public filter).
Run with pytest for correctness. Import `workloads`, `observe`, `batch` for
the final sequential timing comparison described in acceptance.md.
"""
import hashlib
import itertools
import json
import os
from pathlib import Path
import random
import sys
import time

import pytest

TARGET = Path(os.environ["ML_CYCLE_TARGET"]).resolve()
sys.path.insert(0, str(TARGET))
import networkx as nx  # noqa: E402

assert Path(nx.__file__).resolve().parent == TARGET / "networkx"
MODE = os.environ.get("ML_CYCLE_MODE", "candidate")
assert MODE in {"reference", "candidate"}


def selected(G, lower=0, upper=None):
    if MODE == "reference":
        if lower < 0:
            raise ValueError("negative experimental lower bound")
        return (c for c in nx.simple_cycles(G, length_bound=upper) if len(c) >= lower)
    return nx.simple_cycles(G, length_bound=upper, min_length=lower)


def canonical(cycle, G):
    ranks = dict(zip(G, range(len(G))))
    seq = tuple(ranks[v] for v in cycle)
    variants = [seq[i:] + seq[:i] for i in range(len(seq))]
    if not G.is_directed():
        rev = seq[::-1]
        variants += [rev[i:] + rev[:i] for i in range(len(rev))]
    return min(variants)


def brute_cycles(G, lower, upper):
    """Independent bounded permutation oracle; only small correctness fixtures."""
    result = set()
    for size in range(max(1, lower), min(len(G), upper or len(G)) + 1):
        if upper == 0:
            break
        for nodes in itertools.permutations(G, size):
            if size == 1:
                valid = G.has_edge(nodes[0], nodes[0])
            elif size == 2 and not G.is_directed():
                valid = G.is_multigraph() and G.number_of_edges(*nodes) >= 2
            else:
                valid = all(G.has_edge(u, v) for u, v in
                            zip(nodes, nodes[1:] + nodes[:1]))
            if valid:
                result.add(canonical(nodes, G))
    return result


def check(G, lower, upper):
    before = nx.node_link_data(G, edges="edges")
    cycles = list(selected(G, lower, upper))
    actual = [canonical(c, G) for c in cycles]
    assert len(actual) == len(set(actual)), "duplicate cycles"
    assert set(actual) == brute_cycles(G, lower, upper)
    assert before == nx.node_link_data(G, edges="edges"), "input mutated"


@pytest.mark.parametrize("kind", [nx.Graph, nx.DiGraph, nx.MultiGraph, nx.MultiDiGraph])
def test_seeded_small_graphs(kind):
    for seed in range(12):
        rng = random.Random(8128 + seed)
        G = kind()
        G.add_nodes_from(range(6))
        for u in G:
            for v in G:
                if (G.is_directed() or u <= v) and rng.random() < .3:
                    G.add_edge(u, v)
                    if G.is_multigraph() and rng.random() < .3:
                        G.add_edge(u, v)
        for lower in (0, 1, 2, 3, 5, 7):
            for upper in (None, 0, 2, 4, 6):
                check(G, lower, upper)


@pytest.mark.parametrize("directed,n", [(True, 3), (False, 4)])
def test_all_small_loopless_graphs(directed, n):
    edges = [(u, v) for u in range(n) for v in range(n)
             if u != v and (directed or u < v)]
    for mask in range(1 << len(edges)):
        G = nx.DiGraph() if directed else nx.Graph()
        G.add_nodes_from(range(n))
        G.add_edges_from(e for i, e in enumerate(edges) if mask & (1 << i))
        for lower, upper in ((0, None), (3, None), (3, 3), (n + 1, None)):
            check(G, lower, upper)


@pytest.mark.parametrize("kind", [nx.Graph, nx.DiGraph, nx.MultiGraph, nx.MultiDiGraph])
def test_public_example(kind):
    G = kind([(1, 2), (1, 3), (1, 4), (2, 3), (2, 5), (3, 4),
              (3, 6), (4, 7), (7, 1)])
    for lower in (3, 4):
        check(G, lower, 4)


@pytest.mark.parametrize("kind", [nx.Graph, nx.DiGraph, nx.MultiGraph, nx.MultiDiGraph])
def test_labels_loops_and_compatibility(kind):
    labels = ["a", 1, (2, 3), None]  # None is replaced: NetworkX forbids it.
    labels[-1] = frozenset({4})
    G = kind()
    nx.add_cycle(G, labels)
    G.add_edge("a", "a")
    G.add_edge("a", 1)
    G.add_edge(1, "a")
    G.add_nodes_from(["isolated"])
    for lower in (0, 1, 2, 4, 6):
        for upper in (None, 1, 2, 4):
            check(G, lower, upper)
    for upper in (None, 0, 2, 4):
        assert {canonical(c, G) for c in selected(G, 0, upper)} == {
            canonical(c, G) for c in nx.simple_cycles(G, upper)}
    with pytest.raises(ValueError):
        list(selected(G, -1))


def workloads():
    """Fixed synthetic demand probes; no source-conditioned inputs or tuning."""
    dense_d = nx.complete_graph(9, create_using=nx.DiGraph)
    dense_u = nx.complete_graph(9)
    short_d = nx.DiGraph()
    short_u = nx.Graph()
    for G, size in ((short_d, 6), (short_u, 7)):
        for block in range(20):
            nodes = list(range(block * size, (block + 1) * size))
            G.update(nx.complete_graph(nodes, create_using=type(G)))
            if block:
                G.add_edge(nodes[0], nodes[0] - size)
                if G.is_directed():
                    G.add_edge(nodes[0] - size, nodes[0])
        ring = list(range(1000, 1010))
        nx.add_cycle(G, ring)
        G.add_edge(0, ring[0])
        if G.is_directed():
            G.add_edge(ring[0], 0)
    sparse = nx.gnp_random_graph(16, .10, seed=8128, directed=True)
    return [
        ("dense-directed", dense_d, 8, None, "positive"),
        ("dense-undirected", dense_u, 8, None, "positive"),
        ("short-heavy-directed", short_d, 8, None, "positive"),
        ("short-heavy-undirected", short_u, 8, None, "positive"),
        ("output-rich-directed", nx.complete_graph(8, create_using=nx.DiGraph), 0, None, "control"),
        ("output-rich-undirected", nx.complete_graph(8), 3, 6, "control"),
        ("sparse-directed", sparse, 3, None, "control"),
        ("acyclic", nx.path_graph(2000, create_using=nx.DiGraph), 3, None, "control"),
    ]


def observe(G, lower, upper):
    cycles = [canonical(c, G) for c in selected(G, lower, upper)]
    assert len(cycles) == len(set(cycles))
    encoded = json.dumps(sorted(cycles), separators=(",", ":")).encode()
    return {"count": len(cycles), "sha256": hashlib.sha256(encoded).hexdigest()}


def batch(G, lower, upper, iterations):
    # Build input graphs and verify exact outputs outside the timed interval.
    start = time.perf_counter()
    count = total_length = 0
    for _ in range(iterations):
        for cycle in selected(G, lower, upper):
            count += 1
            total_length += len(cycle)
    return {"seconds": time.perf_counter() - start, "iterations": iterations,
            "count": count, "total_length": total_length}


if __name__ == "__main__":
    # Preparation baseline only; no candidate solving, source search or AI calls.
    assert MODE == "reference", "Use pytest / the documented final comparison for candidates."
    results = []
    for name, graph, lower, upper, role in workloads():
        output = observe(graph, lower, upper)
        warm = batch(graph, lower, upper, 1)
        iterations = min(100, max(1, int(.25 / max(warm["seconds"], 1e-6)) + 1))
        results.append({"name": name, "nodes": len(graph), "edges": graph.number_of_edges(),
                        "lower": lower, "upper": upper, "role": role,
                        "output": output, "warmup": warm,
                        "batch": batch(graph, lower, upper, iterations)})
    print(json.dumps({"mode": MODE, "python": sys.version, "networkx": nx.__version__,
                      "target_revision": "9d866a5f447d9fe1c989b31f90c520dc2813ee26",
                      "workloads": results}, indent=2))
