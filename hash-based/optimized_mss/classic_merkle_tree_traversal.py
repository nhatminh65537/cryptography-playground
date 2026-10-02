from hashlib import sha256

class TreeHashStack:
    def __init__(self, leaf_generator):
        self.stack = []
        self.leaf_generator = leaf_generator
        self._change_generator = self._make_change()
        self.used = False

    def _make_change(self):
        if self.used:
            raise RuntimeError("Leaf generator already used")
        self.used = True
        for leaf in self.leaf_generator:
            node1 = {
                'height': 0,
                'hash': leaf
            }
            while self.stack and node1['height'] == self.stack[-1]['height']:
                node2 = self.stack.pop()
                yield
                node1 = {
                    'height': node1['height'] + 1,
                    'hash': sha256(node2['hash'] + node1['hash']).digest()
                }
            self.stack.append(node1)
            yield

    def traverse(self):
        if self.used:
            raise RuntimeError("Leaf generator already used")
        self.used = True
        for leaf in self.leaf_generator:
            node1 = {
                'height': 0,
                'hash': leaf
            }
            yield node1
            while self.stack and node1['height'] == self.stack[-1]['height']:
                node2 = self.stack.pop()
                node1 = {
                    'height': node1['height'] + 1,
                    'hash': sha256(node2['hash'] + node1['hash']).digest()
                }
                yield node1
            self.stack.append(node1)
            
    
    def push(self, node):
        self.stack.append(node)

    def pop_hash(self):
        if self.stack:
            return self.stack.pop()['hash']
        else:
            raise IndexError("Stack is empty")
    
    def change(self):
        try:
            next(self._change_generator)
        except StopIteration:
            pass


class ClassicMerkleTreeTraversal:
    def __init__(self, height, leaf_func):
        self.height = height
        self.leaf_func = leaf_func

        self.stacks = [TreeHashStack(leaf_func(0)) for i in range(self.height)]
        self.authentication_path = [None] * self.height
        siblings = [None] * self.height

        for node in TreeHashStack(leaf_func(0)).traverse():
            h = node['height']
            
            if h == self.height:
                break
            if siblings[h] is None:
                siblings[h] = node
            elif self.authentication_path[h] is None:
                self.authentication_path[h] = node['hash']
        
        for i, stack in enumerate(self.stacks):
            stack.push(siblings[i])
        
        self.root = node['hash']
        self.s = 0

    def next(self):
        authentication_path = self.authentication_path[:]
        if self.s < 2**self.height - 1:
            h = 0
            while (self.s + 1) % (1 << h) == 0 and h < self.height:
                self.authentication_path[h] = self.stacks[h].pop_hash()
                
                self.stacks[h] = TreeHashStack(self.leaf_func((self.s + 1 + (2 ** h)) ^ (2 ** h)))
                self.stacks[h].change()
                h += 1


            for i in range(1, self.height):
                self.stacks[i].change()
                self.stacks[i].change()
            
            self.s += 1
        return authentication_path
    
    def get_root(self):
        return self.root

def leaf_func(index, leafs):
    return iter(leafs[index:])

if __name__ == "__main__":
    leafs = [sha256(str(i).encode()).digest() for i in range(8)]
    hashtree = [leafs]
    for _ in range(3):
        hashtree.append(
            [sha256(hleft + hright).digest() for hleft, hright in zip(
                hashtree[-1][ ::2], 
                hashtree[-1][1::2]
            )]
        )

    mtt = ClassicMerkleTreeTraversal(3, lambda h: leaf_func(h, leafs))

    for i in range(8):
        auth_path = mtt.next()
        vs = []
        for h in range(3):
            v = hashtree[h].index(auth_path[h])
            vs.append(v)
        print(f"Verification values for leaf {i}: {vs}")
    

