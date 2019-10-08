import db
import time
from leader import Leader
from client import Client

print("load clients")
c1 = Client(filename="clients/ushigome-rimi.key").identity[:96]
c2 = Client(filename="clients/yamabuki-saaya.key").identity[:96]
c3 = Client(filename="clients/toyama-kasumi.key").identity[:96]
c4 = Client(filename="clients/ichigaya-arisa.key").identity[:96]
c5 = Client(filename="clients/hanazono-otae.key").identity[:96]
c6 = Client(filename="clients/matsubara-kanon.key").identity[:96]
c7 = Client(filename="clients/imai-lisa.key").identity[:96]
c8 = Client(filename="clients/minato-yukina.key").identity[:96]
c9 = Client(filename="clients/hikawa-sayo.key").identity[:96]
c0 = Client(filename="clients/hikawa-hina.key").identity[:96]

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