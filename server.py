# import Flask
from json import loads as json_loads
from binascii import unhexlify as unhex
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5

import db
from block import *

chain = Blockchain()

def new_transaction(transaction_json):
    tmp = json_loads(transaction_json)
    transaction = Transaction(tmp['sender'], tmp['recipient'], tmp['amount'])
    transaction.timestamp = tmp['timestamp']
    transaction.signature = tmp['signature']
    key = RSA.import_key(unhex(transaction.sender))
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

