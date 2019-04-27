import collections
from binascii import hexlify
from datetime import datetime
from Crypto.Hash import SHA
from Crypto.Signature import PKCS1_v1_5


class Transaction:
    def __init__(self, sender, recipient, amount):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.timestamp = datetime.now()
        self.signature = self.sign_transaction()

    def to_dict(self):
        return collections.OrderedDict({
            'sender': self.sender.identity,
            'recipient': self.recipient.identity,
            'amount': self.amount,
            'time': self.timestamp})

    def sign_transaction(self):
        signer = PKCS1_v1_5.new(self.sender._private_key)
        hash = SHA.new(str(self.to_dict()).encode('utf8'))
        return hexlify(signer.sign(hash)).decode('ascii')

    def display(self):
        print("----")
        print("sender:\t\t" + self.sender.identity)
        print("--")
        print("recipient:\t" + self.recipient.identity)
        print("--")
        print("amount:\t\t" + str(self.amount))
        print("--")
        print("timestamp:\t" + str(self.timestamp))
        print("----")
