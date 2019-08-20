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

    # # create an empty block for the first block
    # def genesis(self):
    #     block = Block(
    #         index=0,
    #         previous_hash="0000000000000000000000000000000000000000000000000000000000000000",
    #         transactions=[]
    #     )
    #     # block.nonce = self.mine(0, block)
    #     self.blocks.append(block)

    # adds all verified pending transactions to block
    # and creates a new one
    # NOTE: transactions that have not been verified are
    # REMOVED COMPLETELY, and don't stay in pending_transactions
    # def write_block(self, new_transactions):
    #     # previous_nonce = self.last_block.nonce
    #     if (len(self.blocks)):
    #         previous_hash = self.last_block.hash
    #     else:
    #         previous_hash = "0000000000000000000000000000000000000000000000000000000000000000"
    #     block = Block(
    #         index=len(self.blocks),
    #         previous_hash=previous_hash,
    #         transactions=new_transactions
    #     )
    #     # self.pending_transactions = []
    #     # block.nonce = self.mine(previous_nonce, block)
    #     self.blocks.append(block)

    # def add_transaction(self, transaction):
    #     self.pending_transactions.append(transaction)

    # @property
    # def transactions(self):
    #     return helpers.jsonify(self.pending_transactions)

    @property
    def json(self):
        return helpers.jsonify(self)

    @property
    def last_block(self):
        try:
            return self.blocks[-1]
        except IndexError:
            return Block("0000000000000000000000000000000000000000000000000000000000000000", [])

    # @staticmethod
    # def mine(previous_nonce, block):
    #     nonce = previous_nonce
    #     hash = block.hash
    #     while True:
    #         digest = helpers.sha256(str(nonce) + hash)
    #         if (digest.startswith('000')):
    #             return nonce
    #         nonce += 1

