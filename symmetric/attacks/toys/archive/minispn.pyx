# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True
from libc.stdint cimport uint64_t

SBOX = [42, 35, 11, 41, 30, 47, 26, 61, 18, 51, 49, 58, 1, 34, 7, 5, 6, 23, 9, 37, 12, 19, 14, 27, 16, 36, 62, 54, 46, 45, 57, 21, 53, 32, 33, 39, 59, 52, 43, 15, 4, 63, 38, 8, 13, 0, 55, 2, 40, 50, 25, 48, 44, 28, 3, 17, 56, 29, 20, 10, 60, 31, 22, 24]
PERM = [0, 6, 12, 18, 24, 30, 36, 42, 1, 7, 13, 19, 25, 31, 37, 43, 2, 8, 14, 20, 26, 32, 38, 44, 3, 9, 15, 21, 27, 33, 39, 45, 4, 10, 16, 22, 28, 34, 40, 46, 5, 11, 17, 23, 29, 35, 41, 47]

cdef uint64_t MASK = (<uint64_t>1 << 48) - 1

cdef uint64_t T[8][64]
cdef uint64_t P[6][256]
cdef uint64_t IS[4096]

def _build_tables():
    cdef int s, v, j, k, i, o
    cdef uint64_t r
    cdef int sbox[64]
    cdef int inv[64]
    cdef int perm[48]
    cdef int invperm[48]

    for i in range(64):
        sbox[i] = SBOX[i]
    for i in range(64):
        inv[sbox[i]] = i
    for i in range(48):
        perm[i] = PERM[i]
    for i in range(48):
        invperm[perm[i]] = i

    for s in range(8):
        for v in range(64):
            o = sbox[v]
            r = 0
            for j in range(6):
                if (o >> (5 - j)) & 1:
                    r |= (<uint64_t>1) << (47 - perm[6 * s + j])
            T[s][v] = r

    for k in range(6):
        for v in range(256):
            r = 0
            for j in range(8):
                if (v >> (7 - j)) & 1:
                    r |= (<uint64_t>1) << (47 - invperm[8 * k + j])
            P[k][v] = r

    for v in range(4096):
        IS[v] = (<uint64_t>inv[v >> 6] << 6) | <uint64_t>inv[v & 63]

_build_tables()

cdef inline uint64_t _enc(uint64_t x, uint64_t* rk) noexcept nogil:
    cdef int r
    for r in range(6):
        x ^= rk[r]
        x = (T[0][x >> 42] ^ T[1][(x >> 36) & 63] ^ T[2][(x >> 30) & 63]
             ^ T[3][(x >> 24) & 63] ^ T[4][(x >> 18) & 63]
             ^ T[5][(x >> 12) & 63] ^ T[6][(x >> 6) & 63] ^ T[7][x & 63])
    return x ^ rk[6]

cdef inline uint64_t _dec(uint64_t x, uint64_t* rk) noexcept nogil:
    cdef int r
    for r in range(6, 0, -1):
        x ^= rk[r]
        x = (P[0][x >> 40] ^ P[1][(x >> 32) & 255] ^ P[2][(x >> 24) & 255]
             ^ P[3][(x >> 16) & 255] ^ P[4][(x >> 8) & 255] ^ P[5][x & 255])
        x = ((IS[x >> 36] << 36) | (IS[(x >> 24) & 4095] << 24)
             | (IS[(x >> 12) & 4095] << 12) | IS[x & 4095])
    return x ^ rk[0]

cdef uint64_t _bits2int(list bits) except? 0xFFFFFFFFFFFFFFFF:
    if len(bits) != 48:
        raise ValueError("block must have exactly 48 bits")
    cdef uint64_t x = 0
    cdef int i, b
    for i in range(48):
        b = bits[i]
        x = (x << 1) | <uint64_t>(b & 1)
    return x

cdef list _int2bits(uint64_t x):
    cdef list out = [0] * 48
    cdef int i
    for i in range(48):
        out[i] = <int>((x >> (47 - i)) & 1)
    return out

