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

CHAIN_FILE = "polm_chain.json"

TARGET_BLOCK_TIME = 30
difficulty = 2**250

print("===== PoLM Node v2 =====")
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


def adjust_difficulty(chain):

    global difficulty

    if len(chain) < 3:
        return

    last = chain[-1]
    prev = chain[-2]

    block_time = last["timestamp"] - prev["timestamp"]

    if block_time < TARGET_BLOCK_TIME:

        difficulty = difficulty - difficulty//20

    else:

        difficulty = difficulty + difficulty//20


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

                adjust_difficulty(chain)

                print("BLOCK RECEIVED", block["height"])

        except:
            pass

        conn.close()


def mine():

    global difficulty

    miner_address = input("Miner address: ")

    while True:

        chain = load_chain()

        last_block = chain[-1]

        seed = random.randint(0,2**32)

        latency = memory_graph(seed)

        data = str(seed + latency + len(chain)).encode()

        h = hashlib.sha256(data).hexdigest()

        if int(h,16) < difficulty:

            mempool_txs = load_mempool()

            reward_tx = {
                "from":"network",
                "to":miner_address,
                "amount":50,
                "timestamp":time.time()
            }

            txs = [reward_tx] + mempool_txs

            block = {
                "height":len(chain),
                "previous_hash":last_block["hash"],
                "timestamp":time.time(),
                "seed":seed,
                "latency":latency,
                "transactions":txs,
                "hash":h
            }

            chain.append(block)

            save_chain(chain)

            adjust_difficulty(chain)

            print("BLOCK MINED", block["height"], "| reward ->", miner_address)

            broadcast(block)


threading.Thread(target=server,daemon=True).start()

mine()
