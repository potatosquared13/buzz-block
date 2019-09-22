import db
import json

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

l = Leader(10)
l.start()

# create a client and a transaction to add balance into the blockchain
# name should be a string, amount should be a float or int
def create_client(name, contact, amount, is_vendor):
    c = Client(name)
    clients.append((c, contact, amount, is_vendor))
    transaction = Transaction(2, "add funds", c.identity, amount)
    l.client.sign(transaction)
    transactions.append(transaction)

def save_client(client_id, name, contact, amount, is_vendor):
    c = Client(name)
    client = {'id': client_id, 'name': name, 'contact': contact, 'amount': amount, 'is_vendor': is_vendor}
    create_client(name, contact, amount, int(is_vendor))
    clients = json.load(open('clients.json', 'r'))
    clients['clients'].append(client)
    storage = open('clients.json', 'w+')
    storage.write(jsonify(clients))

def add_funds(client_id, amount):
    l.add_funds(client_id, amount)
    return ''

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
    url_for('static', filename='css/style.css')
    clients = []
    client_file = json.load(open('clients.json', 'r'))
    if len(client_file['clients']) > 0:
        for client in client_file['clients']:
            create_client(client['name'], client['contact'], client['amount'], int(client['is_vendor']))
        for client in clients:
            print(client)
    return render_template('register.html', can_register=can_register, clients=clients)

@app.route('/overview')
def overview():
    url_for('static', filename='js/overview.js')
    url_for('static', filename='css/style.css')
    senders = []
    recipients = []
    for block in l.chain.blocks:
        for transaction in block.transactions:
            sender = db.search(transaction.sender)
            if sender is not None:
                senders.append(sender)
            else:
                senders.append('unnamed')
            recipient = db.search(transaction.address)
            if recipient is not None:
                recipients.append(recipient)
            else:
                recipients.append('unnamed')
    print(l.pending_transactions)
    print(senders)
    print(recipients)
    return render_template('overview.html', blocks=l.chain.blocks, senders=senders, recipients=recipients)

@app.route('/register', methods=['POST'])
def register():
    print('good')
    client_id = request.args.get('clientId')
    uname = request.args.get('name')
    amt = request.args.get('amount')
    contact = request.args.get('contactNumber')
    is_vendor = request.args.get('isVendor')
    save_client(client_id, uname, contact, amt, int(is_vendor))
    return ''

@app.route('/clients')
def get_clients():
    f = open('clients.json', 'r+')
    lines = f.readlines()
    result_string = ''
    for line in lines:
        result_string += line
    print(result_string)

@app.route('/finalize', methods=['GET'])
def finalize():
    url_for('static', filename='css/style.css')
    for c in clients:
        db.insert(c[0], c[1], c[2], c[3])
        c[0].export()
    l.chain.genesis(transactions)
    l.chain.export()
    # finalize_for_real()
    return render_template('register.html', can_register=False)

@app.route('/close')
def close():
    l.stop()
    return 'leader has been stopped'