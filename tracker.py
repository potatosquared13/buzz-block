# tracker node esponsible for recording transactions and controlling block creation

import db

from node import *

class Tracker(Node):
    def __init__(self):
        super().__init__()
        self.start()
        while (not self.address[1]):
            time.sleep(1)
        self.tracker = self.address

    def new_block(self):
        if self.pending_transactions:
            pending_hashes = []
            for transaction in self.pending_transactions:
                pending_hashes.append(sha256(transaction.json))
            for peer in self.peers:
                if (peer[0] != self.address):
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        sock.connect(peer)
                        self.send(sock, Con.bftstart, jsonify(pending_hashes))
            self.pbft_send(self.pending_transactions)
            logging.info("Waiting for network consensus")
            while (self.pending_block):
                time.sleep(1)
            logging.info("Updating client balances")
            affected = set()
            for transaction in self.pending_transactions:
                affected.add(transaction.sender)
                affected.add(transaction.recipient)
            for identity in affected:
                db.update_balance(identity)

    def record_transaction(self, transaction):
        if (db.search(transaction.sender)):
            if (db.search(transaction.sender)[0].pending_balance > transaction.amount):
                    db.update_pending(transaction.sender, transaction.recipient, transaction.amount)
                    return super().record_transaction(transaction)
        return False

    # TODO
    def add_funds(self):
        pass

    def get_tracker(self):
        pass

    def send_transaction(self, sender, amount):
        pass

    def disconnect(self):
        pass


