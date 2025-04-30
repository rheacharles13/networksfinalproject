import time
from block import Blockchain
from transaction import Transaction
from p2p import start_server, broadcast_transaction, broadcast_block
from transaction_pool import TransactionPool
from peer_manager import PeerManager


def main():
    blockchain = Blockchain(difficulty=2)  # Create a blockchain with a difficulty of 2
    transaction_pool = TransactionPool()
    peer_manager = PeerManager()

    # Simulate creating a transaction
    transaction = Transaction(sender="Alice", receiver="Bob", amount=10)
    transaction_pool.add_transaction(transaction)
    
    # Broadcast the transaction to peers
    broadcast_transaction(transaction, peer_manager.peers)
    
    # Mine a new block with the current transactions
    blockchain.mine()
    
    # Broadcast the mined block to peers
    broadcast_block(blockchain.get_last_block(), peer_manager.peers)
    
    # Start the server to listen for incoming peer connections
    start_server(50001, blockchain)


if __name__ == "__main__":
    main()
