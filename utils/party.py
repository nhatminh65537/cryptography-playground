class Party:

    def __init__(self, name, network):
        self.name = name
        self.network = network
        self.state = {}

    def send(self, receiver, type, payload):
        msg = {
            "sender": self.name,
            "receiver": receiver,
            "type": type,
            "payload": payload
        }
        self.network.deliver(msg)

    def receive(self, msg):
        raise NotImplementedError