from flask import Flask, render_template, jsonify
from transaction_pool import TransactionPool
from peer_manager import PeerManager
import time

app = Flask(__name__)

# Sample data to simulate the blockchain environment
peer_manager = PeerManager()
transaction_pool = TransactionPool()

# List of connected users (simulated)
users = []

# Add some dummy users and transactions for simulation
users.append('Alice')
users.append('Bob')

# Dummy transaction data
transactions = [
    {'sender': 'Alice', 'receiver': 'Bob', 'amount': 5},
    {'sender': 'Bob', 'receiver': 'Alice', 'amount': 3},
]

@app.route('/')
def index():
    return render_template('index.html', users=users, transactions=transactions)

@app.route('/get_updates')
def get_updates():
    # This route will return updated data (users and transactions) as JSON
    return jsonify({
        'users': users,
        'transactions': transactions
    })

@app.route('/add_user/<username>', methods=['GET'])
def add_user(username):
    """Simulate a user joining the network."""
    users.append(username)
    return jsonify({"message": f"User {username} added"}), 200

@app.route('/add_transaction/<sender>/<receiver>/<amount>', methods=['GET'])
def add_transaction(sender, receiver, amount):
    """Simulate a new transaction being made."""
    transaction = {
        'sender': sender,
        'receiver': receiver,
        'amount': float(amount),
    }
    transactions.append(transaction)
    return jsonify({"message": f"Transaction from {sender} to {receiver} of {amount} added"}), 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
