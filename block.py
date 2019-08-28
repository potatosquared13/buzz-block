import helpers
from copy import deepcopy
from datetime import datetime
from transaction import Transaction

class Block:
    def __init__(self, previous_hash, transactions):
        self.previous_hash = previous_hash
        # self.timestamp = datetime.now().isoformat()
        self.transactions = transactions

    @property
    def json(self):
        return helpers.jsonify(self)

    @property
    def hash(self):
        tmp_block = deepcopy(self)
        return helpers.sha256(helpers.jsonify(tmp_block))


class Blockchain:
    def __init__(self):
        self.blocks = []

    def genesis(self, transactions):
        if (self.blocks):
            raise Exception("can't create new genesis block; the blockchain is already populated")
        else:
            self.blocks.append(Block(None, transactions))

    @property
    def json(self):
        return helpers.jsonify(self)

    @property
    def last_block(self):
        try:
            return self.blocks[-1]
        except IndexError:
            return Block("0000000000000000000000000000000000000000000000000000000000000000", [])


