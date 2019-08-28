import json
from Crypto.Hash import SHA256


# returns sha256 hash of message
def sha256(message):
    return SHA256.new(message.encode('utf8'))

# returns obj as a json object
def jsonify(obj):
    return json.dumps(obj, default=lambda o: o.__dict__, indent=4)