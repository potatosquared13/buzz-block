# A node should be able to create transactions, verify block integrity
# as well as read NFC tags and request the blockchain from other cashiers
# this is basically the script that will be on the cashiers' systems
# TODO - INC store private keys somewhere so we can resume
#      - INC handle new node creation (adding a new client to the tracker)

# import signal
# signal.signal(signal.SIGINT, signal.SIG_DFL)

import json
import socket
import os.path
import threading

from binascii import unhexlify
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import padding
# from Crypto.PublicKey import RSA
# from Crypto.Signature import PKCS1_v1_5

from helpers import *
from block import Blockchain, Block
from client import Client
from transaction import Transaction


class Node(threading.Thread):
    def __init__(self):
        self.listening = False
        self.host = socket.gethostbyname(socket.gethostname())
        self.port = 50000
        self.usock = None
        self.tsock = None
        self.peers = []
        self.chain = Blockchain()

    def write_block_to_file(self):
        log("Writing block to file...")
        with open('blockchain.json', 'w') as f:
            f.write(jsonify(self.chain))
        # json.dump(self.chain, open('blockchain.json', 'w'), default=lambda o: o.__dict__, indent=4)

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
            # temp_block.nonce = bl['nonce']
            temp_block.timestamp = bl['timestamp']
            # verify integrity
            # if (helpers.sha256(str(temp_block.nonce)+str(temp_block.hash)).startswith('000')):
            if (chain_json['blocks'][bl['index']]):
                self.chain.blocks.append(temp_block)
            # else:
                # import sys
                # sys.exit("blockchain.json has been tampered with, not continuing.")
        # for pt in chain_json['pending_transactions']:
        #     tmp = Transaction(pt['sender'], pt['recipient'], pt['amount'])
        #     tmp.timestamp = pt['timestamp']
        #     tmp.signature = pt['signature']
        #     self.chain.pending_transactions.append(tmp)

    def handle_connection(self):
        pass

    def send(self, host, message_type, message):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect(host)
            # log(f"sending message length to {host}:{port}")
            msg = ''.join((str(len(message)).zfill(8), message_type, message))
            # sock.sendall(str(len(message)).zfill(8).encode())
            # sock.send(message_type.encode())
            log(f"sending {len(message)} bytes to {host}:50000")
            sock.sendall(msg.encode())
            data = sock.recv(8)
            if (not int(data.decode())):
                log("Response: OK")
            else:
                pass
            sock.close()

    def receive(self):
        log(f"Listening for connections on {self.host}:{self.port}")
        while self.listening:
            try:
                self.tsock.listen(8)
                self.tsock.settimeout(4)
                c, addr = self.tsock.accept()
                threading.Thread(target=self.handle_connection, args=(c, addr)).start()
            except socket.error:
                pass

    def cleanup(self):
        self.usock.close()
        self.tsock.close()
