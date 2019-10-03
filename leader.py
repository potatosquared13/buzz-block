# leader node responsible for recording transactions and controlling block creation
# TODO ask peer for pending transactions if leader goes down for any reason

import db
from node import *
from copy import deepcopy

class Leader(Node):
    def __init__(self, block_size=100, debug=False):
        if (not os.path.isfile('clients/admin.key')):
            self.client = Client("admin")
            self.client.export()
        super().__init__("clients/admin.key", debug)
        self.block_size = block_size

    def start_consensus(self):
        if self.pending_transactions:
            pt = deepcopy(self.pending_transactions)
            for peer in self.peers:
                self.send(peer.socket, BFTSTART, helpers.jsonify(self.pending_transactions))
            logging.info("Waiting for network consensus")
            self.send_hash(self.pending_transactions)
            while (self.pending_block):
                time.sleep(1)
            logging.info("Updating client balances")
            affected = set()
            for transaction in pt:
                if (transaction.transaction == 1):
                    affected.add(transaction.sender)
                affected.add(transaction.address)
            for identity in affected:
                db.update_balance(identity)

    def record_transaction(self, transaction, peer_identity):
        if (transaction.sender != transaction.address and self.is_valid_signature(transaction, peer_identity)):
            if (transaction.transaction == 0): # initial balance
                pass
            elif (transaction.transaction == 1 and transaction.address == peer_identity): # payment
                sender = db.search_user(transaction.sender)
                if (sender.pending_balance >= transaction.amount):
                    db.update_pending(transaction.sender, transaction.address, transaction.amount)
            elif (transaction.transaction == 2 and transaction.sender == self.client.identity): # add funds
                db.update_pending(None, transaction.address, transaction.amount)
            elif (transaction.transaction == 3): # disable wallet
                self.blacklist.append(transaction.sender)
                # transfer funds to new address
                # update db, replace sender id with new id
                pass
            else:
                return False
            self.pending_transactions.append(transaction)
            return True
        return False

    def advertise(self):
        while(self.active):
            peers = len(self.peers)
            self.get_peers()
            time.sleep(1)
            if (len(self.peers) != peers):
                time.sleep(2)
            else:
                time.sleep(8)

    def start(self):
        try:
            if (not self.active):
                self.active = True
                threading.Thread(target=self.accept_connections).start()
                threading.Thread(target=self.listen).start()
                threading.Thread(target=self.sleep).start()
                while (self.address is None):
                    time.sleep(1)
                self.leader = Peer(None, self.address, self.client.identity)
                threading.Thread(target=self.advertise).start()
        except (KeyboardInterrupt, SystemExit):
            logging.error("Interrupt received. Stopping threads")
            self.stop()
            self.chain.export()

    def sleep(self):
        while (self.active):
            start = time.time()
            while (self.active and time.time() - start < 600 and len(self.pending_transactions) < self.block_size):
                time.sleep(10)
            if (len(self.pending_transactions) >= self.block_size):
                self.start_consensus()

    def get_balance(self, client):
        return db.search(client).pending_balance

    def create_account(self, identity, amount):
        if (self.pending_block is not None):
            logging.debug("Waiting until consensus is over before sending transaction")
        while(self.active and self.pending_block is not None):
            time.sleep(1)
        transaction = Transaction(0, self.client.identity, identity, amount)
        self.client.sign(transaction)
        self.record_transaction(transaction, self.client.identity)
        for peer in self.peers.copy():
            self.send(peer.socket, TRANSACTION, transaction.json)

    def add_funds(self, identity, amount):
        if (identity in self.blacklist):
            logging.warning("ID is in blacklist, not proceding")
            return
        if (self.pending_block is not None):
            logging.debug("Waiting until consensus is over before sending transaction")
        while(self.active and self.pending_block is not None):
            time.sleep(1)
        transaction = Transaction(2, self.client.identity, identity, amount)
        self.client.sign(transaction)
        self.record_transaction(transaction, self.client.identity)
        for peer in self.peers.copy():
            self.send(peer.socket, TRANSACTION, transaction.json)

    def blacklist_account(self, identity):
        transaction = Transaction(3, self.client.identity, identity, None)
        self.client.sign(transaction)
        self.record_transaction(transaction, self.client.identity)
        for peer in self.peers.copy():
            self.send(peer.socket, TRANSACTION, transaction.json)

