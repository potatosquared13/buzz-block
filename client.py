# NOTE - This script will be run from the server, after a user signs up
#      - The user's public key will be saved to the database, along with other
#        identifying information like name, etc.
#      - This object is only used to create the client object
#        the balance, actual name, etc., will be handled in the database

import helpers
import Crypto.Random
from binascii import hexlify
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5


class Client:
    def __init__(self):
        rand = Crypto.Random.new().read
        self._private_key = RSA.generate(1024, rand)
        self._public_key = self._private_key.publickey()
        self._signer = PKCS1_v1_5.new(self._private_key)

    def sign(self, transaction):
        tmp_transaction = transaction
        del tmp_transaction.signature
        hash = SHA.new(helpers.jsonify(tmp_transaction).encode('utf8'))
        transaction.signature =  hexlify(self._signer.sign(hash)).decode('ascii')

    @property
    def identity(self):
        identity = hexlify(self._public_key.exportKey(format='DER'))
        return identity.decode('ascii')
