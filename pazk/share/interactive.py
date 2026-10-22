from collections import deque
from time import perf_counter

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

    Timing: self.time[name] is the total time (seconds) that party spent
    executing its own code, i.e. only while its generator was running.
    Time spent waiting for messages, in other parties, or in wire() is not
    counted. self.wire_time is the total time spent inside wire().
    self.activations[name] counts how many times the party was resumed.
    """

    def __init__(self, parties, wire=None, clock=perf_counter):
        self.gen = {p.name: p.run() for p in parties}
        self.wire = wire
        self.clock = clock
        self.queue = deque()
        self.log = []
        self.result = {}
        self.waiting = set()
        self.stuck = []
        self.time = {name: 0.0 for name in self.gen}
        self.activations = {name: 0 for name in self.gen}
        self.wire_time = 0.0

    def _step(self, name, g, value):
        """Resume generator g once and charge the elapsed time to name."""
        t0 = self.clock()
        try:
            return g.send(value)
        finally:
            self.time[name] += self.clock() - t0

    def _advance(self, name, value=None):
        self.waiting.discard(name)
        self.activations[name] += 1
        g = self.gen[name]
        while True:
            try:
                out = self._step(name, g, value)
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
                t0 = self.clock()
                payload = self.wire(src, dst, payload)
                self.wire_time += self.clock() - t0
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

    def print_times(self, unit="ms"):
        scale = {"s": 1, "ms": 1e3, "us": 1e6}[unit]
        width = max(map(len, self.time), default=4)
        for name, t in self.time.items():
            print(f"{name:<{width}}  {t * scale:10.3f} {unit}  ({self.activations[name]} activations)")
        if self.wire:
            print(f"{'wire':<{width}}  {self.wire_time * scale:10.3f} {unit}")