import sqlite3

import helpers

# open connection to database
conn = sqlite3.connect('database.db')
c = conn.cursor()

# create database if it doesn't exist
with conn:
    c.execute('''create table if not exists clients
                 (name text, identity text, current_balance real, pending_balance real, unique(name))''')

def insert(client, amount):
    with conn:
        c.execute("insert into clients values(?, ?, ?, ?)", (client.name, client.identity, amount, amount,))

def update_balance(identity):
    # change balance to pending_balance
    with conn:
        c.execute("update clients set current_balance=(select pending_balance from clients where identity=?) where identity=?", (identity, identity,))

def update_pending(sender, recipient, amount):
    # get current pending_balance
    sender_balance=0
    recipient_balance=0
    with conn:
        c.execute("select pending_balance from clients where identity=?", (sender,))
        sender_balance=c.fetchone()[0]
        c.execute("select pending_balance from clients where identity=?", (recipient,))
        recipient_balance=c.fetchone()[0]
    # adjust according to amount
    sender_balance -= amount
    recipient_balance += amount
    # update entries in database
    with conn:
        c.execute("update clients set pending_balance=? where identity=?", (sender_balance, sender))
        c.execute("update clients set pending_balance=? where identity=?", (recipient_balance, recipient))

# client object to be used for printing search results
class Entry:
    def __init__(self, name, identity, current_balance, pending_balance):
        self.name = name
        self.identity = identity
        self.current_balance = current_balance
        self.pending_balance = pending_balance

# search the database for clients either by partial name or identity
def search(string):
    with conn:
        c.execute("select * from clients where name like ? or identity=?", ('%{}%'.format(string),'{}'.format(string),))
        list = c.fetchall()
        output = []
        for entry in list:
            e = Entry(entry[0], entry[1], entry[2], entry[3])
            output.append(e)
        return output

