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

    <h3>Blockchain</h3>
    <ul>
        {% for block in chain %}
            <li>
                <strong>Index:</strong> {{ block.index }} |
                <strong>Hash:</strong> {{ block.hash[:10] }}... |
                <strong>TX Count:</strong> {{ block.transactions|length }}
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
    # Ensure our own peer is in balances if not already present
    if PEER_NAME not in balances:
        balances[PEER_NAME] = INIT_BALANCE
        
    return render_template_string(
        HTML, 
        chain=blockchain.chain, 
        peer_name=PEER_NAME,
        balances=balances  # Pass the balances to the template
    )

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    sender = request.form['sender']
    receiver = request.form['receiver']
    amount = int(request.form['amount'])

    # Initialize balances if they don't exist
    if sender not in balances:
        balances[sender] = INIT_BALANCE
    if receiver not in balances:
        balances[receiver] = INIT_BALANCE
        
    if balances[sender] >= amount:
        tx = Transaction(sender, receiver, amount)
        blockchain.current_transactions.append(tx)
        broadcast_transaction(tx)
        # Update temporary balances
        balances[sender] -= amount
        balances[receiver] += amount
    else:
        print(f"{sender} doesn't have enough swipes!")
    return redirect("/")

def recalculate_balances():
    global balances
    # Get all peer names from the tracker
    try:
        url = f"http://{TRACKER_HOST}:{TRACKER_PORT}/peer_info"
        res = requests.get(url)
        if res.status_code == 200:
            peer_names = [info['name'] for info in res.json().values()]
            # Reset all known peers to initial balance
            balances = {name: INIT_BALANCE for name in peer_names}
    except Exception as e:
        print(f"⚠️ Could not fetch peer info: {e}")
        # Fallback: just reset existing balances
        balances = {name: INIT_BALANCE for name in balances}
    
    # Replay all transactions
    for block in blockchain.chain:
        for tx in block.transactions:
            # Ensure sender and receiver exist in balances
            if tx.sender not in balances:
                balances[tx.sender] = INIT_BALANCE
            if tx.receiver not in balances:
                balances[tx.receiver] = INIT_BALANCE
                
            balances[tx.sender] -= tx.amount
            balances[tx.receiver] += tx.amount

@app.route('/mine')
def mine():
    blockchain.mine()
    recalculate_balances()
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
    block_data = request.get_json()["data"]
    new_block = blockchain.create_block_from_dict(block_data)
    # You should also validate the block here
    blockchain.add_block(new_block)
    return jsonify({"status": "block received"}), 200
""" 




    

@app.route('/receive_block', methods=['POST'])
def receive_block():
    data = request.get_json()
    block_data = data["data"]
    sender = data.get("sender")

    # Check if block already exists
    if any(block.hash == block_data["hash"] for block in blockchain.chain):
        return jsonify({"status": "block already exists"}), 200

    new_block = blockchain.create_block_from_dict(block_data)
    last_block = blockchain.get_last_block()

    # Validate block structure
    if not all(hasattr(new_block, key) for key in REQUIRED_KEYS):
        return jsonify({"status": "invalid block structure"}), 400

    # Validate proof of work
    if not new_block.hash.startswith('0' * blockchain.difficulty):
        return jsonify({"status": "invalid proof"}), 400

    # Normal case - block extends our chain
    if new_block.previous_hash == last_block.hash:
        blockchain.add_block(new_block)
        # Remove transactions from current_transactions
        blockchain.current_transactions = [
            tx for tx in blockchain.current_transactions
            if tx not in new_block.transactions
        ]
        return jsonify({"status": "block added"}), 200

    # Fork resolution (keep your existing fork resolution code)
  
    # Fork detected – attempt resolution
    if not sender:
        return jsonify({"status": "missing sender info"}), 400

    try:
        url = f"http://{sender['ip']}:{sender['port']}/chain"
        res = requests.get(url)
        if res.status_code != 200:
            return jsonify({"status": "chain fetch failed"}), 502

        peer_chain_data = res.json()["chain"]
        peer_chain_len = res.json()["length"]

        if peer_chain_len > len(blockchain.chain) and is_valid_chain(peer_chain_data):
            blockchain.chain = [blockchain.create_block_from_dict(b) for b in peer_chain_data]
            return jsonify({"status": "fork resolved – chain replaced"}), 200
        else:
            return jsonify({"status": "peer chain invalid or not longer"}), 409

    except Exception as e:
        return jsonify({"status": "fork resolution error", "error": str(e)}), 500


@app.route('/resolve', methods=['GET'])
def resolve_conflicts():
    global blockchain
    longest_chain = blockchain.chain
    for peer in peers:
        try:
            url = f"http://{peer[0]}:{peer[1]}/chain"
            res = requests.get(url)
            if res.status_code != 200:
                continue
            data = res.json()
            chain = data["chain"]
            if data["length"] > len(longest_chain) and is_valid_chain(chain):
                longest_chain = [blockchain.create_block_from_dict(b) for b in chain]
        except:
            continue

    if len(longest_chain) > len(blockchain.chain):
        blockchain.chain = longest_chain
        return jsonify({"status": "chain replaced with longer valid chain"}), 200
    else:
        return jsonify({"status": "our chain is longest"}), 200



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
    for peer in peers:
        try:
            url = f"http://{peer[0]}:{peer[1]}/receive_block"
            block_data = {
                "index": block.index,
                "previous_hash": block.previous_hash,
                "timestamp": block.timestamp,
                "transactions": [tx.__dict__ for tx in block.transactions],
                "proof_of_work": block.proof_of_work,
                "hash": block.hash,
            }
            # Include sender information to prevent circular broadcasting
            requests.post(url, json={
                "type": "block",
                "data": block_data,
                "sender": {"ip": HOST, "port": PORT}  # Add sender info
            })
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
    
    threading.Thread(target=lambda: app.run(host=HOST, port=PORT, debug=False)).start()
    time.sleep(2)
    register_with_tracker()
    time.sleep(1)  # Give time for registration
    initialize_peer_balances()
    try_resolve_chain()
    
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
