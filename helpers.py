# miscellaneous helper functions

import json

from datetime import datetime
from binascii import hexlify
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from math import trunc

# returns utf8-encoded sha256 hash of message
def sha256(message):
    digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
    digest.update(message.encode())
    return hexlify(digest.finalize()).decode()
    # return SHA256.new(message.encode('utf8')).hexdigest()

# returns obj as a json object
def jsonify(obj):
    return json.dumps(obj, default=lambda o: o.__dict__, separators=(',',':'), indent=None, sort_keys=True)

def format_number(number):
    value_past_decimal = number - trunc(number)
    number_sequence = str(trunc(number))
    new_number_sequence = ''
    reverse_sequence = number_sequence[::-1]
    for i in range(len(reverse_sequence)):
        if (((i + 1) % 3) == 0) and (i != len(reverse_sequence) - 1):
            new_number_sequence = ',' + reverse_sequence[i] + new_number_sequence
        else:
            new_number_sequence = reverse_sequence[i] + new_number_sequence
    return new_number_sequence +'.{0:.2f}'.format(value_past_decimal)[2:]