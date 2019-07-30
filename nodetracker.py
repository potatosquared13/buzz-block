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
        if (os.path.isfile('./blockchain.json')):
            log("Reading block from file...")
            self.read_block_from_file()
        else:
            self.chain.genesis()

    def new_client(self, name, amount):
        c = Client(name)
        db.insert(c, amount)
        return c

    # def write_transactions_to_file(self):
    #     if (self.pending_transactions):
    #         log("Writing pending transactions to file...")
    #         with open('transactions.json', 'w') as f:
    #             f.write(jsonify(self.pending_transactions))

    # def read_transactions_from_file(self):
    #     transactions_json = json.load(open('transactions.json', 'r'))
    #     for transaction in transactions_json:
    #         tr = Transaction(transaction['sender'], transaction['recipient'], transaction['amount'])
    #         tr.timestamp = transaction['timestamp']
    #         tr.signature = transaction['signature']
    #         self.pending_transactions.append(tr)

    def new_block(self):
        # go through pending_transactions and make a set of affected accounts
        log("Adding current pending transactions to new block...")
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

    def rebuild_transaction(self, transaction_json):
        import json
        tmp = json.loads(transaction_json)
        transaction = Transaction(tmp['sender'], tmp['recipient'], tmp['amount'])
        transaction.timestamp = tmp['timestamp']
        transaction.signature = tmp['signature']
        return transaction

    def is_valid_transaction(self, transaction):
        if(transaction.recipient):
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
                    return True
                except:
                    return False
        return False

    # TODO change so that new nodes will broadcast the query
    #      instead of the tracker broadcasting constantly.
    #      The tracker will then send a response
    def announce(self):
        log("Listening for discover broadcasts...")
        while self.listening:
            try:
                self.usock.settimeout(4)
                data, addr = self.usock.recvfrom(1024)
                if (data.decode() == '62757a7aDS'):
                    log(f"Found peer at {addr[0]}")
                    if (addr[0] not in self.peers):
                        self.peers.append(addr[0])
                    self.usock.sendto(self.host.encode(), addr)
            except socket.error:
                pass

    def handle_connection(self, c, addr):
        log(f"Accepted connection from {addr[0]}:{addr[1]}")
        message_len = int(c.recv(8))
        message_type = c.recv(2).decode()
        if (message_type == "01"):
            log(f"Receiving transaction ({message_len} bytes)...")
            message = c.recv(message_len).decode()
            while (message_len > len(message)):
                tmp = c.recv(message_len - len(message)).decode()
                message = ''.join((message, tmp))
                print(message)
                # message.join(c.recv(message_len - len(message)).decode())
                # message_len = len(message)
            c.send(b"00000000")
            log(f"Closed connection from {addr[0]}:{addr[1]}")
            transaction = self.rebuild_transaction(message)
            if(self.is_valid_transaction(transaction)):
                db.update_pending(transaction.sender, transaction.recipient, transaction.amount)
                self.pending_transactions.append(transaction)
        else:
            log("Unknown message type")
            c.send(str(0).zfill(8).encode())

    def listen(self):
        self.listening = True
        self.usock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.tsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.usock.bind(('', 60000))
        self.tsock.bind((self.host, self.port))
        threading.Thread(target=self.announce).start()
        time.sleep(0.1)
        threading.Thread(target=self.receive).start()
        try:
            while self.listening:
                time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            log("Interrupt received. Stopping threads...")
            self.listening = False
            self.new_block()
            self.cleanup()
