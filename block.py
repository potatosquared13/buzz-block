import helpers
from datetime import datetime
from transaction import *

class Block:
    def __init__(self, index, previous_hash, transactions):
        self.index = index
        self.proof = 0
        self.previous_hash = previous_hash
        self.transactions = transactions
        self.timestamp = datetime.now().isoformat()

    def display(self):
        print(helpers.jsonify(self))

    @property
    def hash(self):
        import copy
        tmp_block = copy.deepcopy(self)
        del tmp_block.proof
        return helpers.sha256(helpers.jsonify(tmp_block))


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
    def new_block(self):
        verified_transactions = []
        for transaction in self.pending_transactions:
            if transaction.signature:
                verified_transactions.append(transaction)
        previous_proof = self.last_block.proof
        previous_hash = self.last_block.hash
        block = Block(
            index=len(self.blocks),
            previous_hash=previous_hash,
            transactions=verified_transactions
        )
        self.pending_transactions = []
        block.proof = self.mine(previous_proof, block)
        self.blocks.append(block)

    def add_transaction(self, transaction):
        self.pending_transactions.append(transaction)

    def display_pending(self):
        print(helpers.jsonify(self.pending_transactions))

    def display(self):
        print(helpers.jsonify(self))

    @staticmethod
    def mine(previous_proof, block):
        proof = previous_proof
        hash = block.hash
        while True:
            digest = helpers.sha256(str(proof) + str(hash))
            if (digest.startswith('0000')):
                return proof
            proof += 1

    @property
    def last_block(self):
        return self.blocks[-1]
