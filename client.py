# TODO - INC include client type (seller/buyer)
#      - OK  write/read private key from file

# import Crypto.Random
# from Crypto.Cipher import AES
# from Crypto.PublicKey import RSA
# from Crypto.Signature import PKCS1_v1_5

import json

from binascii import hexlify, unhexlify
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import padding

# import db
import helpers


class Client:
    def __init__(self, name = None, filename = None, password = None):
        if name and not token:
            # rand = Crypto.Random.new().read
            self.name = name
            self._private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            self._public_key = self._private_key.public_key()
            # self._private_key = RSA.generate(1024, rand)
            # self._public_key = self._private_key.publickey()
            # self._signer = PKCS1_v1_5.new(self._private_key)
            # db.insert(self, amount)
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
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        transaction.signature = hexlify(signature).decode()
        # return hexlify(signature).decode()
        # tmp_transaction = transaction
        # del tmp_transaction.signature
        # hash = helpers.sha256(helpers.jsonify(tmp_transaction))
        # transaction.signature =  hexlify(self._signer.sign(hash)).decode('ascii')

    def write_to_file(self, password, filename="client.json"):
        key = self._private_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.BestAvailableEncryption(helpers.sha256(password))
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
        # identity = hexlify(self._public_key.exportKey(format='DER'))
        # return identity.decode('ascii')
