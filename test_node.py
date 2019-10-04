import time
from node import Node
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

print("load vendors")
v1 = Node("clients/dunkin-donuts.key")
v2 = Node("clients/mcdonalds.key")
v3 = Node("clients/aoyama-coffee.key", debug=True)
v4 = Node("clients/leylam-shawarma.key")

def stop(): # hammer time
    v1.stop()
    v2.stop()
    v3.stop()
    v4.stop()

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

if (input("Press enter to send transactions ") == 'q'):
    stop()
v2.send_transaction(1, c9, 59)
time.sleep(1)
v1.send_transaction(1, c1, 59)
time.sleep(1)
v1.send_transaction(1, c2, 59)
time.sleep(1)
v1.send_transaction(1, c3, 79)
time.sleep(1)
v1.send_transaction(1, c4, 59)
time.sleep(1)
v1.send_transaction(1, c5, 59)

if (input("Press enter to send transactions ") == 'q'):
    stop()

v2.send_transaction(1, c9, 149)
time.sleep(1)
v2.send_transaction(1, c0, 149)
time.sleep(1)
v2.send_transaction(1, c9, 59)

if (input("Press enter to send transactions ") == 'q'):
    stop()

v3.send_transaction(1, c7, 49)
time.sleep(1)
v3.send_transaction(1, c8, 49)
time.sleep(1)
v3.send_transaction(1, c0, 49)
time.sleep(1)
v2.send_transaction(1, c9, 59)
time.sleep(1)
v3.send_transaction(1, c9, 59)

if (input("Press enter to send transactions ") == 'q'):
    stop()

v4.send_transaction(1, c3, 79)
time.sleep(1)
v4.send_transaction(1, c4, 29)
time.sleep(1)
v2.send_transaction(1, c9, 59)

print("done")