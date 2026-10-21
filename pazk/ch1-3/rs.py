

class RS:

    def __init__(self, p: int):
        self.p = p

    def __call__(self, v: list[int]):
        result = [0] * self.p
        for r in range(self.p):
            for e in v[::-1]:
                result[r] = (r*result[r] + e) % self.p
        return result

if __name__ == "__main__":
    rs = RS(11)

    print(rs([2,1,1]))
    print(rs([2,1,0]))