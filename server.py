from json import loads as json_loads
from binascii import unhexlify as unhex
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5

import os.path

import db
from block import *
from transaction import Transaction

def new_transaction(transaction_json):
    tmp = json_loads(transaction_json)
    transaction = Transaction(tmp['sender'], tmp['recipient'], tmp['amount'])
    transaction.timestamp = tmp['timestamp']
    transaction.signature = tmp['signature']
    key = RSA.import_key(unhex(transaction.recipient))
    signature = unhex(transaction.signature)
    hash = transaction.hash
    if PKCS1_v1_5.new(key).verify(hash, signature):
        # TODO check if sender.balance > amount
        db.update_pending(transaction.sender, transaction.recipient, transaction.amount)
        chain.add_transaction(transaction)
    else:
        print("transaction verification failed, discarding.")
        # TODO send message to sender that transaction can't be verified

def new_block():
    # go through pending_transactions and make a set of affected accounts
    affected = set()
    for transaction in chain.pending_transactions:
        affected.add(transaction.sender)
        affected.add(transaction.recipient)
    for identity in affected:
        db.update_balance(identity)
    chain.write_block()

def save_state():
    import json
    json.dump(chain, open('blockchain.json', 'w'), default=lambda o: o.__dict__, indent=4)
    # import pickle
    # pickle.dump(chain, open('blockchain.dat', 'wb'))

def load_state():
    import json
    global chain
    i = 0
    chain_json = json.load(open('blockchain.json', 'r'))
    for bl in chain_json['blocks']:
        transactions = []
        for tr in bl['transactions']:
            tmp = Transaction(tr['sender'], tr['recipient'], tr['amount'])
            tmp.timestamp = tr['timestamp']
            tmp.signature = tr['signature']
            transactions.append(tmp)
        tmp = Block(bl['index'], bl['previous_hash'], transactions)
        tmp.nonce = bl['nonce']
        tmp.timestamp = bl['timestamp']
        chain.blocks.append(tmp)
    for pt in chain_json['pending_transactions']:
        tmp = Transaction(pt['sender'], pt['recipient'], pt['amount'])
        tmp.timestamp = pt['timestamp']
        tmp.signature = pt['signature']
        chain.pending_transactions.append(tmp)


chain = Blockchain()
if(os.path.isfile('./blockchain.json')):
    load_state()
else:
    chain.genesis()

