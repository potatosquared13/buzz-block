# client object for nodes

import json

from binascii import hexlify, unhexlify
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

import helpers

class Client:
    def __init__(self, name = None, filename = None, password = None):
        if (name and not password):
            self.name = name
            self._private_key = ec.generate_private_key(
                ec.SECP384R1(),
                default_backend()
            )
            self._public_key = self._private_key.public_key()
        else:
            client_json =  json.load(open(filename, 'r'))
            self.name = client_json["name"]
            key_encrypted = client_json["key"]
            self._private_key = serialization.load_der_private_key(
                unhexlify(key_encrypted),
                password=helpers.sha256(password).encode(),
                backend=default_backend()
            )
            self._public_key = self._private_key.public_key()

    def sign(self, transaction):
        msg = unhexlify(transaction.hash)
        signature = self._private_key.sign(
            msg,
            ec.ECDSA(hashes.SHA256())
        )
        transaction.signature = hexlify(signature).decode()

    def write_to_file(self, password, filename="client.json"):
        key = self._private_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.BestAvailableEncryption(helpers.sha256(password).encode())
        )
        o = {'name': self.name, 'key': hexlify(key).decode()}
        with open(filename, 'w') as f:
            f.write(helpers.jsonify(o))

    @property
    def identity(self):
        identity = self._public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return hexlify(identity).decode()


