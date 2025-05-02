import requests

TRACKER_URL = "http://[TRACKER_EXTERNAL_IP]:5000"

def register_peer(my_ip_port):
    requests.post(f"{TRACKER_URL}/register", json={'peer': my_ip_port})

def unregister_peer(my_ip_port):
    requests.post(f"{TRACKER_URL}/unregister", json={'peer': my_ip_port})
    
@app.route('/update_peers', methods=['POST'])
def update_peers():
    global known_peers
    known_peers = request.json.get('peers', [])
    return jsonify({'status': 'ok'})
