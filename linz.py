from collections import namedtuple
from collections import defaultdict
from collections import OrderedDict
from collections import Counter

from enum import Enum

class OpType(Enum):
    BEGIN = 1
    END = 2

class Op(object):
    def __init__(self, thread, _type, func=None, arg=None, result=None):
        self.thread = thread
        self._type = _type
        self.func = func
        self.arg = arg
        self.result = result

class StackVerifier(object):
    def __init__(self):
        self.ls = []

    def push(self, x):
        self.ls.append(x)
        return None

    def pop(self, x):
        try:
            return self.ls.pop()
        except:
            return None

def topological_sorts(nodes, edges, path=[]):
    zero_in = [k for k,v in nodes.items() if v==0]
    if len(zero_in) == 0:
        yield path

    for node in zero_in:
        path.append(node)
        for neighbor in edges[node]:
            nodes[neighbor] -= 1
        del(nodes[node])
        yield from topological_sorts(nodes, edges, path)
        nodes[node] = 0
        for neighbor in edges[node]:
            nodes[neighbor] += 1
        path.pop()

        
def verify(sched, verifier):
    open_events = {}
    events = []

    # From node_id (start time) to causally later events
    edges = defaultdict(list)
    nodes = Counter() # in-degree
    
    for i, op in enumerate(sched):
        if op._type == OpType.BEGIN:
            assert op.thread not in open_events
            open_events[op.thread] = (i, op)

            for op_start, op_end, op2 in events:
                edges[op_start].append(i)
            nodes[i] = len(events)

        elif op._type == OpType.END:
            assert op.thread in open_events
            start, op = open_events[op.thread]
            events.append((start, i, op))
            del(open_events[op.thread])
        else:
            assert False

    # Verify the model for all legal linear orderings
    for path in topological_sorts(nodes, edges):
        vf = verifier()
        print(path)
        for p in path:
            op = sched[p]
            print("  [%d] %s(%s) ==> %s" % (p, op.func.__name__, op.arg, op.result))

            res = op.func(vf, op.arg)
            if res != op.result:
                print("  FAILED: %s != %s" % (res, op.result))
                break
        else:
            print("  PASSED")

sched = [
    Op('t1', OpType.BEGIN, StackVerifier.push, 1, None),
    Op('t2', OpType.BEGIN, StackVerifier.push, 2, None),
    Op('t1', OpType.END),
    Op('t2', OpType.END),
    Op('t1', OpType.BEGIN, StackVerifier.pop, None, 1),
    Op('t2', OpType.BEGIN, StackVerifier.pop, None, 2),
    Op('t1', OpType.END),
    Op('t2', OpType.END),
    ]

sched2 = [
    Op('t1', OpType.BEGIN, StackVerifier.push, 1, None),
    Op('t2', OpType.BEGIN, StackVerifier.push, 2, None),
    Op('t2', OpType.END),
    Op('t1', OpType.END),
    Op('t1', OpType.BEGIN, StackVerifier.push, 3, None),
    Op('t1', OpType.END, StackVerifier.push, 3, None),
    Op('t1', OpType.BEGIN, StackVerifier.pop, None, 1),
    Op('t2', OpType.BEGIN, StackVerifier.pop, None, 3),
    Op('t1', OpType.END),
    Op('t2', OpType.END),
    ]

if __name__ == '__main__':
    verify(sched, StackVerifier)
