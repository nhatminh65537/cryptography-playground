from .interactive import Party
from .mle import MLE
from copy import deepcopy
import math


def fold(table, r):
    n = len(table)
    assert n & (n-1) == 0, "Not power of 2"

    left = table[:n//2]
    right = table[n//2:]

    return [(1-r)*le + r*re for le, re in zip(left, right)]


class MLEProver(Party):

    def __init__(self, name, tables):
        super().__init__(name)

        self.tables = tables
        self.dst = None

    def sum(self):
        return sum(math.prod([t[i] for t in self.tables]) for i in range(len(self.tables[0])))

    def set_dst(self, verifier):
        self.dst = verifier.name

    def run(self):
        assert self.dst is not None, "Please set verifier"
        dst = self.dst
        nt = len(self.tables)
        tables = deepcopy(self.tables)
        l = len(tables[0])
        v = l.bit_length() - 1
        rs = []

        for i in range(v):
            ps = [math.prod([t[i] for t in tables]) for i in range(l)]
            ev = []
            ev.append(sum(ps[:l//2]))
            ev.append(sum(ps[l//2:]))
            for t in range(2, nt+1):
                fts = [fold(tbl, t) for tbl in tables]
                ev.append(sum(math.prod([t[i] for t in fts]) for i in range(l//2)))
            yield (dst, (f"g{i+1}", ev))
            if i == v - 1:
                return
            _, (_, r) = yield
            rs.append(r)
            for j in range(nt):
                tables[j] = fold(tables[j], r)
            l = len(tables[0])
            


def trans_tables(tables):
    nt = len(tables)
    l = len(tables[0])
    v = l.bit_length() - 1

    degs = [nt] * v
    mles = [MLE(t) for t in tables]
    g = lambda *x: math.prod([mles[i](*x) for i in range(nt)])
    return g, degs