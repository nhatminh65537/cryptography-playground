# Winternitz OTS

from hashlib import sha256
from os import urandom
from math import log2, ceil, floor


N  = 256
W  = 6
T1 = ceil(N / W)
T2 = ceil((floor(log2(T1)) + 1 + W) / W)
T  = T1 + T2


class WinternitzOTS:
    def __init__(self):
        self.priv = [urandom(N // 8) for _ in range(T)]
        self.pub  = [self._one_way_func(x, 2**W - 1) for x in self.priv]

    @staticmethod
    def _one_way_func(x, times):
        for _ in range(times):
            x = sha256(x).digest()
        return x

    @staticmethod
    def _hash_func(x):
        return sha256(x).digest()
    
    @staticmethod
    def _int_to_chunks(x, size):
        bits = f"{x:b}".zfill(size*W)
        return [int(bits[i:i+W], 2) for i in range(0, size*W, W)]
    
    def _msg_to_chunks(self, m):
        d = int.from_bytes(self._hash_func(m))
        d_chunks = self._int_to_chunks(d, T1)

        c = T1*2**W - sum(d_chunks)
        c_chunks = self._int_to_chunks(c, T2)

        chunks = d_chunks + c_chunks
        assert len(chunks) == T
        
        return chunks

    
    def sign(self, m):
        chunks = self._msg_to_chunks(m)
        sig = [self._one_way_func(x, t) for x, t in zip(self.priv, chunks)]
        return sig
    
    def verify(self, m, sig):
        chunks = self._msg_to_chunks(m)
        hsig = [self._one_way_func(s, 2**W - 1 - t) for s, t in zip(sig, chunks)]
        return hsig == self.pub

if __name__ == "__main__":
    scheme = WinternitzOTS()

    x = urandom(32)
    y = scheme._one_way_func(x, 5)
    assert scheme._one_way_func(x, 12) == scheme._one_way_func(y, 7), "Error on OWF"

    msg = b"Good morning everyone, this signature implement by Rougitsune."
    sig = scheme.sign(msg)
    assert scheme.verify(msg, sig)
    print("The implementation works!")
    
