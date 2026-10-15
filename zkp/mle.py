import numpy as np
from functools import reduce
from itertools import product


class MLE:

    def __init__(self, p, nvars):
        self.p = p
        self.nvars = nvars

    def evaluate(self, vs, xs):
        assert len(xs) == self.nvars

        xi = reduce(np.kron, [[1 - x, x] for x in xs])
        return np.dot(vs, xi) % self.p

    def __call__(self, vs):

        result = np.zeros((self.p, ) * self.nvars, int)
        for xs in product(range(self.p), repeat=self.nvars):
            result[xs] = self.evaluate(vs, xs)

        return result


if __name__ == "__main__":
    vs = [1, 2, 1, 4]
    mle = MLE(5, 2)
    print(mle(vs))