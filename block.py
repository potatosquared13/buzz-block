import helpers
from copy import deepcopy
from datetime import datetime
from transaction import *

class Block:
    def __init__(self, index, previous_hash, transactions):
        self.index = index
        self.nonce = 0
        self.previous_hash = previous_hash
        self.timestamp = datetime.now().isoformat()
        self.transactions = transactions

    def json(self):
        return helpers.jsonify(self)

    @property
    def hash(self):
        tmp_block = deepcopy(self)
        del tmp_block.nonce
        return helpers.sha256(helpers.jsonify(tmp_block)).hexdigest()


class Blockchain:
    def __init__(self):
        self.blocks = []
        self.pending_transactions = []
        self.genesis()

    # create an empty block for the first block
    def genesis(self):
        block = Block(
            index=0,
            previous_hash=0,
            transactions=[]
        )
        self.blocks.append(block)

    # adds all verified pending transactions to block
    # and creates a new one
    # NOTE: transactions that have not been verified are
    # REMOVED COMPLETELY, and don't stay in pending_transactions
    def write_block(self):
        previous_nonce = self.last_block.nonce
        previous_hash = self.last_block.hash
        block = Block(
            index=len(self.blocks),
            previous_hash=previous_hash,
            transactions=deepcopy(self.pending_transactions)
        )
        self.pending_transactions = []
        block.nonce = self.mine(previous_nonce, block)
        self.blocks.append(block)

    def add_transaction(self, transaction):
        self.pending_transactions.append(transaction)

    @property
    def transactions(self):
        return helpers.jsonify(self.pending_transactions)

    @property
    def json(self):
        return helpers.jsonify(self)

    @property
    def last_block(self):
        return self.blocks[-1]

    @staticmethod
    def mine(previous_nonce, block):
        nonce = previous_nonce
        hash = block.hash
        while True:
            digest = helpers.sha256(str(nonce) + str(hash)).hexdigest()
            if (digest.startswith('0000')):
                return nonce
            nonce += 1

