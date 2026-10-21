from .field import F

class UniPoly:

    def __init__(self, v):
        if any(not isinstance(ve, F | int) for ve in v):
            raise TypeError('Invalid type for field')
        self.v = [F(ve) for ve in v]
        self.degree = len(v) - 1

    def __call__(self, x):

        if not isinstance(x, F | int):
            raise TypeError('Invalid type for field')

        x = F(x)
        n = self.degree + 1

        if 0 <= x.n <= self.degree:
            return self.v[x.n]

        delta = F(1)
        for k in range(1, n):
            delta *= (x - k)/(0 - k)

        result = self.v[0] * delta
        for i in range(1, n):
            delta *= (x - (i - 1))*(i - n)/(x - i)/i
            result += self.v[i] * delta

        return result


if __name__ == "__main__":
    f = UniPoly([1, 6, 17])
    print(f(5))