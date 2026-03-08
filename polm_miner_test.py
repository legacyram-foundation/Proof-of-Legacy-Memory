#!/usr/bin/env python3

import time
import random
import hashlib
import platform
import os

ROUNDS = 2000000
BLOCK_TARGET = 2**250

print("===== PoLM Miner Test =====")

print("CPU:", platform.processor())
print("Cores:", os.cpu_count())

def mine():

    nonce = random.randint(0,100000000)

    start = time.time()

    for _ in range(ROUNDS):

        data = str(nonce).encode()

        h = hashlib.sha256(data).hexdigest()

        if int(h,16) < BLOCK_TARGET:

            return True

        nonce += 1

    return False


blocks = 0
start_time = time.time()

while True:

    found = mine()

    if found:

        blocks += 1

        print("BLOCK FOUND", blocks)

    if time.time() - start_time > 60:

        print("Blocks in 60s:", blocks)

        break
