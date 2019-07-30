from binascii import unhexlify as unhex
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5

import os.path

import db
from block import *
from transaction import Transaction

def is_valid_transaction(transaction):
    key = RSA.import_key(unhex(transaction.recipient))
    signature = unhex(transaction.signature)
    hash = transaction.hash
    return PKCS1_v1_5.new(key).verify(hash, signature)

def rebuild_transaction(transaction_json):
    import json
    tmp = json.loads(transaction_json)
    transaction = Transaction(tmp['sender'], tmp['recipient'], tmp['amount'])
    transaction.timestamp = tmp['timestamp']
    transaction.signature = tmp['signature']
    return transaction

def new_transaction(transaction_json):
    transaction = rebuild_transaction(transaction_json)
    if is_valid_transaction(transaction):
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

def write_state():
    import json
    json.dump(chain, open('blockchain.json', 'w'), default=lambda o: o.__dict__, indent=4)
    # import pickle
    # pickle.dump(chain, open('blockchain.dat', 'wb'))

def read_state():
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
        # verify integrity
        from helpers import sha256
        if (sha256(str(tmp.nonce)+str(tmp.hash)).hexdigest().startswith('000')):
            chain.blocks.append(tmp)
        else:
            import sys
            sys.exit("blockchain.json has been tampered with, cannot continue.")
    for pt in chain_json['pending_transactions']:
        tmp = Transaction(pt['sender'], pt['recipient'], pt['amount'])
        tmp.timestamp = pt['timestamp']
        tmp.signature = pt['signature']
        chain.pending_transactions.append(tmp)


chain = Blockchain()
if(os.path.isfile('./blockchain.json')):
    read_state()
else:
    chain.genesis()

