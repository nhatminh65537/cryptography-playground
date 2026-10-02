class Message:
    def __init__(self, sender, receiver, type, payload):
        self.sender = sender
        self.receiver = receiver
        self.type = type
        self.payload = payload

    def __repr__(self):
        return f"{self.sender}->{self.receiver}:{self.type}"