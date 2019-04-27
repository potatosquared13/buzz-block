from client import *
from transaction import *
from block import *
from miner import *


# blocksize = 10

print("creating 3 clients...")
print("aoi = Client()")
aoi = Client()
print("jia = Client()")
jia = Client()
print("meina = Client()")
meina = Client()

print("creating 3 transactions...")
print("t0 = Transaction(aoi, meina, 500)")
t0 = Transaction(aoi, meina, 500)
print("t1 = Transaction(aoi, jia, 700)")
t1 = Transaction(aoi, jia, 700)
print("t2 = Transaction(jia, meina, 100)")
t2 = Transaction(jia, meina, 100)

# print("creating blockchain...")
# print("chain = Blockchain()")
# chain = Blockchain()

# t0 = Transaction(aoi, aoi, 5000.0)
# block0 = Block()
# block0.previous_hash = None
# block0.transactions.append(t0)
# block0.proof = mine(block0)
# digest = hash(block0)
# blockchain.append(block0)
# last_block_hash = digest

# t1 = Transaction(aoi, jia, 1500)
# t2 = Transaction(aoi, meina, 1500)
# t3 = Transaction(jia, aoi, 700)
# t4 = Transaction(meina, jia, 750)
# t5 = Transaction(aoi, jia, 50)
# t6 = Transaction(jia, meina, 500)
# t7 = Transaction(jia, aoi, 100)
# t8 = Transaction(aoi, jia, 100)
# t9 = Transaction(meina, jia, 150)

# last_transaction_index = 0
# block1 = Block()

# for i in range(blocksize if
#                len(pending_transactions) > blocksize
#                else len(pending_transactions)):
#     transaction = pending_transactions[last_transaction_index]
# #   validate (check )
# #   if valid:
#     block1.transactions.append(transaction)
#     last_transaction_index += 1

# block1.previous_hash = last_block_hash
# block1.proof = mine(block1)
# digest = hash(block1)
# blockchain.append(block1)
# last_block_hash = digest
