# peer.py
from flask import Flask, request, jsonify, render_template_string, redirect
import threading, requests, time, json
from block import Blockchain
from transaction import Transaction
import sys



app = Flask(__name__)
HOST = "0.0.0.0"
# PORT = 5002  # Change for each peer
PORT = int(sys.argv[2])  # Convert port to integer
PEER_NAME = f"peer-{PORT}"  # Name based on port

TRACKER_HOST = sys.argv[1]
#socket
#
TRACKER_PORT = 8000

INIT_BALANCE = 150

balances = {}
# Initialize balances with our own peer
balances[PEER_NAME] = INIT_BALANCE

blockchain = Blockchain(difficulty=2)
peers = set()

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>{{ peer_name }} - Blockchain Peer</title>
    <style>
        :root {
            --primary: #3498db;
            --secondary: #2ecc71;
            --dark: #2c3e50;
            --light: #ecf0f1;
            --danger: #e74c3c;
            --success: #27ae60;
            --warning: #f39c12;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f8f9fa;
            color: #333;
            line-height: 1.6;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        header {
            background-color: var(--dark);
            color: white;
            padding: 20px 0;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        h1, h2, h3 {
            margin-top: 0;
        }
        
        h1 {
            font-size: 2.2rem;
            margin-bottom: 10px;
        }
        
        h2 {
            color: var(--dark);
            font-size: 1.8rem;
            border-bottom: 2px solid var(--primary);
            padding-bottom: 10px;
            margin-top: 30px;
        }
        
        h3 {
            color: var(--dark);
            font-size: 1.4rem;
            margin: 25px 0 15px;
        }
        
        .card {
            background: white;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            padding: 20px;
            margin-bottom: 25px;
        }
        
        .transaction-list, .block-list {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        
        .transaction-item, .block-item {
            background: white;
            border-left: 4px solid var(--primary);
            margin-bottom: 10px;
            padding: 15px;
            border-radius: 4px;
            box-shadow: 0 2px 3px rgba(0,0,0,0.05);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .transaction-item:hover, .block-item:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        
        .block-item {
            border-left-color: var(--secondary);
        }
        
        .transaction-details, .block-details {
            font-size: 0.9rem;
            color: #666;
            margin-top: 8px;
        }
        
        .balance-card {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 25px;
        }
        
        .balance-item {
            background: white;
            padding: 15px;
            border-radius: 6px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            text-align: center;
        }
        
        .balance-name {
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .balance-amount {
            font-size: 1.2rem;
        }
        
        .balance-positive {
            color: var(--success);
        }
        
        .balance-negative {
            color: var(--danger);
        }
        
        .form-group {
            margin-bottom: 15px;
        }
        
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
        }
        
        input[type="text"],
        input[type="number"] {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 1rem;
            transition: border 0.3s;
        }
        
        input[type="text"]:focus,
        input[type="number"]:focus {
            border-color: var(--primary);
            outline: none;
        }
        
        .btn {
            display: inline-block;
            background-color: var(--primary);
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 1rem;
            font-weight: 600;
            text-decoration: none;
            transition: background-color 0.3s;
        }
        
        .btn:hover {
            background-color: #2980b9;
        }
        
        .btn-success {
            background-color: var(--success);
        }
        
        .btn-success:hover {
            background-color: #219955;
        }
        
        .btn-warning {
            background-color: var(--warning);
        }
        
        .btn-warning:hover {
            background-color: #e67e22;
        }
        
        .action-buttons {
            display: flex;
            gap: 15px;
            margin-top: 30px;
        }
        
        .empty-state {
            color: #777;
            text-align: center;
            padding: 30px;
            background: #f9f9f9;
            border-radius: 6px;
        }
        
        .tx-arrow {
            color: var(--primary);
            font-weight: bold;
            margin: 0 5px;
        }
        
        .status-badge {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: bold;
            background: #eee;
            color: #555;
        }
        
        .block-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .block-index {
            font-weight: bold;
            color: var(--dark);
        }
        
        .block-hash {
            font-family: monospace;
            color: #666;
            font-size: 0.9rem;
            word-break: break-all;
        }
    </style>
</head>
<body>
    <header>
        <div class="container">
            <h1>{{ peer_name }}</h1>
            <p>Blockchain Node</p>
        </div>
    </header>
    
    <main class="container">
        <section>
            <h2>Network Balances</h2>
            <div class="card">
                {% if balances %}
                <div class="balance-card">
                    {% for peer, balance in balances.items() %}
                    <div class="balance-item">
                        <div class="balance-name">{{ peer }}</div>
                        <div class="balance-amount {% if balance >= 0 %}balance-positive{% else %}balance-negative{% endif %}">
                            {{ balance }}
                        </div>
                    </div>
                    {% endfor %}
                </div>
                {% else %}
                <div class="empty-state">No balance information available</div>
                {% endif %}
            </div>
        </section>
        
        <section>
            <h2>Pending Transactions</h2>
            <div class="card">
                {% if blockchain.current_transactions %}
                <ul class="transaction-list">
                    {% for tx in blockchain.current_transactions %}
                    <li class="transaction-item">
                        <div>
                            <span class="status-badge">Pending</span>
                            <strong>{{ tx.sender }}</strong> 
                            <span class="tx-arrow">→</span> 
                            <strong>{{ tx.receiver }}</strong>
                        </div>
                        <div class="transaction-details">
                            Amount: {{ tx.amount }} | 
                            Not yet confirmed in a block
                        </div>
                    </li>
                    {% endfor %}
                </ul>
                {% else %}
                <div class="empty-state">No pending transactions</div>
                {% endif %}
            </div>
        </section>
        
        <section>
            <h2>Blockchain</h2>
            {% if blockchain.chain %}
            <ul class="block-list">
                {% for block in blockchain.chain|reverse %}
                <li class="block-item">
                    <div class="block-header">
                        <span class="block-index">Block #{{ block.index }}</span>
                        <span class="status-badge">Confirmed</span>
                    </div>
                    <div class="block-hash">Hash: {{ block.hash[:16] }}...</div>
                    
                    {% if block.transactions %}
                    <h3>Transactions ({{ block.transactions|length }})</h3>
                    <ul class="transaction-list">
                        {% for tx in block.transactions %}
                        <li class="transaction-item">
                            <div>
                                <strong>{{ tx.sender }}</strong> 
                                <span class="tx-arrow">→</span> 
                                <strong>{{ tx.receiver }}</strong>
                            </div>
                            <div class="transaction-details">
                                Amount: {{ tx.amount }} | 
                                Confirmed in block {{ block.index }}
                            </div>
                        </li>
                        {% endfor %}
                    </ul>
                    {% else %}
                    <div class="empty-state">No transactions in this block</div>
                    {% endif %}
                </li>
                {% endfor %}
            </ul>
            {% else %}
            <div class="card">
                <div class="empty-state">Blockchain is empty</div>
            </div>
            {% endif %}
        </section>
        
        <section>
            <h2>Create Transaction</h2>
            <div class="card">
                <form method="POST" action="/add_transaction">
                    <div class="form-group">
                        <label for="sender">Sender:</label>
                        <input type="text" id="sender" name="sender" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="receiver">Receiver:</label>
                        <input type="text" id="receiver" name="receiver" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="amount">Amount:</label>
                        <input type="number" id="amount" name="amount" min="1" required>
                    </div>
                    
                    <button type="submit" class="btn btn-success">Submit Transaction</button>
                </form>
            </div>
        </section>
        
        <div class="action-buttons">
            <a href="/mine" class="btn btn-warning">⛏️ Mine New Block</a>
            <a href="/peers" class="btn">🔗 View Network Peers</a>
        </div>
    </main>
</body>
</html>
"""

REQUIRED_KEYS = ['hash', 'previous_hash']

def is_valid_chain(chain_data):
    for i in range(1, len(chain_data)):
        prev = chain_data[i - 1]
        curr = chain_data[i]

        # Defensive check
        for key in REQUIRED_KEYS:
            if key not in curr:
                print(f"Block {i} is missing key: {key}")
                return False
            if key not in prev and key == 'hash':
                print(f"Previous block {i-1} is missing key: 'hash'")
                return False

        # Check hash linkage
        if curr['previous_hash'] != prev['hash']:
            return False
        
        # Check proof of work
        if not curr['hash'].startswith('0' * blockchain.difficulty):
            return False
        
        # Recalculate the hash
        block_obj = blockchain.create_block_from_dict(curr)
        if block_obj.hash != curr['hash']:
            return False

    return True



@app.route('/')
def index():
    if PEER_NAME not in balances:
        balances[PEER_NAME] = INIT_BALANCE
        
    return render_template_string(
        HTML, 
        chain=blockchain.chain, 
        peer_name=PEER_NAME,
        balances=balances,
        pending_txs=blockchain.current_transactions  # Add this line
    )

def get_effective_balance(peer_name):
    """Calculate balance based on confirmed blocks only"""
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
    sender = request.form['sender']
    receiver = request.form['receiver']
    amount = int(request.form['amount'])

    # Initialize balances if needed (for display only)
    if sender not in balances:
        balances[sender] = INIT_BALANCE
    if receiver not in balances:
        balances[receiver] = INIT_BALANCE
        
    # Just store the transaction locally - no broadcasting
    tx = Transaction(sender, receiver, amount)
    if tx not in blockchain.current_transactions:
        blockchain.current_transactions.append(tx)
    else:
        print("Transaction already in pending pool")
    return redirect("/")

def recalculate_balances():
    global balances
    # Reset all balances
    balances = {name: INIT_BALANCE for name in balances}
    
    # Only process mined transactions
    for block in blockchain.chain:
        for tx in block.transactions:
            if tx.sender not in balances:
                balances[tx.sender] = INIT_BALANCE
            if tx.receiver not in balances:
                balances[tx.receiver] = INIT_BALANCE
                
            balances[tx.sender] -= tx.amount
            balances[tx.receiver] += tx.amount

@app.route('/mine')
def mine():
    if not blockchain.current_transactions:
        return "No transactions to mine", 400
        
    # Mine all pending transactions at once
    blockchain.mine()
    
    # Recalculate balances based on new blockchain state
    recalculate_balances()
    
    # Broadcast the new block (which contains all transactions)
    broadcast_block(blockchain.get_last_block())
    
    return redirect("/")

@app.route('/update_peers', methods=['POST'])
def update_peers():
    global peers, balances
    data = request.get_json()
    peers = set(tuple(p) for p in data.get("peers", []))
    
    # Initialize balances for new peers
    for peer_name in data.get("peer_names", []):
        if peer_name not in balances:
            balances[peer_name] = INIT_BALANCE
            
    return jsonify({"status": "ok"}), 200


"""
@app.route('/receive_transaction', methods=['POST'])
def receive_transaction():
    tx_data = request.get_json()["data"]
    tx = Transaction(**tx_data)
    
    # Check if transaction already exists
    if tx in blockchain.current_transactions:
        return jsonify({"status": "transaction already exists"}), 200
        
    blockchain.current_transactions.append(tx)
    return jsonify({"status": "received"}), 200
""" 
@app.route('/receive_block', methods=['POST'])
def receive_block():
    data = request.get_json()
    block_data = data["data"]
    sender = data.get("sender")
    force = data.get("force", False)

    # Skip validation if forced (for initial sync)
    if not force:
        # [Keep all your existing validation checks...]
        pass

    new_block = blockchain.create_block_from_dict(block_data)
    
    # Always add the block if it's the next in sequence
    if new_block.previous_hash == blockchain.get_last_block().hash:
        blockchain.add_block(new_block)
        # Remove any included transactions from pending
        blockchain.current_transactions = [
            tx for tx in blockchain.current_transactions
            if tx not in new_block.transactions
        ]
        recalculate_balances()
        return jsonify({"status": "block added"}), 200
    else:
        # If not the next block, trigger chain resolution
        resolve_conflicts()
        return jsonify({"status": "chain resolution triggered"}), 200




    




def resolve_conflicts():
    global blockchain
    
    print("🔁 Resolving chain conflicts...")
    longest_chain = None
    max_length = len(blockchain.chain)
    
    for peer in peers:
        try:
            if peer[1] == PORT:  # Skip self
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
        # Return appropriate response based on context
        if request:  # If called as a route
            return jsonify({"status": "chain replaced"}), 200
        return True
    
    print("✅ Our chain is already the longest")
    if request:  # If called as a route
        return jsonify({"status": "chain unchanged"}), 200
    return False



@app.route('/peers')
def show_peers():
    return jsonify(list(peers))

@app.route('/chain', methods=['GET'])
def get_chain():
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
    try:
        url = f"http://{TRACKER_HOST}:{TRACKER_PORT}/register"
        payload = {"name": PEER_NAME, "port": PORT}
        res = requests.post(url, json=payload)
        print(f"✅ Registered with tracker: {res.json()}")
        # Initialize balance for this peer
        balances[PEER_NAME] = INIT_BALANCE
    except Exception as e:
        print(f"❌ Could not register: {e}")

def broadcast_transaction(transaction):
    for peer in peers:
        try:
            url = f"http://{peer[0]}:{peer[1]}/receive_transaction"
            requests.post(url, json={"type": "transaction", "data": transaction.__dict__})
        except Exception as e:
            print(f"❌ Could not send tx to {peer}: {e}")

def broadcast_block(block):
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
            # Skip sending to ourselves
            if peer[1] == PORT:
                continue
                
            url = f"http://{peer[0]}:{peer[1]}/receive_block"
            requests.post(url, json={
                "data": block_data,
                "sender": {"ip": HOST, "port": PORT},
                "force": True  # Add this flag to ensure acceptance
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
    # Initialize our own balance
    balances[PEER_NAME] = INIT_BALANCE
    
    # Start Flask in a separate thread
    threading.Thread(target=lambda: app.run(host=HOST, port=PORT, debug=False)).start()
    time.sleep(2)  # Give Flask time to start
    
    # Register with tracker
    register_with_tracker()
    time.sleep(1)  # Give time for registration
    
    # Use application context for resolve_conflicts
    with app.app_context():
        resolve_conflicts()
    
    # Initial balance calculation
    recalculate_balances()
    
def initialize_peer_balances():
    try:
        # Get peer info from tracker
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
