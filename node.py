import sys
import time
import json
import zlib
import errno
import base64
import socket
import logging
import os.path
import threading
import cryptography.exceptions

import helpers
from block import Blockchain, Block
from client import Client
from binascii import hexlify, unhexlify
from transaction import Transaction
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

# message type
RESPONSE = 0
TRANSACTION = 1
BFTSTART = 2
BFTVERIFY = 3
BALANCEREQUEST = 4
BALANCE = 5
CHAINREQUEST = 6
CHAIN = 7
PEER = 8
LEADER = 9
UNKNOWN = 10

# object for organising connected peers
class Peer():
    def __init__(self, sock, addr, identity):
        self.socket = sock
        self.address = addr
        self.identity = identity

# object for connecting to peers and listening for messages from them
class Node(threading.Thread):
    def __init__(self, filename, debug=False):
        if (os.path.isfile('./blockchain.json')):
            self.chain = Blockchain()
            self.chain.rebuild(open('./blockchain.json', 'r').read())
        self.client = Client(filename=filename)
        self.active = False
        self.address = None
        self.peers = set()
        self.leader = None
        self.pending_block = None
        self.pending_transactions = []
        self.hashes = []
        self.chain = Blockchain()
        if(os.path.isfile('./blockchain.json')):
            self.chain.rebuild(open('./blockchain.json', 'r').read())
        # root = logging.getLogger()
        # handler = logging.StreamHandler(sys.stdout)
        if (debug):
            logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.DEBUG)
        else:
            logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

    ######## Networking functions ########

    # tell node to start listening for messages
    def start(self):
        if (not self.active):
            self.active = True
            threading.Thread(target=self.accept_connections).start()
            threading.Thread(target=self.listen).start()

    # tell node to stop listening and close existing connections
    def stop(self):
        if (self.active):
            self.active = False
            for peer in self.peers.copy():
                if (not peer.socket._closed):
                    peer.socket.shutdown(socket.SHUT_RDWR)
            logging.debug("Stopped")

    # wait for a peer to connect and then keep an open connection
    def accept_connections(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(([ip for ip in socket.gethostbyname_ex(socket.getfqdn())[2] if not ip.startswith('169')][0], 0))
            self.address = sock.getsockname()
            logging.debug(self.address)
            sock.settimeout(4)
            logging.debug(f"Listening for connections")
            while self.active:
                try:
                    sock.listen(8)
                    c, addr = sock.accept()
                    id = hexlify(c.recv(96)).decode()
                    if (not [p for p in self.peers if p.identity == id]):
                        peer = Peer(c, c.getpeername(), id)
                        self.peers.add(peer)
                        c.sendall(unhexlify(self.client.identity))
                        threading.Thread(target=self.handle_connection, args=(peer,)).start()
                        if (self.leader is not None):
                            if (self.leader.address == self.address):
                                logging.info("asserting dominance")
                                self.send(c, LEADER, self.client.identity)
                    else:
                        c.shutdown(socket.SHUT_RDWR)
                        c.close()
                except socket.timeout:
                    continue
                except socket.error as e:
                    logging.error(f"Node.accept_connections(): {e}")

    # connect to a peer
    def connect(self, addr):
        if (not self.active):
            logging.error("call Node.start() first.")
        elif (addr != self.address):
            peer = [p for p in self.peers if p.address == addr]
            if (not peer):
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                try:
                    # sock.bind(self.address)
                    logging.debug(f"Attempting to connect to {addr[0]}:{addr[1]}")
                    sock.connect(addr)
                    sock.settimeout(4)
                    sock.sendall(unhexlify(self.client.identity))
                    id = hexlify(sock.recv(96)).decode()
                    peer = Peer(sock, addr, id)
                    self.peers.add(peer)
                    threading.Thread(target=self.handle_connection, args=(peer,)).start()
                    if (self.leader is not None):
                        if (self.leader.address == self.address):
                            logging.info("asserting dominance")
                            self.send(c, LEADER, self.client.identity)
                    return True
                except socket.timeout:
                    pass
                except socket.error as e:
                    logging.error(f"Node.connect(): {e}")
            else:
                logging.debug("peer already known")
        else:
            logging.error("Node.connect(): can't connect to self")
        return False

    # helper functions for sending and receiving messages
    def send(self, sock, msg_type, msg):
        payload = base64.b64encode(zlib.compress(msg.encode(), 9))
        bmessage = str(len(payload)).zfill(8).encode() + str(msg_type).zfill(2).encode() + payload
        sock.sendall(bmessage)
        logging.debug(f"send {len(payload) + 10} bytes to {sock.getpeername()}")

    def receive(self, sock):
        try:
            length = int(sock.recv(8))
        except ValueError:
            return 0, b''
        message_type = int(sock.recv(2))
        bmessage = sock.recv(length)
        while (length > len(bmessage)):
            m = sock.recv(length - len(bmessage))
            bmessage = bmessage + m
        message = zlib.decompress(base64.b64decode(bmessage)).decode()
        logging.debug(f"receive {len(bmessage) + 10} bytes from {sock.getpeername()}")
        return message_type, message

    # listen for messages from a peer
    # each connected peer has its own thread for this
    def handle_connection(self, peer):
        logging.info(f"connected to {peer.identity[:8]}")
        peer.socket.settimeout(4)
        while (self.active and peer in self.peers):
            try:
                message_type, message = self.receive(peer.socket)
                if (len(message) == 0):
                    break
                elif (message_type == RESPONSE):
                    logging.info(f"Response from {peer.identity[:8]}: {message}")
                elif (message_type == TRANSACTION):
                    logging.info(f"Transaction from {peer.identity[:8]}")
                    transaction = self.rebuild_transaction(json.loads(message))
                    if (not self.record_transaction(transaction, peer.identity)):
                        self.send(peer.socket, RESPONSE, "Invalid transaction")
                elif (message_type == BFTSTART):
                    logging.info("Validating new block")
                    pending = json.loads(message)
                    pending_transactions = []
                    for tr in pending:
                        pending_transactions.append(self.rebuild_transaction(tr))
                    self.send_hash(pending_transactions)
                elif (message_type == BFTVERIFY):
                    logging.info(f"Hash from {peer.identity[:8]}")
                    self.hashes.append((peer.identity, message))
                elif (message_type == CHAINREQUEST):
                    logging.info(f"Sending chain to {peer.identity[:8]}")
                    while (self.active and self.pending_block):
                        time.sleep(1)
                    if (message != helpers.sha256(self.chain.json)):
                        self.send(peer.socket, CHAIN, self.chain.json)
                elif (message_type == CHAIN):
                    if (message != "UP TO DATE"):
                        logging.info("Rebuiling chain")
                        self.chain = self.chain.rebuild(message)
                    logging.info("Chain is up to date")
                elif (message_type == LEADER):
                    self.leader = peer
            except socket.timeout:
                continue
            except socket.error as e:
                break
        peer.socket.close()
        self.peers.remove(peer)
        logging.info(f"Closed connection to {peer.identity[:8]}")

    # broadcast connect message to network to discover peers
    # nodes receiving this broadcast that aren't already connected will try to connect
    def get_peers(self):
        logging.debug("Sending peer discovery broadcast")
        while (self.address is None):
            time.sleep(1)
        msg = "62757a7aGP" + str(self.address[1])
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            sock.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_IF, socket.inet_aton(self.address[0]))
            sock.sendto(msg.encode(), ('224.98.117.122', 60000))

    # listen for broadcasts
    # will try to connect to an address on a connect message
    # will remove node on a disconnect message
    def listen(self):
        while (self.active and self.address is None):
            time.sleep(1)
        logging.debug("Listening for broadcasts")
        group = socket.inet_aton('224.98.117.122')
        iface = socket.inet_aton(self.address[0])
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, group+iface)
            sock.bind(('', 60000))
            sock.settimeout(30)
            while (self.active):
                try:
                    data, addr = sock.recvfrom(256)
                    msg = data.decode()
                    if (msg.startswith('62757a7aGP')):
                        port = int(msg[10:])
                        if ((addr[0], port) != self.address):
                            self.connect((addr[0], port))
                except socket.error:
                    pass
                except (KeyboardInterrupt, SystemExit):
                    self.stop()

    ######## Validator functions #########

    # rebuild a transaction object from given JSON data
    def rebuild_transaction(self, transaction_json):
        transaction = Transaction(transaction_json['transaction'], transaction_json['sender'], transaction_json['address'], transaction_json['amount'])
        transaction.timestamp = transaction_json['timestamp']
        transaction.signature = transaction_json['signature']
        return transaction

    # verify the signature of a transaction
    def is_valid_transaction(self, transaction, peer_identity):
        if (transaction.signature):
            try:
                identity = unhexlify("3076301006072a8648ce3d020106052b8104002203620004" + peer_identity)
                msg = unhexlify(transaction.hash)
                sig = unhexlify(transaction.signature)
                key = serialization.load_der_public_key(identity, backend=default_backend())
                key.verify(sig, msg, ec.ECDSA(hashes.SHA256()))
                return True
            except cryptography.exceptions.InvalidSignature:
                logging.error("Invalid signature")
        return False

    # add a transaction to own list of pending transactions if it passes several checks
    def record_transaction(self, transaction, peer_identity):
        if (transaction.sender != transaction.address and
            self.is_valid_transaction(transaction, peer_identity)):
            self.pending_transactions.append(transaction)
            return True
        return False

    # send a transaction to connected peers
    def send_transaction(self, transaction_type, identity, amount):
        if (self.pending_block is not None):
            logging.debug("Waiting until consensus is over before sending transaction")
        while(self.active and self.pending_block is not None):
            time.sleep(1)
        if (transaction_type == 1):
            transaction = Transaction(1, identity[:96], self.client.identity, amount)
        elif (transaction_type == 2):
            transaction = Transaction(2, self.client.identity, identity[:96], amount)
        self.client.sign(transaction)
        self.pending_transactions.append(transaction)
        for peer in self.peers.copy():
            self.send(peer.socket, TRANSACTION, transaction.json)

    # parse own copy of the blockchain + pending transactions to calculate a client's balance
    def get_balance(self, identity):
        balance = 0
        transactions = []
        for block in self.chain.blocks:
            for txn in block.transactions:
                transactions.append(txn)
        transactions = transactions + self.pending_transactions
        sending = list((t for t in transactions if t.sender == identity))
        receiving = list((t for t in transactions if t.address == identity and t.transaction == 2))
        if (not sending and not receiving):
            return -1
        for transaction in sending:
            balance -= transaction.amount
        for transaction in receiving:
            balance += transaction.amount
        return balance

    # ask a node to send its copy of the blockchain
    # along with the hash of this node's blockchain for comparison
    def update_chain(self, peer):
        self.send(peer.socket, CHAINREQUEST, helpers.sha256(self.chain.json))

    # send the hash of the pending block to other nodes for comparison
    def send_hash(self, pending_transactions):
        self.pending_block = Block(self.chain.last_block.hash, pending_transactions)
        self.pending_transactions = []
        logging.info("Sending hash to peers")
        for peer in self.peers.copy():
            logging.debug(f"Sending hash to {peer.identity[:8]}")
            self.send(peer.socket, BFTVERIFY, self.pending_block.hash)
        self.hashes.append((self.client.identity, self.pending_block.hash))
        threading.Thread(target=self.pbft).start()

    # practical byzantine fault tolerance algorithm
    # waits until it has all other nodes' hashes, or until a minute has passed
    # then it compares its hash against the received hashes
    # if at least 2/3rds of the received hashes are the same as its own computed one,
    # it accepts its generated block as the next official one.
    # the remaining 1/3rd could comprise of wrong hashes, or a lack of one
    def pbft(self):
        start = time.time()
        while (time.time() - start < 60 and len(self.hashes) <= len(self.peers)):
            time.sleep(2)
            # print(f"{len(self.hashes)}/{len(self.peers)}")
        hashes = [h[1] for h in self.hashes]
        if (len(hashes) < len(self.peers) + 1):
            hashes += ['0'] * (1 + len(self.peers) - len(hashes))
        mode = max(set(hashes), key=hashes.count)
        if (hashes.count(mode)/len(hashes) >= 2/3 and self.pending_block.hash == mode):
            self.chain.new_block(self.pending_block)
            logging.info("New block added to chain")
            self.chain.export()
        else:
            current_chain = helpers.sha256(self.chain.json)
            for peer in [p for p in self.hashes if p[0] in [h for h in hashes if h == mode]]:
                try:
                    logging.debug(f"Requesting current chain from {peer.identity[:8]}")
                    self.update_chain(peer.address)
                    time.sleep(1)
                    if (helpers.sha256(self.chain.json) != current_chain):
                        break
                except socket.error:
                    pass
        self.hashes = []
        self.pending_block = None

