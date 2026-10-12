import json,time
from _pytest._code.code import ExceptionInfo,Traceback

STATES = iter(())

def walk(state):
    walk(next(STATES))

def capture(states):
    global STATES
    STATES = iter(states)
    try:
        walk(next(STATES))
    except StopIteration:
        exc = ExceptionInfo.from_current()
    return Traceback(entry for entry in exc.traceback if entry.frame.code.raw is walk.__code__)

class CountedValue:
    calls=0
    def __init__(self,value):self.value=value
    def __eq__(self,other):
        type(self).calls+=1
        return type(other) is type(self) and self.value==other.value
    __hash__=None

results=[]
for n in (20,40,80,160):
    trace=capture([CountedValue(i) for i in range(n)])
    CountedValue.calls=0;tic=time.perf_counter();index=trace.recursionindex();elapsed=time.perf_counter()-tic
    result={'frames':len(trace),'index':index,'equality_calls':CountedValue.calls,'wall_seconds':elapsed}
    assert index is None,result
    results.append(result)
checks=[]
for name,states,expected in [('same_state',[0,0],1),('cycle_then_tail',[0,1,0,2,3],2),('no_repetition',[0,1,2,3],None),('equal_distinct_values',[CountedValue(7),CountedValue(7)],1)]:
    actual=capture(states).recursionindex();assert actual==expected,(name,actual,expected)
    checks.append({'name':name,'expected':expected,'actual':actual})
class RaisingValue:
    def __eq__(self,other):raise ValueError("comparison unavailable")
trace=capture([RaisingValue(),RaisingValue()])
from _pytest._code.code import ExceptionInfoFormatter
retained,warning=ExceptionInfoFormatter()._truncate_recursive_traceback(trace)
assert warning and "error occurred locating the origin" in warning and "ValueError" in warning
checks.append({'name':'comparison_error_is_disclosed','expected':'explicit unknown-origin warning','actual':warning})

source="def walk(state):\n    NEXT(state)\n"
one={};two={};exec(compile(source,'equal-code.py','exec'),one);exec(compile(source,'equal-code.py','exec'),two)
first,second=one['walk'],two['walk']
assert first.__code__==second.__code__ and first.__code__ is not second.__code__
def terminal(state):raise StopIteration
one['NEXT']=second;two['NEXT']=terminal
try:first(0)
except StopIteration:exc=ExceptionInfo.from_current()
trace=Traceback(entry for entry in exc.traceback if any(entry.frame.code.raw is f.__code__ for f in (first,second)))
actual=trace.recursionindex();assert actual is None
checks.append({'name':'equal_distinct_code_objects_are_separate','expected':None,'actual':actual})
print(json.dumps({'scaling':results,'semantic_controls':checks},indent=2))
