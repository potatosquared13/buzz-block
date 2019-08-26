# Source file for tracker
# Responsible for recording transaction details in a database
# and sending out the instruction to create a new block
# TODO - take part in the consensus: send own hash as well

import struct

import db

from node import *

import cryptography.exceptions

class Tracker(Node):
    def __init__(self):
        super().__init__()
        # if(not os.path.isfile('./blockchain.json')):
        #     self.chain.genesis()

    def new_block(self):
        if self.pending_transactions:
            for peer in self.peers:
                if (peer[0] != self.address):
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        sock.connect((peer, 50001))
                        self.send(sock, 'bftbegin', jsonify(self.pending_transactions))
            self.pbft_send(self.pending_transactions)

    def add_transaction(self, transaction_json):
        transaction = self.rebuild_transaction(transaction_json)
        # check that sender exists,
        if (db.search(transaction.sender)):
            # check that the sender's balance is enough,
            if (db.search(transaction.sender)[0].pending_balance > transaction.amount):
                if (self.validate_transaction(transaction)):
                    db.update_pending(transaction.sender, transaction.recipient, transaction.amount)
                    self.pending_transactions.append(transaction)
        else:
            logging.info("No matches in database")

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
                    if (msg.startswith('62757a7aCN')):
                        logging.info(f"Sending tracker status to {addr[0]}")
                        sock.sendto(self.address.encode(), addr)
                    elif (msg.startswith('62757a7aGP')):
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

    def handle_connection(self, c, addr):
        logging.debug(f"Accepted connection from {addr[0]}:{addr[1]}")
        if (addr[0] not in self.peers):
            logging.info(f"Discovered peer at {addr[0]}")
            self.peers.append(addr[0])
        msg = self.receive(c)
        response = ""
        response_type = ""
        # transaction
        if (msg[0] == 'txnstore'):
            logging.info(f"Transaction from {addr[0]}")
            self.add_transaction(msg[1])
        # receive hashes
        elif (msg[0] == 'bftverif'):
            logging.info(f"Hash from {addr[0]}")
            self.pbft_receive(addr[0], msg[1])
        # database query
        elif (msg[0] == 'balquery'):
            logging.info(f"Balance query from {addr[0]}")
            response_type = 'balreply'
            response = str(db.search(msg[1].decode())[0].pending_balance)
        # block update
        elif (msg[0] == 'getchain'):
            logging.info(f"Sending chain to {addr[0]}")
            response_type = 'newchain'
            if (msg[1] != sha256(self.chain.json)):
                if (self.pending_block):
                    logging.info("Waiting for new block to be added before responding")
                while (self.pending_block):
                    time.sleep(1)
                response = self.chain.json
            else:
                response = "UP TO DATE"
        else:
            logging.info(f"Unknown message type ({msg[0]})")
            response = "UNKNOWN"
        if (response):
            self.send(c, response_type, response)
        logging.debug(f"Closed connection from {addr[0]}:{addr[1]}")

    def start(self):
        try:
            threading.Thread(target=super().start).start()
        except (KeyboardInterrupt, SystemExit):
            logging.error("Interrupt received. Stopping threads")
            self.listening = False
            # self.new_block()
            self.stop()

    def get_tracker(self):
        pass

    def get_balance(self, client):
        pass

    def send_transaction(self, sender, amount):
        pass

    def disconnect(self):
        pass

    def pbft_receive(self, addr, hash=None):
        if (hash and hash not in self.hashes):
            self.hashes.append((addr, hash.decode()))
        if (len(self.hashes) == len(self.peers)):
            hashes = [h[1] for h in self.hashes]
            mode = max(set(hashes), key=hashes.count)
            if (hashes.count(mode)/len(hashes) > 2/3):
                if(not self.pending_block)
                    logging.warning("Waiting for own block to be generated before continuing")
                while (not self.pending_block):
                    time.sleep(1)
                if (len(self.hashes) < 3 or self.pending_block.hash == mode):
                    logging.info("Own block matches network majority")
                    self.chain.blocks.append(self.pending_block)
                    logging.info("New block added to chain")
                    logging.info("Updating client balances")
                    affected = set()
                    for transaction in self.pending_transactions:
                        affected.add(transaction.sender)
                        affected.add(transaction.recipient)
                    for identity in affected:
                        db.update_balance(identity)
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


