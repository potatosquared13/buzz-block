import os.path

from node import *

class Peer(Node):
    def __init__(self, filename='client.json', password=None):
        super().__init__()
        if password:
            self.client = Client(filename=filename, password=password)
        self.tracker = (None, None)

    def send_transaction(self, sender, amount):
        if (amount < 1):
            return
        transaction = Transaction(sender, self.client.identity, amount)
        self.client.sign(transaction)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect(self.tracker)
            self.send(sock, 1, transaction.json)
            response = self.receive(sock)
            logging.info(f"Response: {response[1]}")

    def get_balance(self, client):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect(self.tracker)
            self.send(sock, 2, client)
            response == self.receive(sock)
            return response[1]

    def update_chain(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect(self.tracker)
            self.send(sock, 3, str(len(self.chain.blocks)))
            response = self.receive(sock)
            if (not response[1] == "UP TO DATE"):
                logging.info("Rebuilding chain")
                self.chain = self.rebuild_chain(response[1])
            logging.info(f"Chain is up to date ({self.chain.last_block.timestamp})")

    def get_peers(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect(self.tracker)
            self.send(sock, 4, "")

    def connect(self):
        self.tracker = (None, None)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.bind(('', 0))
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(4)
            msg = "62757a7aCN" + self.client.identity
            try:
                while (self.tracker == (None, None)):
                    sock.sendto(msg.encode(), ('<broadcast>', 60000))
                    data, addr = sock.recvfrom(1024)
                    logging.info(f"Found tracker at {addr[0]}")
                    self.tracker = (addr[0], 50000)
            except socket.timeout:
                logging.error("Tracker doesn't seem to be running")

    def disconnect(self):
        msg = "62757a7aDC" + self.client.identity
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.bind(('', 0))
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(msg.encode(), (self.tracker[0], 60000))
        self.stop()

    def handle_connection(self):
        pass

    def start_server(self):
        self.listening = True
        self.address = (socket.gethostbyname(socket.gethostname()), 50001)
        self.usock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.tsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.usock.bind((self.address[0], 60001))
        self.tsock.bind(self.address)
        threading.Thread(target=wait_for_connection).start()
        try:
            while self.listening:
                time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            logging.error("Interrupt received. Stopping threads")
            self.listening = False
            self.write_block_to_file()
            self.stop()
