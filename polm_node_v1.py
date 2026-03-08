#!/usr/bin/env python3

import time
import random
import hashlib
import json
import os
import socket
import threading
import platform

PORT = 5001

PEERS = [
"192.168.0.100",
"192.168.0.103",
"192.168.0.102"
]

BUFFER_SIZE = 128 * 1024 * 1024
NODES = BUFFER_SIZE // 8
ROUNDS = 200000

BLOCK_TARGET = 2**250

CHAIN_FILE = "polm_chain.json"

print("===== PoLM Node v1 =====")
print("CPU:", platform.processor())
print("Cores:", os.cpu_count())

# LOCK para evitar corrupção do arquivo
chain_lock = threading.Lock()

# criar grafo na memória
graph = [random.randint(0, NODES-1) for _ in range(NODES)]


def memory_graph(seed):

    node = seed % NODES

    for _ in range(ROUNDS):
        node = graph[node]

    return node


def load_chain():

    with chain_lock:

        if not os.path.exists(CHAIN_FILE):

            genesis = {
                "height": 0,
                "previous_hash": "0",
                "timestamp": time.time(),
                "hash": "genesis"
            }

            with open(CHAIN_FILE, "w") as f:
                json.dump([genesis], f)

        try:
            with open(CHAIN_FILE) as f:
                return json.load(f)
        except:
            return []


def save_chain(chain):

    with chain_lock:

        with open(CHAIN_FILE, "w") as f:
            json.dump(chain, f)


def broadcast(block):

    for peer in PEERS:

        if peer == "127.0.0.1":
            continue

        try:

            s = socket.socket()
            s.connect((peer, PORT))

            s.send(json.dumps(block).encode())

            s.close()

        except:
            pass


def server():

    s = socket.socket()
    s.bind(("0.0.0.0", PORT))
    s.listen()

    while True:

        conn, addr = s.accept()

        try:

            data = conn.recv(4096)

            block = json.loads(data.decode())

            chain = load_chain()

            if block["height"] == len(chain):

                chain.append(block)

                save_chain(chain)

                print("BLOCK RECEIVED", block["height"])

        except:
            pass

        conn.close()


def mine():

    while True:

        chain = load_chain()

        last_block = chain[-1]

        seed = random.randint(0, 2**32)

        latency = memory_graph(seed)

        data = str(seed + latency + len(chain)).encode()

        h = hashlib.sha256(data).hexdigest()

        if int(h, 16) < BLOCK_TARGET:

            block = {
                "height": len(chain),
                "previous_hash": last_block["hash"],
                "timestamp": time.time(),
                "seed": seed,
                "latency": latency,
                "hash": h
            }

            chain.append(block)

            save_chain(chain)

            print("BLOCK MINED", block["height"])

            broadcast(block)


# iniciar servidor em thread
threading.Thread(target=server, daemon=True).start()

# iniciar mineração
mine()
