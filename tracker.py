from flask import Flask, request, jsonify

app = Flask(__name__)
peers = []

@app.route('/register', methods=['POST'])
def register():
    peer = request.json
    if peer not in peers:
        peers.append((peer['host'], peer['port']))
        print(f"📥 Registered: {peer}")
        update_all_peers()
    return jsonify({'status': 'registered', 'peers': peers})

def update_all_peers():
    for peer in peers:
        try:
            import requests
            url = f"http://{peer[0]}:{peer[1]}/update_peers"
            requests.post(url, json={"peers": peers})
        except Exception as e:
            print(f"⚠️ Failed to update {peer}: {e}")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)

