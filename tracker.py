from flask import Flask, request, jsonify
import requests

app = Flask(__name__)
peers = []  # (host, port)
peer_info = {}  # { (host,port): {name: str, initial_balance: int} }

@app.route('/register', methods=['POST'])
def register():
    """
    Register a new peer node with the network.
    
    Receives peer information via POST request and adds it to the network registry.
    Automatically updates all existing peers about the new network state.
    
    Request JSON format:
    {
        "port": int,    # The port the peer is listening on
        "name": str     # Human-readable name for the peer
    }
    
    Returns:
        JSON response containing registration status, peer list, and initial balance
    """
    peer_data = request.json
    peer_host = request.remote_addr
    peer_port = peer_data['port']
    peer_name = peer_data['name']
    
    peer_tuple = (peer_host, peer_port)
    if peer_tuple not in peers:
        peers.append(peer_tuple)
        peer_info[peer_tuple] = {
            'name': peer_name,
            'initial_balance': 150
        }
        print(f"📥 Registered: {peer_name} at {peer_host}:{peer_port}")
        update_all_peers()
    return jsonify({
        'status': 'registered',
        'peers': peers,
        'initial_balance': 150
    })

@app.route('/peer_info', methods=['GET'])
def get_peer_info():
    """
    Retrieve information about all registered peers in the network.
    
    Returns:
        JSON dictionary mapping peer addresses to their information:
        {
            "host:port": {
                "name": str,
                "initial_balance": int
            },
            ...
        }
    """

    return jsonify({
        f"{host}:{port}": info 
        for (host, port), info in peer_info.items()
    })

def update_all_peers():
    """
    Notify all registered peers about the current network state.
    
    Sends the complete peer list and names to each peer in the network.
    Silently handles connection errors to individual peers.
    """
    for peer in peers:
        try:
            url = f"http://{peer[0]}:{peer[1]}/update_peers"
            requests.post(url, json={
                "peers": peers,
                "peer_names": [peer_info[p]['name'] for p in peers]
            })
        except Exception as e:
            print(f"⚠️ Failed to update {peer}: {e}")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)