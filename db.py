import sqlite3

import helpers

# open connection to database
conn = sqlite3.connect('clients.db')
c = conn.cursor()

# create database if it doesn't exist
with conn:
    c.execute('''create table if not exists clients
                 (name text, identity text, balance real, balance_pending real, unique(name))''')

# insert initial client information to database. to be called in client.Client.__init__()
def insert(client, amount):
    with conn:
        c.execute("insert into clients values(?, ?, ?, 0)", (client.name, client.identity, amount,))

# change a client's balance. to be called in block.Blockchain.new_block()
def update(identity, amount):
    # change balance to pending_balance
    # set pending_balance to 0
    pass

# change a client's pending balance. to be called in block.Blockchain.add_transaction()
def update_pending(identity, amount):
    # get current balance and add amount to it
    # amount can be either positive, indicating being the recipient
    # or negative, indicating being the sender
    pass

# client object to be used for printing search results
class Entry:
    def __init__(self, name, identity, balance, pending_balance):
        self.name = name
        self.identity = identity
        self.balance = balance
        self.pending_balance = pending_balance

# search the database for clients whose name partially matches the input string
def search_by_name(string):
    with conn:
        c.execute("select * from clients where name like ?", ('%{}%'.format(string),))
        list = c.fetchall()
        output = []
        for entry in list:
            e = Entry(entry[0], entry[1], entry[2], entry[3])
            output.append(e)
        return output

# same thing but instead of a list, return JSON output
def search_by_name_json(string):
    return helpers.jsonify(search_by_name(string))

