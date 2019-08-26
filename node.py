# A node should be able to create transactions, verify block integrity
# as well as read NFC tags and request the blockchain from other cashiers
# this is basically the script that will be on the cashiers' systems
# TODO - INC store private keys somewhere so we can resume
#      - INC handle new node creation (adding a new client to the tracker)

# import signal
# signal.signal(signal.SIGINT, signal.SIG_DFL)

import json
import time
import zlib
import base64
import socket
import logging
import os.path
import threading

from binascii import unhexlify
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from helpers import *
from block import Blockchain, Block
from client import Client
from transaction import Transaction


class Node(threading.Thread):
    def __init__(self, filename="client.json", pin=None):
        self.listening = False
        self.address = socket.gethostbyname(socket.gethostname())
        self.tport = 50001
        self.peers = []
        self.pending_block = None
        self.pending_transactions = []
        self.hashes = []
        self.chain = Blockchain()
        logging.basicConfig(format='[%(asctime)s] %(message)s', level=logging.INFO)
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
        # TODO verify chain has not been tampered with
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
            # block.timestamp = bl['timestamp']
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
        # check if transaction is valid:
        # verify signature
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

    def record_transaction(self, transaction_json):
        transaction = self.rebuild_transaction(transaction_json)
        if (transaction.sender != transaction.recipient and self.validate_transaction(transaction)):
            self.pending_transactions.append(transaction)

    def send_transaction(self, sender, amount):
        transaction = Transaction(sender, self.client.identity, amount)
        self.client.sign(transaction)
        self.pending_transactions.append(transaction)
        for peer in self.peers:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.connect((peer, 50001))
                    self.send(sock, 'txnstore', transaction.json)
            except socket.error:
                logging.error(f"Peer refused connection")
        #with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        #    sock.connect((self.tracker, 50001))
        #    self.send(sock, 'txnstore', transaction.json)

    def get_balance(self, client):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((self.tracker, 50001))
            self.send(sock, 'balquery', client)
            response = self.receive(sock)
            return float(response[1])

    def update_chain(self, address=None):
        if (not address):
            address = self.tracker
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((address, 50001))
            self.send(sock, 'getchain', sha256(self.chain.json))
            response = self.receive(sock)
            if (response[0] == "newchain" and response[1] != "UP TO DATE"):
                logging.info("Rebuilding chain")
                self.chain = self.rebuild_chain(response[1])
                return True
            logging.info("Chain is up to date")
            return False

    def get_peers(self):
        msg = "62757a7aGP"
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
            sock.settimeout(1)
            sock.sendto(msg.encode(), ('224.1.1.1', 60001))

    def get_tracker(self):
        self.tracker = None
        msg = "62757a7aCN" + self.client.identity
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
            sock.settimeout(4)
            try:
                while (self.tracker == None):
                    sock.sendto(msg.encode(), ('224.1.1.1', 60001))
                    data, addr = sock.recvfrom(1024)
                    logging.info(f"Connected to {addr[0]}")
                    self.tracker = addr[0]
            except socket.timeout:
                logging.error("Tracker doesn't seem to be running")

    def disconnect(self):
        msg = "62757a7aDC"
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
            sock.sendto(msg.encode(), ('224.1.1.1', 60001))
        self.stop()
        return True

    def handle_connection(self, c, addr):
        logging.debug(f"Accepted connection from {addr[0]}:{addr[1]}")
        if (addr[0] not in self.peers):
            logging.info(f"Discovered peer at {addr[0]}")
            self.peers.append(addr[0])
        msg = self.receive(c)
        response = ""
        # transaction
        if (msg[0] == 'txnstore'):
            logging.info(f"Transaction from {addr[0]}")
            self.record_transaction(msg[1])
        # validate block
        elif (msg[0] == 'bftbegin'):
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
        elif (msg[0] == 'bftverif'):
            logging.info(f"Hash from {addr[0]}")
            self.pbft_receive(addr[0], msg[1])
        # block update
        elif (msg[0] == 'getchain'):
            logging.info(f"Sending chain to {addr[0]}")
            if (msg[1] != sha256(self.chain.json)):
                self.send(c, "newchain", self.chain.json)

    def send(self, sock, msg_type, msg):
        addr = sock.getpeername()
        payload = base64.b64encode(zlib.compress(msg.encode(),9))
        msg_bytes = msg_type.encode() + str(len(payload)).zfill(8).encode() + payload
        logging.debug(f"Sending {len(msg_bytes)} bytes to {addr[0]}")
        sock.sendall(msg_bytes)

    def receive(self, sock):
        addr = sock.getpeername()
        msg_type = sock.recv(8).decode()
        msg_len = int(sock.recv(8))
        msg_bytes = sock.recv(msg_len)
        while (msg_len > len(msg_bytes)):
            tmp = sock.recv(msg_len - len(msg_bytes))
            msg_bytes = msg_bytes + tmp
        logging.debug(f"Received {16 + len(msg_bytes)} bytes from {addr[0]}")
        msg = zlib.decompress(base64.b64decode(msg_bytes))
        return (msg_type, msg)

    def listen(self):
        group = socket.inet_aton('224.1.1.1')
        iface = socket.inet_aton(self.address)
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
                        if (addr[0] != self.address):
                            if (addr[0] not in self.peers):
                                self.peers.append(addr[0])
                            logging.info(f"Responding to peer at {addr[0]}")
                            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as rsock:
                                rsock.connect((addr[0], 50001))
                                self.send(rsock, 'resppeer', "")
                    elif (msg.startswith('62757a7aDC')):
                        logging.info(f"Peer {addr[0]} disconnected")
                        if (addr[0] in self.peers):
                            self.peers.remove(addr[0])
                except socket.error:
                    pass
                except (KeyboardInterrupt, SystemExit):
                    self.listening = False

    def wait_for_connection(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((self.address, self.tport))
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

    def start(self):
        try:
            threading.Thread(target=self.init_server).start()
        except (KeyboardInterrupt, SystemExit):
            logging.error("Interrupt received. Stopping threads")
            self.listening = False
            self.write_to_file()
            self.stop()

    def init_server(self):
        if (not self.listening):
            self.listening = True
            logging.info(f"Listening on {self.address}")
            if (self.listen.__code__.co_code != b'd\x00S\x00'):
                threading.Thread(target=self.listen).start()
                time.sleep(0.1)
            threading.Thread(target=self.wait_for_connection).start()
            while self.listening:
                time.sleep(1)

    def stop(self):
        self.listening = False

    # implementation of the practical byzantine fault tolerance consensus algorithm
    # This function creates a temporary block and sends its hash to other peers
    def pbft_send(self, pending_transactions):
        self.pending_block = Block(self.chain.last_block.hash, pending_transactions)
        #self.hashes.append(self.pending_block.hash)
        try:
            for peer in self.peers:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.connect((peer, 50001))
                    logging.debug(f"Sending own hash to {peer}")
                    self.send(sock, 'bftverif', self.pending_block.hash)
        except socket.error:
            logging.error("Peer refused connection")

    # implementation of the pBFT algorithm
    # This function handles receiving other hashes and compares it with its own
    def pbft_receive(self, addr, hash=None):
        if (hash and hash not in self.hashes):
            self.hashes.append((addr, hash.decode()))
        if (len(self.hashes) == len(self.peers)):
            hashes = [h[1] for h in self.hashes]
            mode = max(set(hashes), key=hashes.count)
            if (hashes.count(mode)/len(hashes) > 2/3):
                while (not self.pending_block):
                    logging.error("Waiting for own block to be generated before continuing")
                    time.sleep(1)
                if (self.pending_block.hash == mode):
                    logging.info("Own block matches network majority")
                    self.chain.blocks.append(self.pending_block)
                    logging.info("New block added to chain")
                else:
                    for addr in [p[0] for p in self.hashes if p[1] == mode]:
                        try:
                            logging.info(f"Requesting current chain from {addr}")
                            self.update_chain(addr)
                            break
                        except socket.error:
                            pass
                self.hashes = []
                self.pending_transactions = []
                self.pending_block = None


