# peer.py
from flask import Flask, request, jsonify, render_template_string, redirect
import threading, requests, time, json
from block import Blockchain
from transaction import Transaction
import sys

app = Flask(__name__)
HOST = "0.0.0.0"
PORT = 5002  # Change for each peer
PEER_NAME = f"peer-{PORT}"
TRACKER_HOST = sys.argv[1]
#socket
#
TRACKER_PORT = 8000

INIT_BALANCE = 150

blockchain = Blockchain(difficulty=2)
peers = set()

HTML = """
<h2>{{ peer_name }}</h2>
<h3>Blockchain</h3>
<ul>{% for block in chain %}
    <li>Index: {{ block.index }} | Hash: {{ block.hash[:10] }}... | TXs: {{ block.transactions }}</li>
{% endfor %}</ul>

<h3>Add Transaction</h3>
<form method="POST" action="/add_transaction">
    Sender: <input name="sender" required><br>
    Receiver: <input name="receiver" required><br>
    Amount: <input name="amount" type="number" required><br>
    <input type="submit" value="Submit">
</form>

<h3><a href="/mine">⛏️ Mine New Block</a></h3>
<h3><a href="/peers">🔗 View Peers</a></h3>
"""
def is_valid_chain(chain_data):
    for i in range(1, len(chain_data)):
        prev = chain_data[i - 1]
        curr = chain_data[i]

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
    return render_template_string(HTML, chain=blockchain.chain, peer_name=PEER_NAME)

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    sender = request.form['sender']
    receiver = request.form['receiver']
    amount = int(request.form['amount'])

    net_bal = INIT_BALANCE
    for block in blockchain.chain:
        for tx in block.transactions:
            if tx.sender == sender:
                net_bal -= amount
            elif tx.receiver == receiver:
                net_bal += amount
    if net_bal >= 0:
        tx = Transaction(sender, receiver, amount)
        blockchain.current_transactions.append(tx)
        broadcast_transaction(tx)
    else:
        print(f"{sender} doesn't have enough swipes!")
    return redirect("/")

@app.route('/mine')
def mine():
    blockchain.mine()
    broadcast_block(blockchain.get_last_block())
    return redirect("/")

@app.route('/update_peers', methods=['POST'])
def update_peers():
    global peers
    data = request.get_json()
    peers = set(tuple(p) for p in data.get("peers", []))
    return jsonify({"status": "ok"}), 200

@app.route('/receive_transaction', methods=['POST'])
def receive_transaction():
    tx_data = request.get_json()["data"]
    tx = Transaction(**tx_data)
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
    sender = data.get("sender")  # Expecting format: {"ip": ..., "port": ...}

    new_block = blockchain.create_block_from_dict(block_data)
    last_block = blockchain.get_last_block()

    if new_block.previous_hash == last_block.hash:
        # Normal case
        if new_block.hash.startswith('0' * blockchain.difficulty):
            blockchain.add_block(new_block)
            return jsonify({"status": "block added"}), 200
        else:
            return jsonify({"status": "invalid proof"}), 400

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
    return jsonify({
        "length": len(blockchain.chain),
        "chain": [block.__dict__ for block in blockchain.chain]
    })

def register_with_tracker():
    try:
        url = f"http://{TRACKER_HOST}:{TRACKER_PORT}/register"
        payload = {"name": PEER_NAME, "port": PORT}
        res = requests.post(url, json=payload)
        print(f"✅ Registered with tracker: {res.json()}")
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
            requests.post(url, json={"type": "block", "data": block.__dict__})
        except Exception as e:
            print(f"❌ Could not send block to {peer}: {e}")

def start():
    threading.Thread(target=lambda: app.run(host=HOST, port=PORT, debug=False)).start()
    time.sleep(2)
    register_with_tracker()

if __name__ == "__main__":
    start()
