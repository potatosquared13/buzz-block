# buzz-block

Central Philippine University BSCS Thesis - Villanueva Group

An NFC-based transaction system using blockchain.

### Requirements

###### a. [`python3`](https://www.python.org/downloads/)

###### b. PyCrypto - for various cryptographic functions

```
python -m pip install --user pycryptodome
```

###### c. sqlite3 - for the client database

This is a standard python library and doesn't need any additional steps to install.

### Examples

##### Client:

###### Create a client object with name "Client 1":

```
from client import *
client1 = Client("Client 1")
```

The name "_Client 1_" will be included in the client database and used in printing receipts. Their public key/"identity" will be used in the blockchain, checking for balances, and everywhere else.

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
