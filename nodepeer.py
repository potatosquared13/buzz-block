import os.path

from node import *

class Peer(Node):
    def __init__(self, password=None, filename='client.json'):
        super().__init__()
        self.port = 50001
        self.usock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.tsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.usock.bind(('', 60001))
        self.tsock.bind((self.host, self.port))
        if password:
            self.client = Client(filename=filename, password=password)
        self.tracker = (None, None)
        if(os.path.isfile('./blockchain.json')):
            self.read_block_from_file()
        else:
            self.update_block()
            pass

    def send_transaction(self, sender, amount):
        transaction = Transaction(sender, self.client, amount)
        self.client.sign(transaction)
        self.send(self.tracker, "01", transaction.json)

    def update_block(self):
        # ask tracker for block
        pass

    def discover(self):
        self.tracker = (None, None)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.bind(('', 0))
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(4)
            while (self.tracker == (None, None)):
                log("Broadcasting discovery request...")
                sock.sendto('62757a7aDS'.encode(), ('<broadcast>', 60000))
                data, addr = sock.recvfrom(1024)
                log(f"Found tracker at {addr[0]}")
                self.tracker = (addr[0], 50000)

    def handle_connection(self):
        pass

