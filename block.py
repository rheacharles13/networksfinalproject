import hashlib
import json
import time
from transaction import Transaction


class Block:
    def __init__(self, index, previous_hash, timestamp, transactions, proof_of_work):
        """
        Initialize a new Block in the blockchain.

        Parameters:
            index : int
                The position of the block in the blockchain.
            previous_hash : str
                The hash of the previous block in the chain.
            timestamp : float
                The time when the block was created (Unix timestamp).
            transactions : list[Transaction]
                List of transactions included in this block.
            proof_of_work : int
                The proof of work number that satisfies the difficulty requirement.
        """
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.transactions = transactions
        self.proof_of_work = proof_of_work
        self.hash = self.compute_hash()

    def compute_hash(self):
        """
        Compute the SHA-256 hash of the block's contents.

        Returns:
            str
                The hexadecimal string representation of the block's hash.
        """
        block_data = {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "transactions": [str(tx) for tx in self.transactions],
            "proof_of_work": self.proof_of_work,
        }
        block_string = json.dumps(block_data, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()


class Blockchain:
    def __init__(self, difficulty=2):
        """
        Initialize a new Blockchain.

        Parameters:
            difficulty : int, optional
                The number of leading zeros required for a valid block hash (default is 2).
        """
        self.chain = []
        self.current_transactions = []
        self.difficulty = difficulty
        self.create_genesis_block()

    def create_genesis_block(self):
        """
        Create the first block (genesis block) in the blockchain with default values.
        """
        # Create the first block (genesis block)
        genesis_block = Block(0, "0", time.time(), [], "0")
        self.chain.append(genesis_block)

    def add_block(self, block):
        """
        Add a new block to the blockchain.

        Parameters:
            block : Block
                The block to be added to the chain.
        """
        self.chain.append(block)

    def mine(self):
        """
        Mine a new block containing current transactions by finding a valid proof of work.

        Returns:
            Block
                The newly mined block.
        """
        last_block = self.chain[-1]
        index = last_block.index + 1
        previous_hash = last_block.hash
        timestamp = time.time()
        #proof_of_work = self.proof_of_work(index, previous_hash, timestamp)
        proof_of_work = 0
        block = Block(index, previous_hash, timestamp, self.current_transactions, proof_of_work)
        while block.hash[:self.difficulty] != "0" * self.difficulty:
            proof_of_work += 1
            block = Block(index, previous_hash, timestamp, self.current_transactions, proof_of_work)
        self.add_block(block)
        self.current_transactions = []
        return block

    def proof_of_work(self, index, previous_hash, timestamp):
        """
        Find a valid proof of work for a block by brute-forcing until the hash meets difficulty requirements.

        Parameters:
            index : int
                The position of the block in the blockchain.
            previous_hash : str
                The hash of the previous block.
            timestamp : float
                The time when mining started.

        Returns:
            int
                The valid proof of work number.
        """
        proof = 0
        while True:
            block_string = f"{index}{previous_hash}{timestamp}{proof}"
            block_hash = hashlib.sha256(block_string.encode()).hexdigest()
            if block_hash[:self.difficulty] == "0" * self.difficulty:
                return proof
            proof += 1

    def is_valid_chain(self):
        """
        Validate the integrity of the blockchain.

        Returns:
            bool
                True if the chain is valid (proper links and valid hashes), False otherwise.
        """
        for i in range(1, len(self.chain)):
            previous_block = self.chain[i - 1]
            current_block = self.chain[i]
            if current_block.previous_hash != previous_block.hash:
                return False
            if current_block.hash != current_block.compute_hash():
                return False
            if not current_block.hash.startswith('0' * self.difficulty):
                return False
        return True
    
    def create_block_from_dict(self, data):
        """
        Create a Block instance from a dictionary of block data.

        Parameters:
            data : dict
                Dictionary containing block data (index, previous_hash, timestamp, transactions, proof_of_work).

        Returns:
            Block
                The newly created Block instance.
        """
        txs = [Transaction(**tx) if isinstance(tx, dict) else tx for tx in data['transactions']]
        return Block(
            index=data['index'],
            previous_hash=data['previous_hash'],
            timestamp=data['timestamp'],
            transactions=txs,
            proof_of_work=data['proof_of_work']
        )


    def get_last_block(self):
        """
        Get the most recent block in the blockchain.

        Returns:
            Block
                The last block in the chain.
        """
        return self.chain[-1]
