import db
from random import randint
from client import Client
from leader import Leader
from transaction import Transaction

# users
lc = [Client("Ushigome, Rimi"),
      Client("Yamabuki, Saaya"),
      Client("Toyama, Kasumi"),
      Client("Ichigaya, Arisa"),
      Client("Hanazono, Otae"),
      Client("Matsubara, Kanon"),
      Client("Imai, Lisa"),
      Client("Minato, Yukina"),
      Client("Hikawa, Sayo"),
      Client("Hikawa, Hina")]

# vendors
lv = [Client("Dunkin' Donuts"),
      Client("McDonald's"),
      Client("Aoyama Coffee"),
      Client("Leylam Shawarma")]

# create a node for signing transactions
node = Leader(10)

ts = []
for c in lc:
    amount = randint(7,11)*100
    # add client to database
    db.insert_user(c, str(randint(9100000000, 9299999999)), amount)
    # create transaction and add to transaction list
    t = Transaction(0, node.client.identity, c.identity[:96], amount)
    node.client.sign(t)
    ts.append(t)
    # export client keys for reuse later
    c.export('clients/users')
for v in lv:
    db.insert_vendor(v, str(randint(9100000000, 9299999999)), "Food Service")
    v.export('clients/vendors')

# create genesis block and export initialised blockchain to file
node.chain.genesis(ts)
node.chain.export()