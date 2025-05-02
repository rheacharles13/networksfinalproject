# peer.py
from flask import Flask, request, jsonify, render_template_string, redirect
import threading, requests, time, json
from block import Blockchain
from transaction import Transaction

app = Flask(__name__)
HOST = "0.0.0.0"
PORT = 5001  # Change for each peer
PEER_NAME = f"peer-{PORT}"
TRACKER_HOST = "tracker_vm_ip"
TRACKER_PORT = 8000

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

@app.route('/')
def index():
    return render_template_string(HTML, chain=blockchain.chain, peer_name=PEER_NAME)

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    sender = request.form['sender']
    receiver = request.form['receiver']
    amount = int(request.form['amount'])
    tx = Transaction(sender, receiver, amount)
    blockchain.current_transactions.append(tx)
    broadcast_transaction(tx)
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

@app.route('/receive_block', methods=['POST'])
def receive_block():
    block_data = request.get_json()["data"]
    new_block = blockchain.create_block_from_dict(block_data)
    # You should also validate the block here
    blockchain.add_block(new_block)
    return jsonify({"status": "block received"}), 200

@app.route('/peers')
def show_peers():
    return jsonify(list(peers))

def register_with_tracker():
    try:
        url = f"http://{TRACKER_HOST}:{TRACKER_PORT}/register"
        payload = {"name": PEER_NAME, "host": "peer_vm_ip", "port": PORT}
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
