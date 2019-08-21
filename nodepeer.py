import os.path

from statistics import mode

from node import *

class Peer(Node):
    def __init__(self, filename='client.json', password=None):
        super().__init__()
        if password:
            self.client = Client(filename=filename, password=password)
        self.tracker = None
        self.tport = 50001
        self.pending_block = None
        self.hashes = []

    def add_transaction(self, transaction_json):
        transaction = self.rebuild_transaction(transaction_json)
        if (self.validate_transaction(transaction)):
            self.pending_transactions.append(transaction)

    def send_transaction(self, sender, amount):
        transaction = Transaction(sender, self.client.identity, amount)
        self.client.sign(transaction)
        self.pending_transactions.append(transaction)
        for peer in self.peers:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.connect((peer[0], 50001))
                    self.send(sock, 'txnstore', transaction.json)
            except socket.error:
                logging.error(f"Peer refused connection")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((self.tracker, 50000))
            self.send(sock, 'txnstore', transaction.json)

    # implementation of the practical byzantine fault tolerance consensus algorithm
    # This function creates a temporary block and sends its hash to other peers
    def pbft_send(self, pending_transactions_json):
        pending_transactions_json = json.loads(pending_transactions_json)
        pending_transactions = []
        for tr in pending_transactions_json:
            transaction = Transaction(tr['sender'], tr['recipient'], tr['amount'])
            transaction.timestamp = tr['timestamp']
            transaction.signature = tr['signature']
            pending_transactions.append(tr)
        self.pending_block = Block(self.chain.last_block.hash, pending_transactions)
        self.hashes.append(self.pending_block.hash)
        if (self.peers):
            try:
                for peer in self.peers:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        sock.connect((peer[0], 50001))
                        logging.debug(f"Sending own hash to {peer[0]}")
                        self.send(sock, 'bftverif', self.pending_block.hash)
            except socket.error:
                logging.error("Peer refused connection")
        else:
            self.pbft_receive()

    # implementation of the pBFT algorithm
    # This function handles receiving other hashes and compares it with its own
    # TODO for each transaction in self.hashes, remove the transaction from self.pending_transactions
    def pbft_receive(self, hash=None):
        if (not self.peers):
            self.get_peers()
        if (len(self.hashes) == len(self.peers) and
            self.hashes.count(self.pending_block.hash)/len(self.hashes) > 2/3):
            logging.debug("Own hash matches majority of peer hashes.")
            self.chain.blocks.append(self.pending_block)
            logging.info("New block added to chain")
            self.hashes = []
            self.pending_block = None
        else:
            logging.debug("Requesting updated chain from tracker")
            self.update_chain()
            self.hashes = []
            self.pending_block = None

    def get_balance(self, client):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((self.tracker, 50000))
            self.send(sock, 'balquery', client)
            response = self.receive(sock)
            return response[1]

    def update_chain(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((self.tracker, 50000))
            self.send(sock, 'updchain', str(len(self.chain.blocks)))
            response = self.receive(sock)
            if (not response[1] == "UP TO DATE"):
                logging.debug("Rebuilding chain")
                self.chain = self.rebuild_chain(response[1])
                return True
            logging.info(f"Chain is up to date ({self.chain.last_block.timestamp})")
            return False

    def get_peers(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((self.tracker, 50000))
            self.send(sock, 'getpeers', self.client.identity)
            response = self.receive(sock)
            for i in json.loads(response[1]):
                if ((i[0], i[1]) not in self.peers and i[1] != self.client.identity):
                    self.peers.append((i[0], i[1]))

    def connect(self):
        self.tracker = None
        msg = "62757a7aCN" + self.client.identity
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
            #sock.bind(('', 0))
            #sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(4)
            try:
                while (self.tracker == None):
                    sock.sendto(msg.encode(), ('224.1.1.1', 60000))
                    data, addr = sock.recvfrom(1024)
                    logging.debug(f"Found tracker at {addr[0]}")
                    self.tracker = addr[0]
                    self.get_peers()
            except socket.timeout:
                logging.error("Tracker doesn't seem to be running")

    def disconnect(self):
        msg = "62757a7aDC" + self.client.identity
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.bind(('', 0))
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(msg.encode(), ('<broadcast>', 60000))
        self.stop()

    def handle_connection(self, c, addr):
        logging.debug(f"Accepted connection from {addr[0]}:{addr[1]}")
        msg = self.receive(c)
        response = ""
        if (msg[0] == 'txnstore'):
            logging.info(f"Transaction from {addr[0]}")
            self.add_transaction(msg[1])
        elif (msg[0] == 'bftbegin'):
            logging.info(f"Validating block from {addr[0]}")
            self.pbft_send(msg[1])
        elif (msg[0] == 'bftverif'):
            logging.info(f"Hash from {addr[0]}")
            self.pbft_receive(msg[1])

    def start(self):
        try:
            threading.Thread(target=super().start).start()
        except (KeyboardInterrupt, SystemExit):
            logging.error("Interrupt received. Stopping threads")
            self.listening = False
            self.write_block_to_file()
            self.stop()

