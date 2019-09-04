# data structures for blockchain

import helpers
from datetime import datetime
from transaction import Transaction

class Block:
    def __init__(self, previous_hash, transactions):
        self.previous_hash = previous_hash
        self.transactions = transactions

    @property
    def json(self):
        return helpers.jsonify(self)

    @property
    def hash(self):
        return helpers.sha256(helpers.jsonify(self))

class Blockchain:
    def __init__(self):
        self.blocks = []

    def genesis(self, transactions):
        if (self.blocks):
            raise Exception("blockchain already exists")
        else:
            self.blocks.append(Block("0".zfill(64), transactions))

    @property
    def json(self):
        return helpers.jsonify(self)

    @property
    def last_block(self):
        return self.blocks[-1]

