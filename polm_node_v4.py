#!/usr/bin/env python3

import time
import random
import hashlib
import json
import os
import socket
import threading
import platform
import math

PORT = 5001

PEERS = [
"192.168.0.100",
"192.168.0.103",
"192.168.0.102"
]

CHAIN_FILE = "polm_chain.json"

BUFFER_SIZE = 128 * 1024 * 1024
NODES = BUFFER_SIZE // 8
ROUNDS = 200000

BASE_DIFFICULTY = 2**250
BLOCK_REWARD = 50

print("===== PoLM Node v4 =====")
print("CPU:", platform.processor())
print("Cores:", os.cpu_count())

chain_lock = threading.Lock()

# memory graph
graph = [random.randint(0, NODES-1) for _ in range(NODES)]


def memory_graph(seed):

    node = seed % NODES

    for _ in range(ROUNDS):
        node = graph[node]

    return node


def latency_score(latency):

    score = latency / 1000000

    if score < 1:
        score = 1

    return score


def load_chain():

    with chain_lock:

        if not os.path.exists(CHAIN_FILE):

            genesis = {
                "height":0,
                "previous_hash":"0",
                "timestamp":time.time(),
                "transactions":[],
                "hash":"genesis"
            }

            with open(CHAIN_FILE,"w") as f:
                json.dump([genesis],f)

        try:
            with open(CHAIN_FILE) as f:
                return json.load(f)
        except:
            return []


def save_chain(chain):

    with chain_lock:

        with open(CHAIN_FILE,"w") as f:
            json.dump(chain,f)


def load_mempool():

    if not os.path.exists("mempool.json"):
        return []

    try:

        with open("mempool.json") as f:
            tx = json.load(f)

        os.remove("mempool.json")

        return [tx]

    except:

        return []


def broadcast(block):

    for peer in PEERS:

        try:

            s = socket.socket()
            s.connect((peer,PORT))
            s.send(json.dumps(block).encode())
            s.close()

        except:
            pass


def server():

    s = socket.socket()
    s.bind(("0.0.0.0",PORT))
    s.listen()

    while True:

        conn,addr = s.accept()

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

    miner_address = input("Miner address: ")

    while True:

        chain = load_chain()

        last_block = chain[-1]

        seed = random.randint(0,2**32)

        latency = memory_graph(seed)

        score = latency_score(latency)

        data = str(seed + latency + len(chain)).encode()

        h = hashlib.sha256(data).hexdigest()

        threshold = BASE_DIFFICULTY * math.sqrt(score)

        if int(h,16) < threshold:

            mempool_txs = load_mempool()

            reward_tx = {
                "from":"network",
                "to":miner_address,
                "amount":BLOCK_REWARD,
                "timestamp":time.time()
            }

            txs = [reward_tx] + mempool_txs

            block = {
                "height":len(chain),
                "previous_hash":last_block["hash"],
                "timestamp":time.time(),
                "seed":seed,
                "latency":latency,
                "score":score,
                "transactions":txs,
                "hash":h
            }

            chain.append(block)

            save_chain(chain)

            print("BLOCK MINED", block["height"], "| score:", round(score,2))

            broadcast(block)


threading.Thread(target=server,daemon=True).start()

mine()
