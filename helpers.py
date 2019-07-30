import json
from datetime import datetime
from binascii import hexlify
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
# from Crypto.Hash import SHA256


# returns utf8-encoded sha256 hash of message
def sha256(message):
    digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
    digest.update(message.encode())
    return hexlify(digest.finalize()).decode()
    # return SHA256.new(message.encode('utf8')).hexdigest()

# returns obj as a json object
def jsonify(obj):
    return json.dumps(obj, default=lambda o: o.__dict__, indent=4)

# prints message with timestamp
def log(msg):
    print("[" + datetime.now().isoformat() + "] " , end='', flush=True)
    print(msg)

