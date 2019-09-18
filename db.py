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
    c.execute('''create table if not exists clients
                 (name text, identity text, contact text, is_vendor boolean not null check(is_vendor in (0, 1)), current_balance real, pending_balance real, unique(name, identity))''')

def insert(client, contact, amount, is_vendor=0):
    with conn:
        c.execute("insert into clients values(?, ?, ?, ?, ?, ?)", (client.name, client.identity, contact, is_vendor, amount, amount,))

def update_balance(identity):
    # change balance to pending_balance
    with conn:
        lock.acquire()
        c.execute("update clients set current_balance=(select pending_balance from clients where identity=?) where identity=?", (identity, identity,))
        lock.release()

def update_pending(sender, recipient=None, amount=None):
    # get current pending_balance
    sender_balance = 0
    recipient_balance = 0
    lock.acquire()
    with conn:
        if (recipient is not None):
            c.execute("select pending_balance from clients where identity=?", (recipient,))
            recipient_balance=c.fetchone()[0]
            recipient_balance += amount
            c.execute("update clients set pending_balance=? where identity=?", (recipient_balance, recipient))
        if (sender is not None):
            c.execute("select pending_balance from clients where identity=?", (sender,))
            sender_balance=c.fetchone()[0]
            sender_balance -= amount
            c.execute("update clients set pending_balance=? where identity=?", (sender_balance, sender))
    lock.release()

# client object to be used for printing search results
class Entry:
    def __init__(self, name, identity, contact, is_vendor, current_balance, pending_balance):
        self.name = name
        self.identity = identity
        self.contact = contact
        self.is_vendor = "yes" if is_vendor else "no"
        self.current_balance = current_balance
        self.pending_balance = pending_balance

# search the database for clients either by partial name or identity
def search(string):
    e = None
    with conn:
        try:
            lock.acquire(True)
            c.execute("select * from clients where name like ? or identity=?", ('%{}%'.format(string),'{}'.format(string),))
            e = c.fetchone()
            if (e is not None):
                entry = Entry(e[0], e[1], e[2], e[3], e[4], e[5])
            else:
                entry = None
        finally:
            lock.release()
    return entry

