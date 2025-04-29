

# class for block 
# clas for blockchain 
# class for transaction 

import hashlib
import time
import json

class Block:
    def __init__(self, index, transactions, previous_hash, timestamp=None, nonce=0):
        self.index = index
        self.timestamp = timestamp or time.time()
        self.transactions = transactions  # list of transaction strings
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.compute_hash()
    
    def compute_hash(self):
        block_data = {
            'index': self.index,
            'timestamp': self.timestamp,
            'transactions': self.transactions,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce,
        }
        block_string = json.dumps(block_data, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()
    
    def mine(self, difficulty):
        """Find a hash with the required number of leading zeros."""
        prefix = '0' * difficulty
        while True:
            self.hash = self.compute_hash()
            if self.hash.startswith(prefix):
                break
            self.nonce += 1

    @staticmethod
    def from_dict(block_data):
        block = Block(
            index=block_data['index'],
            transactions=block_data['transactions'],
            previous_hash=block_data['previous_hash'],
            timestamp=block_data['timestamp'],
            nonce=block_data['nonce']
        )
        block.hash = block_data['hash']  # override computed hash with the received one
        return block



         

class Blockchain:
    def __init__(self, difficulty=4):
        self.chain = []
        self.difficulty = difficulty
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(0, ["Genesis Block"], "0")
        genesis_block.mine(self.difficulty)
        self.chain.append(genesis_block)

    def add_block(self, transactions):
        last_block = self.get_last_block()
        new_block = Block(
            index=last_block.index + 1,
            transactions=transactions,
            previous_hash=last_block.hash
        )
        print("⛏️ Mining block...")
        new_block.mine(self.difficulty)
        self.chain.append(new_block)
        return new_block
    
    def get_last_block(self):
        return self.chain[-1]
    
    #add without mining 
    
    """
    def is_valid_chain(self):
    prefix = '0' * self.difficulty
    for i in range(1, len(self.chain)):
        prev = self.chain[i - 1]
        curr = self.chain[i]
        if curr.previous_hash != prev.hash:
            return False
        if curr.hash != curr.compute_hash():
            return False
        if not curr.hash.startswith(prefix):  # <-- NEW
            return False
    return True
""" 



class Transaction:
    def __init__(self, sender, recipient, amount, timestamp=None):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.timestamp = timestamp or time.time()

    def to_dict(self):
        return {
            'sender': self.sender,
            'recipient': self.recipient,
            'amount': self.amount,
            'timestamp': self.timestamp
        }

    def __str__(self):
        return json.dumps(self.to_dict(), sort_keys=True)

    def __repr__(self):
        return f"{self.sender} → {self.recipient}: {self.amount} swipes"