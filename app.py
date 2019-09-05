import db

from client import Client
from leader import Leader
from transaction import Transaction
from helpers import jsonify
import os.path

from flask import Flask, render_template, url_for, request
app = Flask(__name__)

# for registration
clients = []
transactions = []

l = Leader("1111")

# create a client and a transaction to add balance into the blockchain
# name should be a string, amount should be a float or int
def create_client(name, contact, amount, is_vendor):
    c = Client(name)
    clients.append((c, contact, amount, is_vendor))
    transaction = Transaction("add funds", c.identity, amount)
    l.client.sign(transaction)
    transactions.append(transaction)

# create the genesis block, which introduces the initial balance for all clients to the blockchain
# so that the balance can be determined by reading through the blockchain in the future
# def finalize_for_real():

@app.route('/')
def home():
    if os.path.isfile('./blockchain.json'):
        can_register = False
    else:
        can_register = True
    url_for('static', filename='js/register.js')
    return render_template('register.html', can_register=can_register)

@app.route('/overview')
def overview():
    url_for('static', filename='js/overview.js')
    senders = []
    recipients = []
    for block in l.chain.blocks:
        for transaction in block.transactions:
            sender = db.search(transaction.sender)
            if sender is not None:
                senders.append(sender.name)
            else:
                senders.append('unnamed')
            recipient = db.search(transaction.recipient)
            if recipient is not None:
                recipients.append(recipient.name)
            else:
                recipients.append('unnamed')
    return render_template('overview.html', blocks=l.chain.blocks, senders=senders, recipients=recipients)

@app.route('/register', methods=['POST'])
def register():
    print('good')
    uname = request.args.get('name')
    amt = request.args.get('amount')
    contact = request.args.get('contactNumber')
    is_vendor = request.args.get('isVendor')
    print(uname)
    print(amt)
    print(contact)
    print(is_vendor)
    for transaction in l.chain.blocks:
        print(dir(transaction.transactions[0]))
    create_client(uname, contact, amt, int(is_vendor))
    return ''

@app.route('/finalize', methods=['GET'])
def finalize():
    for c in clients:
        db.insert(c[0], c[1], c[2], c[3])
    l.chain.genesis(transactions)
    l.chain.export()
    # finalize_for_real()
    return render_template('register.html', can_register=False)