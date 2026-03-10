import os
import json
import time
import hashlib
import threading
import random
import requests
import socket
from flask import Flask, request, jsonify

app = Flask(__name__)

BLOCKCHAIN_FILE = "blockchain.json"

PEERS = [
"192.168.0.100",
"192.168.0.102",
"192.168.0.103"
]

TARGET_BLOCK_TIME = 15
BLOCK_REWARD = 32

MAX_SUPPLY = 32000000

difficulty = 3
max_threads = 4
supply = 0

mempool = []

# ---------------- WALLET ----------------

def load_wallet():

    if not os.path.exists("wallet.json"):

        priv = hashlib.sha256(str(random.random()).encode()).hexdigest()
        addr = hashlib.sha256(priv.encode()).hexdigest()

        wallet = {
            "private": priv,
            "address": addr
        }

        with open("wallet.json","w") as f:
            json.dump(wallet,f)

    with open("wallet.json") as f:
        return json.load(f)

wallet = load_wallet()

# ---------------- HASH ----------------

def hash_block(b):

    return hashlib.sha256(json.dumps(b,sort_keys=True).encode()).hexdigest()

# ---------------- BLOCKCHAIN ----------------

def load_chain():

    global supply

    if not os.path.exists(BLOCKCHAIN_FILE):

        genesis = {
            "index":0,
            "timestamp":1700000000,
            "prev_hash":"0",
            "nonce":0,
            "miner":"PoLM Genesis",
            "tx":[],
            "latency":0,
            "difficulty":difficulty
        }

        genesis["hash"] = "000000POLMGENESISBLOCK000000"

        with open(BLOCKCHAIN_FILE,"w") as f:
            json.dump([genesis],f,indent=2)

    with open(BLOCKCHAIN_FILE) as f:
        chain = json.load(f)

    supply = (len(chain)-1) * BLOCK_REWARD

    return chain

blockchain = load_chain()

def save_chain():

    with open(BLOCKCHAIN_FILE,"w") as f:
        json.dump(blockchain,f,indent=2)

# ---------------- RAM LATENCY ----------------

def ram_latency():

    total = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')

    threads = min(os.cpu_count(),max_threads)

    use = int((total * 0.5) / threads)

    arr = bytearray(use)

    start = time.time()

    for i in range(0,len(arr),4096):
        arr[i] = random.randint(0,255)

    return time.time()-start

# ---------------- DIFFICULTY ----------------

def adjust_difficulty():

    global difficulty

    if len(blockchain) < 5:
        return

    last = blockchain[-1]["timestamp"]
    prev = blockchain[-5]["timestamp"]

    avg = (last-prev)/5

    if avg < TARGET_BLOCK_TIME*0.7:
        difficulty += 1

    if avg > TARGET_BLOCK_TIME*1.5 and difficulty > 1:
        difficulty -= 1

# ---------------- MINING ----------------

def mine():

    global blockchain
    global supply

    while True:

        if supply >= MAX_SUPPLY:

            print("MAX SUPPLY REACHED")

            time.sleep(60)

            continue

        prev = blockchain[-1]

        block = {
            "index": prev["index"]+1,
            "timestamp": time.time(),
            "prev_hash": prev["hash"],
            "nonce": 0,
            "miner": wallet["address"],
            "tx": mempool.copy(),
            "latency":0,
            "difficulty": difficulty
        }

        mempool.clear()

        latency = ram_latency()

        block["latency"] = latency

        while True:

            block["nonce"] += 1

            h = hash_block(block)

            if h.startswith("0"*difficulty):

                block["hash"] = h

                blockchain.append(block)

                supply += BLOCK_REWARD

                save_chain()

                adjust_difficulty()

                print(
                    "BLOCK",
                    h[:8],
                    "| diff",
                    difficulty,
                    "| latency",
                    round(latency,4),
                    "| supply",
                    supply
                )

                propagate(block)

                break

# ---------------- NETWORK ----------------

def propagate(block):

    for peer in PEERS:

        try:

            requests.post(
                f"http://{peer}:8080/receive_block",
                json=block,
                timeout=2
            )

        except:
            pass

# ---------------- SYNC ----------------

def sync_chain():

    global blockchain

    for peer in PEERS:

        try:

            r = requests.get(f"http://{peer}:8080/chain",timeout=3)

            peer_chain = r.json()

            if len(peer_chain) > len(blockchain):

                blockchain = peer_chain

                save_chain()

                print("CHAIN SYNCED FROM",peer)

        except:
            pass

# ---------------- API ----------------

@app.route("/receive_block",methods=["POST"])
def receive():

    block = request.json

    if block["prev_hash"] != blockchain[-1]["hash"]:
        return "reject",400

    if not block["hash"].startswith("0"*block["difficulty"]):
        return "reject",400

    blockchain.append(block)

    save_chain()

    print("SYNC",block["hash"][:8])

    return "ok"

@app.route("/chain")
def chain():

    return jsonify(blockchain)

@app.route("/stats")
def stats():

    return jsonify({
        "height":len(blockchain),
        "difficulty":difficulty,
        "supply":supply,
        "miner":wallet["address"][:16]
    })

# ---------------- START ----------------

def start_miners():

    threads = min(os.cpu_count(),max_threads)

    print("Threads:",threads)

    for _ in range(threads):

        t = threading.Thread(target=mine)

        t.daemon=True

        t.start()

# ---------------- BOOT ----------------

print("\n===== PoLM v1.0 FINAL =====\n")

print("Node:",socket.gethostname())
print("Miner:",wallet["address"][:16])
print("Peers:",PEERS)
print("Max Supply:",MAX_SUPPLY)

sync_chain()

start_miners()

app.run(host="0.0.0.0",port=8080)
