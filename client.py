# client object for nodes

import os
# import json
import helpers

from binascii import hexlify, unhexlify
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec


class Client:
    def __init__(self, name = None, filename=None):
        if (name and not filename):
            self.name = name
            self._private_key = ec.generate_private_key(
                ec.SECP384R1(),
                default_backend()
            )
            self._public_key = self._private_key.public_key()
            # client_json =  json.load(open(name, 'r'))
            # self.name = client_json["name"]
            # key_encrypted = client_json["key"]
        else:
            with open(filename, 'r') as file:
                f = file.read().splitlines()
                self.name = f[0]
                priv = "-----BEGIN PRIVATE KEY-----\n" + f[1] + "\n-----END PRIVATE KEY-----"
                pub = "-----BEGIN PUBLIC KEY-----\n" + f[2] + "\n-----END PUBLIC KEY-----"
            # with open("private.pem", 'r') as f:
                self._private_key = serialization.load_pem_private_key(
                    priv.encode(),
                    password=None,
                    backend=default_backend()
                )
            # with open("public.pem", 'r') as f:
                self._public_key = serialization.load_pem_public_key(
                    pub.encode(),
                    backend=default_backend()
                )
            # file = open(name, 'r')
            # self.name = file.readline().rstrip()
            # self._private_key = serialization.load_pem_private_key(
            #     file.read().encode(),
            #     # password=helpers.sha256(password).encode(),
            #     password=None,
            #     backend=default_backend()
            # )
            # self._public_key = self._private_key.public_key()

    def sign(self, transaction):
        msg = unhexlify(transaction.hash)
        signature = self._private_key.sign(
            msg,
            ec.ECDSA(hashes.SHA256())
        )
        transaction.signature = hexlify(signature).decode()

    def export(self):
        private_key = self._private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            # encryption_algorithm=serialization.BestAvailableEncryption(helpers.sha256(password).encode())
            encryption_algorithm=serialization.NoEncryption()
        ).decode().replace("-----BEGIN PRIVATE KEY-----","").replace("-----END PRIVATE KEY-----","")
        public_key = self._public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode().replace("-----BEGIN PUBLIC KEY-----","").replace("-----END PUBLIC KEY-----","")
        # o = {'name': self.name, 'key': key.decode()}
            # f.write(helpers.jsonify(o))
        import unicodedata
        import re
        filename = self.name
        filename = unicodedata.normalize('NFKD', filename).encode('ascii', 'ignore').decode()
        filename = re.sub('[^\w\s-]', '', filename).strip().lower()
        filename = re.sub('[-\s]+', '-', filename)
        filename = filename + ".key"
        if (not os.path.exists('clients')):
            os.makedirs('clients')
        filename = "clients/"+filename
        with open(filename, 'w') as f:
            f.write(f"{self.name}\n{''.join(private_key.splitlines())}\n{''.join(public_key.splitlines())}")
        # with open("private.pem", 'w') as f:
            # f.write(f"{private_key}")
        # with open("public.pem", 'w') as f:
            # f.write(f"{public_key}")

    @property
    def identity(self):
        identity = self._public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return hexlify(identity).decode()[48:]

