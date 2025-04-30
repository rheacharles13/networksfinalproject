import socket
import json
from block import Blockchain
from transaction import Transaction


def start_server(port, blockchain):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('127.0.0.1', port))
    server.listen(5)
    print(f"[LISTENING] on 127.0.0.1:{port}")
    
    while True:
        client, addr = server.accept()
        print(f"[CONNECTION] from {addr}")
        message = client.recv(1024).decode()
        if message:
            message_data = json.loads(message)
            handle_message(message_data, blockchain)
        client.close()


def handle_message(message_data, blockchain):
    if message_data["type"] == "transaction":
        # Handle transaction logic
        transaction = Transaction(**message_data["data"])
        print(f"Received transaction: {transaction}")
        blockchain.current_transactions.append(transaction)
    elif message_data["type"] == "block":
        # Handle new block (e.g., validate and add it)
        pass  # Block handling logic would go here


def send_message(peer_address, message):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(peer_address)
    client.send(json.dumps(message).encode())
    client.close()


def broadcast_block(block, peers):
    message = {
        "type": "block",
        "data": block.__dict__,
    }
    for peer in peers:
        send_message(peer, message)


def broadcast_transaction(transaction, peers):
    message = {
        "type": "transaction",
        "data": transaction.__dict__,
    }
    for peer in peers:
        send_message(peer, message)

