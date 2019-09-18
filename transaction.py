# transaction structure to be used in blocks

import helpers
from copy import deepcopy
from datetime import datetime

class Transaction:
    def __init__(self, transaction, sender=None, recipient=None, amount=0):
        self.transaction = transaction
        self.sender = sender
        self.address = recipient
        self.amount = float(amount)
        self.timestamp = datetime.now().isoformat("T", "seconds")
        self.signature = None

    @property
    def json(self):
        return helpers.jsonify(self)

    @property
    def hash(self):
        tmp_transaction = deepcopy(self)
        del tmp_transaction.signature
        return helpers.sha256(helpers.jsonify(tmp_transaction))

