#!/usr/bin/env python3

import time
import random
import hashlib
import statistics
import platform
import os

BUFFER_SIZE = 128 * 1024 * 1024
ROUNDS = 20000
BLOCK_TARGET = 2**250

memory = bytearray(BUFFER_SIZE)

print("===== PoLM Miner v0.4 (Memory Chaos) =====")
print("CPU:", platform.processor())
print("Cores:", os.cpu_count())

def chaos_test(seed):

    index = seed % BUFFER_SIZE
    latencies = []

    for _ in range(ROUNDS):

        start = time.perf_counter_ns()

        value = memory[index]

        end = time.perf_counter_ns()

        latencies.append(end-start)

        index = (index ^ (value * 11400714819323198485)) % BUFFER_SIZE

    variance = statistics.pvariance(latencies)

    return variance


blocks = 0
start_time = time.time()

while True:

    seed = random.randint(0,2**32)

    chaos = chaos_test(seed)

    data = str(seed + chaos).encode()

    h = hashlib.sha256(data).hexdigest()

    if int(h,16) < BLOCK_TARGET:

        blocks += 1
        print("BLOCK FOUND", blocks)

    if time.time() - start_time > 60:

        print("Blocks in 60s:", blocks)
        break
