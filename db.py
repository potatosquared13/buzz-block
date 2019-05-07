import sqlite3 as lite
from client import *

conn = lite.connect('clients.db')
c = conn.cursor()

with conn:
    c.execute('''create table if not exists clients
                 (name text, identity text, balance real, balance_pending real)''')

def insert(name, amount):
    client = Client(name)
    with conn:
        c.execute("insert into clients values(?, ?, ?, 0)", (client.name, client.identity, amount,))

def update():
    pass

def search_by_name(name):
    with conn:
        c.execute("select * from clients where name=?", (name,))
        print(c.fetchall())

