# A node should be able to create transactions, verify block integrity
# as well as read NFC tags and request the blockchain from other cashiers
# this is basically the script that will be on the cashiers' systems
# TODO - INC store private keys somewhere so we can resume
#      - INC handle new node creation (adding a new client to the tracker)

# import signal
# signal.signal(signal.SIGINT, signal.SIG_DFL)

import json
import time
import socket
import logging
import os.path
import threading

from binascii import unhexlify
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import padding

from helpers import *
from block import Blockchain, Block
from client import Client
from transaction import Transaction


class Node(threading.Thread):
    def __init__(self):
        self.listening = False
        self.address = socket.gethostbyname(socket.gethostname())
        self.uport = 60000
        self.tport = 50000
        self.usock = None
        self.tsock = None
        self.peers = []
        self.pending_transactions = []
        self.chain = Blockchain()
        logging.basicConfig(format='[%(asctime)s] %(message)s', level=logging.DEBUG)
        if(os.path.isfile('./blockchain.json')):
            self.read_block_from_file()

    def write_block_to_file(self):
        logging.debug("Writing block to file")
        with open('blockchain.json', 'w') as f:
            f.write(jsonify(self.chain))

    def read_block_from_file(self):
        logging.debug("Reading block from file")
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
        # verify signature,
        if(transaction.signature):
            try:
                msg = unhexlify(transaction.hash)
                sig = unhexlify(transaction.signature)
                identity = unhexlify(transaction.recipient)
                key = serialization.load_der_public_key(identity, backend=default_backend())
                key.verify(
                    sig,
                    msg,
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH),
                    hashes.SHA256()
                )
                valid = True
            except cryptography.exceptions.InvalidSignature:
                logging.error("Invalid transaction signature")
        return valid

    def handle_connection(self):
        pass

    def send(self, sock, message_type, message):
        addr = sock.getpeername()
        msg = ''.join((message_type, str(len(message)).zfill(8), message))
        logging.debug(f"Sending {len(msg)} bytes to {addr[0]}")
        sock.sendall(msg.encode())

    def receive(self, sock):
        addr = sock.getpeername()
        message_type = sock.recv(8).decode()
        message_len = int(sock.recv(8))
        message = sock.recv(message_len).decode()
        while (message_len > len(message)):
            tmp = sock.recv(message_len - len(message)).decode()
            message = ''.join((message, tmp))
        logging.debug(f"Received {len(message_type+message)+8} bytes from {addr[0]}")
        return (message_type, message)

    def listen(self):
        pass

    def wait_for_connection(self):
        logging.debug(f"Listening for connections on {self.address}")
        while self.listening:
            try:
                self.tsock.listen(8)
                self.tsock.settimeout(4)
                c, addr = self.tsock.accept()
                threading.Thread(target=self.handle_connection, args=(c, addr)).start()
            except socket.error:
                pass
            except (KeyboardInterrupt, SystemExit):
                self.listening = False

    def start(self):
        logging.debug("Started listening for connections")
        self.listening = True
        self.usock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.tsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.usock.bind((self.address, self.uport))
        self.tsock.bind((self.address, self.tport))
        threading.Thread(target=self.listen).start()
        time.sleep(0.1)
        threading.Thread(target=self.wait_for_connection).start()
        while self.listening:
            time.sleep(1)

    def stop(self):
        self.listening = False
        if self.usock:
            self.usock.close()
        if self.tsock:
            self.tsock.close()
