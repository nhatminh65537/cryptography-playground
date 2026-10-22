from .field import F
from .mle import MLE
from .poly import UniPoly
from math import prod, log2
from .interactive import Party
from random import randint


ADD = "ADD"
MUL = "MUL"
VAR = "var"

add = lambda *inp: (ADD, *inp)
mul = lambda *inp: (MUL, *inp)
var = lambda v   : (VAR, v   )

class ArithCircuit:

    def __init__(self, layers):
        self.layers = layers
        self.d      = len(layers)

    def __call__(self, *x):
        w = [[F(x[i]) for _, i in self.layers[-1]]]
        for i in range(self.d - 2, -1, -1):
            we = []
            for op, x1, x2 in self.layers[i]:
                if op == ADD: we.append(w[0][x1] + w[0][x2])
                else:         we.append(w[0][x1] * w[0][x2])
            w = [we] + w

        return w

    def wiring(self, i, *op):
        return [(j,*x) for j, (jop, *x) in enumerate(self.layers[i]) if jop in op]


def chi(i, r):
    return prod([(ie*re + (1-ie)*(1-re)) for ie, re in zip(i, r)])


def fold(table, r):
    n = len(table)
    assert n & (n-1) == 0, "Not power of 2"
    return [(1-r)*le + r*re for le, re in zip(table[:n//2], table[n//2:])]


def int2bit(i, k):
    return [(i >> j) & 1 for j in range(k - 1, -1, -1)]


class GKRProver(Party):
    
    def __init__(self, name, curcuit):
        super().__init__(name)
        
        self.circuit = curcuit
        self.w       = None
        self.dst     = None

    def loop(self, r, li):
        dst = self.dst

        wadd = self.circuit.wiring(li, ADD)
        wmul = self.circuit.wiring(li, MUL)

        ln = (len(self.circuit.layers[li]) - 1).bit_length() 

        chiadd = [chi(int2bit(a, ln), r) for a, *_ in wadd]
        chimul = [chi(int2bit(a, ln), r) for a, *_ in wmul]

        ln = (len(self.circuit.layers[li+1]) - 1).bit_length()

        wb = self.w[li+1]
        wc = self.w[li+1]

        rs = []

        for i in range(2*ln - 1, -1, -1):
            l = 2**i
            v = []
            for t in range(3):
                addi = [0] * l
                muli = [0] * l

                for j, (a, b, c) in enumerate(wadd):
                    x = (b << ln) | c
                    e = (x >> i) & 1
                    addi[x & (l - 1)] += chiadd[j]*(t*e + (1 - t)*(1 - e))

                for j, (a, b, c) in enumerate(wmul):
                    x = (b << ln) | c
                    e = (x >> i) & 1
                    muli[x & (l - 1)] += chimul[j]*(t*e + (1 - t)*(1 - e))

                if i < ln:
                    wbt = wb
                    wct = fold(wc, t)
                else:
                    wbt = fold(wb, t)
                    wct = wc

                v.append(sum(
                    addi[j]*(wbt[j >> ln] + wct[j & (2**ln - 1)]) +
                    muli[j]*(wbt[j >> ln] * wct[j & (2**ln - 1)]) for j in range(l)
                ))

            yield dst, v
            _, r = yield
            rs.append(r)
            if i < ln:
                wc = fold(wc, r)
                chiadd = [k*(r*(e := (c >> ln) & 1) + (1 - r)*(1 - e)) for k, (_, _, c) in zip(chiadd, wadd)]
                chimul = [k*(r*(e := (c >> ln) & 1) + (1 - r)*(1 - e)) for k, (_, _, c) in zip(chimul, wmul)]
            else:
                wb = fold(wb, r)
                chiadd = [k*(r*(e := (b >> (i - ln)) & 1) + (1 - r)*(1 - e)) for k, (_, b, _) in zip(chiadd, wadd)]
                chimul = [k*(r*(e := (b >> (i - ln)) & 1) + (1 - r)*(1 - e)) for k, (_, b, _) in zip(chimul, wmul)]

        r1 = rs[:ln]
        r2 = rs[ln:]

        lp = [UniPoly([r1e, r2e]) for r1e, r2e in zip(r1, r2)]
        l  = lambda x: [lpe(x) for lpe in lp]
        g  = MLE(self.w[li+1])
        yield dst, [g(*l(i)) for i in range(ln + 1)]
        _, r = yield

        return r

    def run(self):
        dst = self.dst

        _, inp = yield
        self.w = self.circuit(*inp)
        yield dst, self.w[0]

        _, r = yield
        for i in range(len(self.circuit.layers) - 1):
            r = yield from self.loop(r, i)

        return self.w[0]


class GKRVerifier(Party):

    def __init__(self, name, circuit, inp):
        super().__init__(name)

        self.circuit = circuit
        self.inp = inp
        self.dst = None

    def loop(self, wr, r, li):
        dst = self.dst
        ln = (len(self.circuit.layers[li+1]) - 1).bit_length()
        rs = []
        claims = [wr]

        for i in range(2*ln - 1, -1, -1):
            _, v = yield

            if len(v) > 3:
                return None, None

            g = UniPoly(v)
            if g(0) + g(1) != claims[-1]:
                return None, None

            c = F(randint(1, F.p))
            rs.append(c)
            claims.append(g(c))
            yield dst, c

        _, v = yield
        if len(v) > ln + 1:
            return None, None

        r1 = rs[:ln]
        r2 = rs[ln:]

        f = UniPoly(v)
        wadd = self.circuit.wiring(li, ADD)
        wmul = self.circuit.wiring(li, MUL)
        lni = (len(self.circuit.layers[li]) - 1).bit_length()

        i2b = int2bit
        addi = sum(chi(r+rs, i2b(a, lni)+i2b(b, ln)+i2b(c, ln)) for a, b, c in wadd)
        muli = sum(chi(r+rs, i2b(a, lni)+i2b(b, ln)+i2b(c, ln)) for a, b, c in wmul)
        if addi*(f(0) + f(1)) + muli*(f(0) * f(1)) != claims[-1]:
            return None, None

        r  = F(randint(1, F.p))
        wr = f(r)

        r1 = rs[:ln]
        r2 = rs[ln:]

        lp = [UniPoly([r1e, r2e]) for r1e, r2e in zip(r1, r2)]
        l  = lambda x: [lpe(x) for lpe in lp]

        lr = l(r)
        yield dst, lr

        return wr, lr

    def run(self):
        dst = self.dst
        yield dst, self.inp
        _, out = yield

        r  = [F(randint(1, F.p)) for _ in range(log2(len(out)))]
        wr = MLE(out)(*r)

        yield dst, r
        for i in range(len(self.circuit.layers) - 1):
            wr, r = yield from self.loop(wr, r, i)
            if wr is None:
                return False

        return MLE(self.inp)(*r) == wr


if __name__ == "__main__":
    c = ArithCircuit([
        [mul(0, 1), mul(2, 3)],
        [mul(0, 0), mul(1, 1), mul(1, 2), mul(3, 3)],
        [var(0), var(1), var(2), var(3)]
    ])

    print(c(3, 2, 3, 1))