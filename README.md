# buzz-block

Central Philippine University BSCS Thesis - Villanueva Group

An NFC-based transaction system for local events using blockchain.

### Requirements

###### a. [`python3`](https://www.python.org/downloads/)

###### b. python library [`pyca/cryptography`](https://cryptography.io/en/latest/)

```
python -m pip install --user cryptography
```

###### c. sqlite3 - for the client database

### TO DO

- [X] move chain.pending_transactions to tracker
- [X] block creation is left to the tracker
- [ ] peer to peer networking
- [ ] consensus algorithm
- [X] switch to cryptography instead of pycrypto
- [X] query the tracker's user database for account balance
- [X] disallow negative balances
- [ ] multiple trackers

### Examples

- Creating a tracker:

```
>>> from nodetracker import Tracker
>>> tracker = Tracker()
>>> tracker.listen()
```

This creates a tracker and tells it to start listening on the network for connections. It ultimately maintains and records the blockchain. It keeps a local database that contains all user identities and their balances. Connections come from peers, which mainly send transactions to be verified and added to the blockchain.

- Creating a peer:

```
>>> from nodepeer import Peer
>>> peer = Peer([password=None], [filename="client.json"])
```

This creates a peer that can create transactions and send these to the tracker. A peer is usually a smartphone that can read NFC tags. Client information stored in `filename` is decrypted with `password`, and a client object is created with this. Requires a client object in order to create and sign transactions.

- Create a transaction:

```
>>> peer.send_transaction(sender, amount)
```

This creates a transaction object with the peer's client object as the recipient. `sender`(of the amount, not the transaction) is the hexadecimal identifier found on an NFC chip that will be scanned by the peer. The peer then sends this to the tracker for verification before being added to a list of pending transactions to be added.
