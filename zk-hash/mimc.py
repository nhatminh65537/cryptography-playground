from sage.all import GF, log, ceil

n = 129
K = GF(2**n, 'i')
e = 3 # gcd(3, 2**n - 1) = 1
d = (2**(n + 1) - 1) // 3 # ed = 1 mod 2**n - 1
r = ceil(n / log(3, 2))
constants = [K.random_element() for _ in range(2 * r)]

class MiMCnn:
    def __init__(self, key):
        self.key = key
    
    def encrypt_block(self, x):
        for i in range(r - 1):
            x = (x + self.key + constants[i]) ** e
        return x + self.key

    def decrypt_block(self, y):
        x = y - self.key
        for i in reversed(range(r - 1)):
            x = x**d - self.key - constants[i]
        return x


class MiMC2nn:
    def __init__(self, key):
        self.key = key
    
    def encrypt_block(self, x):
        xL, xR = x
        for i in range(2*r - 1):
            xL, xR = (xL + self.key + constants[i]) ** e + xR, xL
        return xL, (xL + self.key + constants[2*r - 1]) ** e + xR
    
    def decrypt_block(self, y):
        yL, yR = y
        xL, xR = yL, yR - (yL + self.key + constants[2*r - 1]) ** e
        for i in reversed(range(2*r - 1)):
            xL, xR = xR, xL - (xR + self.key + constants[i]) ** e
        return xL, xR


class MiMCPermutation:
    def __init__(self, version=1):
        if version == 1:
            self.cipher = MiMCnn(K(0))
        elif version == 2:
            self.cipher = MiMC2nn(K(0))
        else:
            raise ValueError("Invalid MiMC version. Use 1 or 2.")
        
    def permute(self, state):
        return self.cipher.encrypt_block(state)
    

class MiMCHash:
    def __init__(self, l = 128, rate=64, version=1):
        self.permutation = MiMCPermutation(version)
        self.rate = rate
        self.capacity = n - rate
        assert l % 8 == 0, "Output length l must be a multiple of 8 bits."
        self.l = l

    def hash(self, input_data):
        byte_rate = self.rate // 8
        padded_input = input_data + b'\x80' + b'\x00' * (byte_rate - (len(input_data) + 1) % byte_rate)
        state = K(0)
        for i in range(0, len(padded_input), byte_rate):
            block = padded_input[i:i + byte_rate]
            block_on_K = K._cache.fetch_int(int.from_bytes(block, 'big'))
            state = self.permutation.permute(state + block_on_K)
        
        digest = state.to_bytes()[- byte_rate:]
        while len(digest) < self.l // 8:
            state = self.permutation.permute(state)
            digest += state.to_bytes()[- byte_rate:]
        
        return digest[:self.l // 8]


class GMiMCHash:
    def __init__(self, t = 2, l = 128, rate = 1, version=1):
        self.permutation = MiMCPermutation(version)
        self.t = t
        self.l = l
        self.rate = rate
        self.capacity = t - rate

    def _permutation(self, state):
        assert len(state) == self.t, f"State must have length {self.t}"
        x0 = state[0]
        x0 += self.permutation.permute(state[1])
        for j in range(1, self.t):
            state[j] += self.permutation.permute(state[(j + 1) % self.t])
        state[0] = x0
        return state
    
    def hash(self, input_data):
        byte_rate = n // 8 * self.rate
        padded_input = input_data + b'\x80' + b'\x00' * (byte_rate - (len(input_data) + 1) % byte_rate)
        state = [K(0)] * self.t
        for i in range(0, len(padded_input), byte_rate):
            block = padded_input[i:i + byte_rate]
            block_on_Kvec = [K._cache.fetch_int(int.from_bytes(block[j*8:(j+1)*8], 'big')) for j in range(0, self.rate, n // 8)]
            for j in range(len(block_on_Kvec)):
                state[j] += block_on_Kvec[j]
            state = self._permutation(state)

        digest = b''
        while True:
            for j in range(self.rate):
                digest += state[j].to_bytes()
            if len(digest) >= self.l // 8:
                break
            state = self._permutation(state)
        
        return digest[:self.l // 8]

if __name__ == "__main__":
    msg = b"Hello, MiMC!"
    msg_on_K = K._cache.fetch_int(int.from_bytes(msg, 'big'))
    key = K.random_element()
    print(f"Key: {key}")

    mimcnn = MiMCnn(key)
    ciphertext = mimcnn.encrypt_block(msg_on_K)
    print(f"Ciphertext: {ciphertext}")
    plaintext = mimcnn.decrypt_block(ciphertext)
    assert plaintext == msg_on_K
    print("MiMCnn implementation successful!")

    mimc2nn = MiMC2nn(key)
    ciphertext_L, ciphertext_R = mimc2nn.encrypt_block((msg_on_K, msg_on_K))
    print(f"Ciphertext L: {ciphertext_L}, Ciphertext R: {ciphertext_R}")
    plaintext_L, plaintext_R = mimc2nn.decrypt_block((ciphertext_L, ciphertext_R))
    assert plaintext_L == msg_on_K and plaintext_R == msg_on_K
    print("MiMC2nn implementation successful!")


    mimchash = MiMCHash(l=128, version=1)
    digest = mimchash.hash(msg)
    print(f"MiMCHash digest: {digest.hex()}")

    gmimchash = GMiMCHash(t=2, rate=1, version=1)
    digest = gmimchash.hash(msg)
    print(f"GMiMCHash digest: {digest.hex()}")

    print(f"Message: {plaintext.to_bytes()}")


