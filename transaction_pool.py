class TransactionPool:
    def __init__(self):
        self.pool = []

    def add_transaction(self, transaction):
        self.pool.append(transaction)

    def get_transactions(self):
        return self.pool

    def clear_pool(self):
        self.pool = []
