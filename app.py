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
saved_state_initialized = False
pending_transactions_saved_state = None

node = Leader()

def get_transactions():
    t_senders = []
    t_recipients = []
    pt_senders = []
    pt_recipients = []
    if pending_transactions_saved_state != node.pending_transactions:
        pending_transactions_saved_state = node.pending_transactions
    for block in node.chain.blocks:
        for t in block.transactions:
            t_sender = db.search(t.sender)
            if t_sender is not None:
                t_senders.append(t_sender)
            else:
                t_senders.append('unnamed')
            t_recipient = db.search(t.address)
            if t_recipient is not None:
                t_recipients.append(t_recipient)
            else:
                t_recipients.append('unnamed')
    for pt in node.pending_transactions:
        pt_sender = db.search(pt.sender)
        if pt_sender is not None:
            pt_senders.append(pt_sender)
        else:
            pt_senders.append('unnamed')
        pt_recipient = db.search(pt.address)
        if pt_recipient is not None:
            pt_recipients.append(pt_recipient)
        else:
            pt_recipients.append('unnamed')
    return render_template('transactions.html', blocks=node.chain.blocks, t_senders=t_senders, t_recipients=t_recipients, pending_transactions=node.pending_transactions, pt_senders=pt_senders, pt_recipients=pt_recipients)

@app.route('/')
def home():
    url_for('static', filename='js/register.js')
    url_for('static', filename='css/style.css')
    return render_template('registration.html')

@app.route('/transactions')
def overview():
    if not saved_state_initialized:
        pending_transactions_saved_state = node.pending_transactions
        saved_state_initialized = True
    url_for('static', filename='js/transactions.js')
    url_for('static', filename='css/style.css')
    return get_transactions()

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

@app.route('/finalize')
def finalize():
    transactions = []
    for client in clients:
        c = Client(client[0])
        c.export()
        db.insert(c, client[1], client[2])
        transactions.append(Transaction(1, node.client.identity, c.identity[:96], client[2]))
    for vendor in vendors:
        v = Client(vendor[0])
        v.export()
        db.insert(v, vendor[1], 0, 1)
    node.chain.genesis(transactions)
    node.chain.export()
    return get_transactions()

# for toggling the leader
@app.route('/toggle')
def toggle():
    if node.active:
        node.stop()
    else:
        node.start()

@app.route('/check_transactions_changed')
def check_transactions_changed():
    if pending_transactions_saved_state != node.pending_transactions:
        return get_transactions()
    else:
        return ''