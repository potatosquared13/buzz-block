# there'll probably only be one node, but should networking be added anyway?
# should the miner be able to verify the validity of transactions?
#   i.e., check if clients have enough funds to carry out the transaction?
#   or should this be baked into the client?
# TODO automatically wait for pending transactions to be 100 before mining
#   or wait 1 minute at most before creating a new block regardless of size

from helpers import *

last_transaction_index = 0


def mine(message):
    i = 0
    print("generating proof of work for block... ", end='')
    while True:
        digest = sha256(str(i) + str(hash(message)))
        if digest.startswith('0000'):
            print(i)
            return digest
        i += 1
