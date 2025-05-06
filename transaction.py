import time


class Transaction:
    """Represents a financial transaction between two parties in the blockchain network.
    
    Attributes:
        sender (str): The public key or address of the sender
        receiver (str): The public key or address of the receiver
        amount (float): The amount being transferred
        timestamp (float): Unix timestamp of when the transaction was created
    """
    def __init__(self, sender, receiver, amount, timestamp=None):
        """Initialize a new Transaction.
        
        Args:
            sender (str): Identifier of the sending party
            receiver (str): Identifier of the receiving party
            amount (float): Transaction amount (must be positive)
            timestamp (float, optional): Custom timestamp. Defaults to current time.
        """
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.timestamp = timestamp or time.time()

    def __repr__(self):
        """Return an unambiguous string representation of the transaction.
        
        Returns:
            str: The string representation showing all transaction details
        """
        return f"Transaction(sender={self.sender}, receiver={self.receiver}, amount={self.amount}, timestamp={self.timestamp})"
