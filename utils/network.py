class Network:

    def __init__(self):
        self.parties = {}

    def register(self, party):
        self.parties[party.name] = party

    def deliver(self, msg):
        dst = msg["receiver"]
        print("NETWORK:", msg)
        self.parties[dst].receive(msg)