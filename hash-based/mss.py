# Merkle's Signature Schemes

from hashlib import sha256
from w_ots import WinternitzOTS as OTS

H = 7

class MerkleSS:
    def __init__(self):
        self.pubs = []
        self.privs = []

        for _ in range(2**H):
            ots = OTS()
            self.pubs.append(ots.pub)
            self.privs.append(ots.priv)

        self.hashtree = [[self._hash_func(str(pub).encode()) for pub in self.pubs]]
        for _ in range(H):
            self.hashtree.append(
                [self._hash_func(hleft + hright) for hleft, hright in zip(
                    self.hashtree[-1][::2], 
                    self.hashtree[-1][1::2]
                )]
            )
        self.index = 0
        self.merkleroot = self.hashtree[-1][0]
            
    @staticmethod
    def _hash_func(x):
        return sha256(x).digest()
    
    def sign(self, msg):
        assert self.index < 2**H, "All key used"
        ots = OTS()
        ots.priv = self.privs[self.index]
        sig_ots  = ots.sign(msg)
        pub      = self.pubs[self.index]
        hashpath = []

        for i in range(H):
            d = self.index // 2**i
            hashpath.append(
                self.hashtree[i][d + (-1)**d]
            )
        
        sig =  {
            'index': self.index,
            'sig_ots': sig_ots,
            'pub': pub,
            'hashpath': hashpath
        }

        self.index += 1
        
        return sig

    def verify(self, msg, sig):
        ots = OTS()
        ots.pub = sig['pub']
        
        if not ots.verify(msg, sig['sig_ots']):
            return False

        checkroot = self._hash_func(str(sig['pub']).encode())
        for i in range(H):
            d = sig['index'] // 2**i
            if d % 2 == 1:
                checkroot = self._hash_func(sig['hashpath'][i] + checkroot)
            else:
                checkroot = self._hash_func(checkroot + sig['hashpath'][i])
        
        return checkroot == self.merkleroot
    

if __name__ == "__main__":
    scheme = MerkleSS()
    msg = b"Good morning everyone, this signature implement by Rougitsune."
    sig = scheme.sign(msg)
    assert scheme.verify(msg, sig)

    msg = b"Good morning everyone, this signature implement by Rougitsune."
    sig = scheme.sign(msg)
    assert scheme.verify(msg, sig)
    
    print("The implementation works!")
    