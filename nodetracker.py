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
        self.pending_transactions = []
        if(not os.path.isfile('./blockchain.json')):
            self.chain.genesis()

    def new_block(self):
        if self.pending_transactions:
            logging.info("Adding current pending transactions to new block")
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
        transaction = self.rebuild_transaction(transaction_json)
        valid = False
        response = "OKAY"
        # check if transaction is valid:
        # check that sender exists,
        if (not db.search(transaction.sender)):
            response = "NO SUCH CLIENT"
        else:
            # check that the sender's balance is enough,
            if (db.search(transaction.sender)[0].pending_balance < transaction.amount):
                response = "INSUFFICIENT BALANCE"
            else:
                # verify signature,
                if(not transaction.signature):
                    response = "NO SIGNATURE"
                else:
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
                        # finally, add it to the blockchain
                        valid = True
                        db.update_pending(transaction.sender, transaction.recipient, transaction.amount)
                        self.pending_transactions.append(transaction)
                        logging.info("Added transaction")
                    except:
                        response = "INVALID SIGNATURE"
        if not valid:
            logging.error("Discarding invalid transaction")
        return response

    def listen(self):
        logging.debug("Listening for UDP messages")
        while self.listening:
            try:
                self.usock.settimeout(4)
                data, addr = self.usock.recvfrom(1024)
                msg = data.decode()
                if (msg.startswith('62757a7aCN')):
                    logging.info(f"Peer {addr[0]} connected")
                    if (addr[0] not in self.peers):
                        self.peers.append((addr[0], msg[10:]))
                    self.usock.sendto(self.address[0].encode(), addr)
                elif (msg.startswith('62757a7aDC')):
                    logging.info(f"Peer {addr[0]} disconnected")
                    self.peers.remove((addr[0], msg[10:]))
            except socket.error:
                pass

    def handle_connection(self, c, addr):
        logging.debug(f"Accepted connection from {addr[0]}:{addr[1]}")
        msg = self.receive(c)
        response = ""
        # transaction
        if (msg[0] == 1):
            response_type = 1
            response = self.add_transaction(msg[1])
        # database query
        elif (msg[0] == 2):
            response_type = 2
            response = db.search(client)[0].pending_balance
        # block update
        elif (msg[0] == 3):
            response_type = 3
            if (not msg[1] == len(self.chain.blocks)):
                response = self.chain.json
                logging.info(f"Sending blockchain to {addr[0]}")
            else:
                response = "UP TO DATE"
        # peerlist update
        elif (msg[0] == 4):
            response_type = 4
            response = jsonify(self.peers)
        else:
            logging.info(f"Unknown message type ({msg[0]})")
            response = "UNKNOWN"
        self.send(c, response_type, response)
        logging.debug(f"Closed connection from {addr[0]}:{addr[1]}")

    def start_server(self):
        logging.info("Started listening for connections")
        self.listening = True
        self.address = (socket.gethostbyname(socket.gethostname()), 50000)
        self.usock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.tsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.usock.bind((self.address[0], 60000))
        self.tsock.bind(self.address)
        threading.Thread(target=self.listen).start()
        time.sleep(0.1)
        threading.Thread(target=self.wait_for_connection).start()
        try:
            while self.listening:
                time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            logging.error("Interrupt received. Stopping threads")
            self.listening = False
            self.new_block()
            self.stop()
