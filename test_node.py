import time
from node import Node
from client import Client

print("load clients")
c1 = Client(filename="ushigome-rimi.key")
c2 = Client(filename="yamabuki-saaya.key")
c3 = Client(filename="toyama-kasumi.key")
c4 = Client(filename="ichigaya-arisa.key")
c5 = Client(filename="hanazono-otae.key")
c6 = Client(filename="matsubara-kanon.key")
c7 = Client(filename="imai-lisa.key")
c8 = Client(filename="minato-yukina.key")
c9 = Client(filename="hikawa-sayo.key")
c0 = Client(filename="hikawa-hina.key")

print("load vendors")
v1 = Node("dunkin-donuts.key")
v2 = Node("mcdonalds.key")
v3 = Node("aoyama-coffee.key", debug=True)
v4 = Node("leylam-shawarma.key")

print("start vendors")
v1.start()
v2.start()
v3.start()
v4.start()

time.sleep(2)

v1.get_peers()
v2.get_peers()
v3.get_peers()
v4.get_peers()

time.sleep(2)

input("Press enter to start sending transactions ")
v2.send_transaction(1, c9.identity, 59)
v1.send_transaction(1, c1.identity, 59)
v1.send_transaction(1, c2.identity, 59)
v1.send_transaction(1, c3.identity, 79)
v1.send_transaction(1, c4.identity, 59)
v1.send_transaction(1, c5.identity, 59)

time.sleep(2)

v2.send_transaction(1, c9.identity, 149)
v2.send_transaction(1, c0.identity, 149)
v2.send_transaction(1, c9.identity, 59)

time.sleep(2)

v3.send_transaction(1, c7.identity, 49)
v3.send_transaction(1, c8.identity, 49)
v3.send_transaction(1, c0.identity, 49)
v2.send_transaction(1, c9.identity, 59)
v3.send_transaction(1, c9.identity, 59)

time.sleep(2)

v4.send_transaction(1, c3.identity, 79)
v4.send_transaction(1, c4.identity, 29)
v2.send_transaction(1, c9.identity, 59)

print("done")

def stop(): # hammer time
    v1.stop()
    v2.stop()
    v3.stop()
    v4.stop()

