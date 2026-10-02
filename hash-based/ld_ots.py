# Lamport-Diffie one-time signature schemes

from hashlib import sha256
from os import urandom


N = 256


class LamportDiffieOTS:
    def __init__(self):
        self.priv = []
        self.pub  = []

        for _ in range(N):
            x0 = urandom(N // 8)
            x1 = urandom(N // 8)

            y0 = self._one_way_func(x0)
            y1 = self._one_way_func(x1)

            self.priv.append([x0, x1])
            self.pub.append([y0, y1])
    
    @staticmethod
    def _one_way_func(x):
        return sha256(x).digest()
    
    @staticmethod
    def _hash_func(x):
        return sha256(x).digest()
    
    @staticmethod
    def _bytes_to_bits(bs):
        return list(map(int, ''.join([f"{b:08b}" for b in bs])))

    def sign(self, m):
        h = self._hash_func(m)
        bits = self._bytes_to_bits(h)
        sig = [x[bit] for x, bit in zip(self.priv, bits)]
        return sig
    
    def verify(self, m, sig):
        h = self._hash_func(m)
        bits = self._bytes_to_bits(h)
        hsig = [self._one_way_func(x) for x in sig]
        hcheck = [y[bit] for y, bit in zip(self.pub, bits)]
        return hsig == hcheck
    

if __name__ == "__main__":    
    scheme = LamportDiffieOTS()
    msg = b"Good morning everyone, this signature implement by Rougitsune."
    sig = scheme.sign(msg)
    assert scheme.verify(msg, sig)
    print("The implementation works!")