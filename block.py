# data structures for blockchain

import json

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
        self.timestamp = datetime.now().isoformat("T", "seconds")

    def genesis(self, transactions):
        if (self.blocks):
            raise Exception("blockchain already exists")
        else:
            self.blocks.append(Block("0", transactions))

    def new_block(self, block):
        self.blocks.append(block)
        self.timestamp = datetime.now().isoformat("T", "seconds")

    def export(self):
        with open('blockchain.json', 'w') as f:
            f.write(helpers.jsonify(self))

    def rebuild(self, block_json):
        tmp = json.loads(block_json)
        for bl in tmp['blocks']:
            transactions = []
            for tr in bl['transactions']:
                transaction = Transaction(tr['transaction'], tr['sender'], tr['address'], tr['amount'])
                transaction.timestamp = tr['timestamp']
                transaction.signature = tr['signature']
                transactions.append(transaction)
            block = Block(bl['previous_hash'], transactions)
            self.new_block(block)
            self.timestamp = tmp['timestamp']

    @property
    def json(self):
        return helpers.jsonify(self)

    @property
    def last_block(self):
        return self.blocks[-1]

