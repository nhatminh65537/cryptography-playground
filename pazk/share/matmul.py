from .interactive import Party
from .mle import MLE
from .mlesumcheck import MLEProver, trans_tables
from .sumcheck import Verifier
from copy import deepcopy


def fold(table, r, idx=0):
    n = len(table)
    assert n & (n-1) == 0, "Not power of 2"

    left = [table[i] for i in range(n) if (n >> idx + 1) & i == 0]
    right = [table[i] for i in range(n) if (n >> idx + 1) & i != 0]

    return [(1-r)*le + r*re for le, re in zip(left, right)]


class MatmulProver(Party):

    def __init__(self, name, A, B):
        super().__init__(name)

        self.A = A
        self.B = B
        self.ln = (len(A).bit_length() - 1) // 2
        self.C = self.calc_C()

        self.dst = None

    def calc_C(self):
        ln = self.ln
        n = 1 << ln
        A, B = self.A, self.B
        l = len(A)
        C = [0] * l

        for ic in range(l):
            i = ic >> ln
            j = ic & (n - 1)

            for k in range(n):
                ia = (i << ln) | k
                ib = (k << ln) | j
                C[ic] += A[ia] * B[ib]

        return C

    def set_dst(self, verifier):
        self.dst = verifier.name

    def run(self):
        ln  = self.ln

        dst, (r1, r2) = yield
        claim = MLE(self.C)(*r1, *r2)
        yield dst, claim

        A = deepcopy(self.A)
        B = deepcopy(self.B)

        for i in range(ln):
            A = fold(A, r1[i])
            B = fold(B, r2[i], ln)

        mleprover = MLEProver(self.name, [A, B])
        mleprover.dst = dst
        yield from mleprover.run()


class MatmulVerifier(Party):

    def __init__(self, name, r, A, B):
        super().__init__(name)

        self.r = r
        self.A = A
        self.B = B
        self.ln = (len(A).bit_length() - 1) // 2

        self.dst = None
        self.sum = None

    def set_dst(self, prover):
        self.dst = prover.name

    def run(self):
        assert self.dst is not None, "Please set prover"
        dst = self.dst

        yield dst, self.r
        _, claim = yield

        self.sum = claim

        A = deepcopy(self.A)
        B = deepcopy(self.B)

        ln = self.ln

        for i in range(ln):
            A = fold(A, self.r[0][i])
            B = fold(B, self.r[1][i], ln)

        verifier = Verifier(self.name, *trans_tables([A, B]), claim)
        result = yield from verifier.run()
        return result


if __name__ == "__main__":
    print(fold([1, 2, 3, 4], 0))