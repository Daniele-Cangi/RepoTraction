"""Fixed native assessment command; no solver, acquisition or API calls."""
import importlib.util
import json
import os
from pathlib import Path
import sys

repo=Path(__file__).resolve().parents[3]
frozen=repo/'docs/experiments/paired-assistance-2026-10-23'
spec=importlib.util.spec_from_file_location('frozen_cycle_acceptance',frozen/'native_acceptance.py')
case=importlib.util.module_from_spec(spec)
spec.loader.exec_module(case)
expected={row['name']:row for row in json.loads((frozen/'baseline-workloads.json').read_text(encoding='utf-8'))['workloads']}
output=[]
for name,graph,lower,upper,role in case.workloads():
    initial=case.nx.node_link_data(graph,edges='edges')
    observed=case.observe(graph,lower,upper)
    assert observed==expected[name]['output'], (name,'changed output',observed,expected[name]['output'])
    assert initial==case.nx.node_link_data(graph,edges='edges'), (name,'input changed during validation')
    iterations=expected[name]['batch']['iterations']
    case.batch(graph,lower,upper,1)  # same untimed warmup for every version/batch
    measured=case.batch(graph,lower,upper,iterations)
    assert initial==case.nx.node_link_data(graph,edges='edges'), (name,'input changed during timing')
    assert measured['count']==iterations*observed['count'], (name,'timed count differs')
    assert measured['total_length']==expected[name]['batch']['total_length']//expected[name]['batch']['iterations']*iterations
    output.append({'name':name,'role':role,'output':observed,**measured})
print(json.dumps({'batch':int(sys.argv[1]),'arm':sys.argv[2],'mode':case.MODE,'workloads':output},indent=2))
