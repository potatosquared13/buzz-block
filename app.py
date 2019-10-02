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
pending_transactions_saved_state = []

node = Leader(10)

def get_transactions():
    global pending_transactions_saved_state
    if len(pending_transactions_saved_state) == 0:
        pending_transactions_saved_state = node.pending_transactions.copy()
    t_senders = []
    t_recipients = []
    pt_senders = []
    pt_recipients = []
    if pending_transactions_saved_state != node.pending_transactions.copy():
        pending_transactions_saved_state = node.pending_transactions.copy()
    for block in node.chain.blocks:
        for t in block.transactions:
            if (t.transaction == 0):
                t_senders.append('Admin')
                t_recipient = db.search_user(t.address)
                if t_recipient is not None:
                    t_recipients.append(t_recipient)
                else:
                    t_recipients.append('unnamed')
            elif (t.transaction == 1):
                t_sender = db.search_user(t.sender)
                if t_sender is not None:
                    t_senders.append(t_sender)
                else:
                    t_senders.append('unnamed')
                t_recipient = db.search_vendor(t.address)
                if t_recipient is not None:
                    t_recipients.append(t_recipient)
                else:
                    t_recipients.append('unnamed')
            elif (t.transaction == 2):
                t_senders.append('Admin')
                t_recipient = db.search_user(t.address)
                if t_recipient is not None:
                    t_recipients.append(t_recipient)
                else:
                    t_recipients.append('unnamed')
            elif (t.transaction == 3):
                t_senders.append('Admin')
                t_recipient = db.search_user(t.address)
                if t_recipient is not None:
                    t_recipients.append(t_recipient)
                else:
                    t_recipients.append('unnamed')
    for pt in node.pending_transactions:
        if (pt.transaction == 0):
            pt_senders.append({name:"Admin"})
            pt_recipient = db.search_user(pt.address)
            if pt_recipient is not None:
                pt_recipients.append(pt_recipient)
            else:
                pt_recipients.append('unnamed')
        elif (pt.transaction == 1):
            pt_sender = db.search_user(pt.sender)
            if pt_sender is not None:
                pt_senders.append(pt_sender)
            else:
                pt_senders.append({name:"unnamed"})
            pt_recipient = db.search_vendor(pt.address)
            if pt_recipient is not None:
                pt_recipients.append(pt_recipient)
            else:
                pt_recipients.append('unnamed')
        elif (pt.transaction == 2):
            pt_senders.append({name:"Admin"})
            pt_recipient = db.search_user(pt.address)
            if pt_recipient is not None:
                pt_recipients.append(pt_recipient)
            else:
                pt_recipients.append('unnamed')
        elif (pt.transaction == 3):
            pt_senders.append({name:"Admin"})
            pt_recipient = db.search_user(pt.address)
            if pt_recipient is not None:
                pt_recipients.append(pt_recipient)
            else:
                pt_recipients.append('unnamed')
    return render_template('transactions.html', blocks=node.chain.blocks, t_senders=t_senders, t_recipients=t_recipients, pending_transactions=pending_transactions_saved_state, pt_senders=pt_senders, pt_recipients=pt_recipients)

@app.route('/get_vendor_transactions')
def get_vendor_transactions():
    vendors = db.get_vendors()
    vendor = request.args.get('vendor')
    transactions = [t for sublist in [b.transactions for b in node.chain.blocks] for t in sublist if t.address == vendor]
    total = 0
    for t in transactions:
        total += t.amount
    return render_template('reportgeneration.html', vendors=vendors, transactions=transactions, t_length=len(transactions), t_total=total)

@app.route('/')
def home():
    url_for('static', filename='js/register.js')
    url_for('static', filename='css/style.css')
    return render_template('registration.html')

@app.route('/transactions')
def overview():
    url_for('static', filename='js/transactions.js')
    url_for('static', filename='css/style.css')
    return get_transactions()

@app.route('/report')
def report():
    vendors = db.get_vendors()
    return render_template('reportgeneration.html', vendors=vendors, transactions=[], t_length=0, t_total=0)

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
    v = Client(vendor[0])
    v.export()
    db.insert(v, vendor[1], 0, 1)
    # vendors.append((name, contact))
    print(vendors)
    return ''

@app.route('/finalize')
def finalize():
    transactions = []
    for client in clients:
        c = Client(client[0])
        c.export()
        db.insert(c, client[1], client[2])
        t = Transaction(0, node.client.identity, c.identity[:96], client[2])
        node.client.sign(t)
        transactions.append(t)
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
        print('node stopped')
    else:
        node.start()
        print('node started')
    return ''

@app.route('/check_transactions_changed', methods=['POST'])
def check_transactions_changed():
    global pending_transactions_saved_state
    if pending_transactions_saved_state != node.pending_transactions.copy():
        print('changes made')
        return 'good'
    else:
        return ''