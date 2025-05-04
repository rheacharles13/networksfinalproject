import hashlib
import json
import time
from transaction import Transaction


class Block:
    def __init__(self, index, previous_hash, timestamp, transactions, proof_of_work):
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.transactions = transactions
        self.proof_of_work = proof_of_work
        self.hash = self.compute_hash()

    def compute_hash(self):
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
        self.chain = []
        self.current_transactions = []
        self.difficulty = difficulty
        self.create_genesis_block()

    def create_genesis_block(self):
        # Create the first block (genesis block)
        genesis_block = Block(0, "0", time.time(), [], "0")
        self.chain.append(genesis_block)

    def add_block(self, block):
        self.chain.append(block)

    def mine(self):
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

    def proof_of_work(self, index, previous_hash, timestamp):
        # This method finds a valid proof of work for a given block.
        # Simple brute-force to find a hash starting with difficulty zeros.
        proof = 0
        while True:
            block_string = f"{index}{previous_hash}{timestamp}{proof}"
            block_hash = hashlib.sha256(block_string.encode()).hexdigest()
            if block_hash[:self.difficulty] == "0" * self.difficulty:
                return proof
            proof += 1

    def is_valid_chain(self):
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
        txs = [Transaction(**tx) if isinstance(tx, dict) else tx for tx in data['transactions']]
        return Block(
            index=data['index'],
            previous_hash=data['previous_hash'],
            timestamp=data['timestamp'],
            transactions=txs,
            proof_of_work=data['proof_of_work']
        )


    def get_last_block(self):
        return self.chain[-1]
