import json
import hashlib

# returns hexadecimal representation of sha256 hash of message
def sha256(message):
    return hashlib.sha256(message.encode()).hexdigest()

# returns obj as a json object
def jsonify(obj):
    return json.dumps(obj, default=lambda o: o.__dict__, indent=4)