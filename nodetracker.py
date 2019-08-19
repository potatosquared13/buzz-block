# A tracker is essentially the miner and database manager
# It is the "server" that will receive incoming transactions,
# add them to the blockchain, then push the new block to
# the cashiers for verification and storage
# TODO - don't add identical transactions (based on hash)
#      - take part in the consensus: send own hash as well
#      - move balance update after consensus

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
            affected = set()
            for transaction in self.pending_transactions:
                affected.add(transaction.sender)
                affected.add(transaction.recipient)
            for identity in affected:
                db.update_balance(identity)
            for peer in self.peers:
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        sock.connect((peer[0], 50001))
                        self.send(sock, 'bftbegin', jsonify(self.pending_transactions))
                except socket.error:
                    logging.error("Peer refused connection")
                    # listen for len(self.peers) replies and if 2/3 are in agreement, create new block and update all balances
            new_block = Block(self.last_block.hash, self.pending_transactions)
            self.chain.blocks.append(new_block)
            self.write_block_to_file()

    def add_transaction(self, transaction_json):
        transaction = self.rebuild_transaction(transaction_json)
        # check that sender exists,
        if (db.search(transaction.sender)):
            # check that the sender's balance is enough,
            if (db.search(transaction.sender)[0].pending_balance > transaction.amount):
                if (self.validate_transaction(transaction)):
                    db.update_pending(transaction.sender, transaction.recipient, transaction.amount)
                    self.pending_transactions.append(transaction)

    def listen(self):
        logging.debug("Listening for UDP messages")
        while self.listening:
            try:
                self.usock.settimeout(4)
                data, addr = self.usock.recvfrom(1024)
                msg = data.decode()
                if (msg.startswith('62757a7aCN')):
                    logging.info(f"Peer {addr[0]} connected")
                    if ((addr[0], msg[10:]) not in self.peers):
                        self.peers.append((addr[0], msg[10:]))
                    self.usock.sendto(self.address.encode(), addr)
                elif (msg.startswith('62757a7aDC')):
                    logging.info(f"Peer {addr[0]} disconnected")
                    self.peers.remove((addr[0], msg[10:]))
            except socket.error:
                pass
            except (KeyboardInterrupt, SystemExit):
                self.listening = False

    def handle_connection(self, c, addr):
        logging.debug(f"Accepted connection from {addr[0]}:{addr[1]}")
        msg = self.receive(c)
        response = ""
        response_type = ""
        # transaction
        if (msg[0] == 'txnstore'):
            logging.info(f"Transaction from {addr[0]}")
            self.add_transaction(msg[1])
        # database query
        elif (msg[0] == 'balquery'):
            logging.info(f"Balance query from {addr[0]}")
            response_type = 'balreply'
            response = str(db.search(msg[1])[0].pending_balance)
        # block update
        elif (msg[0] == 'updchain'):
            logging.info(f"Chain update request from {addr[0]}")
            response_type = 'updreply'
            if (not msg[1] == len(self.chain.blocks)):
                response = self.chain.json
            else:
                response = "UP TO DATE"
        # peerlist update
        elif (msg[0] == 'getpeers'):
            response_type = 'peerlist'
            response = jsonify(self.peers)
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
