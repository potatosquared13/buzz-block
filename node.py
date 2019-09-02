# network node responsible for creating transactions and verifying other transactions

import json
import time
import zlib
import base64
import socket
import logging
import os.path
import threading

from enum import Enum
from binascii import unhexlify
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from helpers import *
from block import Blockchain, Block
from client import Client
from transaction import Transaction

# enum for tcp connection type
class Con(Enum):
    response = 0
    transaction = 1
    bftstart = 2
    bftverify = 3
    balancerequest = 4
    balance = 5
    chainrequest = 6
    chain = 7
    peerdiscovery = 8
    unknown = 9

class Node(threading.Thread):
    def __init__(self, filename="client.json", pin=None):
        self.listening = False
        self.address = (socket.gethostbyname(socket.getfqdn()), 0)
        self.peers = []
        self.pending_block = None
        self.pending_transactions = []
        self.hashes = []
        self.chain = Blockchain()
        logging.basicConfig(format='[%(asctime)s] %(message)s', level=logging.DEBUG)
        if(os.path.isfile('./blockchain.json')):
            self.read_from_file()
        if pin:
            self.client = Client(filename=filename, password=pin)
            self.tracker = None

    def write_to_file(self):
        logging.info("Writing block to file")
        with open('blockchain.json', 'w') as f:
            f.write(jsonify(self.chain))

    def read_from_file(self):
        logging.info("Reading block from file")
        self.chain = self.rebuild_chain(open('blockchain.json', 'r').read())

    def rebuild_chain(self, chain_json):
        tmp = json.loads(chain_json)
        chain = Blockchain()
        for bl in tmp['blocks']:
            transactions = []
            for tr in bl['transactions']:
                transaction = Transaction(tr['sender'], tr['recipient'], tr['amount'])
                transaction.timestamp = tr['timestamp']
                transaction.signature = tr['signature']
                transactions.append(transaction)
            block = Block(bl['previous_hash'], transactions)
            chain.blocks.append(block)
        return chain

    def rebuild_transaction(self, transaction_json):
        tmp = json.loads(transaction_json)
        transaction = Transaction(tmp['sender'], tmp['recipient'], tmp['amount'])
        transaction.timestamp = tmp['timestamp']
        transaction.signature = tmp['signature']
        return transaction

    def validate_transaction(self, transaction):
        valid = False
        if(transaction.signature):
            try:
                msg = unhexlify(transaction.hash)
                sig = unhexlify(transaction.signature)
                identity = unhexlify(transaction.recipient)
                key = serialization.load_der_public_key(identity, backend=default_backend())
                key.verify(sig, msg, ec.ECDSA(hashes.SHA256()))
                valid = True
            except cryptography.exceptions.InvalidSignature:
                logging.error("Invalid transaction signature")
        return valid

    def record_transaction(self, transaction):
        if (transaction.sender != transaction.recipient and self.validate_transaction(transaction)):
            self.pending_transactions.append(transaction)
            return True
        return False

    def send_transaction(self, sender, amount):
        transaction = Transaction(sender, self.client.identity, amount)
        self.client.sign(transaction)
        self.pending_transactions.append(transaction)
        for peer in self.peers:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.connect(peer)
                    self.send(sock, Con.transaction, transaction.json)
            except socket.error:
                logging.error(f"Peer refused connection")

    def get_balance(self, client):
        balance = 0
        transactions = []
        for block in self.chain.blocks:
            for txn in block.transactions:
                transactions.append(txn)
        transactions = transactions + self.pending_transactions
        sending = list((t for t in transactions if t.sender == client))
        receiving = list((t for t in transactions if t.recipient == client))
        if (not sending and not receiving):
            return -1
        for transaction in sending:
            balance -= transaction.amount
        for transaction in receiving:
            balance += transaction.amount
        return balance

    def update_chain(self, address=None):
        if (not address):
            address = self.tracker
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect(address)
            self.send(sock, Con.chainrequest, sha256(self.chain.json))
            response = self.receive(sock)
            if (response[0] == Con.chain and response[1] != "UP TO DATE"):
                logging.info("Rebuilding chain")
                self.chain = self.rebuild_chain(response[1])
                return True
            logging.info("Chain is up to date")
            return False

    def get_peers(self):
        msg = "62757a7aGP" + str(self.address[1])
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
            sock.settimeout(1)
            sock.sendto(msg.encode(), ('224.1.1.1', 60001))

    def get_tracker(self):
        self.tracker = None
        msg = "62757a7aCN" + str(self.address[1])
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
            sock.settimeout(4)
            try:
                while (self.tracker == None):
                    sock.sendto(msg.encode(), ('224.1.1.1', 60001))
                    data, addr = sock.recvfrom(1024)
                    port = int(data)
                    logging.info(f"Discovered tracker at {addr[0]}:{port}")
                    self.tracker = (addr[0], port)
            except socket.timeout:
                logging.error("Tracker doesn't seem to be running")

    # tell peers to remove this node as an active node
    def disconnect(self):
        msg = "62757a7aDC"
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
            sock.sendto(msg.encode(), ('224.1.1.1', 60001))
        self.listening = False
        return True

    def handle_connection(self, c, addr):
        logging.debug(f"Accepted connection from {addr[0]}")
        msg = self.receive(c)
        if (msg[0] == Con.response):
            logging.info(f"Response from {addr[0]}")
        # transaction
        elif (msg[0] == Con.transaction):
            logging.info(f"Transaction from {addr[0]}")
            transaction = self.rebuild_transaction(msg[1])
            if(not self.record_transaction(transaction)):
                self.send(c, Con.response, "Invalid transaction")
        # validate block
        elif (msg[0] == Con.bftstart):
            logging.info(f"Validating block from {addr[0]}")
            pending_transactions_json = json.loads(msg[1])
            pending_transactions = []
            for tr in pending_transactions_json:
                transaction = Transaction(tr['sender'], tr['recipient'], tr['amount'])
                transaction.timestamp = tr['timestamp']
                transaction.signature = tr['signature']
                pending_transactions.append(transaction)
            self.pbft_send(pending_transactions)
        # receive hashes
        elif (msg[0] == Con.bftverify):
            logging.info(f"Hash from {addr[0]}")
            peer = [p for p in self.peers if p[0] == addr[0]][0]
            self.pbft_receive(peer, msg[1])
        # block update
        elif (msg[0] == Con.chainrequest):
            logging.info(f"Sending chain to {addr[0]}")
            if (self.pending_block):
                logging.info("Waiting for new block to be added before responding")
            while (self.pending_block):
                time.sleep(1)
            if (msg[1] != sha256(self.chain.json)):
                self.send(c, Con.chain, self.chain.json)
            else:
                self.send(c, Con.chain, "UP TO DATE")
        elif (msg[0] == Con.peerdiscovery):
            port = int(msg[1])
            if ((addr[0], port) not in self.peers):
                logging.info(f"Discovered peer at {addr[0]}:{int(msg[1])}")
                self.peers.append((addr[0], port))
        else:
            logging.info(f"Unknown message ({msg[0]}, {msg[1]})")
        logging.debug(f"Closed connection from {addr[0]}")

    def send(self, sock, msg_type, msg):
        addr = sock.getpeername()
        payload = base64.b64encode(zlib.compress(str(msg).encode(),9))
        msg_bytes = str(msg_type.value).encode() + str(len(payload)).zfill(8).encode() + payload
        logging.debug(f"Sending {len(msg_bytes)} bytes to {addr[0]}:{addr[1]}")
        sock.sendall(msg_bytes)

    def receive(self, sock):
        addr = sock.getpeername()
        msg_type = int(sock.recv(1))
        msg_len = int(sock.recv(8))
        msg_bytes = sock.recv(msg_len)
        while (msg_len > len(msg_bytes)):
            tmp = sock.recv(msg_len - len(msg_bytes))
            msg_bytes = msg_bytes + tmp
        logging.debug(f"Received {9 + len(msg_bytes)} bytes from {addr[0]}:{addr[1]}")
        msg = zlib.decompress(base64.b64decode(msg_bytes))
        return (Con(msg_type), msg)

    # handles udp multicasts
    def listen(self):
        group = socket.inet_aton('224.1.1.1')
        iface = socket.inet_aton(self.address[0])
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, group+iface)
            sock.bind(('', 60001))
            sock.settimeout(2)
            while self.listening:
                try:
                    data, addr = sock.recvfrom(1024)
                    msg = data.decode()
                    if (msg.startswith('62757a7aGP')):
                        port = int(msg[10:])
                        if (self.address != (addr[0], port)):
                            if ((addr[0], port) not in self.peers):
                                self.peers.append((addr[0], port))
                            logging.info(f"Responding to peer at {addr[0]}")
                            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as rsock:
                                rsock.connect((addr[0], port))
                                self.send(rsock, Con.peerdiscovery, self.address[1])
                    elif (msg.startswith('62757a7aCN')):
                        if (self.address == self.tracker):
                            logging.info(f"Sending port to {addr[0]}")
                            sock.sendto(str(self.tracker[1]).encode(), addr)
                    elif (msg.startswith('62757a7aDC')):
                        logging.info(f"Peer {addr[0]} disconnected")
                        try:
                            self.peers.remove(list(peer for peer in self.peers if peer[0] == addr[0])[0])
                        except IndexError:
                            pass
                except socket.error:
                    pass
                except (KeyboardInterrupt, SystemExit):
                    self.listening = False

    # handles tcp connections
    def wait_for_connection(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((self.address[0], 0))
            self.address = sock.getsockname()
            sock.settimeout(4)
            while self.listening:
                try:
                    sock.listen(8)
                    c, addr = sock.accept()
                    threading.Thread(target=self.handle_connection, args=(c, addr)).start()
                except socket.error:
                    pass
                except (KeyboardInterrupt, SystemExit):
                    self.listening = False

    # tells node to start listening for multicasts / accept connections
    def start(self):
        try:
            threading.Thread(target=self.init_server).start()
        except (KeyboardInterrupt, SystemExit):
            logging.error("Interrupt received. Stopping threads")
            self.listening = False
            self.write_to_file()

    def init_server(self):
        if (not self.listening):
            self.listening = True
            if (self.listen.__code__.co_code != b'd\x00S\x00'):
                threading.Thread(target=self.listen).start()
                time.sleep(0.1)
            threading.Thread(target=self.wait_for_connection).start()
            time.sleep(1)
            logging.info(f"Listening on {self.address[0]}:{self.address[1]}")
            while self.listening:
                time.sleep(1)

    # practical byzantine fault tolerance 1/2
    # creates a block out of received transactions and sends the computed hash to other nodes
    def pbft_send(self, pending_transactions):
        self.pending_block = Block(self.chain.last_block.hash, pending_transactions)
        self.hashes.append((self.address, self.pending_block.hash))
        try:
            for peer in self.peers:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.connect(peer)
                    logging.debug(f"Sending own hash to {peer[0]}:{peer[1]}")
                    self.send(sock, Con.bftverify, self.pending_block.hash)
        except socket.error:
            logging.error("Peer refused connection")

    # pBFT 2/2
    # waits until all other nodes' hashes are received and compares it with its own
    def pbft_receive(self, addr, hash=None):
        if (hash and (addr, hash) not in self.hashes):
            self.hashes.append((addr, hash.decode()))
        if (len(self.hashes) > len(self.peers)):
            hashes = [h[1] for h in self.hashes]
            mode = max(set(hashes), key=hashes.count)
            if (hashes.count(mode)/len(hashes) >= 2/3):
                if (not self.pending_block):
                    logging.error("Waiting for own block to be generated before continuing")
                while (not self.pending_block):
                    time.sleep(1)
                if (self.pending_block.hash == mode):
                    logging.info("Own block matches network majority")
                    self.chain.blocks.append(self.pending_block)
                    logging.info("New block added to chain")
                else:
                    for addr in [p[0] for p in self.hashes if p[1] == mode and addr != self.address]:
                        try:
                            logging.info(f"Requesting current chain from {addr}")
                            self.update_chain(addr)
                            break
                        except socket.error:
                            pass
                self.hashes = []
                self.pending_transactions = []
                self.pending_block = None
        else:
            logging.info(f"Received {len(self.hashes) - 1}/{len(self.peers)} hashes")


