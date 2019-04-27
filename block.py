from helpers import *
from datetime import datetime


class Block:
    def __init__(self, index, previous_hash, transactions):
        self.index = index
        self.proof = 0
        self.previous_hash = previous_hash
        self.transactions = transactions
        self.timestamp = datetime.now()

    def display(self):
        print("====")
        print("block:\t\t" + str(self.index))
        print("proof:\t\t" + str(self.proof))
        for transaction in self.transactions:
            transaction.display()
        print("====")

    @property
    def block_hash(self):
        block_string = "{}{}{}{}".format(self.index, self.previous_hash,
                                         self.transactions, self.timestamp)
        return sha256(block_string)


class Blockchain:
    def __init__(self):
        self.blocks = []
        self.pending_transactions = []
        self.new_block(0)

    def new_block(self, previous_hash):
        # TODO verify transactions before adding to block
        block = Block(
            index=len(self.blocks),
            previous_hash=previous_hash,
            transactions=self.pending_transactions,
        )
        block.proof = self.mine(block)
        self.pending_transactions = []
        self.blocks.append(block)

    def add_transaction(self, transaction):
        self.pending_transactions.append(transaction)

    def display(self):
        print("length: " + str(len(self.blocks)) + " blocks")
        for n in range(len(self.blocks)):
            print("========")
            block = self.blocks[n]
            block.display()
            print("========")

    @staticmethod
    def mine(block):
        print("generating proof of work... ", end='')
        proof = 0
        block_hash = block.block_hash
        while True:
            digest = sha256(str(proof) + str(block_hash))
            if (digest.startswith('00000000')):
                print(str(proof))
                return proof
            proof += 1

    @property
    def last_block(self):
        return self.blocks[-1]
