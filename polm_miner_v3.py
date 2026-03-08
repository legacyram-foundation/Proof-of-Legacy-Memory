#!/usr/bin/env python3

import time
import random
import hashlib
import platform
import os
import psutil

# detectar RAM
ram = psutil.virtual_memory().total / (1024**3)

# ajustar buffer automaticamente
if ram < 6:
    BUFFER_SIZE = 128 * 1024 * 1024
elif ram < 16:
    BUFFER_SIZE = 256 * 1024 * 1024
else:
    BUFFER_SIZE = 512 * 1024 * 1024

ROUNDS = 300000
BLOCK_TARGET = 2**250

memory = bytearray(BUFFER_SIZE)

print("===== PoLM Miner v0.3 =====")
print("CPU:", platform.processor())
print("Cores:", os.cpu_count())
print("RAM:", int(ram), "GB")
print("Buffer:", BUFFER_SIZE // (1024*1024), "MB")


def pointer_chase(seed):

    index = seed % BUFFER_SIZE

    start = time.perf_counter_ns()

    for _ in range(ROUNDS):

        value = memory[index]

        # stride pseudo-aleatório dependente
        index = (index ^ (value * 11400714819323198485)) % BUFFER_SIZE

    end = time.perf_counter_ns()

    return end - start


blocks = 0
start_time = time.time()

while True:

    seed = random.randint(0,2**32)

    latency = pointer_chase(seed)

    data = str(seed + latency).encode()

    h = hashlib.sha256(data).hexdigest()

    if int(h,16) < BLOCK_TARGET:

        blocks += 1
        print("BLOCK FOUND", blocks)

    if time.time() - start_time > 60:

        print("Blocks in 60s:", blocks)
        break
