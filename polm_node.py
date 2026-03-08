#!/usr/bin/env python3

import socket
import threading
import time
import random
import hashlib
import json

PORT = 5000

PEERS = [
"192.168.0.100",
"192.168.0.103",
"192.168.0.102"
]

BLOCKCHAIN = []

BUFFER_SIZE = 128 * 1024 * 1024
ROUNDS = 200000
BLOCK_TARGET = 2**250

memory = bytearray(BUFFER_SIZE)

def pointer_chase(seed):

    index = seed % BUFFER_SIZE

    for _ in range(ROUNDS):

        value = memory[index]
        index = (index ^ (value * 11400714819323198485)) % BUFFER_SIZE

    return index


def mine():

    while True:

        seed = random.randint(0,2**32)

        latency = pointer_chase(seed)

        data = str(seed + latency).encode()

        h = hashlib.sha256(data).hexdigest()

        if int(h,16) < BLOCK_TARGET:

            block = {
                "seed": seed,
                "latency": latency,
                "hash": h,
                "time": time.time()
            }

            add_block(block)
            broadcast(block)


def add_block(block):

    BLOCKCHAIN.append(block)

    print("NEW BLOCK", len(BLOCKCHAIN))


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

        data = conn.recv(4096)

        block = json.loads(data.decode())

        add_block(block)

        conn.close()


threading.Thread(target=server).start()

mine()
