# transaction structure to be used in blocks

import helpers
from copy import deepcopy
from datetime import datetime

class Transaction:
    def __init__(self, sender, recipient, amount):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.signature = None

    @property
    def json(self):
        return helpers.jsonify(self)

    @property
    def hash(self):
        tmp_transaction = deepcopy(self)
        del tmp_transaction.signature
        return helpers.sha256(helpers.jsonify(tmp_transaction))

