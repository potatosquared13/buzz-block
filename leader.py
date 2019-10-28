# leader node responsible for recording transactions and controlling block creation
# TODO ask peer for pending transactions if leader goes down for any reason

import db
from node import *
from copy import deepcopy

class Leader(Node):
    def __init__(self, block_size=100, debug=False):
        if (not os.path.isfile('clients/admin.key')):
            self.client = Client("admin")
            self.client.export('clients')
        super().__init__("clients/admin.key", debug)
        self.block_size = block_size
        if os.path.isfile('invalid_transactions.json'):
            transactions = json.loads(open('invalid_transactions.json', 'r').read())
            for transaction in transactions:
                self.invalid_transactions.append((Transaction.rebuild(transaction[0]), transaction[1]))


    def start_consensus(self):
        if self.chain.pending_transactions:
            pt = deepcopy(self.chain.pending_transactions)
            for peer in self.peers:
                self.send(peer.socket, BFTSTART, helpers.jsonify(self.chain.pending_transactions))
            logging.info("Waiting for network consensus")
            self.send_hash(self.chain.pending_transactions)
            self.not_in_consensus.wait()
            logging.info("Updating client balances")
            affected = set()
            for transaction in pt:
                if (transaction.transaction == 1):
                    affected.add(transaction.sender)
                affected.add(transaction.address)
            for identity in affected:
                db.update_balance(identity)

    def record_transaction(self, transaction, peer_identity):
        reason = ""
        status = True
        if (transaction in self.chain.pending_transactions):
            reason = "duplicate transaction"
            status = False
        elif (transaction.sender in self.blacklist or transaction.address in self.blacklist):
            logging.warning("ID is in blacklist, not proceeding")
            reason = "blacklisted"
            status = False
        elif (transaction.sender == transaction.address):
            logging.warning("Transaction attempts to send amount to same address")
            reason = "same sender and address"
            status = False
        elif (not self.is_valid_signature(transaction, peer_identity)):
            logging.warning("Transaction signature is missing or invalid")
            reason = "invalid signature"
            status = False
        if (status):
            status = False
            if (transaction.transaction == 0): # initial balance
                l = []
                for block in self.chain.blocks:
                    l = l + list([t for t in block.transactions if t.transaction == 0 and t.address == transaction.address])
                if (l):
                    logging.warning("Only one initial balance transaction is allowed per address")
                    reason = "duplicate initial balance transaction"
                else:
                    status = True
            elif (transaction.transaction == 1): # payment
                sender = db.search_user(transaction.sender)
                if (transaction.address == peer_identity and sender.pending_balance >= transaction.amount):
                    db.update_pending(transaction.sender, transaction.address, transaction.amount)
                    status = True
                else:
                    logging.warning("Payment transaction is invalid")
                    reason = "insufficient funds"
            elif (transaction.transaction == 2): # add funds
                if (transaction.sender == peer_identity and peer_identity == self.leader.identity):
                    db.update_pending(None, transaction.address, transaction.amount)
                    status = True
                else:
                    logging.warning("Add funds transaction is invalid")
                    reason = "invalid transaction"
            elif (transaction.transaction == 3 and transaction.sender == self.client.identity): # disable wallet
                self.blacklist.append(transaction.address)
                status = True
            else:
                reason = "unknown type"
        if (status):
            self.chain.pending_transactions.append(transaction)
        else:
            self.invalid_transactions.append((transaction, reason))
        return status

    def advertise(self):
        while(self.running.is_set()):
            peers = len(self.peers)
            self.get_peers()
            time.sleep(1)
            if (len(self.peers) != peers):
                time.sleep(2)
            else:
                time.sleep(8)

    def start(self):
        try:
            if (not self.running.is_set()):
                self.threads.append(threading.Thread(name="connection_accept", target=self.accept_connections))
                self.threads.append(threading.Thread(name="broadcast_listen", target=self.listen))
                self.threads.append(threading.Thread(name="broadcast_advertise", target=self.advertise))
                self.threads.append(threading.Thread(name="consensus_condition_wait", target=self.sleep))
                for thread in self.threads:
                    thread.start()
                self.accepting.wait()
                self.listening.wait()
                self.running.set()
                self.not_in_consensus.set()
                self.leader = Peer(None, self.address, self.client.identity)
        except (KeyboardInterrupt, SystemExit):
            logging.error("Interrupt received. Stopping threads")
            self.stop()
            self.chain.export()

    def sleep(self):
        self.running.wait()
        while (self.running.is_set()):
            start = time.time()
            plen = len(self.chain.pending_transactions)
            while (self.running.is_set() and time.time() - start < 600 and len(self.chain.pending_transactions) < self.block_size):
                time.sleep(10)
            if (plen == len(self.chain.pending_transactions) and len(self.chain.pending_transactions) > 0):
                self.start_consensus()

    def get_balance(self, client):
        return db.search_user(client).pending_balance

    def create_account(self, identity, amount):
        self.not_in_consensus.wait()
        transaction = Transaction(0, self.client.identity, identity, amount)
        self.client.sign(transaction)
        self.record_transaction(transaction, self.client.identity)
        for peer in self.peers.copy():
            self.send(peer.socket, TRANSACTION, transaction.json)

    def add_funds(self, identity, amount):
        if (identity in self.blacklist):
            logging.warning("ID is in blacklist, not proceeding")
            return
        self.not_in_consensus.wait()
        transaction = Transaction(2, self.client.identity, identity, amount)
        self.client.sign(transaction)
        self.record_transaction(transaction, self.client.identity)
        for peer in self.peers.copy():
            self.send(peer.socket, TRANSACTION, transaction.json)

    def blacklist_account(self, identity):
        transaction = Transaction(3, self.client.identity, identity, 0)
        self.client.sign(transaction)
        self.record_transaction(transaction, self.client.identity)
        for peer in self.peers.copy():
            self.send(peer.socket, TRANSACTION, transaction.json)

    def stop(self):
        if not self.running.wait(10):
            return
        self.accepting.clear()
        self.listening.clear()
        self.running.clear()
        logging.debug("waiting for threads to stop")
        for thread in self.threads.copy():
            thread.join()
            self.threads.remove(thread)
        self.chain.export()
        if (self.invalid_transactions):
            with open('invalid_transactions.json', 'w') as f:
                f.write(helpers.jsonify(self.invalid_transactions))
        self.running.clear()
        logging.info("Stopped")

