import db

from client import Client
from tracker import Tracker
from transaction import Transaction

from flask import Flask, render_template, url_for, request
app = Flask(__name__)

# for registration
clients = []
transactions = []

t = Tracker("1111")

# create a client and a transaction to add balance into the blockchain
# name should be a string, amount should be a float or int
def create_client(name, contact, amount, is_vendor):
    c = Client(name)
    clients.append((c, contact, amount, is_vendor))
    transaction = Transaction("add funds", c.identity, amount)
    t.client.sign(transaction)
    transactions.append(transaction)

# create the genesis block, which introduces the initial balance for all clients to the blockchain
# so that the balance can be determined by reading through the blockchain in the future
def finalize():
    for c in clients:
        db.insert(c[0], c[1], c[2], c[3])
    t.chain.genesis(transactions)

@app.route('/', methods=['GET', 'POST'])
def home():
    url_for('static', filename='js/register.js')
    return render_template('register.html', blocks=t.chain.blocks)

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
    for transaction in t.chain.blocks:
        print(transaction.transactions)
    create_client(uname, contact, amt, int(is_vendor))
    return ''