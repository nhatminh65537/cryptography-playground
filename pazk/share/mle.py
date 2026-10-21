from .field import F
from functools import reduce
from itertools import product

class MLE:
    def __init__(self, v):
        n = len(v)
        if n & (n - 1) != 0:
            raise ValueError("Invalid length for hypercube")
        if any(not isinstance(ve, F | int) for ve in v):
            raise TypeError('Invalid type for field')

        self.nvars = n.bit_length() - 1
        self.v = [F(ve) for ve in v]

    def _chi_table(self, x):
        kron = lambda a, b: [ae * be for ae, be in product(a, b)]
        return reduce(kron, [[1 - xe, xe] for xe in x])
        

    def __call__(self, *x):
        if len(x) != self.nvars:
            raise ValueError("Invalid input x")
        

        chi_table = self._chi_table(x)
        return sum([ve * chi for ve, chi in zip(self.v, chi_table)], F(0))


if __name__ == "__main__":
    F.p = 11
    f = MLE([3, 4, 1, 2])
    print(f(2, 4))

        