#!/usr/bin/env python3

import time
import random
import hashlib
import platform
import os

BUFFER_SIZE = 256 * 1024 * 1024
ROUNDS = 50000
BLOCK_TARGET = 2**250

memory = bytearray(BUFFER_SIZE)

print("===== PoLM Miner v0.8 (Memory Storm) =====")
print("CPU:", platform.processor())
print("Cores:", os.cpu_count())

def memory_storm(seed):

    index = seed % BUFFER_SIZE
    total = 0

    start = time.perf_counter_ns()

    for _ in range(ROUNDS):

        for i in range(64):

            index = (index * 11400714819323198485 + i) % BUFFER_SIZE
            total ^= memory[index]

    end = time.perf_counter_ns()

    return total ^ (end - start)


blocks = 0
start_time = time.time()

while True:

    seed = random.randint(0,2**32)

    result = memory_storm(seed)

    data = str(seed + result).encode()

    h = hashlib.sha256(data).hexdigest()

    if int(h,16) < BLOCK_TARGET:

        blocks += 1
        print("BLOCK FOUND", blocks)

    if time.time() - start_time > 60:

        print("Blocks in 60s:", blocks)
        break
