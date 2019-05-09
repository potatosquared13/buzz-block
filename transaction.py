import helpers
from copy import deepcopy
from datetime import datetime


class Transaction:
    def __init__(self, sender_identity, recipient_identity, amount):
        self.sender = sender_identity
        self.recipient = recipient_identity
        self.amount = amount
        self.timestamp = datetime.now().isoformat()
        self.signature = None

    @property
    def json(self):
        return helpers.jsonify(self)

    @property
    def hash(self):
        tmp_transaction = deepcopy(self)
        del tmp_transaction.signature
        return helpers.sha256(helpers.jsonify(tmp_transaction))

