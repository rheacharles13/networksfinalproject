
# DESIGN.md for Final Project

# Benjamin Vazzana (bav2113), Rhea Charles (rtc2133), Shinjini Mukherjee (sm5160), Shreeya Patel (sjp2236)

# Blockchain Design
Our project will use a decentralized ledger to monitor transactions and keep track of meal swipe transfers between members of a friend group. Our blockchain will distribute the user's meal swipe "data" (count of meal swipes left) across a network of "friend" nodes, or a chosen group of nodes. Each block of the chain stores transactions in a way that is easy to audit and verify, but difficult to edit or change. It is important that transactions cannot be edited/changed because once someone receives a swipe they may use it immediately. 


# P2P Protocol
Upon joining the network, each new node must first contact a central server to obtain a list of peers. Before making any transactions, a new node must either join a group or create a new one. If joining an existing group, the node must include a valid group code in its request to the central server. When a user joins an existing group, the server broadcasts the user’s information (UNI, swipe balance, etc) to every peer within the group. After obtaining peer information, the new node sends a request to a randomly selected peer within the group to obtain the most up-to-date copy of the blockchain. For every transaction, a peer broadcasts the transaction information to each peer within the group, and each peer updates their local ledger.

Example Workflow \\
Alice wants to send Bob 1 meal swipe.
Alice signs a transaction and broadcasts it.
Peers verify Alice has ≥1 swipe and relay the transaction.
The block leader includes it in the next block.
After consensus, the block is added, and Bob’s balance updates.


# Demo Application Design
Assuming each peer node runs its own server and local blockchains logic, as well as the fact that peer communication will broadcast new transactions to sync and track across peers, we would want to implement a Python flask server with HTML/CSS/JS to implement the UI. The key pages will be:
Home: see the latest swipe activity in the friend group
Offer swipe
Accept swipe: view open offers and click a button to accept
Ledger: view transaction history

