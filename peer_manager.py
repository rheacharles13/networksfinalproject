class PeerManager:
    def __init__(self):
        self.peers = [("127.0.0.1", 50001), ("127.0.0.1", 50002)]  # Example peers

    def broadcast_message(self, message):
        for peer in self.peers:
            send_message(peer, message)

    def add_peer(self, peer_address):
        self.peers.append(peer_address)
