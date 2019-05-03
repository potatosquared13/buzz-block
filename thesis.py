from client import *
from block import *


# blocksize = 10

print("creating 3 clients...")
print("\taoi = Client()")
aoi = Client()
print("\tjia = Client()")
jia = Client()
print("\tmeina = Client()")
meina = Client()

print("creating 4 sample transactions...")
print("\tt0 = Transaction(aoi.identity, meina.identity, 500)")
t0 = Transaction(aoi.identity, meina.identity, 500)
print("\taoi.sign(t0)")
aoi.sign(t0)
print("\tt1 = Transaction(aoi.identity, jia.identity, 700)")
t1 = Transaction(aoi.identity, jia.identity, 700)
print("\taoi.sign(t1)")
aoi.sign(t1)
print("\tt2 = Transaction(jia.identity, meina.identity, 200)")
t2 = Transaction(meina.identity, jia.identity, 50)
print("\tmeina.sign(t2)")
meina.sign(t2)
print("\tt3 = Transaction(jia.identity, meina.identity, 200)")
t3 = Transaction(jia.identity, meina.identity, 200)

print("creating blockchain...")
print("\tchain = Blockchain()")
chain = Blockchain()

print("adding transactions to chain...")
print("\tchain.add_transaction(t0)")
chain.add_transaction(t0)
print("\tchain.add_transaction(t1)")
chain.add_transaction(t1)
print("\tchain.add_transaction(t3)")
chain.add_transaction(t3)
# print("creating new block and initialising new one...")
# print("\tchain.new_block()")
# chain.new_block()
