# peer.py
from flask import Flask, request, jsonify, render_template_string, redirect
import threading, requests, time, json
from block import Blockchain
from transaction import Transaction
import sys

""" 
Implements a complete peer node in a blockchain network with:
- Transaction processing and validation
- Block mining with proof-of-work
- Network synchronization and peer discovery
- Conflict resolution for blockchain forks
- Balance tracking and verification
- Web interface for monitoring node status

The peer connects to a central tracker for peer discovery and maintains
its own copy of the blockchain while communicating with other peers.
"""

app = Flask(__name__)
HOST = "0.0.0.0"
PORT = int(sys.argv[2])
PEER_NAME = f"peer-{PORT}"

TRACKER_HOST = sys.argv[1]
TRACKER_PORT = 8000

INIT_BALANCE = 150

balances = {}

balances[PEER_NAME] = INIT_BALANCE

blockchain = Blockchain(difficulty=2)
peers = set()

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>{{ peer_name }}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 40px;
            background-color: #f4f4f4;
            color: #333;
        }
        h2 {
            color: #2c3e50;
        }
        h3 {
            margin-top: 30px;
            color: #34495e;
        }
        ul {
            background: #fff;
            padding: 15px;
            border-radius: 5px;
            list-style-type: none;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        li {
            margin-bottom: 10px;
            padding: 10px;
            background: #ecf0f1;
            border-left: 5px solid #3498db;
        }
        form {
            background: #fff;
            padding: 15px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            display: inline-block;
            margin-bottom: 20px;
        }
        input[type="text"],
        input[type="number"] {
            width: 200px;
            padding: 8px;
            margin: 5px 0;
            border: 1px solid #ccc;
            border-radius: 4px;
        }
        input[type="submit"] {
            background-color: #27ae60;
            color: white;
            border: none;
            padding: 10px 15px;
            border-radius: 4px;
            cursor: pointer;
        }
        input[type="submit"]:hover {
            background-color: #219150;
        }
        a {
            display: inline-block;
            margin-top: 10px;
            text-decoration: none;
            color: #2980b9;
            font-weight: bold;
            padding: 10px 15px;
            background-color: #ecf0f1;
            border-radius: 4px;
        }
        a:hover {
            text-decoration: underline;
            background-color: #d6eaf8;
        }
        .balance-positive { color: green; }
        .balance-negative { color: red; }
    </style>
</head>
<body>
    <h2>{{ peer_name }}</h2>

    <h3>Balances</h3>
    <ul>
        {% for peer, balance in balances.items() %}
            <li>
                <strong>{{ peer }}:</strong> 
                <span class="{% if balance >= 0 %}balance-positive{% else %}balance-negative{% endif %}">
                    {{ balance }}
                </span>
            </li>
        {% endfor %}
    </ul>

    

    <h3>Pending Transactions</h3>
    <ul>
        {% for tx in pending_txs %}
        <li>
            {{ tx.sender }} → {{ tx.receiver }}: {{ tx.amount }}
        </li>
        {% else %}
        <li>No pending transactions</li>
        {% endfor %}
    </ul>

    <h3>Blockchain</h3>
    <ul>
        {% for block in chain %}
            <li>
                <strong>Index:</strong> {{ block.index }} |
                <strong>Hash:</strong> {{ block.hash[:10] }}... |
                <strong>TXs:</strong> {{ block.transactions|length }}
                {% if block.transactions %}
                <ul>
                    {% for tx in block.transactions %}
                    <li>
                        {{ tx.sender }} → {{ tx.receiver }}: {{ tx.amount }}
                    </li>
                    {% endfor %}
                </ul>
                {% endif %}
            </li>
        {% endfor %}
    </ul>

    <h3>Add Transaction</h3>
    <form method="POST" action="/add_transaction">
        Sender: <input name="sender" required><br>
        Receiver: <input name="receiver" required><br>
        Amount: <input name="amount" type="number" required><br>
        <input type="submit" value="Submit">
    </form>

    <h3><a href="/mine">⛏️ Mine New Block</a></h3>
    <h3><a href="/peers">🔗 View Peers</a></h3>
</body>
</html> 
"""


REQUIRED_KEYS = ['hash', 'previous_hash']

def is_valid_chain(chain_data):
    """
    Validate the integrity of a blockchain.
    
    Args:
        chain_data (list): List of block dictionaries to validate
        
    Returns:
        bool: True if chain is valid, False otherwise
        
    Validation checks:
    1. Required fields present in each block
    2. Correct hash linking between blocks
    3. Valid proof-of-work (leading zeros)
    4. Hash recalculation matches stored hash
    """
    for i in range(1, len(chain_data)):
        prev = chain_data[i - 1]
        curr = chain_data[i]

        for key in REQUIRED_KEYS:
            if key not in curr:
                print(f"Block {i} is missing key: {key}")
                return False
            if key not in prev and key == 'hash':
                print(f"Previous block {i-1} is missing key: 'hash'")
                return False

        # check hash linkage
        if curr['previous_hash'] != prev['hash']:
            return False
        
        # check proof of work (must have N difficulty leading zeros)
        if not curr['hash'].startswith('0' * blockchain.difficulty):
            print(f"Block {i} has invalid proof of work: {curr['hash']}")
            return False
        
        # recalculate the hash to verify
        block_obj = blockchain.create_block_from_dict(curr)
        if block_obj.hash != curr['hash']:
            print(f"Block {i} hash verification failed")
            return False

    return True


@app.route('/')
def index():
    """
    Render the main dashboard showing:
    - Current peer name
    - Account balances
    - Pending transactions
    - Blockchain status
    - Transaction submission form
    """
    if PEER_NAME not in balances:
        balances[PEER_NAME] = INIT_BALANCE
        
    return render_template_string(
        HTML, 
        chain=blockchain.chain, 
        peer_name=PEER_NAME,
        balances=balances,
        pending_txs=blockchain.current_transactions
    )

def get_effective_balance(peer_name):
    """
    Calculate confirmed balance based on blockchain transactions only.
    
    Args:
        peer_name (str): Name of peer to calculate balance for
        
    Returns:
        int: Current confirmed balance (excluding pending transactions)
    """

    balance = INIT_BALANCE
    for block in blockchain.chain:
        for tx in block.transactions:
            if tx.sender == peer_name:
                balance -= tx.amount
            elif tx.receiver == peer_name:
                balance += tx.amount
    return balance

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    """
    Add a new transaction to the network.
    
    Required form parameters:
    - sender: Sending peer name
    - receiver: Receiving peer name  
    - amount: Positive integer amount
    
    Validates:
    - Positive amount
    - Different sender/receiver
    - Sufficient sender balance
    
    Broadcasts valid transactions to all peers.
    """
    sender = request.form['sender']
    receiver = request.form['receiver']
    amount = int(request.form['amount'])

    if amount <= 0:
        return "Amount must be positive", 400
    if sender == receiver:
        return "Sender and receiver must be different", 400
        
    # initialize balances if needed
    if sender not in balances:
        balances[sender] = INIT_BALANCE
    if receiver not in balances:
        balances[receiver] = INIT_BALANCE
        
    # check sender balance
    confirmed_balance = get_effective_balance(sender)
    pending_debits = sum(
        tx.amount for tx in blockchain.current_transactions
        if tx.sender == sender
    )
    if confirmed_balance - pending_debits < amount:
        return "Insufficient balance", 400
        
    tx = Transaction(sender, receiver, amount)
    if tx not in blockchain.current_transactions:
        blockchain.current_transactions.append(tx)
        # broadcast to network
        threading.Thread(target=broadcast_transaction, args=(tx,)).start()
    else:
        print("Transaction already in pending pool")
    return redirect("/")


def recalculate_balances():
    """
    Recompute all peer balances based on:
    1. Initial balances from tracker
    2. Confirmed transactions in blockchain
    
    Updates the global balances dictionary.
    """
    global balances
    
    # get all known peers from tracker
    try:
        url = f"http://{TRACKER_HOST}:{TRACKER_PORT}/peer_info"
        res = requests.get(url)
        if res.status_code == 200:
            peer_names = [info['name'] for info in res.json().values()]
            # initialize all known peers with base balance
            balances = {name: INIT_BALANCE for name in peer_names}
    except Exception as e:
        print(f"⚠️ Could not fetch peer info: {e}")

        balances = {name: INIT_BALANCE for name in balances}
    
    # apply all transactions from blockchain
    for block in blockchain.chain:
        for tx in block.transactions:
            # ensure sender and receiver exist
            if tx.sender not in balances:
                balances[tx.sender] = INIT_BALANCE
            if tx.receiver not in balances:
                balances[tx.receiver] = INIT_BALANCE
                
            # apply transaction
            balances[tx.sender] -= tx.amount
            balances[tx.receiver] += tx.amount


@app.route('/mine')
def mine():
    """
    Mine a new block containing pending transactions.
    
    Steps:
    1. Validates there are transactions to mine
    2. Performs proof-of-work mining
    3. Updates balances
    4. Broadcasts new block to network
    
    Redirects to dashboard after completion.
    """
    if not blockchain.current_transactions:
        return "No transactions to mine", 400
        
    # mine all pending transactions at once
    last_block = blockchain.get_last_block()
    new_block = blockchain.mine()
    
    # check if mining was successful
    if new_block is None:
        return "Mining failed - no new block created", 400
    
    # verify we actually mined a new block
    if new_block.index == last_block.index:
        return "Mining failed - same block index", 400
    
    recalculate_balances()
    
    # broadcast the new block to all peers
    broadcast_block(new_block)
    
    return redirect("/")

@app.route('/update_peers', methods=['POST'])
def update_peers():
    """
    Update peer list from tracker/network.
    
    Expected JSON:
    {
        "peers": [(host, port), ...],
        "peer_names": [name1, name2, ...] 
    }
    
    Also initializes balances for new peers.
    """
    global peers, balances
    data = request.get_json()
    peers = set(tuple(p) for p in data.get("peers", []))
    
    # initialize balances for new peers
    for peer_name in data.get("peer_names", []):
        if peer_name not in balances:
            balances[peer_name] = INIT_BALANCE
            
    return jsonify({"status": "ok"}), 200


@app.route('/receive_transaction', methods=['POST'])
def receive_transaction():
    """
    Receive a transaction from another peer.
    
    Expected JSON:
    {
        "data": transaction_data,
        "from_peer": bool
    }
    
    Validates and adds transaction if new.
    Rebroadcasts if not from another peer.
    """
    tx_data = request.get_json()
    if "data" not in tx_data:
        return jsonify({"status": "invalid data"}), 400
        
    tx = Transaction(**tx_data["data"])
    
    # check if transaction already exists
    if tx in blockchain.current_transactions:
        return jsonify({"status": "transaction already exists"}), 200
        
    # validate transaction
    blockchain.current_transactions.append(tx)
    
    if not tx_data.get("from_peer", False):
        threading.Thread(target=broadcast_transaction, args=(tx,)).start()
        
    return jsonify({"status": "received"}), 200

@app.route('/receive_block', methods=['POST'])
def receive_block():
    """
    Receive a new block from the network.
    
    Expected JSON:
    {
        "data": block_data,
        "sender": peer_info,
        "force": bool
    }
    
    Handles:
    - Duplicate blocks
    - Chain extensions
    - Fork resolution
    """
    data = request.get_json()
    block_data = data["data"]
    sender = data.get("sender")
    force = data.get("force", False)

    # check if block already exists
    if any(block.hash == block_data["hash"] for block in blockchain.chain):
        # Remove any transactions that are in this block
        blockchain.current_transactions = [
            tx for tx in blockchain.current_transactions
            if not any(
                block_tx.sender == tx.sender and 
                block_tx.receiver == tx.receiver and
                block_tx.amount == tx.amount
                for block_tx in [Transaction(**tx_data) for tx_data in block_data["transactions"]]
            )
        ]
        return jsonify({"status": "block already exists"}), 200

    try:
        new_block = blockchain.create_block_from_dict(block_data)
    except Exception as e:
        return jsonify({"status": f"invalid block data: {str(e)}"}), 400
    
    # validate proof of work
    if not new_block.hash.startswith('0' * blockchain.difficulty):
        return jsonify({"status": "invalid proof of work"}), 400

    # case 1: vlock extends current chain
    if new_block.previous_hash == blockchain.get_last_block().hash:
        blockchain.add_block(new_block)
        
        blockchain.current_transactions = []
        recalculate_balances()
        return jsonify({"status": "block added"}), 200
    
    # case 2: block causes a fork
    return handle_chain_resolution(new_block)

def handle_chain_resolution(new_block):
    """
    Resolve blockchain forks by adopting the longest valid chain.
    
    Args:
        new_block (Block): The conflicting block
        
    Returns:
        JSON response with resolution status
    """
    print("⚠️ Fork detected - resolving chain...")
    
    # get all peer chains to find the longest valid one
    all_chains = [blockchain.chain]
    
    for peer in peers:
        try:
            # skip self 
            if peer[1] == PORT:
                continue
                
            url = f"http://{peer[0]}:{peer[1]}/chain"
            response = requests.get(url, timeout=3)
            
            if response.status_code == 200:
                data = response.json()
                peer_chain = [blockchain.create_block_from_dict(b) for b in data["chain"]]
                if is_valid_chain(data["chain"]):
                    all_chains.append(peer_chain)
        except Exception as e:
            print(f"⚠️ Could not fetch chain from {peer}: {e}")

    # find the longest valid chain
    longest_chain = max(all_chains, key=len)
    
    if len(longest_chain) > len(blockchain.chain):
        print(f"🔄 Adopting longer chain (length {len(longest_chain)})")
        blockchain.chain = longest_chain
        blockchain.current_transactions = []
        recalculate_balances()
        return jsonify({"status": "chain replaced"}), 200
    
    print("✅ Our chain remains the longest")
    return jsonify({"status": "chain unchanged"}), 200

def resolve_conflicts():
    """
    Actively check network for longer valid chains.
    
    Queries all peers for their chains and adopts the longest valid one.
    
    Returns:
        bool/JSON: True if chain replaced, False otherwise
                   or JSON response if called via route
    """
    global blockchain
    
    print("🔁 Resolving chain conflicts...")
    longest_chain = None
    max_length = len(blockchain.chain)
    
    for peer in peers:
        try:
            # skip self
            if peer[1] == PORT:
                continue
                
            url = f"http://{peer[0]}:{peer[1]}/chain"
            response = requests.get(url, timeout=3)
            
            if response.status_code == 200:
                data = response.json()
                if data["length"] > max_length and is_valid_chain(data["chain"]):
                    max_length = data["length"]
                    longest_chain = data["chain"]
        except Exception as e:
            print(f"⚠️ Could not fetch chain from {peer}: {e}")

    if longest_chain:
        print(f"🔄 Adopting longer chain (length {max_length})")
        blockchain.chain = [blockchain.create_block_from_dict(b) for b in longest_chain]
        recalculate_balances()
        
        if request: 
            return jsonify({"status": "chain replaced"}), 200
        return True
    
    print("✅ Our chain is already the longest")
    if request:  # If called as a route
        return jsonify({"status": "chain unchanged"}), 200
    return False

@app.route('/peers')
def show_peers():
    """Return JSON list of known peers."""
    return jsonify(list(peers))

@app.route('/chain', methods=['GET'])
def get_chain():
    """
    Return the current blockchain.
    
    Returns:
        JSON: {
            "length": chain_length,
            "chain": [block1_data, block2_data, ...]
        }
    """
    chain = []
    for block in blockchain.chain:
        block_data = {
            "index": block.index,
            "previous_hash": block.previous_hash,
            "timestamp": block.timestamp,
            "transactions": [tx.__dict__ for tx in block.transactions],
            "proof_of_work": block.proof_of_work,
            "hash": block.hash,
        }
        chain.append(block_data)
    return jsonify({
        "length": len(blockchain.chain),
        "chain": chain,
    })

def register_with_tracker():
    """Register this peer with the central tracker."""
    try:
        url = f"http://{TRACKER_HOST}:{TRACKER_PORT}/register"
        payload = {"name": PEER_NAME, "port": PORT}
        res = requests.post(url, json=payload)
        print(f"✅ Registered with tracker: {res.json()}")
        # initialize balance for this peer
        balances[PEER_NAME] = INIT_BALANCE
    except Exception as e:
        print(f"❌ Could not register: {e}")

def broadcast_transaction(transaction):
    """
    Broadcast a transaction to all peers.
    
    Args:
        transaction (Transaction): Transaction to broadcast
    """
    for peer in peers:
        try:
            # skip self
            if peer[1] == PORT:
                continue
                
            url = f"http://{peer[0]}:{peer[1]}/receive_transaction"
            requests.post(url, json={
                "data": transaction.__dict__,
                "from_peer": True
            }, timeout=3)
        except Exception as e:
            print(f"❌ Could not send tx to {peer}: {e}")

def broadcast_block(block):
    """
    Broadcast a new block to all peers.
    
    Args:
        block (Block): Block to broadcast
    """
    block_data = {
        "index": block.index,
        "previous_hash": block.previous_hash,
        "timestamp": block.timestamp,
        "transactions": [tx.__dict__ for tx in block.transactions],
        "proof_of_work": block.proof_of_work,
        "hash": block.hash,
    }
    
    for peer in peers:
        try:
            if peer[1] == PORT:
                continue
                
            url = f"http://{peer[0]}:{peer[1]}/receive_block"
            requests.post(url, json={
                "data": block_data,
                "sender": {"ip": HOST, "port": PORT},
                "force": True  # ensure peers accept valid blocks
            }, timeout=3)
        except Exception as e:
            print(f"❌ Could not send block to {peer}: {e}")

""" 
def start():
    threading.Thread(target=lambda: app.run(host=HOST, port=PORT, debug=False)).start()
    time.sleep(2)
    register_with_tracker()
""" 

def start():
    """
    Initialize and start the peer node.
    
    Steps:
    1. Initialize balances
    2. Start Flask server
    3. Register with tracker
    4. Sync with network
    5. Initialize balances
    """
    # initialize own balance
    balances[PEER_NAME] = INIT_BALANCE
    
    # start Flask in a separate thread
    threading.Thread(target=lambda: app.run(host=HOST, port=PORT, debug=False)).start()
    time.sleep(2)
    
    # register with tracker
    register_with_tracker()
    time.sleep(1)
    
    # sync with network and get latest blockchain
    with app.app_context():
        resolve_conflicts()
    
    # calculate balances based on blockchain state
    recalculate_balances()
    
def initialize_peer_balances():
    """Initialize balances for all known peers from tracker data."""
    try:
        # get peer info from tracker
        url = f"http://{TRACKER_HOST}:{TRACKER_PORT}/peer_info"
        res = requests.get(url)
        if res.status_code == 200:
            for peer_str, info in res.json().items():
                peer_name = info['name']
                if peer_name not in balances:
                    balances[peer_name] = info['initial_balance']
    except Exception as e:
        print(f"⚠️ Could not initialize peer balances: {e}")

def try_resolve_chain():
    """Attempt to sync with the longest valid chain from peers."""
    global blockchain
    print("🔍 Trying to sync blockchain from peers...")
    longest_chain = blockchain.chain
    for peer in peers:
        try:
            url = f"http://{peer[0]}:{peer[1]}/chain"
            res = requests.get(url, timeout=3)
            if res.status_code != 200:
                continue
            data = res.json()
            chain_data = data["chain"]
            if data["length"] > len(longest_chain) and is_valid_chain(chain_data):
                longest_chain = [blockchain.create_block_from_dict(b) for b in chain_data]
                print(f"🔄 Found a longer chain from {peer}")
        except Exception as e:
            print(f"⚠️ Could not contact peer {peer}: {e}")

    if len(longest_chain) > len(blockchain.chain):
        blockchain.chain = longest_chain
        print("✅ Synced with longer valid chain.")
    else:
        print("✅ Current chain is already the longest.")


if __name__ == "__main__":
    start()
