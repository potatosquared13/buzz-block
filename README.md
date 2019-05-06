# buzz-block

Central Philippine University BSCS Thesis - Villanueva Group

An NFC-based transaction system using blockchain.

The backend is mainly written in Python3, and the use of some web technologies are planned.

Currently nothing is saved when python exits.

### Requirements
###### a. [`python3`](https://www.python.org/downloads/)
###### b. `python3-pycryptodomex` - Assuming python is installed:

```
python -m pip install pycryptodome
```

### Examples

##### client

###### Create a client object with the ability to sign transactions:

```
from client import *
client1 = Client()
```

##### transaction

###### Create a transaction between two clients:

```
from transaction import *
transaction1 = Transaction(client1.identity, client2.identity, 100)
```


##### block

###### Create and initialise an empty blockchain.
An empty block with proof 0 and last_hash 0 are made and added as the genesis block.

```
from block import *
blockchain = Blockchain()
```

###### Add a transaction to the list of pending transactions:

```
blockchain.add_transaction(transaction1)
```

###### Create a new block populated with current pending transactions:

```
blockchain.new_block()
```
