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

##### Client:

###### Create a client object with name "Client 1" and a balance of 500:

```
from client import *
client1 = Client("Client 1", 500)
```

"Client 1," a hexadecimal representation of their public key, and their initial balance will be included in their entry in the client database.

##### Transaction:

###### Create a transaction between two clients:

```
from transaction import *
transaction1 = Transaction(client1.identity, client2.identity, 100)
```

where _client1_ sends _client2_ an amount of _100._ Transaction verification currently isn't implemented yet.

##### Blockchain

###### Create and initialise a blockchain.

```
from block import *
blockchain = Blockchain()
```

An empty block is added as the genesis block.

###### Add a transaction to the list of pending transactions:

```
blockchain.add_transaction(transaction1)
```

###### Create a new block:

```
blockchain.new_block()
```

This adds all pending transactions to the new block and drops all transactions that can't be verified. This behaviour should be changed in the future.
