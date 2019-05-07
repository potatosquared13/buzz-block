from client import *
from block import *


# blocksize = 10

print("creating 3 clients...")
print("\tclient1 = Client(\"Client 1\")")
client1 = Client("Client 1")
print("\tclient2 = Client(\"Client 2\")")
client2 = Client("Client 2")
print("\tclient3 = Client(\"Client 3\")")
client3 = Client("Client 3")

print("creating 4 sample transactions...")
print("\tt0 = Transaction(client1.identity, client3.identity, 500)")
t0 = Transaction(client1.identity, client3.identity, 500)
print("\tclient1.sign(t0)")
client1.sign(t0)
print("\tt1 = Transaction(client1.identity, client2.identity, 700)")
t1 = Transaction(client1.identity, client2.identity, 700)
print("\tclient1.sign(t1)")
client1.sign(t1)
print("\tt2 = Transaction(client2.identity, client3.identity, 200)")
t2 = Transaction(client3.identity, client2.identity, 50)
print("\tclient3.sign(t2)")
client3.sign(t2)
print("\tt3 = Transaction(client2.identity, client3.identity, 200)")
t3 = Transaction(client2.identity, client3.identity, 200)

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
