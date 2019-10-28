import db
import time
from leader import Leader
from client import Client

print("load clients")
c6 = Client(filename="clients/users/matsubara-kanon.key").identity[:96]
c9 = Client(filename="clients/users/hikawa-sayo.key").identity[:96]
c0 = Client(filename="clients/users/hikawa-hina.key").identity[:96]

print("load leader node")
node = Leader(10)
node.start()

if (input("Press enter to add funds to accounts ") == 'q'):
    node.stop()

node.add_funds(c0, 200)
node.add_funds(c9, 200)

if (input("Press enter to blacklist account ") == 'q'):
    node.stop()

node.blacklist_account(c6)
r = Client("Matsubara, Kanon")
db.replace_id(c6, r.identity[:96])
node.create_account(r.identity[:96], db.search_user(c6).pending_balance)

print("done")