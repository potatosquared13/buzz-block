import db
import json

from client import Client
from leader import Leader
from transaction import Transaction
from helpers import jsonify
import os.path

from flask import Flask, render_template, url_for, request, redirect
app = Flask(__name__)

# for registration
clients = []
vendors = []
pending_transactions_saved_state = []
invalid_transactions_saved_state = []

node = Leader(10)
if os.path.isfile('blockchain.json') and os.path.isfile('database.db'):
    node.start()

def get_transaction_count():
    tcount = 0
    for block in node.chain.blocks:
        tcount = tcount + len(block.transactions)
    return tcount

def get_pending_count():
    return len(node.chain.pending_transactions)

def get_total_amount():
    amount = 0
    for block in node.chain.blocks:
        for transaction in (t for t in block.transactions if t.transaction == 0 or t.transaction == 2):
            amount = amount + transaction.amount
    return amount

def get_reg_amount():
    reg_amount = 0
    for block in node.chain.blocks:
        for transaction in (t for t in block.transactions if t.transaction == 0):
            reg_amount = reg_amount + 25
    return reg_amount

def get_transactions():
    global pending_transactions_saved_state
    global invalid_transactions_saved_state
    if (not pending_transactions_saved_state):
        pending_transactions_saved_state = node.chain.pending_transactions.copy()
    if (not invalid_transactions_saved_state):
        invalid_transactions_saved_state = node.invalid_transactions.copy()
    pending_transactions_saved_state = node.chain.pending_transactions.copy()
    invalid_transactions_saved_state = node.invalid_transactions.copy()
    t_senders = []
    t_recipients = []
    pt_senders = []
    pt_recipients = []
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
    for pt in node.chain.pending_transactions:
        if (pt.transaction == 0):
            pt_senders.append('Admin')
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
                pt_senders.append('unnamed')
            pt_recipient = db.search_vendor(pt.address)
            if pt_recipient is not None:
                pt_recipients.append(pt_recipient)
            else:
                pt_recipients.append('unnamed')
        elif (pt.transaction == 2):
            pt_senders.append('Admin')
            pt_recipient = db.search_user(pt.address)
            if pt_recipient is not None:
                pt_recipients.append(pt_recipient)
            else:
                pt_recipients.append('unnamed')
        elif (pt.transaction == 3):
            pt_senders.append('Admin')
            pt_recipient = db.search_user(pt.address)
            if pt_recipient is not None:
                pt_recipients.append(pt_recipient)
            else:
                pt_recipients.append('unnamed')
    return render_template('transactions.html', pcount=get_pending_count(), tcount=get_transaction_count(), acount=get_total_amount(), blocks=node.chain.blocks, t_senders=t_senders, t_recipients=t_recipients, pending_transactions=pending_transactions_saved_state, pt_senders=pt_senders, pt_recipients=pt_recipients, invalid_transactions=invalid_transactions_saved_state)

@app.route('/get_vendor_transactions')
def get_vendor_transactions():
    vendors = db.get_vendors()
    vendor = request.args.get('vendor')
    vendor_requested = db.search_vendor(vendor)
    transactions = [t for sublist in [b.transactions for b in node.chain.blocks] for t in sublist if t.address == vendor]
    total = 0
    for t in transactions:
        total += t.amount
    return render_template('reportgeneration.html', vendor_requested=vendor_requested, vendors=vendors, transactions=transactions, t_length=len(transactions), t_total=total, amount=get_total_amount(), reg_amount=get_reg_amount())

@app.route('/')
def home():
    url_for('static', filename='js/register.js')
    url_for('static', filename='css/style.css')
    return get_transactions()

@app.route('/accounts')
def accounts():
    return render_template('registration.html', ccount=len(db.get_users()), vcount=len(db.get_vendors()))

@app.route('/accounts/users')
def user_registration():
    return render_template('registration_user.html', users=db.get_users())

@app.route('/accounts/vendors')
def vendor_registration():
    return render_template('registration_vendor.html', vendors=db.get_vendors(), blockchain=1 if node.chain.blocks else 0)

@app.route('/transactions')
def overview():
    url_for('static', filename='js/transactions.js')
    url_for('static', filename='css/style.css')
    return get_transactions()

@app.route('/report')
def report():
    vendors = db.get_vendors()
    return render_template('reportgeneration.html', vendor_requested=None, vendors=vendors, transactions=[], t_length=0, t_total=0, amount=get_total_amount(), reg_amount=get_reg_amount())

@app.route('/register_client', methods=['POST'])
def register_client():
    name = request.args.get('name')
    amount = request.args.get('amount')
    client = Client(name)
    client.export('clients/users')
    if (not bool(request.args.get('replace'))):
        contact = request.args.get('contact')
        db.insert_user(client, contact, amount)
        if (node.chain.blocks):
            if (not node.running.is_set()):
                node.start()
            node.create_account(client.identity[:96], amount)
        else:
            clients.append((client, contact, amount))
    else:
        old_id = request.args.get('identity')
        node.blacklist_account(old_id)
        db.replace_id(old_id, client.identity[:96])
        node.create_account(client.identity[:96], amount)
    return ''

@app.route('/register_vendor', methods=['POST'])
def register_vendor():
    name = request.args.get('name')
    contact = request.args.get('contact')
    btype = request.args.get('type')
    client = Client(name)
    client.export('clients/vendors')
    db.insert_vendor(client, contact, btype)
    vendors.append((name, contact, btype))
    return ''

@app.route('/finalize')
def finalize():
    if (not node.chain.blocks):
        transactions = []
        for client in clients:
            t = Transaction(0, node.client.identity, client[0].identity[:96], client[2])
            node.client.sign(t)
            transactions.append(t)
        node.chain.genesis(transactions)
        node.chain.export()
    return redirect('/transactions')

# for toggling the node
@app.route('/toggle')
def toggle():
    if node.running.is_set():
        node.stop()
    else:
        node.start()
    return ''

@app.route('/check_toggle')
def check_toggle():
    if node.running.is_set():
        return '1'
    return '0'

@app.route('/check_transactions_changed', methods=['POST'])
def check_transactions_changed():
    global pending_transactions_saved_state
    global invalid_transactions_saved_state
    if (pending_transactions_saved_state != node.chain.pending_transactions.copy() or invalid_transactions_saved_state != node.invalid_transactions.copy()):
        return 'good'
    else:
        return ''

@app.route('/add_funds', methods=['POST'])
def add_funds():
    identity = request.args.get('identity')
    amount = request.args.get('amount')
    node.add_funds(identity, amount)
    return ''