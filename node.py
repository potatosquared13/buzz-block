# A node should be able to create transactions, verify block integrity
# as well as read NFC tags and request the blockchain from other cashiers
# this is basically the script that will be on the cashiers' systems
# TODO - INC store private keys somewhere so we can resume
#      - INC handle new node creation (adding a new client to the tracker)

# import signal
# signal.signal(signal.SIGINT, signal.SIG_DFL)

import json
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
        self.address = None
        self.usock = None
        self.tsock = None
        self.peers = []
        self.chain = Blockchain()
        logging.basicConfig(format='[%(asctime)s] %(message)s', level=logging.INFO)
        if(os.path.isfile('./blockchain.json')):
            self.read_block_from_file()


    def write_block_to_file(self):
        logging.info("Writing block to file")
        with open('blockchain.json', 'w') as f:
            f.write(jsonify(self.chain))

    def read_block_from_file(self):
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
            block = Block(bl['index'], bl['previous_hash'], transactions)
            block.timestamp = bl['timestamp']
            chain.blocks.append(block)
        return chain

    def rebuild_transaction(self, transaction_json):
        tmp = json.loads(transaction_json)
        transaction = Transaction(tmp['sender'], tmp['recipient'], tmp['amount'])
        transaction.timestamp = tmp['timestamp']
        transaction.signature = tmp['signature']
        return transaction

    def handle_connection(self):
        pass

    def send(self, sock, message_type, message):
        addr = sock.getpeername()
        msg = ''.join((str(message_type), str(len(message)).zfill(8), message))
        logging.debug(f"Sending {len(msg)} bytes to {addr[0]}:{addr[1]}")
        sock.sendall(msg.encode())

    def receive(self, sock):
        addr = sock.getpeername()
        message_type = int(sock.recv(1))
        message_len = int(sock.recv(8))
        message = sock.recv(message_len).decode()
        while (message_len > len(message)):
            tmp = sock.recv(message_len - len(message)).decode()
            message = ''.join((message, tmp))
        logging.debug(f"Received {9 + message_len} bytes from {addr[0]}:{addr[1]}")
        return (message_type, message)

    def wait_for_connection(self):
        logging.debug(f"Listening for connections on {self.address[0]}:{self.address[1]}")
        while self.listening:
            try:
                self.tsock.listen(8)
                self.tsock.settimeout(4)
                c, addr = self.tsock.accept()
                threading.Thread(target=self.handle_connection, args=(c, addr)).start()
            except socket.error:
                pass

    def start_server(self):
        pass

    def stop(self):
        if self.usock:
            self.usock.close()
        if self.tsock:
            self.tsock.close()
