import db

from client import Client
from tracker import Tracker
from transaction import Transaction

from flask import Flask

# for registration
clients = []
transactions = []

t = Tracker()

# create a client and a transaction to add balance into the blockchain
# name should be a string, amount should be a float or int
def create_client(name, amount):
    c = Client(name)
    clients.append((c, amount))
    transactions.append(Transaction("genesis", c.identity, amount))

# create the genesis block, which introduces the initial balance for all clients to the blockchain
# so that the balance can be determined by reading through the blockchain in the future
def finalize():
    for c in clients:
        db.insert(c[0], c[1])
    t.chain.genesis(transactions)
