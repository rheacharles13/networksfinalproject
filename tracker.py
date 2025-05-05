from flask import Flask, request, jsonify
import requests

app = Flask(__name__)
peers = []  # Stores (host, port) tuples
peer_info = {}  # Stores { (host,port): {name: str, initial_balance: int} }

@app.route('/register', methods=['POST'])
def register():
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
    """Endpoint to get all peer information"""
    return jsonify({
        f"{host}:{port}": info 
        for (host, port), info in peer_info.items()
    })

def update_all_peers():
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