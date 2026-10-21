

class LDE:

    def __init__(self, p):
        self.p = p

    def evaluate(self, v, x):
        p = self.p
        delta = 1
        n = len(v)
        if n == 0:
            return 0
        if 0 <= x < n:
            return v[x] % p
        
        for k in range(1, n):
            delta *= (x - k)*pow(0 - k, -1, p) % p

        result = v[0]*delta
        for i in range(1, n):
            delta *= (x - (i - 1))*pow(x - i, -1, p)*pow(i, -1, p)*(-(n-i)) % p
            result += v[i]*delta % p

        return result % p

    def __call__(self, v):
        return [self.evaluate(v, i) for i in range(self.p)]


if __name__ == "__main__":
    lde = LDE(11)

    print(lde([2,1,1]))
    print(lde([2,1,0]))