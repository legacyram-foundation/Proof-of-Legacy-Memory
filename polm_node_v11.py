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
import subprocess

PORT = 5001

PEERS = [
"192.168.0.100",
"192.168.0.103",
"192.168.0.102"
]

CHAIN_FILE = "polm_chain.json"

MEMORY_SIZE = 512 * 1024 * 1024
BUFFER = bytearray(MEMORY_SIZE)

BLOCK_REWARD = 50
TARGET_BLOCK_TIME = 10

MAX_THREADS = 2
GRAPH_SIZE = 2000000

chain_lock = threading.Lock()
mine_lock = threading.Lock()

BASE_DIFFICULTY = 2**248


# ---------------- RAM DETECTION ----------------

def detect_ram():

    try:

        out = subprocess.check_output(
            "sudo dmidecode -t memory | grep 'Type:'",
            shell=True
        ).decode()

        if "DDR2" in out:
            return "DDR2", 2.5

        if "DDR3" in out:
            return "DDR3", 1.8

        if "DDR4" in out:
            return "DDR4", 1.0

        if "DDR5" in out:
            return "DDR5", 0.7

    except:
        pass

    return "UNKNOWN", 1.0


RAM_TYPE, RAM_MULT = detect_ram()

print("===== PoLM Node v11 (Stable Protocol) =====")
print("CPU:", platform.processor())
print("Cores:", os.cpu_count())
print("Thread cap:", MAX_THREADS)
print("Memory buffer:", MEMORY_SIZE // (1024*1024), "MB")
print("RAM detected:", RAM_TYPE)
print("RAM multiplier:", RAM_MULT)


# ---------------- MEMORY GRAPH ----------------

def generate_graph(seed, prev_hash):

    try:
        mix = seed + int(prev_hash[:16],16)
    except:
        mix = seed

    random.seed(mix)

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

    latency = time.perf_counter() - start

    return total, latency


def latency_score(latency):

    score = latency * 100 * RAM_MULT

    if score < 1:
        score = 1

    if score > 120:
        score = 120

    return score


# ---------------- DIFFICULTY ----------------

def calculate_difficulty(chain):

    if len(chain) < 5:
        return BASE_DIFFICULTY

    last = chain[-1]
    prev = chain[-5]

    time_diff = last["timestamp"] - prev["timestamp"]

    avg_time = time_diff / 5

    difficulty = BASE_DIFFICULTY

    if avg_time < TARGET_BLOCK_TIME:

        difficulty = difficulty * 1.2

    else:

        difficulty = difficulty * 0.8

    return difficulty


# ---------------- BLOCKCHAIN ----------------

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


# ---------------- NETWORK ----------------

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


# ---------------- MINER ----------------

def miner_thread(miner_address):

    while True:

        chain = load_chain()

        last_block = chain[-1]

        seed = random.randint(0,2**32)

        graph = generate_graph(seed, last_block["hash"])

        work, latency = memory_graph_walk(graph)

        score = latency_score(latency)

        data = str(seed + work + len(chain)).encode()

        h = hashlib.sha256(data).hexdigest()

        difficulty = calculate_difficulty(chain)

        threshold = difficulty * math.sqrt(score)

        if int(h,16) < threshold:

            with mine_lock:

                chain = load_chain()

                if len(chain) != last_block["height"] + 1:
                    continue

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
                    "ram_type":RAM_TYPE,
                    "transactions":txs,
                    "hash":h
                }

                chain.append(block)

                save_chain(chain)

                print(
                    "BLOCK MINED",
                    block["height"],
                    "| latency:", round(latency,3),
                    "| score:", round(score,2),
                    "| RAM:", RAM_TYPE
                )

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