cdef class Cipher:
    cdef uint64_t rk[7]

    def set_round_keys(self, keys):
        if len(keys) != 7:
            raise ValueError("need 7 round keys")
        cdef int i
        for i in range(7):
            self.rk[i] = <uint64_t>keys[i] & MASK

    cpdef uint64_t encrypt_int(self, uint64_t x):
        return _enc(x & MASK, self.rk)

    cpdef uint64_t decrypt_int(self, uint64_t x):
        return _dec(x & MASK, self.rk)

    def encrypt_bits(self, list bits):
        return _int2bits(_enc(_bits2int(bits), self.rk))

    def decrypt_bits(self, list bits):
        return _int2bits(_dec(_bits2int(bits), self.rk))

    def encrypt_many(self, xs):
        cdef list out = []
        cdef uint64_t x
        for x in xs:
            out.append(_enc(x & MASK, self.rk))
        return out

    def decrypt_many(self, xs):
        cdef list out = []
        cdef uint64_t x
        for x in xs:
            out.append(_dec(x & MASK, self.rk))
        return out

    def encrypt_inplace(self, uint64_t[::1] buf):
        cdef Py_ssize_t i, n = buf.shape[0]
        with nogil:
            for i in range(n):
                buf[i] = _enc(buf[i] & MASK, self.rk)

    def decrypt_inplace(self, uint64_t[::1] buf):
        cdef Py_ssize_t i, n = buf.shape[0]
        with nogil:
            for i in range(n):
                buf[i] = _dec(buf[i] & MASK, self.rk)

_BLOCK, _SBOX_BITS, _ROUNDS = 48, 6, 6

def _b2i(bits):
    v = 0
    for b in bits:
        v = (v << 1) | b
    return v

class MiniSPN:
    def __init__(self, block_size=_BLOCK, sbox_size=_SBOX_BITS, num_rounds=_ROUNDS, /,
                 sbox=None, perm=None):
        if (block_size, sbox_size, num_rounds) != (_BLOCK, _SBOX_BITS, _ROUNDS):
            raise NotImplementedError("only the 48/6/6 configuration is supported")
        if sbox is not None and list(sbox) != SBOX:
            raise NotImplementedError("only the built-in SBOX is supported")
        if perm is not None and list(perm) != PERM:
            raise NotImplementedError("only the built-in PERM is supported")

        self.block_size = block_size
        self.sbox_size = sbox_size
        self.num_rounds = num_rounds
        self.sbox = list(SBOX)
        self.perm = list(PERM)

        self.key = None
        self.round_keys = None
        self._c = Cipher()

    def add_key(self, key):
        assert len(key) == self.block_size, "Length of key must be equal block size"
        self.key = key
        self.round_keys = self._expand_key(key)
        self._c.set_round_keys([_b2i(k) for k in self.round_keys])

    def _expand_key(self, key):
        round_keys = []
        state = key
        for i in range(self.num_rounds + 1):
            round_constant = self._num2bit((i + 1) * 1337, self.block_size)
            state = self._substitute(self._xor(self._rotate(state, 13), round_constant))
            round_keys.append(state)
        return round_keys

    def _num2bit(self, num, size):
        bits = list(map(int, f"{num:b}"))
        return ([0] * (size - len(bits)) + bits)[:size]

    def _substitute(self, block):
        new_block = []
        for s in range(0, self.block_size, self.sbox_size):
            index = int("".join(map(str, block[s:s + self.sbox_size])), 2)
            new_block.extend(self._num2bit(self.sbox[index], self.sbox_size))
        return new_block

    def _xor(self, a, b):
        return [x ^ y for x, y in zip(a, b)]

    def _rotate(self, a, i):
        i = i % self.block_size
        return a[-i:] + a[:-i]

    def encrypt_block(self, block):
        assert self.round_keys is not None, "Please add key before encrypting"
        return self._c.encrypt_bits(block)

    def decrypt_block(self, block):
        assert self.round_keys is not None, "Please add key before decrypting"
        return self._c.decrypt_bits(block)

    def _check(self):
        assert self.round_keys is not None, "Please add key first"

    def encrypt_int(self, x):
        self._check(); return self._c.encrypt_int(x)

    def decrypt_int(self, x):
        self._check(); return self._c.decrypt_int(x)

    def encrypt_many(self, xs):
        self._check(); return self._c.encrypt_many(xs)

    def decrypt_many(self, xs):
        self._check(); return self._c.decrypt_many(xs)

    def encrypt_inplace(self, buf):
        self._check(); self._c.encrypt_inplace(buf)

    def decrypt_inplace(self, buf):
        self._check(); self._c.decrypt_inplace(buf)

miniSPN = MiniSPN()
