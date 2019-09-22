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
vendors = []
transactions = []

# create a client and a transaction to add balance into the blockchain
# name should be a string, amount should be a float or int
def create_client(name, contact, amount, is_vendor):
    c = Client(name)
    clients.append((c, contact, amount, is_vendor))
    transaction = Transaction(2, "add funds", c.identity, amount)
    l.client.sign(transaction)
    transactions.append(transaction)
    db.insert(c, contact, amount, is_vendor)
    c.export()

def save_client(client_id, name, contact, amount, is_vendor):
    c = Client(name)
    client = {'id': client_id, 'name': name, 'contact': contact, 'amount': amount, 'is_vendor': is_vendor}
    create_client(name, contact, amount, int(is_vendor))
    clients = json.load(open('clients.json', 'r'))
    clients['clients'].append(client)
    storage = open('clients.json', 'w+')
    storage.write(jsonify(clients))

# create the genesis block, which introduces the initial balance for all clients to the blockchain
# so that the balance can be determined by reading through the blockchain in the future
# def finalize_for_real():

@app.route('/')
def home():
    url_for('static', filename='js/register.js')
    url_for('static', filename='css/style.css')
    return render_template('registration.html')

@app.route('/transactions')
def overview():
    url_for('static', filename='js/transactions.js')
    url_for('static', filename='css/style.css')
    return render_template('transactions.html')

@app.route('/register_client', methods=['POST'])
def register_client():
    name = request.args.get('name')
    amount = request.args.get('amount')
    contact = request.args.get('contact')
    clients.append((name, contact, amount))
    print(clients)
    return ''

@app.route('/register_vendor', methods=['POST'])
def register_vendor():
    name = request.args.get('name')
    contact = request.args.get('contact')
    vendors.append((name, contact))
    print('helo')
    print(vendors)
    return ''

@app.route('/finalize', methods=['POST'])
def finalize():
    pass

# for toggling the leader
@app.route('/toggle')
def toggle():
    l = Leader(10)
    l.start() # change here if needed