import hashlib


def sha256(message):
    return hashlib.sha256(message.encode()).hexdigest()
