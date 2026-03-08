#!/usr/bin/env python3

import time
import random
import platform
import os
import hashlib

BUFFER_SIZE = 256 * 1024 * 1024
ROUNDS = 200000
BLOCK_TARGET = 2**250

memory = bytearray(BUFFER_SIZE)

print("===== PoLM Miner v0.2 =====")

print("CPU:", platform.processor())
print("Cores:", os.cpu_count())


def memory_workload(seed):

    index = seed % BUFFER_SIZE

    start = time.perf_counter_ns()

    for _ in range(ROUNDS):

        value = memory[index]

        index = (index ^ (value * 2654435761)) % BUFFER_SIZE

    end = time.perf_counter_ns()

    return end - start


blocks = 0
start_time = time.time()

while True:

    seed = random.randint(0,2**32)

    latency = memory_workload(seed)

    data = str(seed + latency).encode()

    h = hashlib.sha256(data).hexdigest()

    if int(h,16) < BLOCK_TARGET:

        blocks += 1
        print("BLOCK FOUND", blocks)

    if time.time() - start_time > 60:

        print("Blocks in 60s:", blocks)
        break
