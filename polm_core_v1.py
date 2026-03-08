#!/usr/bin/env python3

import time
import random
import hashlib
import json
import os
import platform

BUFFER_SIZE = 128 * 1024 * 1024
NODES = BUFFER_SIZE // 8
ROUNDS = 200000

BLOCK_TARGET = 2**250

CHAIN_FILE = "polm_chain.json"

print("===== PoLM Core v1 =====")
print("CPU:", platform.processor())
print("Cores:", os.cpu_count())

# criar grafo na memória
graph = [random.randint(0, NODES-1) for _ in range(NODES)]


def memory_graph(seed):

    node = seed % NODES

    start = time.perf_counter_ns()

    for _ in range(ROUNDS):

        node = graph[node]

    end = time.perf_counter_ns()

    return end - start


def load_chain():

    if not os.path.exists(CHAIN_FILE):

        genesis = {
            "height":0,
            "previous_hash":"0",
            "timestamp":time.time(),
            "hash":"genesis"
        }

        with open(CHAIN_FILE,"w") as f:
            json.dump([genesis],f,indent=2)

    with open(CHAIN_FILE) as f:
        return json.load(f)


def save_chain(chain):

    with open(CHAIN_FILE,"w") as f:
        json.dump(chain,f,indent=2)


def mine():

    chain = load_chain()

    while True:

        last_block = chain[-1]

        seed = random.randint(0,2**32)

        latency = memory_graph(seed)

        data = str(seed + latency + len(chain)).encode()

        h = hashlib.sha256(data).hexdigest()

        if int(h,16) < BLOCK_TARGET:

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

            print("BLOCK MINED:", block["height"])


mine()
