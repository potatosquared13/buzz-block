### Instructions
- clone the testing branch somewhere and `cd` into it

- run `test_create.py`
This will create a few clients and vendors, and initialise the client balances to 500. It will also create a `blockchain.json`, `database.db`, and a bunch of client / vendor key files.

- in a python shell:
```
>>> from leader import Leader
>>> node = Leader(N) 
```
where `N` is the number of pending transactions to hold before starting consensus.

- in a separate commandline:
```
> python -i test_node.py
```
This will load a bunch of clients and vendors, and the vendors will attempt to connect to each other (and the leader node, which will inform the other nodes that it's the leader. So make sure the leader is running before ). The vendor nodes will not do anything.

- (on the phone) delete `buzz/blockchain.json` if it exists, and replace `client.key` and `vendor.key` with newly created files. Pick one anime girl and rename the file to client.key, and one restaurant/establishment to vendor.key. Put these in buzz/.

- run the mobile application. It will try to connect to all of the nodes above, and request an up-to-date copy of the blockchain from the leader node.

- Cry. This step is vital to the success of the mobile application.

- You can now test your mobile application. You can also leave the leader / vendor nodes running even if you restart the mobile application.

- Make sure to run `node.stop()` in the shell you started the leader node on, and `stop()` in the terminal you ran `test_node.py` in. It will take a few seconds for the sockets to timeout and allow you to close the terminals.