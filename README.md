
# READ.md for Final Project

# Benjamin Vazzana (bav2113), Rhea Charles (rtc2133), Shinjini Mukherjee (sm5160), Shreeya Patel (sjp2236)

This is a minimal blockchain implementation in Python that uses Flask-based peer-to-peer networking. This guide includes setup instructions for deploying the system on **Google Cloud VMs**, with one tracker and three peers.

---

## Project Structure
.
├── main.py               # Main file
├── block.py              # Block and Blockchain classes
├── transaction.py        # Transaction structure
├── p2p.py                # Peer node (blockchain logic + Flask server)
├── tracker.py            # Central tracker server
├── transaction_pool.py   # Optional frontend for adding transactions
├── peer_manager.py       # Defines utility for managing peer node list
├── DESIGN.md             # Describes blockchain and p2p design
├── TESTING.md            # Describes set of tests we ran 
└── README.md             # Explains code structure and how to compile

# Requirements
Python 3.7+
Flask
'requests' library (install with the command 'pip install flask requests')

---

# Setup Instructions (Google Cloud)
Create 4 Google Cloud VM Instances
- 1 for the tracker
- 3 for peer nodes

Choose:
- Ubuntu 20.04 LTS
- Allow HTTP traffic

Ensure the following before deploying:
- Each VM has Python 3 installed.
- All files are copied to each VM.
- Google Cloud firewall rules allow:
  - TCP traffic on port `8000` for the tracker
  - TCP traffic on ports `5001`, `5002`, `5003`, etc., for each peer node

---

# Running the System on Google Cloud VMs

## Start the Tracker

SSH into the **tracker VM** (named `tracker_vm`) and run:
python3 tracker.py

The tracker listens on port 8000 by default.

Modify tracker.py if you need to bind to a different port or IP.

2. Start Peer Nodes
SSH into each **peer VM** (named `peer1_vm`, `peer2_vm`, or `peer3_vm`) and start a peer by running:

python3 peer.py <TRACKER_EXTERNAL_IP> <PEER_PORT>

Example:
If your tracker is running at IP 34.46.72.68, and you want to start a peer on port 5002:

python3 peer.py 34.46.72.68 5002
Repeat this on different VMs for multiple peers:

Peer 1: python3 peer.py 34.46.72.68 5001
Peer 2: python3 peer.py 34.46.72.68 5002
Peer 3: python3 peer.py 34.46.72.68 5003

Ensure each peer uses a unique port number.

## Accessing Peer Services in the Browser
Each peer in the system may expose a service that can be accessed via a browser (e.g., an API or web interface). To open the service for each peer:

1. Open the relevant ports in Google Cloud Firewall:
Ensure the firewall allows inbound traffic on the ports you are using for each peer (e.g., 5001, 5002, 5003).

2. Identify the External IP Address of Each Peer:
Find the external IP for each peer VM by navigating to VM instances in the Google Cloud Console.

3. Access the Peer Services:
Open any modern web browser (e.g., Chrome, Firefox) and navigate to the following addresses to access each peer:
Peer 1: http://<peer1-external-ip>:5001
Peer 2: http://<peer2-external-ip>:5002
Peer 3: http://<peer3-external-ip>:5003

For example, if the external IPs are:
peer1_vm: 34.46.72.69
peer2_vm: 34.46.72.68
peer3_vm: 34.46.72.70

You can access each peer via the following URLs:
Peer 1: http://34.46.72.69:5001
Peer 2: http://34.46.72.68:5002
Peer 3: http://34.46.72.70:5003