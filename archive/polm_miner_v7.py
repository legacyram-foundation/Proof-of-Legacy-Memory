#!/usr/bin/env python3

import time
import random
import hashlib
import platform
import os

BUFFER_SIZE = 256 * 1024 * 1024
NODES = BUFFER_SIZE // 8

ROUNDS = 200000
BLOCK_TARGET = 2**250

print("===== PoLM Miner v0.7 (Multi Pointer Walk) =====")
print("CPU:", platform.processor())
print("Cores:", os.cpu_count())

# criar grafo na memória
graph = [random.randint(0, NODES-1) for _ in range(NODES)]

def multi_walk(seed):

    node = seed % NODES

    start = time.perf_counter_ns()

    for _ in range(ROUNDS):

        # múltiplos acessos dependentes
        node = graph[node]
        node = graph[node]
        node = graph[node]
        node = graph[node]

    end = time.perf_counter_ns()

    return end - start


blocks = 0
start_time = time.time()

while True:

    seed = random.randint(0, 2**32)

    latency = multi_walk(seed)

    data = str(seed + latency).encode()

    h = hashlib.sha256(data).hexdigest()

    if int(h,16) < BLOCK_TARGET:

        blocks += 1
        print("BLOCK FOUND", blocks)

    if time.time() - start_time > 60:

        print("Blocks in 60s:", blocks)
        break
