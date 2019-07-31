# A tracker is essentially the miner and database manager
# It is the "server" that will receive incoming transactions,
# add them to the blockchain, then push the new block to
# the cashiers for verification and storage
# TODO - NST new_transaction(): check if sender.balance > amount
#      - NST don't add identical transactions (based on hash)
#      - NST actual server listen/reply code

import time

import db

from node import *

class Tracker(Node):
    def __init__(self):
        super().__init__()
        self.address = (socket.gethostbyname(socket.gethostname()), 50000)
        self.pending_transactions = []
        if (os.path.isfile('./blockchain.json')):
            logging.info("Reading block from file...")
            self.read_block_from_file()
        else:
            self.chain.genesis()

    def new_block(self):
        logging.info("Adding current pending transactions to new block...")
        if self.pending_transactions:
            affected = set()
            for transaction in self.pending_transactions:
                affected.add(transaction.sender)
                affected.add(transaction.recipient)
            for identity in affected:
                db.update_balance(identity)
            self.chain.write_block(self.pending_transactions)
            self.write_block_to_file()
            self.pending_transactions = []

    def add_transaction(self, transaction_json):
        import json
        tmp = json.loads(transaction_json)
        transaction = Transaction(tmp['sender'], tmp['recipient'], tmp['amount'])
        transaction.timestamp = tmp['timestamp']
        transaction.signature = tmp['signature']
        # check if transaction is valid:
        # verify signature,
        valid = True
        reason = "OKAY"
        if(transaction.signature):
            try:
                msg = unhexlify(transaction.hash)
                sig = unhexlify(transaction.signature)
                identity = unhexlify(transaction.recipient)
                key = serialization.load_der_public_key(identity, backend=default_backend())
                key.verify(
                    sig,
                    msg,
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH),
                    hashes.SHA256()
                )
            except:
                valid = False
                reason = "NSIG"
        else:
            valid = False
            reason = "NSIG"
        # check that the sender's balance is enough,
        if (db.search(transaction.sender)[0].pending_balance < transaction.amount):
            valid = False
            reason = "NBAL"
        # and check that the transaction hash is unique.
        # TODO
        # finally, add it to the blockchain
        if (valid):
            db.update_pending(transaction.sender, transaction.recipient, transaction.amount)
            self.pending_transactions.append(transaction)
        return (valid, reason)

    def announce(self):
        logging.info("Listening for discover broadcasts...")
        while self.listening:
            try:
                self.usock.settimeout(4)
                data, addr = self.usock.recvfrom(1024)
                if (data.decode() == '62757a7aDS'):
                    logging.info(f"Found peer at {addr[0]}")
                    if (addr[0] not in self.peers):
                        self.peers.append(addr[0])
                    self.usock.sendto(self.address[0].encode(), addr)
            except socket.error:
                pass

    def handle_connection(self, c, addr):
        logging.info(f"Accepted connection from {addr[0]}:{addr[1]}")
        msg = self.receive(c)
        response = (None, None)
        # transaction
        if (msg[0] == 1):
            logging.info("Transaction received. Rebuilding and attempting to add...")
            response = self.add_transaction(msg[1])
            if (not response[0]):
                logging.warning("Invalid transaction")
        # database query
        elif (msg[0] == 2):
            pass
        else:
            logging.info(f"Unknown message type ({msg[0]})")
            response[1] = "NMSG"
        self.send(c, "0", response[1])
        logging.info(f"Closed connection from {addr[0]}:{addr[1]}")

    def start(self):
        self.listening = True
        self.usock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.tsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.usock.bind(('', 60000))
        self.tsock.bind(self.address)
        threading.Thread(target=self.announce).start()
        time.sleep(0.1)
        threading.Thread(target=self.listen).start()
        try:
            while self.listening:
                time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            logging.info("Interrupt received. Stopping threads...")
            self.listening = False
            self.new_block()
            self.stop()
