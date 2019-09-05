# leader node esponsible for recording transactions and controlling block creation

import db
from node import *

class Leader(Node):
    def __init__(self, password):
        if (not os.path.isfile('./leader.json')):
            self.client = Client("")
            self.client.export("leader.json", password)
        super().__init__("leader.json", password)
        self.new_funds = []

    def start_consensus(self):
        self.pending_transactions = self.new_funds + self.pending_transactions
        if self.pending_transactions:
            for peer in self.peers:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.connect(peer.address)
                    self.send(sock, Con.bftstart, helpers.jsonify(self.pending_transactions))
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
            self.new_funds = []

    def record_transaction(self, transaction):
        sender = db.search(transaction.sender)
        recipient = db.search(transaction.recipient)
        if (recipient.is_vendor == "yes" and sender.is_vendor == "no"):
            if (sender.pending_balance >= transaction.amount):
                db.update_pending(transaction.sender, transaction.recipient, transaction.amount)
                return super().record_transaction(transaction)
        return False

    def listen(self):
        group = socket.inet_aton('224.98.117.122')
        iface = socket.inet_aton(self.address[0])
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, group+iface)
            sock.bind(('', 60000))
            sock.settimeout(2)
            while self.listening:
                try:
                    data, addr = sock.recvfrom(1024)
                    msg = data.decode()
                    while (not self.address[1]):
                        time.sleep(1)
                    if (msg.startswith('62757a7aGP')):
                        p = msg[10:].split(",")
                        port = int(p[0])
                        identity = p[1]
                        if (self.address != (addr[0], port)):
                            if (not any(p.identity == identity for p in self.peers)):
                                logging.info(f"New peer at {addr[0]}")
                                self.peers.add(Peer((addr[0], port), identity))
                            logging.info(f"Responding to peer at {addr[0]}")
                            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as rsock:
                                rsock.connect((addr[0], port))
                                msg = str(self.address[1]) + "," + self.client.identity
                                self.send(rsock, Con.peer, msg)
                    elif (msg.startswith('62757a7aCN')):
                        logging.info(f"Sending port and identity to {addr[0]}")
                        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as rsock:
                            rsock.connect((addr[0], int(msg[10:])))
                            msg = str(self.address[1]) + "," + self.client.identity
                            self.send(rsock, Con.leader, msg)
                    elif (msg.startswith('62757a7aDC')):
                        logging.info(f"Peer {addr[0]} disconnected")
                        try:
                            self.peers.remove(list(peer for peer in self.peers if peer[0] == addr[0])[0])
                        except IndexError:
                            pass
                except socket.error:
                    pass
                except (KeyboardInterrupt, SystemExit):
                    self.stop()

    def start(self):
        try:
            threading.Thread(target=self.init_server).start()
            while (not self.address[1]):
                time.sleep(1)
            self.leader = Peer(self.address, self.client.identity)
        except (KeyboardInterrupt, SystemExit):
            logging.error("Interrupt received. Stopping threads")
            self.stop()
            self.chain.export()

    def add_funds(self, recipient, amount):
        transaction = Transaction("add funds", recipient, amount)
        self.client.sign(transaction)
        self.pending_transactions.append(transaction)
        for peer in self.peers:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.connect(peer.address)
                    self.send(sock, Con.transaction, transaction.json)
            except socket.error:
                logging.error(f"Peer refused connection")

    def get_balance(self, client):
        return db.search(client).pending_balance

    def get_leader(self):
        pass

    def send_transaction(self, sender, amount):
        pass

    def disconnect(self):
        pass

