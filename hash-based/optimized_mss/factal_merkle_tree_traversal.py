from hashlib import sha256

H = 16
L = 4
h = H // L

class MerkleTreeNode:
    def __init__(self, hash, height):
        self.hash = hash
        self.height = height

class MerkleTreeHashTraversal:
    def __init__(self, leaf_iter):
        self._leaf_iter = leaf_iter
        self._stack = []
        self._iter = self.make_iter()
        
    def make_iter(self):
        for leaf in self._leaf_iter:
            node1 = MerkleTreeNode(
                sha256(leaf).digest(),
                0
            )
            yield node1
            while self._stack and node1.height == self._stack[-1].height:
                node2 = self._stack.pop()
                node1 = MerkleTreeNode(
                    sha256(node2.hash + node1.hash).digest(),
                    node1.height + 1
                )
                yield node1
            self._stack.append(node1)

    def __next__(self):
        return self._iter.__next__()

    def __iter__(self):
        return self
        

class SubTree:
    def __init__(self, leaf_iter, level, pos):
        self.height = level * h
        self.stored_hash = [[] for _ in range(h)]
        self.counter = (1 << (h*level)) * pos
        self.pos = pos
        self.traversal = MerkleTreeHashTraversal(leaf_iter)
        self.iter = self.make_iter()

    def make_iter(self):
        for node in self.traversal:
            if node.height == self.height:
                break
            if node.height >= self.height - h:
                self.stored_hash[node.height - self.height + h].append(node.hash)
            yield
        while True:
            yield

    def update(self):
        next(self.iter)

    def next(self):
        authentication_path = []
        for i in range(h):
            # print(f"SubTree level {self.height}, pos {self.pos}, i {i}, counter {self.counter}")
            authentication_path.append(self.stored_hash[i][((self.counter >> (self.height - h + i)) & ((1 << (h - i)) - 1)) ^ 1])
        self.counter += 1
        return authentication_path
    

class FractalMerkleTreeTraversal:
    def __init__(self, leaf_func):
        self.leaf_func = leaf_func
        self.exists = [SubTree(leaf_func(0), level, 0) for level in range(1, L + 1)]
        self.desires = [SubTree(leaf_func(1 << (h * level)), level, 1) for level in range(1, L)]

        for node in MerkleTreeHashTraversal(leaf_func(0)):
            if node.height == H:
                self.root = node.hash
                break
            level = node.height // h + 1
            i = node.height % h
            l = len(self.exists[level - 1].stored_hash[i])
            if l < (1 << (h - i)):
                self.exists[level - 1].stored_hash[i].append(node.hash)
        
        self.s = 0
        
    def next(self):
        authentication_path = []

        for subtree in self.exists:
            authentication_path.extend(subtree.next())

        for i in range(1, L):
            if (self.s + 1) % (1 << (h * i)) == 0:
                exist = self.exists[i - 1]
                self.exists[i - 1] = self.desires[i - 1]
                self.desires[i - 1] = SubTree(self.leaf_func(self.s + 1 + (1 << (h * i))), i, exist.pos + 1)
        
        for subtree in self.desires:
            subtree.update()
            subtree.update()

        self.s += 1
        return authentication_path          


if __name__ == "__main__":
    leafs = [str(i).encode() for i in range(1 << H)]
    hashtree = [[sha256(leaf).digest() for leaf in leafs]]
    for _ in range(H):
        hashtree.append(
            [sha256(hleft + hright).digest() for hleft, hright in zip(
                hashtree[-1][ ::2], 
                hashtree[-1][1::2]
            )]
        )
    
    traversal = FractalMerkleTreeTraversal(lambda i: iter(leafs[i:]))
    for i in range(1 << H):
        authentication_path = traversal.next()
        # indices = [hashtree[j].index(authentication_path[j]) for j in range(H)]
        # print(f"Authentication path for leaf {i}: {indices}")
        assert authentication_path == [hashtree[j][(i >> (j)) ^ 1] for j in range(H)]

    print("All tests passed!")
