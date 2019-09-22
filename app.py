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

node = Leader()

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
    print(vendors)
    return ''

@app.route('/finalize', methods=['POST'])
def finalize():
    transactions = []
    for client in clients:
        c = Client(client[0])
        c.export()
        db.insert(c, client[1], client[2])
        transactions.append(Transaction(1, node.client.identity, c.identity[:96], client[2]))
    for vendor in vendors:
        c = Client(vendor[0])
        c.export()
        db.insert(v, vendor[1], 0, 1)
    node.chain.genesis(transactions)
    node.chain.export()
    return ''

# for toggling the leader
@app.route('/toggle')
def toggle():
    l = Leader(10)
    l.start() # change here if needed