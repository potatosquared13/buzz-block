# buzz-block

Central Philippine University BSCS Thesis - Villanueva Group

An NFC-based transaction system for local events using blockchain.

### Requirements

###### a. [`python3`](https://www.python.org/downloads/)

###### b. PyCrypto - for various cryptographic functions

```
python -m pip install --user pycryptodome
```

###### c. sqlite3 - for the client database

### Notes on missing functionality/etc

- __networking:__ initially the blockchain should be on a single node which receives transactions from clients over a local network. Currently transactions are created and added on the same machine.

- __client database:__ this is where client information such as their name, identity(public key), balance and pending balance(balance after all pending transactions are added) will be stored. For now, it will reside on the same machine that the single node will be on.

- __actual client creation:__ when a client registers, for the users who will use the system to buy items, they probably don't need to know their private key since that is only used for signing transactions, which is the job of the stall owners/cashiers ("staff"). We need a way to securely send staff their private keys, or rethink about this part of the system.

### Examples

- Requirements for testing locally:

```
> python
>>> import db
>>> import server
>>> from client import Client
>>> from transaction import Transaction
```

- Create a client:

```
>>> c1 = Client("Villanueva, Daniel", 500)
>>> c2 = Client("Ibelgaufts, Justin", 500)
```

This creates two clients and adds their public keys, names, and an initial amount of 500 to the client table in database.db.
_Note:_ the private keys are stored in memory in the Client object created, which will be lost when exiting the python interpreter and so another client object will have to be made to sign transactions afterwards. This will be fixed eventually, but in the meantime the database can be deleted when wanting to start over.

- Create a transaction:

```
>>> t1 = Transaction(c1.identity, c2.identity, 100)
```

We pass the client identities (_c1.identity, c2.identity_), which are hexadecimal representations of their public keys, and an amount (_100_). This creates a transaction object which still has to be signed by the sender of the transaction (c1).

- Sign a transaction:

```
>>> c1.sign(t1)
```

This takes the transaction object, strips the _signature_ field from it, gets its hash, and then signs it using c1's private key. The signature becomes part of the transaction, and it can be easily verified with the sender's identity([example shown in server.py under the function new_transaction](server.py)).

We can see the transaction by `print()`ing the transaction's `json` property.

- Add to blockchain:

```
>>> server.new_transaction(t1.json)
```

We pass the JSON of the transaction instead of the actual transaction because the server will receive the transaction over a local network, and sending a stream of text is easier than python objects. The transaction is verified before it is added to the blockchain's list of pending transactions. This also updates the client database so that their pending balance reflects the newly added transactions.

- Create a new block (and add pending transactions to it):

```
>>> server.new_block()
```

This updates the client database so that the affected accounts have their balances updated.

- Check client database

```
>>> import helpers
>>> print(helpers.jsonify(db.search("Villanueva")))
```

The search function accepts both a partial string of the client's name or their identity. The above will print their entry in the database in JSON.
