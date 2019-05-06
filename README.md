# buzz-block

Central Philippine University BSCS Thesis - Villanueva Group

An NFC-based transaction system using blockchain.

Mainly written in python, with tinyDB for the database.

Flask might eventually be used.

### Requirements

###### a. [`python3`](https://www.python.org/downloads/)

###### b. PyCrypto - for various cryptographic functions

```
python -m pip install --user pycryptodome
```

###### c. tinydb (not used yet) - for the client database

```
python -m pip install --user tinydb
```

### Examples

##### Client:

###### Create a client object:

```
from client import *
client1 = Client()
```

##### Transaction:

###### Create a transaction between two clients:

```
from transaction import *
transaction1 = Transaction(client1.identity, client2.identity, 100)
```

where _client1_ sends _client2_ an amount of _100_


##### Blockchain

###### Create and initialise an empty blockchain.

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
