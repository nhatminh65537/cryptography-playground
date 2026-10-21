from .interactive import Party
from .poly import UniPoly
from itertools import product
from random import randint
from .field import F


class Prover(Party):

    def __init__(self, name, g, degs):
        super().__init__(name)

        self.g = g
        self.degs = degs
        self.dst = None

    def _sum(self, f, v):
        return sum(f(*x) for x in product([0, 1], repeat=v))

    def sum(self):
        return self._sum(self.g, len(self.degs))

    def set_dst(self, verifier):
        self.dst = verifier.name

    def run(self):
        assert self.dst is not None, "Please set verifier"
        dst = self.dst
        g = self.g
        degs = self.degs
        v = len(degs)
        rs = []

        for i in range(v):
            ev = [self._sum(lambda *x: g(*rs, j, *x) , v-i-1) for j in range(degs[i]+1)]
            yield (dst, (f"g{i+1}", ev))
            if i == v - 1:
                return
            _, (_, r) = yield
            rs.append(r)


class Verifier(Party):

    def __init__(self, name, g, degs, claim):
        super().__init__(name)

        self.claims = [claim]
        self.g = g
        self.degs = degs

    def run(self):
        degs = self.degs
        claims = [self.claims[0]]
        v = len(degs)
        rs = []

        for i in range(v):
            dst, (_, ev) = yield
            if len(ev) > degs[i]+1:
                return False
            gi = UniPoly(ev)
            if gi(1) + gi(0) != claims[-1]:
                return False
            r = F(randint(0, F.p-1))
            rs.append(r)
            claims.append(gi(r))
            if i == v - 1:
                break
            yield dst, (f"r{i+1}", r)

        if self.g(*rs) != claims[-1]:
            return False

        return True


if __name__ == "__main__":
    from .interactive import Simulation

    def g(x, y, z):
        return F(2*x*x*x + x*z + y*z)

    prover = Prover("Alice", g, [3, 1, 1])
    s = prover.sum()
    print(s)
    verifier = Verifier("Bob", g, [3, 1, 1], s)
    prover.set_dst(verifier)

    sim = Simulation([prover, verifier])

    sim.run()

    print(sim.result)
    sim.print_log()

    verifier = Verifier("Bob", g, [3, 1, 1], s+1)
    prover.set_dst(verifier)
    
    sim = Simulation([prover, verifier])

    sim.run()

    print(sim.result)
    sim.print_log()

    