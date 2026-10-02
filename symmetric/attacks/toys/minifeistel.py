class MiniFeistel:
    def __init__(self, block_size, nibble_size, num_round, /, sbox=None, perm=None):
        assert block_size % nibble_size == 0, "Block size must be divided by nibble size"
        assert nibble_size % 4 == 0, "Nibble size must be divided by 4"

        self.block_size  = block_size
        self.nibble_size = nibble_size
        self.num_round   = num_round

        self.sbox = self._random_sbox() if sbox is None else sbox
        self.perm = self._random_perm() if perm is None else perm

        assert 2**(nibble_size // 4 + 2) == len(self.sbox), "Invalid sbox"

        self.key = None
        self.round_keys = None

    def _random_sbox(self):
        import random

        sbox = list(range(2**(self.nibble_size // 4 + 2)))
        random.shuffle(sbox)

        return sbox

    def _random_perm(self):
        import random

        perm = list(range(self.nibble_size))
        random.shuffle(perm)

        return perm

    def add_key(self, key):
        assert len(key) == self.block_size, "Length of key must be equal block size"

        self.key = key
        self.round_keys = self._expand_key(key)

    def _expand_key(self, key):
        key_nibbles = [key[s:s+self.nibble_size] for s in range(0, self.block_size, self.nibble_size)]

        round_keys = []

        for r in range(self.num_round):
            round_constant = self._num2bit((r + 1) * 1337, self.nibble_size)
            new_nibble = self._xor(key_nibbles[0], self._substitute(self._xor(self._rotate(key_nibbles[1], 13), round_constant)))
            round_keys.append(new_nibble)
            key_nibbles = key_nibbles[1:] + [new_nibble]

        return round_keys

    def _num2bit(self, num, size):
        bits = list(map(int, f"{num:b}"))
        bits = ([0] * (size - len(bits)) + bits)[:size]       
        return bits

    def _bit2num(self, bits):
        return int("".join(map(str, bits)), 2)

    def _xor(self, a, b):
        return [ea ^ eb for ea, eb in zip(a, b)]

    def _rotate(self, a, i):
        i = i % len(a)
        return a[-i:] + a[:-i]

    def _substitute(self, nibble):
        new_nibble = []

        for si in range(4):
            index = self._bit2num(nibble[si*self.nibble_size//4: (si+1)*self.nibble_size//4] + [si // 2, si % 2])
            value = self._num2bit(self.sbox[index], self.nibble_size//4 + 2)[1:-1]
            new_nibble.extend(value)

        return new_nibble

    def encrypt_block(self, block):
        assert self.round_keys is not None, "Please add key before encrypting"

        nibbles = [block[s:s+self.nibble_size] for s in range(0, self.block_size, self.nibble_size)]

        for r in range(self.num_round):
            new_nibble = self._xor(nibbles[0], self._F(nibbles[1], self.round_keys[r]))
            nibbles = nibbles[1:] + [new_nibble]

        return sum(nibbles, [])

    def _F(self, nibble, round_key):
        nibble = self._xor(nibble, round_key)
        nibble = self._substitute(nibble)
        nibble = self._permutate(nibble)

        return nibble

    def _permutate(self, nibble):
        new_nibble = [0] * self.nibble_size
        for i in range(self.nibble_size):
            new_nibble[self.perm[i]] = nibble[i]
        return new_nibble

    def decrypt_block(self, block):
        assert self.round_keys is not None, "Please add key before decrypting"
        
        nibbles = [block[s:s+self.nibble_size] for s in range(0, self.block_size, self.nibble_size)]

        for r in range(self.num_round):
            new_nibble = self._xor(nibbles[-1], self._F(nibbles[0], self.round_keys[-r-1]))
            nibbles = [new_nibble] + nibbles[:-1]

        return sum(nibbles, [])


miniFeistel = MiniFeistel(
    48, 24, 8,
    sbox=[109, 48, 111, 114, 180, 159, 84, 119, 112, 165, 161, 86, 185, 90, 213, 163, 189, 204, 225, 18, 62, 211, 140, 234, 85, 181, 68, 173, 104, 28, 56, 253, 3, 113, 98, 179, 45, 133, 30, 158, 53, 232, 16, 117, 236, 82, 199, 103, 202, 195, 251, 152, 43, 214, 186, 242, 147, 83, 13, 93, 20, 63, 170, 57, 233, 21, 36, 219, 221, 145, 59, 130, 69, 148, 12, 39, 106, 108, 94, 31, 35, 122, 58, 115, 47, 192, 224, 220, 95, 120, 70, 206, 33, 190, 229, 166, 134, 76, 171, 65, 80, 174, 141, 129, 60, 22, 228, 193, 162, 175, 239, 156, 153, 194, 78, 6, 29, 227, 245, 136, 182, 23, 144, 40, 154, 96, 81, 107, 10, 222, 201, 155, 121, 9, 66, 176, 124, 74, 254, 79, 118, 212, 142, 167, 169, 208, 243, 177, 196, 24, 26, 210, 19, 246, 99, 250, 249, 102, 75, 240, 15, 135, 25, 17, 230, 223, 87, 100, 143, 125, 64, 77, 54, 44, 127, 241, 217, 138, 146, 137, 203, 110, 149, 55, 8, 150, 2, 205, 218, 139, 73, 126, 235, 187, 71, 97, 105, 88, 0, 216, 207, 198, 89, 226, 38, 61, 209, 4, 188, 131, 34, 244, 92, 67, 215, 46, 252, 183, 197, 50, 11, 178, 123, 49, 32, 5, 172, 27, 247, 116, 51, 42, 160, 41, 238, 231, 72, 1, 37, 14, 157, 184, 237, 168, 128, 191, 7, 52, 151, 101, 91, 132, 255, 200, 164, 248],
    perm=[0, 4, 8, 12, 16, 20, 1, 5, 9, 13, 17, 21, 2, 6, 10, 14, 18, 22, 3, 7, 11, 15, 19, 23]
)

if __name__ == "__main__":
    key = [0, 0, 0, 0, 1, 1, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 0, 1, 0, 1, 1, 0, 0, 1, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1, 1, 0, 1]
    miniFeistel.add_key(key)
    
    plt = [0, 1, 0, 1, 1, 0, 1, 1, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 1, 0, 0, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1]
    cpt = miniFeistel.encrypt_block(plt)
    assert plt == miniFeistel.decrypt_block(cpt)