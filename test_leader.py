import time
from leader import Leader
from client import Client

print("load clients")
c1 = Client(filename="clients/ushigome-rimi.key")
c2 = Client(filename="clients/yamabuki-saaya.key")
c3 = Client(filename="clients/toyama-kasumi.key")
c4 = Client(filename="clients/ichigaya-arisa.key")
c5 = Client(filename="clients/hanazono-otae.key")
c6 = Client(filename="clients/matsubara-kanon.key")
c7 = Client(filename="clients/imai-lisa.key")
c8 = Client(filename="clients/minato-yukina.key")
c9 = Client(filename="clients/hikawa-sayo.key")
c0 = Client(filename="clients/hikawa-hina.key")

print("load leader node")
node = Leader(10)
node.start()

if (input("Press enter to add funds to accounts ") == 'q'):
    node.stop()
    exit()

node.add_funds(c0.identity[:96], 200)
node.add_funds(c9.identity[:96], 200)

if (input("Press enter to blacklist account ") == 'q'):
    node.stop()
    exit()

node.blacklist_account(c9.identity[:96])

print("done")