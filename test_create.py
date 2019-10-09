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
lv = [Client("Dunkin' Donuts", vendor=True),
      Client("McDonald's", vendor=True),
      Client("Aoyama Coffee", vendor=True),
      Client("Leylam Shawarma", vendor=True)]

# create a node for signing transactions
node = Leader(10)

ts = []
for c in lc:
    # add client to database
    db.insert_user(c, str(randint(100000000, 999999999)), 500)
    # create transaction and add to transaction list
    t = Transaction(0, node.client.identity, c.identity[:96], 500)
    node.client.sign(t)
    ts.append(t)
    # export client keys for reuse later
    c.export()
for v in lv:
    db.insert_vendor(v, str(randint(100000000, 999999999)), "Food Service")
    v.export()

# create genesis block and export initialised blockchain to file
node.chain.genesis(ts)
node.chain.export()