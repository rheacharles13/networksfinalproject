from flask import Flask, request, jsonify
app = Flask(__name__)

peers = set()

@app.route('/register', methods=['POST'])
def register():
    peer = request.json.get('peer')
    peers.add(peer)
    notify_all()
    return jsonify({'status': 'registered', 'peers': list(peers)})

@app.route('/unregister', methods=['POST'])
def unregister():
    peer = request.json.get('peer')
    peers.discard(peer)
    notify_all()
    return jsonify({'status': 'unregistered', 'peers': list(peers)})

@app.route('/peers', methods=['GET'])
def get_peers():
    return jsonify(list(peers))

def notify_all():
    import requests
    for peer in peers:
        try:
            requests.post(f'http://{peer}/update_peers', json={'peers': list(peers)})
        except:
            continue 

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
