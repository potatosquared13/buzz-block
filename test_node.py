import db
import time
from node import Node
from client import Client

print("load clients")
c1 = Client(filename="clients/users/ushigome-rimi.key").identity[:96]
c2 = Client(filename="clients/users/yamabuki-saaya.key").identity[:96]
c3 = Client(filename="clients/users/toyama-kasumi.key").identity[:96]
c4 = Client(filename="clients/users/ichigaya-arisa.key").identity[:96]
c5 = Client(filename="clients/users/hanazono-otae.key").identity[:96]
c6 = Client(filename="clients/users/matsubara-kanon.key").identity[:96]
c7 = Client(filename="clients/users/imai-lisa.key").identity[:96]
c8 = Client(filename="clients/users/minato-yukina.key").identity[:96]
c9 = Client(filename="clients/users/hikawa-sayo.key").identity[:96]
c0 = Client(filename="clients/users/hikawa-hina.key").identity[:96]

print("load vendors")
v1 = Node("clients/vendors/dunkin-donuts.key")
v2 = Node("clients/vendors/mcdonalds.key")
v3 = Node("clients/vendors/aoyama-coffee.key", debug=True)
v4 = Node("clients/vendors/leylam-shawarma.key")
v5 = Node("clients/vendors/tawawa-gifts-souvenirs.key")

def stop(): # hammer time
    v1.stop()
    v2.stop()
    v3.stop()
    v4.stop()
    v5.stop()

print("start vendors")
v1.start()
v2.start()
v3.start()
v4.start()
v5.start()

time.sleep(2)

v1.get_peers()
v2.get_peers()
v3.get_peers()
v4.get_peers()
v5.get_peers()

time.sleep(2)

if (input("Press enter to send transactions ") == 'q'):
    stop()
v1.send_transaction(c1, 59)
time.sleep(1)
v1.send_transaction(c2, 59)
time.sleep(1)
v1.send_transaction(c3, 79)
time.sleep(1)
v1.send_transaction(c4, 59)
time.sleep(1)
v1.send_transaction(c5, 59)
time.sleep(1)
v2.send_transaction(c9, 59)
time.sleep(1)
v2.send_transaction(c6, 159)

if (input("Press enter to send transactions ") == 'q'):
    stop()

v2.send_transaction(c9, 149)
time.sleep(1)
v2.send_transaction(c0, 149)
time.sleep(1)
v2.send_transaction(c9, 59)
time.sleep(1)
v3.send_transaction(c6, 55)

if (input("Press enter to send transactions ") == 'q'):
    stop()

v3.send_transaction(c7, 49)
time.sleep(1)
v3.send_transaction(c8, 49)
time.sleep(1)
v3.send_transaction(c0, 49)
time.sleep(1)
v2.send_transaction(c6, 198)

if (input("Press enter to send transactions ") == 'q'):
    stop()

v4.send_transaction(c3, 79)
time.sleep(1)
v4.send_transaction(c4, 29)
time.sleep(1)
v2.send_transaction(db.search_user("Matsubara, Kanon").identity, 59)
time.sleep(1)
v1.send_transaction(c3, 79)
time.sleep(1)
v1.send_transaction(c4, 59)
time.sleep(1)
v5.send_transaction(c7, 100)
time.sleep(1)
v5.send_transaction(c1, 100)

if (input("Press enter to send transactions ") == 'q'):
    stop()

v3.send_transaction(c1, 59)
v3.send_transaction(c2, 59)
v3.send_transaction(c3, 69)
v3.send_transaction(c4, 59)
v3.send_transaction(c5, 59)
v3.send_transaction(c6, 69)
v3.send_transaction(c7, 59)
v3.send_transaction(c8, 59)
v3.send_transaction(c9, 59)
v3.send_transaction(c0, 69)

print("done")