from flask import Flask, request, jsonify, render_template_string, redirect
import threading, requests, time, json
from block import Blockchain
from transaction import Transaction
import sys

app = Flask(__name__)
HOST = "0.0.0.0"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 5000
PEER_NAME = f"peer-{PORT}"
TRACKER_HOST = sys.argv[1]
TRACKER_PORT = 8000
INIT_BALANCE = 150

# Initialize blockchain and threading lock
blockchain = Blockchain(difficulty=2)
peers = set()
chain_lock = threading.Lock()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>{{ peer_name }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background-color: #f4f4f4; color: #333; }
        h2 { color: #2c3e50; }
        h3 { margin-top: 30px; color: #34495e; }
        ul { background: #fff; padding: 15px; border-radius: 5px; list-style-type: none; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        li { margin-bottom: 10px; padding: 10px; background: #ecf0f1; border-left: 5px solid #3498db; }
        form { background: #fff; padding: 15px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); display: inline-block; }
        input[type="text"], input[type="number"] { width: 200px; padding: 8px; margin: 5px 0; border: 1px solid #ccc; border-radius: 4px; }
        input[type="submit"] { background-color: #27ae60; color: white; border: none; padding: 10px 15px; border-radius: 4px; cursor: pointer; }
        input[type="submit"]:hover { background-color: #219150; }
        a { display: inline-block; margin-top: 10px; text-decoration: none; color: #2980b9; font-weight: bold; }
        a:hover { text-decoration: underline; }
        .balances { margin-top: 20px; background: #fff; padding: 15px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    </style>
</head>
<body>
    <h2>{{ peer_name }}</h2>

    <h3>Blockchain (Height: {{ chain|length }})</h3>
    <ul>
        {% for block in chain %}
            <li>
                <strong>#{{ block.index }}</strong> | 
                Hash: {{ block.hash[:10] }}... | 
                TXs: {{ block.transactions|length }} | 
                Prev: {{ block.previous_hash[:10] }}...
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
    <h3><a href="/peers">🔗 View Peers ({{ peers|length }})</a></h3>

    <div class="balances">
        <h3>Account Balances</h3>
        <ul>
            {% for account, balance in balances.items() %}
                <li>{{ account }}: {{ balance }} swipes</li>
            {% endfor %}
        </ul>
    </div>
</body>
</html>
"""

def calculate_balances():
    balances = {}
    # Process all blocks
    for block in blockchain.chain:
        for tx in block.transactions:
            # Initialize accounts if not present
            if tx.sender not in balances:
                balances[tx.sender] = INIT_BALANCE
            if tx.receiver not in balances:
                balances[tx.receiver] = INIT_BALANCE
            # Update balances
            balances[tx.sender] -= tx.amount
            balances[tx.receiver] += tx.amount
    
    # Process pending transactions
    for tx in blockchain.current_transactions:
        if tx.sender not in balances:
            balances[tx.sender] = INIT_BALANCE
        if tx.receiver not in balances:
            balances[tx.receiver] = INIT_BALANCE
        balances[tx.sender] -= tx.amount
        balances[tx.receiver] += tx.amount
    
    return balances

@app.route('/')
def index():
    with chain_lock:
        balances = calculate_balances()
        return render_template_string(
            HTML_TEMPLATE,
            chain=blockchain.chain,
            peer_name=PEER_NAME,
            peers=peers,
            balances=balances
        )

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    sender = request.form['sender']
    receiver = request.form['receiver']
    amount = int(request.form['amount'])

    with chain_lock:
        balances = calculate_balances()
        if balances.get(sender, INIT_BALANCE) < amount:
            return f"{sender} doesn't have enough swipes! (Balance: {balances.get(sender, INIT_BALANCE)})", 400
        
        tx = Transaction(sender, receiver, amount)
        blockchain.current_transactions.append(tx)
        broadcast_transaction(tx)
    
    return redirect("/")

@app.route('/mine')
def mine():
    with chain_lock:
        if not blockchain.current_transactions:
            return "No transactions to mine", 400
        
        blockchain.mine()
        broadcast_block(blockchain.get_last_block())
    
    return redirect("/")

@app.route('/update_peers', methods=['POST'])
def update_peers():
    global peers
    peers = set(tuple(p) for p in request.get_json().get("peers", []))
    return jsonify({"status": "ok"}), 200

@app.route('/receive_transaction', methods=['POST'])
def receive_transaction():
    tx_data = request.get_json()["data"]
    tx = Transaction(**tx_data)
    
    with chain_lock:
        if tx in blockchain.current_transactions:
            return jsonify({"status": "duplicate"}), 200
        
        # Verify sender has sufficient balance
        balances = calculate_balances()
        if balances.get(tx.sender, INIT_BALANCE) < tx.amount:
            return jsonify({"status": "insufficient balance"}), 400
            
        blockchain.current_transactions.append(tx)
    
    return jsonify({"status": "added"}), 200

@app.route('/receive_block', methods=['POST'])
def receive_block():
    data = request.get_json()
    block_data = data["data"]
    sender = data.get("sender")

    with chain_lock:
        # Check if block exists
        if any(block.hash == block_data["hash"] for block in blockchain.chain):
            return jsonify({"status": "exists"}), 200

        new_block = blockchain.create_block_from_dict(block_data)
        last_block = blockchain.get_last_block()

        # Validate block
        if not all(hasattr(new_block, key) for key in ['hash', 'previous_hash']):
            return jsonify({"status": "invalid structure"}), 400
        if not new_block.hash.startswith('0' * blockchain.difficulty):
            return jsonify({"status": "invalid proof"}), 400

        # Normal case
        if new_block.previous_hash == last_block.hash:
            blockchain.add_block(new_block)
            blockchain.current_transactions = [
                tx for tx in blockchain.current_transactions
                if tx not in new_block.transactions
            ]
            return jsonify({"status": "added"}), 200

        # Fork resolution
        if not sender:
            return jsonify({"status": "sender info missing"}), 400

        try:
            res = requests.get(f"http://{sender['ip']}:{sender['port']}/chain", timeout=3)
            if res.status_code != 200:
                return jsonify({"status": "chain fetch failed"}), 502

            peer_chain_data = res.json()["chain"]
            if len(peer_chain_data) > len(blockchain.chain) and is_valid_chain(peer_chain_data):
                # Replace chain
                new_chain = [blockchain.create_block_from_dict(b) for b in peer_chain_data]
                blockchain.chain = new_chain
                # Update transaction pool
                blockchain.current_transactions = [
                    tx for tx in blockchain.current_transactions
                    if not any(tx in block.transactions for block in new_chain)
                ]
                return jsonify({"status": "chain replaced"}), 200
            else:
                return jsonify({"status": "chain not longer or invalid"}), 409
        except Exception as e:
            return jsonify({"status": "error", "error": str(e)}), 500

def is_valid_chain(chain_data):
    for i in range(1, len(chain_data)):
        prev, curr = chain_data[i-1], chain_data[i]
        if curr['previous_hash'] != prev['hash']:
            return False
        if not curr['hash'].startswith('0' * blockchain.difficulty):
            return False
        if blockchain.create_block_from_dict(curr).hash != curr['hash']:
            return False
    return True

def broadcast_transaction(tx):
    for peer in peers:
        try:
            requests.post(
                f"http://{peer[0]}:{peer[1]}/receive_transaction",
                json={"data": tx.__dict__},
                timeout=2
            )
        except:
            continue

def broadcast_block(block):
    for peer in peers:
        try:
            requests.post(
                f"http://{peer[0]}:{peer[1]}/receive_block",
                json={
                    "data": {
                        "index": block.index,
                        "previous_hash": block.previous_hash,
                        "timestamp": block.timestamp,
                        "transactions": [tx.__dict__ for tx in block.transactions],
                        "proof_of_work": block.proof_of_work,
                        "hash": block.hash,
                    },
                    "sender": {"ip": HOST, "port": PORT}
                },
                timeout=2
            )
        except:
            continue

def register_with_tracker():
    try:
        requests.post(
            f"http://{TRACKER_HOST}:{TRACKER_PORT}/register",
            json={"name": PEER_NAME, "port": PORT},
            timeout=3
        )
    except:
        print("Failed to register with tracker")

def periodic_sync():
    while True:
        time.sleep(30)
        with chain_lock:
            try_resolve_chain()
            clear_stale_transactions()

def try_resolve_chain():
    longest_chain = blockchain.chain
    for peer in peers:
        try:
            res = requests.get(f"http://{peer[0]}:{peer[1]}/chain", timeout=3)
            if res.status_code == 200:
                data = res.json()
                if data["length"] > len(longest_chain) and is_valid_chain(data["chain"]):
                    longest_chain = [blockchain.create_block_from_dict(b) for b in data["chain"]]
        except:
            continue

    if len(longest_chain) > len(blockchain.chain):
        blockchain.chain = longest_chain

def clear_stale_transactions():
    blockchain.current_transactions = [
        tx for tx in blockchain.current_transactions
        if not any(tx in block.transactions for block in blockchain.chain)
    ]

def start():
    # Start Flask in a separate thread
    threading.Thread(
        target=lambda: app.run(host=HOST, port=PORT, debug=False, use_reloader=False)
    ).start()
    
    # Register with tracker and start background tasks
    time.sleep(2)
    register_with_tracker()
    threading.Thread(target=periodic_sync, daemon=True).start()

if __name__ == "__main__":
    start()