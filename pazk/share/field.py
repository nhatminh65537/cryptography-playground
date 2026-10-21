
class F:
    p = (1 << 61) - 1

    def __init__(self, n):
        if isinstance(n, F):
            self.n = n.n
        else:
            self.n = n % self.p

    def __add__(self, other):
        if isinstance(other, F):
            return F(self.n + other.n)
        if isinstance(other, int):
            return self + F(other)
        return NotImplemented

    def __radd__(self, other):
        return self + other

    def __neg__(self):
        return F(-self.n)

    def __sub__(self, other):
        return self + (-other)

    def __rsub__(self, other):
        return -(self - other)

    def __mul__(self, other):
        if isinstance(other, F):
            return F(self.n * other.n)
        if isinstance(other, int):
            return self * F(other)
        return NotImplemented

    def __rmul__(self, other):
        return self * other

    def __truediv__(self, other):
        return self * pow(F(other).n, -1, self.p)

    def __rtruediv__(self, other):
        return other * F(pow(self.n, -1, self.p))

    def __pow__(self, other):
        return F(pow(self.n, other, self.p))

    def __repr__(self):
        return f"F({self.n})"

    def __eq__(self, other):
        if not isinstance(other, int | F):
            return NotImplemented
        return self.n == F(other).n
