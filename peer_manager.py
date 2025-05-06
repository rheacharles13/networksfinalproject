class PeerManager:
    """Manages a list of peer nodes in the blockchain network.
    
    This class maintains a list of known peer nodes and provides methods
    to add new peers to the network.
    """
    def __init__(self):
        """Initialize the PeerManager with default example peers.
        
        The default peers are set to localhost ports 50001 and 50002 for demonstration.
        In a production environment, these would typically be loaded from configuration
        or discovered through network protocols.
        """
        self.peers = [("127.0.0.1", 50001), ("127.0.0.1", 50002)]  # Example peers

    def add_peer(self, peer_address):
        """Add a new peer to the list of known peers.
        
        Parameters:
            peer_address : tuple
                A (hostname, port) tuple representing the peer's network address
                
        Note:
            Does not check for duplicate peers before adding.
            The peer will not be validated before being added to the list.
        """
        self.peers.append(peer_address)
