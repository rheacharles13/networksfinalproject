import socket
import json
from block import Blockchain
from transaction import Transaction


def start_server(port, blockchain):
    """
    Start a TCP server that listens for incoming blockchain messages (transactions/blocks).

    Parameters:
        port : int
            The port number to listen on.
        blockchain : Blockchain
            The blockchain instance to update with received messages.

    The server runs indefinitely, accepting connections and handling messages.
    """
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
    """
    Process incoming messages and update the blockchain accordingly.

    Parameters:
        message_data : dict
            The parsed JSON message containing either a transaction or block.
        blockchain : Blockchain
            The blockchain instance to be updated.

    Currently handles:
    - "transaction" type: Adds transaction to pending transactions
    - "block" type: Placeholder for future block validation logic
    """
    if message_data["type"] == "transaction":
        # Handle transaction logic
        transaction = Transaction(**message_data["data"])
        print(f"Received transaction: {transaction}")
        blockchain.current_transactions.append(transaction)
    elif message_data["type"] == "block":
        # Handle new block (e.g., validate and add it)
        pass  # Block handling logic would go here


def send_message(peer_address, message):
    """
    Send a JSON-encoded message to a specific peer node.

    Parameters:
        peer_address : tuple
            (IP address, port) of the peer node.
        message : dict
            The message to be sent (will be JSON-encoded).
    """
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(peer_address)
    client.send(json.dumps(message).encode())
    client.close()


def broadcast_block(block, peers):
    """
    Broadcast a newly mined block to all known peer nodes.

    Parameters:
        block : Block
            The block to be broadcasted.
        peers : list
            List of (IP address, port) tuples representing peer nodes.
    """
    message = {
        "type": "block",
        "data": block.__dict__,
    }
    for peer in peers:
        send_message(peer, message)


def broadcast_transaction(transaction, peers):
    """
    Broadcast a new transaction to all known peer nodes.

    Parameters:
        transaction : Transaction
            The transaction to be broadcasted.
        peers : list
            List of (IP address, port) tuples representing peer nodes.
    """
    message = {
        "type": "transaction",
        "data": transaction.__dict__,
    }
    for peer in peers:
        send_message(peer, message)

