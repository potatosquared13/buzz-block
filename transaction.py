# TODO transaction should contain sender/recipient balances

import helpers
from binascii import hexlify
from datetime import datetime
from Crypto.Signature import PKCS1_v1_5


class Transaction:
    def __init__(self, sender_identity, recipient_identity, amount):
        self.sender = sender_identity
        self.recipient = recipient_identity
        self.amount = amount
        self.timestamp = datetime.now().isoformat()
        self.signature = None

    def display(self):
        from copy import deepcopy
        tmp = deepcopy(self)
        tmp.signature = tmp.signature[:10]
        print(helpers.jsonify(self))
