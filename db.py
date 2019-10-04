# database functions

import sqlite3
import threading

import helpers

lock = threading.Lock()

# open connection to database
conn = sqlite3.connect('database.db', check_same_thread=False)
c = conn.cursor()

# create database if it doesn't exist
with conn:
    # c.execute('PRAGMA foreign_keys = ON')
    c.execute('''CREATE TABLE IF NOT EXISTS clients
                 (identity TEXT PRIMARY KEY, name TEXT, contact TEXT, UNIQUE(identity, name))''')
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (identity TEXT, initial_balance REAL, UNIQUE(identity), FOREIGN KEY(identity) REFERENCES clients(identity))''')
    c.execute('''CREATE TABLE IF NOT EXISTS vendors
                 (identity TEXT, business_type TEXT, UNIQUE(identity), FOREIGN KEY(identity) REFERENCES clients(identity))''')
    c.execute('''CREATE TABLE IF NOT EXISTS balances
                 (identity, current_balance REAL, pending_balance REAL, FOREIGN KEY(identity) REFERENCES clients(identity))''')

def insert_user(client, contact, amount):
    with conn:
        c.execute("INSERT INTO clients VALUES(?, ?, ?)", (client.identity[:96], client.name, contact,))
        c.execute("INSERT INTO users VALUES(?, ?)", (client.identity[:96], amount,))
        c.execute("INSERT INTO balances VALUES(?, ?, ?)", (client.identity[:96], amount, amount,))

def insert_vendor(client, contact, business_type):
    with conn:
        c.execute("INSERT INTO clients VALUES(?, ?, ?)", (client.identity, client.name, contact))
        c.execute("INSERT INTO vendors VALUES(?, ?)", (client.identity, business_type,))
        c.execute("INSERT INTO balances VALUES(?, ?, ?)", (client.identity, 0, 0,))

def update_balance(identity):
    # change balance to pending_balance
    with conn:
        lock.acquire()
        c.execute("UPDATE balances SET current_balance=(SELECT pending_balance FROM balances WHERE identity=?) WHERE identity=?", (identity, identity,))
        lock.release()

def update_pending(sender, recipient=None, amount=0):
    # get current pending_balance
    sender_balance = 0
    recipient_balance = 0
    lock.acquire()
    with conn:
        if (recipient is not None):
            c.execute("SELECT pending_balance FROM balances WHERE identity=?", (recipient,))
            recipient_balance=c.fetchone()[0]
            recipient_balance += amount
            c.execute("UPDATE balances SET pending_balance=? WHERE identity=?", (recipient_balance, recipient))
        if (sender is not None):
            c.execute("SELECT pending_balance FROM balances WHERE identity=?", (sender,))
            sender_balance=c.fetchone()[0]
            sender_balance -= amount
            c.execute("UPDATE balances SET pending_balance=? WHERE identity=?", (sender_balance, sender))
    lock.release()

# client object to be used for printing search results
class Entry:
    def __init__(self, client_type, identity, name, contact, current_balance, pending_balance):
        self.client_type = client_type
        self.identity = identity
        self.name = name
        self.contact = contact
        self.current_balance = current_balance
        self.pending_balance = pending_balance

def search_user(string):
    e = None
    b = None
    with conn:
        try:
            lock.acquire()
            c.execute("SELECT clients.identity, clients.name, clients.contact, balances.current_balance, balances.pending_balance FROM users INNER JOIN clients ON users.identity=clients.identity INNER JOIN balances ON users.identity=balances.identity WHERE clients.name LIKE ? OR clients.identity=?", ('%{}%'.format(string),'{}'.format(string),))
            e = c.fetchone()
            if (e is not None):
                entry = Entry("user", e[0], e[1], e[2], e[3], e[4])
            else:
                entry = None
        finally:
            lock.release()
    return entry

def search_vendor(string):
    e = None
    b = None
    with conn:
        try:
            lock.acquire()
            c.execute("SELECT clients.identity, clients.name, clients.contact, balances.current_balance, balances.pending_balance FROM vendors INNER JOIN clients ON vendors.identity=clients.identity INNER JOIN balances ON vendors.identity=balances.identity WHERE clients.name LIKE ? OR clients.identity=?", ('%{}%'.format(string),'{}'.format(string),))
            e = c.fetchone()
            if (e is not None):
                entry = Entry("vendor", e[0], e[1], e[2], e[3], e[4])
            else:
                entry = None
        finally:
            lock.release()
    return entry


def get_vendors():
    vendors = []
    with conn:
        try:
            lock.acquire()
            c.execute("SELECT vendors.identity, clients.name, clients.contact, vendors.business_type, balances.current_balance, balances.pending_balance FROM vendors INNER JOIN clients ON vendors.identity=clients.identity INNER JOIN balances ON vendors.identity=balances.identity")
            vendors = c.fetchall()
        finally:
            lock.release()
    return vendors

def get_users():
    users = []
    with conn:
        try:
            lock.acquire()
            c.execute("SELECT users.identity, clients.name, clients.contact, users.initial_balance, balances.current_balance, balances.pending_balance FROM users INNER JOIN clients ON users.identity=clients.identity INNER JOIN balances ON users.identity=balances.identity")
            users = c.fetchall()
        finally:
            lock.release()
    return users

def replace_id(old_identity, new_identity):
    with conn:
        try:
            lock.acquire()
            c.execute("UPDATE clients SET identity=? WHERE identity=?", (new_identity, old_identity,))
            c.execute("UPDATE users SET identity=? WHERE identity=?", (new_identity, old_identity,))
        finally:
            lock.release()