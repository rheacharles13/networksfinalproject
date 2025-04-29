import socket
import threading
import sys
from blockchain.block import Block, Blockchain, Transaction  # assuming your blockchain classes are in blockchain.py
import json

blockchain = Blockchain()
pending_transactions = []

# Configuration
address = "127.0.0.1"
port = 50001  # This node's port
peer_list = [("127.0.0.1", 50001), ("127.0.0.1", 50002), ("127.0.0.1", 50003)]  # Example peers

# Store received messages (e.g., transactions)
messages = []

def handle_client_connection(conn, addr):
    """Receive and process messages from peers."""
    while True:
        try:
            data = conn.recv(4096)
            if not data:
                break
            message = data.decode()
            print(f"[RECEIVED from {addr}] {message}")

            # Decide message type
            try:
                payload = json.loads(message)
                if payload.get("type") == "transaction":
                    tx_data = payload["data"]
                    transaction = Transaction(**tx_data)
                    pending_transactions.append(transaction)
                    print(f"[TX] {transaction}")
                elif payload['type'] == 'block':
                    block_data = payload['data']
                    new_block = Block.from_dict(block_data)

                    # Optionally: validate block (e.g., check hash, nonce, previous_hash match, etc.)
                    last_block = blockchain.get_last_block()

                    if new_block.previous_hash == last_block.hash and new_block.index == last_block.index + 1:
                            blockchain.chain.append(new_block)
                            print("[BLOCK] Block added to chain!")
                    else:
                            print("[BLOCK] Invalid block. Ignored.")

            except json.JSONDecodeError:
                print("[ERROR] Could not parse message.")

        except ConnectionResetError:
            break
    conn.close()


def listen_for_peers():
    """Listen for incoming peer connections."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((address, port))
    server_socket.listen()
    print(f"[LISTENING] on {address}:{port}")
    
    while True:
        conn, addr = server_socket.accept()
        threading.Thread(target=handle_client_connection, args=(conn, addr)).start()

def send_to_peers(message):
    """Send a message to all peers."""
    for peer in peer_list:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(peer)
                s.sendall(message.encode())
        except ConnectionRefusedError:
            print(f"[ERROR] Could not connect to peer: {peer}")

def user_input_loop():
    """Prompt user to send messages."""
    while True:
        msg = input("Enter a message to broadcast (e.g., 'Alice,Bob,1' or 'mine'): ")

        if msg.lower() == "mine":
            if not pending_transactions:
                print("No pending transactions to mine.")
                continue

            print("⛏️ Mining block...")
            tx_strings = [str(tx) for tx in pending_transactions]
            new_block = blockchain.add_block(tx_strings)
            pending_transactions.clear()

            # Broadcast the new block to all peers
            block_json = {
                "type": "block",
                "data": {
                    "index": new_block.index,
                    "timestamp": new_block.timestamp,
                    "transactions": new_block.transactions,
                    "previous_hash": new_block.previous_hash,
                    "nonce": new_block.nonce,
                    "hash": new_block.hash
                }
            }
            send_to_peers(json.dumps(block_json))
        else:
            try:
                sender, recipient, amount = msg.split(",")
                tx = Transaction(sender, recipient, int(amount))
                pending_transactions.append(tx)

                tx_message = {
                    "type": "transaction",
                    "data": tx.to_dict()
                }
                send_to_peers(json.dumps(tx_message))
            except ValueError:
                print("⚠️ Invalid format. Use: sender,recipient,amount or 'mine'")


port = int(sys.argv[1])
# Run threads
threading.Thread(target=listen_for_peers, daemon=True).start()
threading.Thread(target=user_input_loop, daemon=True).start()

# Keep the main thread alive
try:
    while True:
        pass
except KeyboardInterrupt:
    print("Shutting down...")

