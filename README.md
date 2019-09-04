# buzz-block

Central Philippine University BSCS Thesis - Villanueva Group

An NFC-based transaction system for local events using blockchain.

### Requirements

 a. [`python3`](https://www.python.org/downloads/)

 b. python library [`pyca/cryptography`](https://cryptography.io/en/latest/)

```
python -m pip install --user cryptography
```

 c. sqlite3 - for the client database

### TO DO

- [X] peer to peer networking
- [X] consensus algorithm
- [X] query own blockchain for account balance
- [ ] fallback tracker query for balance
- [X] disallow negative balances
- [X] allow adding funds after genesis block is created
- [ ] better transaction/block structure
- [ ] multiple trackers
- [ ] web app for user registration and transaction tracking
- [ ] android app

### Examples

- Creating a tracker:

```
>>> from tracker import Tracker
>>> t = Tracker(pin)
>>> t.start()
```

This creates a tracker and tells it to start listening on the network. It is a modified node without the ability to send transactions. Its main purpose is to maintain and record the blockchain. It keeps a local database that contains all user identities and their balances. Connections come from peers, which mainly send transactions to be verified and added to the blockchain.
The tracker is also the node that will group transactions and request for the network to create a new block. This can be done by calling `tracker.new_block()`.
_pin_ is a four-character string that will be used to sign transactions that introduce new funds to the network.

- Creating a peer:

```
>>> from node import Node
>>> p = Node(password="1111", filename="client.json")
>>> p.start()
>>> p.get_tracker()
>>> p.get_peers()
```

This creates a peer that can create transactions and send these to the network. A peer will be a smartphone that can read NFC tags. Client information stored in `filename` is decrypted with `password`, and a client object is created with this. Requires a client object in order to create and sign transactions.

- Create a transaction:

```
>>> p.send_transaction(sender, amount)
```

This creates a transaction object with the peer's client object as the recipient. `sender`(of the amount, not the transaction) is the hexadecimal identifier found on an NFC chip that will be scanned by the peer. The peer sends this transaction to the entire network for recording until called to create a new block.
