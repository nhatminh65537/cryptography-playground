

class SpongeState:
    def __init__(self, state=None):
        raise NotImplementedError("Subclasses should implement this method")
    
    def __xor__(self, other):
        raise NotImplementedError("Subclasses should implement this method")
    
    def __getitem__(self, index):
        if isinstance(index, slice):
            raise NotImplementedError("Slicing is not supported")
        raise NotImplementedError("Subclasses should implement this method")

    def __setitem__(self, index, value):
        if isinstance(index, slice):
            raise NotImplementedError("Slicing is not supported")
        raise NotImplementedError("Subclasses should implement this method")


class Sponge:
    def __init__(self, rate, capacity, length,  permutation, initital_state):
        self.rate = rate
        self.capacity = capacity
        self.length = length
        self.permutation = permutation
        self.initial_state = initital_state

    def hash(self, input_data):
        state = self.initial_state

        # Absorb phase
        for i in range(0, len(input_data), self.rate):
            block = input_data[i:i+self.rate]
            for j in range(len(block)):
                state[j] ^= block[j]
            self.permutation(state)
        
        # Squeeze phase
        output = []
        while len(output) < self.length:
            output.extend(state[:self.rate])
            self.permutation(state)
        
        return output[:self.length]