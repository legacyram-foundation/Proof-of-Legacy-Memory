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

# memória total usada pelo miner
MEMORY_SIZE = 512 * 1024 * 1024
BUFFER = bytearray(MEMORY_SIZE)

BASE_DIFFICULTY = 2**250
BLOCK_REWARD = 50

MAX_THREADS = 2

GRAPH_SIZE = 2000000

chain_lock = threading.Lock()

print("===== PoLM Node v8 (Memory Graph Mining) =====")
print("CPU:", platform.processor())
print("Cores:", os.cpu_count())
print("Thread cap:", MAX_THREADS)
print("Memory buffer:", MEMORY_SIZE // (1024*1024), "MB")


def generate_graph(seed):

    random.seed(seed)

    graph = []

    for _ in range(GRAPH_SIZE):

        node = random.randint(0, MEMORY_SIZE-1)

        graph.append(node)

    return graph


def memory_graph_walk(graph):

    total = 0

    start = time.perf_counter()

    for node in graph:

        value = BUFFER[node]

        total ^= value

    end = time.perf_counter()

    latency = end - start

    return total, latency


def latency_score(latency):

    score = latency * 100

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


def miner_thread(miner_address):

    while True:

        chain = load_chain()

        last_block = chain[-1]

        seed = random.randint(0,2**32)

        graph = generate_graph(seed)

        work, latency = memory_graph_walk(graph)

        score = latency_score(latency)

        data = str(seed + work + len(chain)).encode()

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

            print("BLOCK MINED", block["height"], "| latency:", round(latency,4), "| score:", round(score,2))

            broadcast(block)


def start_mining(miner_address):

    threads = []

    for _ in range(MAX_THREADS):

        t = threading.Thread(target=miner_thread,args=(miner_address,))
        t.daemon = True
        t.start()

        threads.append(t)

    while True:
        time.sleep(1)


threading.Thread(target=server,daemon=True).start()

miner_address = input("Miner address: ")

start_mining(miner_address)
