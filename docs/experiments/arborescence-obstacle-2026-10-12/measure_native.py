"""Bounded synthetic matrix-shaped observation of the actual pinned NetworkX API."""
import hashlib
import json
import platform
import random
import sys
import time

import networkx as nx

n = int(sys.argv[1])
seed = int(sys.argv[2]) if len(sys.argv) > 2 else 20261012
rng = random.Random(seed)
graph = nx.DiGraph()
graph.add_nodes_from(range(n))
for u in range(n):
    for v in range(n):
        if u != v:
            graph.add_edge(u, v, weight=rng.randrange(1, 1000001))

def signature():
    return hashlib.sha256(json.dumps(list(graph.edges(data="weight")), separators=(",", ":")).encode()).hexdigest()

before = signature()
wall = time.perf_counter()
cpu = time.process_time()
answer = nx.minimum_spanning_arborescence(graph)
cpu = time.process_time() - cpu
wall = time.perf_counter() - wall
assert nx.is_arborescence(answer)
assert set(answer) == set(graph)
assert signature() == before
print(json.dumps({
    "nodes": n, "edges": graph.number_of_edges(), "seed": seed,
    "graph_sha256": before, "algorithm_wall_seconds": wall,
    "algorithm_cpu_seconds": cpu, "weight": nx.tree.branching_weight(answer),
    "answer_edges": answer.number_of_edges(), "is_spanning_arborescence": True,
    "input_unchanged": True, "networkx_version": nx.__version__,
    "networkx_module": nx.__file__, "python": sys.version, "platform": platform.platform(),
    "scope": "Synthetic complete weighted digraph; the issue supplied no original matrix or latency requirement.",
}, indent=2))
