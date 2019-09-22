# leader node responsible for recording transactions and controlling block creation
# TODO ask peer for pending transactions if leader goes down for any reason

import db
from node import *

class Leader(Node):
    def __init__(self, block_size=100, debug=False):
        if (not os.path.isfile('clients/admin.key')):
            self.client = Client("admin")
            self.client.export()
        super().__init__("clients/admin.key", debug)
        self.new_funds = []
        self.block_size = block_size

    def start_consensus(self):
        self.pending_transactions = self.new_funds + self.pending_transactions
        if self.pending_transactions:
            for peer in self.peers:
                self.send(peer.socket, BFTSTART, helpers.jsonify(self.pending_transactions))
            logging.info("Waiting for network consensus")
            self.send_hash(self.pending_transactions)
            while (self.pending_block):
                time.sleep(1)
            logging.info("Updating client balances")
            affected = set()
            for transaction in self.pending_transactions:
                if (transaction.transaction == 1):
                    affected.add(transaction.sender)
                affected.add(transaction.address)
            for identity in affected:
                db.update_balance(identity)
            self.new_funds = []

    def record_transaction(self, transaction, peer_identity):
        sender = db.search(transaction.sender)
        recipient = db.search(transaction.address)
        if (sender and recipient and transaction.sender != transaction.address and self.is_valid_transaction(transaction, peer_identity)):
            if (transaction.transaction == 1 and sender.pending_balance >= transaction.amount):
                db.update_pending(transaction.sender, transaction.address, transaction.amount)
            elif (transaction.transaction == 2 and recipient.is_vendor == "no"):
                db.update_pending(None, transaction.address, transaction.amount)
            else:
                return False
            self.pending_transactions.append(transaction)
            return True
        return False

    def start(self):
        try:
            if (not self.active):
                self.active = True
                threading.Thread(target=self.accept_connections).start()
                threading.Thread(target=self.listen).start()
                threading.Thread(target=self.sleep).start()
                while (self.address is None):
                    time.sleep(1)
                while(self.active):
                    peers = len(self.peers)
                    self.get_peers()
                    time.sleep(1)
                    if (len(self.peers) != peers):
                        time.sleep(2)
                    else:
                        time.sleep(28)
                self.leader = Peer(None, self.address, self.client.identity)
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

    def add_funds(self, recipient, amount):
        transaction = Transaction("add funds", recipient, amount)
        self.client.sign(transaction)
        self.pending_transactions.append(transaction)
        for peer in self.peers:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.connect(peer.address)
                    self.send(sock, TRANSACTION, transaction.json)
            except socket.error:
                logging.error(f"Peer refused connection")

    def get_balance(self, client):
        return db.search(client).pending_balance

    def send_transaction(self, sender, amount):
        pass

