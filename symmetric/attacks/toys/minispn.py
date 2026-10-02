class MiniSPN:
    def __init__(self, block_size, sbox_size, num_rounds, /, sbox=None, perm=None):
        assert block_size % sbox_size == 0, "Block size must be divided by sbox size"

        self.block_size = block_size
        self.sbox_size  = sbox_size
        self.num_rounds = num_rounds

        self.sbox = self._random_sbox() if sbox is None else sbox
        self.perm = self._random_perm() if perm is None else perm

        self.key = None
        self.round_keys = None

    def _random_sbox(self):
        import random

        sbox = list(range(2**self.sbox_size))
        random.shuffle(sbox)

        return sbox

    def _random_perm(self):
        import random

        perm = list(range(self.block_size))
        random.shuffle(perm)

        return perm

    def add_key(self, key):
        assert len(key) == self.block_size, "Length of key must be equal block size"

        self.key = key
        self.round_keys = self._expand_key(key)

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
        bits = ([0] * (size - len(bits)) + bits)[:size]       
        return bits

    def _substitute(self, block):
        new_block = []
        for s in range(0, self.block_size, self.sbox_size):
            index = int("".join(map(str, block[s:s + self.sbox_size])), 2)
            value = self.sbox[index]
            new_block.extend(self._num2bit(value, self.sbox_size))

        return new_block

    def _xor(self, a, b):
        return [ea ^ eb for ea, eb in zip(a, b)]

    def _rotate(self, a, i):
        i = i % self.block_size
        return a[-i:] + a[:-i]

    def encrypt_block(self, block):
        assert self.round_keys is not None, "Please add key before encrypting"

        state = block
        for r in range(self.num_rounds):
            state = self._permutate(self._substitute(self._xor(state, self.round_keys[r])))

        return self._xor(state, self.round_keys[self.num_rounds])

    def _permutate(self, block):
        new_block = [0] * self.block_size
        for i in range(self.block_size):
            new_block[self.perm[i]] = block[i]
        return new_block

    def decrypt_block(self, block):
        assert self.round_keys is not None, "Please add key before decrypting"

        state = block
        for r in range(self.num_rounds, 0, -1):
            state = self._reverse_substitute(
                self._reverse_permutate(self._xor(state, self.round_keys[r]))
            )

        return self._xor(state, self.round_keys[0])

    def _reverse_permutate(self, block):
        return [block[self.perm[i]] for i in range(self.block_size)]

    def _reverse_substitute(self, block):
        new_block = []
        for s in range(0, self.block_size, self.sbox_size):
            value = int("".join(map(str, block[s:s + self.sbox_size])), 2)
            index = self.sbox.index(value)
            new_block.extend(self._num2bit(index, self.sbox_size))

        return new_block

miniSPN = MiniSPN(
    48, 6, 6,
    sbox = [42, 35, 11, 41, 30, 47, 26, 61, 18, 51, 49, 58, 1, 34, 7, 5, 6, 23, 9, 37, 12, 19, 14, 27, 16, 36, 62, 54, 46, 45, 57, 21, 53, 32, 33, 39, 59, 52, 43, 15, 4, 63, 38, 8, 13, 0, 55, 2, 40, 50, 25, 48, 44, 28, 3, 17, 56, 29, 20, 10, 60, 31, 22, 24],
    perm = [0, 6, 12, 18, 24, 30, 36, 42, 1, 7, 13, 19, 25, 31, 37, 43, 2, 8, 14, 20, 26, 32, 38, 44, 3, 9, 15, 21, 27, 33, 39, 45, 4, 10, 16, 22, 28, 34, 40, 46, 5, 11, 17, 23, 29, 35, 41, 47]
)

if __name__ == "__main__":
    key = [0, 0, 0, 0, 1, 1, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 0, 1, 0, 1, 1, 0, 0, 1, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1, 1, 0, 1]
    miniSPN.add_key(key)
    
    plt = [0, 1, 0, 1, 1, 0, 1, 1, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 1, 0, 0, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1]
    cpt = miniSPN.encrypt_block(plt)
    assert plt == miniSPN.decrypt_block(cpt)