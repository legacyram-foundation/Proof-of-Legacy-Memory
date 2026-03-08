#!/usr/bin/env python3

import time
import random
import hashlib
import json
import os
import socket
import threading
from ecdsa import VerifyingKey, SECP256k1, BadSignatureError

PORT = 5001

CHAIN_FILE = "polm_chain.json"
MEMPOOL_FILE = "mempool.json"
PEERS_FILE = "peers.json"

DIFFICULTY_START = 5
BLOCK_TIME_TARGET = 10
TX_FEE = 0.01

RAM_BUFFER_MB = 64

lock = threading.Lock()

print("Allocating RAM buffer")
ram_buffer = bytearray(os.urandom(RAM_BUFFER_MB * 1024 * 1024))
print("RAM ready")

# ---------------- HASH160 ----------------
def hash160(data):
    sha = hashlib.sha256(data).digest()
    rip = hashlib.new("ripemd160", sha).digest()
    return rip.hex()

# ---------------- MEMORY HASH ----------------
def memory_hash(seed):

    h = hashlib.sha256(str(seed).encode()).digest()

    for _ in range(64):
        idx = int.from_bytes(h[:4],"big") % len(ram_buffer)
        val = ram_buffer[idx]
        h = hashlib.sha256(h + bytes([val])).digest()

    return h.hex()

# ---------------- JSON UTILS ----------------
def load_json(file, default):

    if not os.path.exists(file):
        with open(file,"w") as f:
            json.dump(default,f)

    with open(file) as f:
        return json.load(f)

def save_json(file,data):

    with open(file,"w") as f:
        json.dump(data,f)

# ---------------- CHAIN ----------------
def load_chain():

    chain = load_json(CHAIN_FILE, [])

    if not chain:

        genesis = {
            "height":0,
            "hash":"genesis",
            "parent":"genesis",
            "timestamp":time.time(),
            "difficulty":DIFFICULTY_START,
            "transactions":[]
        }

        save_json(CHAIN_FILE,[genesis])

        return [genesis]

    return chain

def save_chain(chain):
    save_json(CHAIN_FILE, chain)

# ---------------- MEMPOOL ----------------
def load_mempool():
    return load_json(MEMPOOL_FILE, [])

def save_mempool(m):
    save_json(MEMPOOL_FILE, m)

# ---------------- BALANCE ----------------
def balance(addr):

    chain = load_chain()

    bal = 0

    for b in chain:

        if b.get("miner") == addr:
            bal += b.get("reward",0)

        for tx in b.get("transactions",[]):

            if tx["to"] == addr:
                bal += tx["amount"]

            if tx["from"] == addr:
                bal -= tx["amount"] + tx["fee"]

    return bal

# ---------------- VERIFY TX ----------------
def verify_tx(tx):

    try:

        signature = bytes.fromhex(tx["signature"])
        public_key = bytes.fromhex(tx["public_key"])

        addr = hash160(public_key)

        if addr != tx["from"]:
            print("address mismatch")
            return False

        vk = VerifyingKey.from_string(public_key, curve=SECP256k1)

        tx_copy = dict(tx)
        del tx_copy["signature"]

        message = json.dumps(tx_copy, sort_keys=True).encode()

        vk.verify(signature, message)

        return True

    except BadSignatureError:
        print("bad signature")
        return False

    except:
        return False

# ---------------- ADD TX ----------------
def add_tx(tx):

    if not verify_tx(tx):
        print("TX rejected")
        return

    mempool = load_mempool()

    mempool.append(tx)

    save_mempool(mempool)

    print("TX added")

# ---------------- DIFFICULTY ----------------
def get_difficulty(chain):

    if len(chain) < 20:
        return DIFFICULTY_START

    last = chain[-1]
    prev = chain[-20]

    span = last["timestamp"] - prev["timestamp"]
    avg = span / 20

    diff = last["difficulty"]

    if avg < BLOCK_TIME_TARGET:
        diff += 1

    if avg > BLOCK_TIME_TARGET*2 and diff > 1:
        diff -= 1

    return diff

# ---------------- NETWORK ----------------
def send(peer,msg):

    try:
        s = socket.socket()
        s.connect((peer,PORT))
        s.send(json.dumps(msg).encode())
        s.close()
    except:
        pass

def broadcast(msg):

    peers = load_json(PEERS_FILE, [])

    for p in peers:
        send(p,msg)

# ---------------- SERVER ----------------
def server():

    s = socket.socket()

    s.bind(("0.0.0.0",PORT))
    s.listen()

    while True:

        conn,addr = s.accept()

        try:

            msg = json.loads(conn.recv(65536).decode())

            if msg["type"] == "tx":
                add_tx(msg["data"])

            if msg["type"] == "block":

                block = msg["data"]

                chain = load_chain()

                if block["parent"] == chain[-1]["hash"]:

                    chain.append(block)
                    save_chain(chain)

                    print("BLOCK RECEIVED",block["hash"][:10])

        except:
            pass

        conn.close()

# ---------------- MINING ----------------
def mine(addr):

    while True:

        chain = load_chain()

        parent = chain[-1]["hash"]

        height = len(chain)

        diff = get_difficulty(chain)

        seed = random.randint(0,2**64)

        mempool = load_mempool()

        h = memory_hash(seed)

        if h.startswith("0"*diff):

            reward = 10 + sum(tx["fee"] for tx in mempool)

            block = {
                "height":height,
                "parent":parent,
                "hash":h,
                "seed":seed,
                "difficulty":diff,
                "timestamp":time.time(),
                "miner":addr,
                "reward":reward,
                "transactions":mempool
            }

            save_mempool([])

            chain.append(block)

            save_chain(chain)

            print("BLOCK MINED",h[:10])

            broadcast({"type":"block","data":block})

# ---------------- CLI ----------------
def menu():

    print()
    print("1 start mining")
    print("2 balance")
    print()

    c = input("> ")

    if c == "1":

        addr = input("miner address: ")

        mine(addr)

    if c == "2":

        addr = input("address: ")

        print(balance(addr))

# ---------------- START ----------------
threading.Thread(target=server, daemon=True).start()

while True:
    menu()
