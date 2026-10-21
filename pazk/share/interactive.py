from collections import deque

DROP = object()


class Party:
    """Skeleton for a protocol participant. Subclass it and implement run() as a generator.

    yield (dst, payload)    send payload to the party named dst, then keep running
    src, payload = yield    wait until a message arrives
    return v                finish; v becomes this party's result
    """

    def __init__(self, name):
        self.name = name

    def run(self):
        raise NotImplementedError


class Simulation:
    """Runs any number of parties and routes messages between them by name.

    wire(src, dst, payload) models the network: it receives every message in
    transit and returns the payload to deliver (possibly modified), or DROP.
    """

    def __init__(self, parties, wire=None):
        self.gen = {p.name: p.run() for p in parties}
        self.wire = wire
        self.queue = deque()
        self.log = []
        self.result = {}
        self.waiting = set()
        self.stuck = []

    def _advance(self, name, value=None):
        self.waiting.discard(name)
        g = self.gen[name]
        while True:
            try:
                out = g.send(value)
            except StopIteration as e:
                self.result[name] = e.value
                return
            if out is None:
                self.waiting.add(name)
                return
            dst, payload = out
            self.queue.append((name, dst, payload))
            value = None

    def run(self):
        for name in self.gen:
            self._advance(name)
        while self.queue:
            src, dst, payload = self.queue.popleft()
            if self.wire:
                payload = self.wire(src, dst, payload)
                if payload is DROP:
                    continue
            self.log.append((src, dst, payload))
            if dst in self.waiting:
                self._advance(dst, (src, payload))
        self.stuck = sorted(self.waiting)
        for g in self.gen.values():
            g.close()
        return self.result

    def print_log(self):
        for line in self.log:
            print(f"{line[0]} -> {line[1]}: {line[2]}")