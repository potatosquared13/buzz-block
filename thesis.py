from client import *
from block import *


# blocksize = 10

print("creating 3 clients...")
print("\tclient1 = Client(\"Client 1\", 1000)")
client1 = Client("Client 1", 1000)
print("\tclient2 = Client(\"Client 2\", 0)")
client2 = Client("Client 2", 0)
print("\tclient3 = Client(\"Client 3\", 0)")
client3 = Client("Client 3", 0)

print("creating 4 sample transactions...")
print("\tt0 = Transaction(client1.identity, client3.identity, 150)")
t0 = Transaction(client1.identity, client3.identity, 150)
print("\tclient1.sign(t0)")
client1.sign(t0)
print("\tt1 = Transaction(client1.identity, client2.identity, 250)")
t1 = Transaction(client1.identity, client2.identity, 250)
print("\tclient1.sign(t1)")
client1.sign(t1)
print("\tt2 = Transaction(client2.identity, client3.identity, 50)")
t2 = Transaction(client3.identity, client2.identity, 50)
print("\tclient3.sign(t2)")
client3.sign(t2)
print("\tt3 = Transaction(client2.identity, client3.identity, 100)")
t3 = Transaction(client2.identity, client3.identity, 100)

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
