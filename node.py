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
        logging.basicConfig(format='[%(asctime)s] %(message)s', level=logging.DEBUG)

    def write_block_to_file(self):
        logging.info("Writing block to file...")
        with open('blockchain.json', 'w') as f:
            f.write(jsonify(self.chain))

    def read_block_from_file(self):
        i = 0
        chain_json = json.load(open('blockchain.json', 'r'))
        for bl in chain_json['blocks']:
            transactions = []
            for tr in bl['transactions']:
                temp_transaction = Transaction(tr['sender'], tr['recipient'], tr['amount'])
                temp_transaction.timestamp = tr['timestamp']
                temp_transaction.signature = tr['signature']
                transactions.append(temp_transaction)
            temp_block = Block(bl['index'], bl['previous_hash'], transactions)
            temp_block.timestamp = bl['timestamp']
            if (chain_json['blocks'][bl['index']]):
                self.chain.blocks.append(temp_block)

    def handle_connection(self):
        pass

    def send(self, sock, message_type, message):
        addr = sock.getpeername()
        msg = ''.join((message_type, str(len(message)).zfill(8), message))
        logging.info(f"Sending {len(message)} bytes to {addr[0]}:{addr[1]}...")
        sock.sendall(msg.encode())

    def receive(self, sock):
        addr = sock.getpeername()
        message_type = int(sock.recv(1))
        message_len = int(sock.recv(8))
        logging.info(f"Receiving {message_len} bytes from {addr[0]}:{addr[1]}...")
        message = sock.recv(message_len).decode()
        while (message_len > len(message)):
            tmp = sock.recv(message_len - len(message)).decode()
            message = ''.join((message, tmp))
        return (message_type, message)

    def listen(self):
        logging.info(f"Listening for connections on {self.address[0]}:{self.address[1]}")
        while self.listening:
            try:
                self.tsock.listen(8)
                self.tsock.settimeout(4)
                c, addr = self.tsock.accept()
                threading.Thread(target=self.handle_connection, args=(c, addr)).start()
            except socket.error:
                pass

    def stop(self):
        self.usock.close()
        self.tsock.close()
