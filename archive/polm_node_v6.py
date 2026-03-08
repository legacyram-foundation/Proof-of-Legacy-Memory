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

BASE_DIFFICULTY = 2**250
BLOCK_REWARD = 50

chain_lock = threading.Lock()


def detect_ram():

    try:

        output = subprocess.check_output(
            "sudo dmidecode -t memory",
            shell=True
        ).decode()

        if "DDR5" in output:
            return "DDR5"

        if "DDR4" in output:
            return "DDR4"

        if "DDR3" in output:
            return "DDR3"

        if "DDR2" in output:
            return "DDR2"

    except:

        pass

    return "UNKNOWN"


def ram_multiplier(ram):

    if ram == "DDR2":
        return 2.0

    if ram == "DDR3":
        return 1.5

    if ram == "DDR4":
        return 1.0

    if ram == "DDR5":
        return 0.8

    return 1.0


RAM_TYPE = detect_ram()
RAM_MULT = ram_multiplier(RAM_TYPE)

print("===== PoLM Node v6 =====")
print("CPU:", platform.processor())
print("Cores:", os.cpu_count())
print("RAM detected:", RAM_TYPE)
print("Legacy multiplier:", RAM_MULT)
print("Memory buffer:", MEMORY_SIZE // (1024*1024), "MB")


def memory_pressure(seed):

    random.seed(seed)

    index = random.randint(0, MEMORY_SIZE-1)

    total = 0

    for _ in range(500000):

        index = (index * 1103515245 + 12345) % MEMORY_SIZE

        value = BUFFER[index]

        total ^= value

    return total


def latency_score(work):

    score = (work % 100 + 1) * RAM_MULT

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

        work = memory_pressure(seed)

        score = latency_score(work)

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
                "work":work,
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
