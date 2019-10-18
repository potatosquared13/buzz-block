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
    def __init__(self, sock, identity):
        self.socket = sock
        self.address = self.socket.getpeername()
        self.identity = identity

# object for connecting to peers and listening for messages from them
class Node(threading.Thread):
    def __init__(self, filename, debug=False):
        # synchronisation variables
        self.threads = []
        self.running = threading.Event()
        self.accepting = threading.Event()
        self.listening = threading.Event()
        self.not_in_consensus = threading.Event()
        # networking variables
        self.peers = set()
        self.leader = None
        self.address = None
        # vendor variables
        self.blacklist = []
        self.chain = Blockchain()
        self.client = Client(filename=filename)
        # validator variables
        self.hashes = []
        self.pending_block = None
        self.pending_transactions = []
        self.invalid_transactions = []
        # statistic variables
        self.messages_send = 0
        self.messages_received = 0
        self.transactions_sent = 0
        if (debug):
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)

    ######## Networking functions ########

    # tell node to start listening for messages
    def start(self):
        if not self.running.is_set():
            self.threads.append(name="accept_connections", target=self.accept_connections)
            self.threads.append(name="listen", target=self.listen)
            for thread in self.threads:
                thread.start()
            self.accepting.wait()
            self.listening.wait()
            self.running.set()
            self.not_in_consensus.set()

    # tell node to stop listening and close existing connections
    def stop(self):
        if not self.running.wait(10):
            return
        self.accepting.clear()
        self.listening.clear()
        for thread in self.threads:
            thread.join()
        self.running.clear()
        self.chain.export()

    # wait for a peer to connect and then keep an open connection
    def accept_connections(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith('169')][0], 0))
            except socket.gaierror:
                sock.bind(([ip for ip in socket.gethostbyname_ex(socket.getfqdn())[2] if not ip.startswith('169')][0], 0))
            self.address = sock.getsockname()
            logging.debug(self.address)
            sock.settimeout(4)
            self.accepting.set()
            while self.accepting.is_set():
                try:
                    sock.listen(8)
                    c, addr = sock.accept()
                    identity = hexlify(c.recv(96)).decode()
                    c.sendall(unhexlify(self.client.identity))
                    if [p for p in self.peers if p.identity == identity]:
                        c.close()
                    peer = Peer(c, identity)
                    self.peers.add(peer)
                    thread = threading.Thread(name=identity[:8], target=self.handle_connection, args=(peer,))
                    self.threads.append()
                    thread.start()
                    if self.leader is not None:
                        if self.leader.address == self.address:
                            logging.debug("sending lead node status")
                            self.send(peer.socket, LEADER, self.client.identity)
                except socket.timeout:
                    continue
                except socket.error as e:
                    logging.error(f"Node.accept_connections(): {e}")

    # connect to a peer
    def connect(self, addr):
        if not self.running.wait(10):
            return False
        if addr == self.address or [p for p in self.peers if p.address == addr]:
            return False
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.connect(addr)
            sock.settimeout(4)
            sock.sendall(unhexlify(self.client.identity))
            identity = hexlify(sock.recv(96)).decode()
            if [p for p in self.peers if p.identity == identity]:
                sock.close()
                return False
            peer = Peer(sock, identity)
            self.peers.add(peer)
            thread = threading.Thread(name=identity[:8], target=self.handle_connection, args=(peer,)).start()
            self.threads.append(thread)
            thread.start()
            if self.leader is not None:
                if self.leader.address == self.address:
                    logging.info("sending lead node status")
                    self.send(peer.socket, LEADER, self.client.identity)
            return True
        except socket.timeout:
            pass
        except socket.error as e:
            logging.error(e)
            return False

    # helper functions for sending and receiving messages
    def send(self, sock, msg_type, msg):
        payload = base64.b64encode(zlib.compress(msg.encode(), 9))
        bmessage = hex(len(payload))[2:].zfill(8).encode() + str(hex(msg_type))[2:].encode() + payload
        sock.sendall(bmessage)
        logging.debug(f"send {len(payload) + 10} bytes to {sock.getpeername()}")

    def receive(self, sock):
        try:
            length = int(sock.recv(8), 16)
        except ValueError:
            return 0, b''
        message_type = int(sock.recv(1), 16)
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
        logging.info(f"Connected to {peer.identity[:8]}")
        peer.socket.settimeout(0.2)
        while self.running.is_set() and peer in self.peers.copy():
            try:
                message_type, message = self.receive(peer.socket)
                if (len(message) == 0):
                    break
                elif (message_type == RESPONSE):
                    logging.info(f"Response from {peer.identity[:8]}: {message}")
                elif (message_type == TRANSACTION):
                    transaction = Transaction.rebuild(json.loads(message))
                    logging.info(f"Transaction type {transaction.transaction} from {peer.identity[:8]}")
                    if (not self.record_transaction(transaction, peer.identity)):
                        self.send(peer.socket, RESPONSE, "Invalid transaction")
                elif (message_type == BFTSTART):
                    logging.info("Validating new block")
                    self.not_in_consensus.clear()
                    pending = json.loads(message)
                    pending_transactions = []
                    for tr in pending:
                        pending_transactions.append(Transaction.rebuild(tr))
                    self.send_hash(pending_transactions)
                elif (message_type == BFTVERIFY):
                    self.hashes.append((peer.identity, message))
                elif (message_type == CHAINREQUEST):
                    logging.info(f"Sending chain to {peer.identity[:8]}")
                    self.not_in_consensus.wait()
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
                logging.error(e)
                break
        peer.socket.close()
        self.peers.remove(peer)
        logging.info(f"Closed connection to {peer.identity[:8]}")

    # broadcast connect message to network to discover peers
    # nodes receiving this broadcast that aren't already connected will try to connect
    def get_peers(self):
        logging.debug("Sending peer discovery broadcast")
        self.accepting.wait()
        msg = "62757a7aGP" + str(self.address[1])
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.sendto(msg.encode(), ('<broadcast>', 62757))

    # listen for broadcasts
    # will try to connect to an address on a connect message
    def listen(self):
        self.accepting.wait()
        logging.debug("Listening for broadcasts")
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('', 62757))
            sock.settimeout(10)
            self.listening.set()
            while self.listening.is_set():
                try:
                    data, addr = sock.recvfrom(256)
                    msg = data.decode()
                    if msg.startswith('62757a7aGP'):
                        port = int(msg[10:])
                        if (addr[0], port) != self.address:
                            self.connect((addr[0], port))
                except socket.timeout:
                    continue
                except socket.error as e:
                    logging.error(e)
                    break

    # verify the signature of a transaction
    def is_valid_signature(self, transaction, peer_identity):
        if (transaction.signature):
            try:
                identity = unhexlify("3076301006072a8648ce3d020106052b8104002203620004" + peer_identity)
                msg = unhexlify(transaction.hash)
                sig = unhexlify(transaction.signature)
                key = serialization.load_der_public_key(identity, backend=default_backend())
                key.verify(sig, msg, ec.ECDSA(hashes.SHA256()))
                return True
            except cryptography.exceptions.InvalidSignature:
                pass
        return False

    # add a transaction to own list of pending transactions if it passes several checks
    def record_transaction(self, transaction, peer_identity):
        reason = ""
        status = True
        if (transaction in self.chain.pending_transactions):
            reason = "duplicate transaction"
            status = False
        elif (transaction.sender in self.blacklist or transaction.address in self.blacklist):
            logging.warning("ID is in blacklist, not proceeding")
            reason = "blacklisted"
            status = False
        elif (transaction.sender == transaction.address):
            logging.warning("Transaction attempts to send amount to same address")
            reason = "same sender and address"
            status = False
        elif (not self.is_valid_signature(transaction, peer_identity)):
            logging.warning("Transaction signature is missing or invalid")
            reason = "invalid signature"
            status = False
        if (status):
            status = False
            if (transaction.transaction == 0): # initial balance
                l = []
                for block in self.chain.blocks:
                    l = l + list([t for t in block.transactions if t.transaction == 0 and t.address == transaction.address])
                if (l):
                    logging.warning("Only one initial balance transaction is allowed per address")
                    reason = "duplicate initial balance transaction"
                else:
                    status = True
            elif (transaction.transaction == 1): # payment
                if (transaction.address == peer_identity and self.get_balance(transaction.sender) >= transaction.amount):
                    status = True
                else:
                    logging.warning("Payment transaction is invalid")
            elif (transaction.transaction == 2): # add funds
                if (transaction.sender == peer_identity and peer_identity == self.leader.identity):
                    status = True
                else:
                    logging.warning("Add funds transaction is invalid")
            elif (transaction.transaction == 3): # disable wallet
                self.blacklist.append(transaction.address)
                status = True
            else:
                reason = "unknown type"
                status = False
        if (status):
            self.chain.pending_transactions.append(transaction)
        else:
            self.invalid_transactions.append((transaction, reason))
        return status

    # send a transaction to connected peers
    def send_transaction(self, identity, amount):
        self.running.wait()
        self.not_in_consensus.wait()
        transaction = Transaction(1, identity, self.client.identity, amount)
        self.client.sign(transaction)
        self.record_transaction(transaction, self.client.identity)
        for peer in self.peers.copy():
            self.send(peer.socket, TRANSACTION, transaction.json)

    # parse own copy of the blockchain + pending transactions to calculate a client's balance
    def get_balance(self, identity):
        balance = 0
        transactions = []
        for block in self.chain.blocks:
            for txn in block.transactions:
                transactions.append(txn)
        transactions = transactions + self.chain.pending_transactions
        sending = list((t for t in transactions if t.sender == identity))
        receiving = list((t for t in transactions if t.address == identity and (t.transaction == 0 or t.transaction == 2)))
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
        self.chain.pending_transactions = []
        for peer in self.peers.copy():
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
        while (time.time() - start < 30 and len(self.hashes) <= len(self.peers)):
            time.sleep(2)
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

