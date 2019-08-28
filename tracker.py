# Source file for tracker
# Responsible for recording transactions and controlling block creation

import db

from node import *

class Tracker(Node):
    def __init__(self):
        super().__init__()
        self.tracker = self.address

    def new_block(self):
        if self.pending_transactions:
            for peer in self.peers:
                if (peer[0] != self.address):
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        sock.connect((peer, 50001))
                        self.send(sock, Con.bftstart, jsonify(self.pending_transactions))
            self.pbft_send(self.pending_transactions)

    def record_transaction(self, transaction_json):
        transaction = self.rebuild_transaction(transaction_json)
        # check that sender exists,
        if (db.search(transaction.sender) and transaction.sender != transaction.recipient):
            # check that the sender's balance is enough,
            if (db.search(transaction.sender)[0].pending_balance > transaction.amount):
                if (self.validate_transaction(transaction)):
                    db.update_pending(transaction.sender, transaction.recipient, transaction.amount)
                    self.pending_transactions.append(transaction)
                    return True
        return False

    def get_tracker(self):
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
                if(not self.pending_block):
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


