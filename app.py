import db

from client import Client
from tracker import Tracker
from transaction import Transaction

from flask import Flask, render_template, url_for, request
app = Flask(__name__)

# for registration
clients = []
transactions = []

t = Tracker()

# create a client and a transaction to add balance into the blockchain
# name should be a string, amount should be a float or int
def create_client(name, amount, is_vendor):
    c = Client(name)
    clients.append((c, amount, is_vendor))
    transactions.append(Transaction("genesis", c.identity, amount))

# create the genesis block, which introduces the initial balance for all clients to the blockchain
# so that the balance can be determined by reading through the blockchain in the future
def finalize():
    for c in clients:
        db.insert(c[0], c[1], c[2])
    t.chain.genesis(transactions)

@app.route('/', methods=['GET', 'POST'])
def home():
    url_for('static', filename='css/register.css')
    url_for('static', filename='js/register.js')
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register():
    print('good')
    uname = request.args.get('username')
    amt = request.args.get('amount')
    print(uname)
    print(amt)
    for transaction in t.chain.blocks:
        print(transaction.transactions)
    create_client(uname, amt)
    return ''

@app.route('/overview')
def overview():
    return render_template('overview.html', blocks=t.chain.blocks)