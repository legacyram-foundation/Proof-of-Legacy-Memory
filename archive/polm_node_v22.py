#!/usr/bin/env python3

import time
import random
import hashlib
import json
import os
import socket
import threading

PORT=5001

PEERS=[
"192.168.0.102",
"192.168.0.103",
"192.168.0.100"
]

CHAIN_FILE="polm_chain.json"

BLOCK_REWARD=10

lock=threading.Lock()

# ---------------- HASH ----------------

def sha(data):
    return hashlib.sha256(data.encode()).hexdigest()

# ---------------- CHAIN ----------------

def atomic_write(chain):

    tmp="polm_chain.tmp"

    with open(tmp,"w") as f:
        json.dump(chain,f)

    os.replace(tmp,CHAIN_FILE)

def load_chain():

    if not os.path.exists(CHAIN_FILE):

        genesis={
            "hash":"genesis",
            "parents":[],
            "transactions":[]
        }

        atomic_write([genesis])

    with open(CHAIN_FILE) as f:
        return json.load(f)

def save_chain(chain):

    atomic_write(chain)

# ---------------- BLOCK HELPERS ----------------

def get_last_hashes(chain,n=2):

    hashes=[]

    for b in reversed(chain):

        if len(hashes)>=n:
            break

        hashes.append(b["hash"])

    return hashes

def block_exists(chain,h):

    for b in chain:
        if b["hash"]==h:
            return True

    return False

# ---------------- VALIDATION ----------------

def validate_block(chain,block):

    if block_exists(chain,block["hash"]):
        return False

    for p in block["parents"]:

        found=False

        for b in chain:
            if b["hash"]==p:
                found=True
                break

        if not found:
            return False

    return True

# ---------------- NETWORK ----------------

def broadcast(block):

    msg=json.dumps(block).encode()

    for peer in PEERS:

        try:

            s=socket.socket()

            s.settimeout(2)

            s.connect((peer,PORT))

            s.send(msg)

            s.close()

        except:
            pass

# ---------------- SERVER ----------------

def server():

    s=socket.socket()

    s.bind(("0.0.0.0",PORT))

    s.listen()

    while True:

        conn,addr=s.accept()

        try:

            data=conn.recv(4096)

            block=json.loads(data.decode())

            with lock:

                chain=load_chain()

                if validate_block(chain,block):

                    chain.append(block)

                    save_chain(chain)

                    print("BLOCK RECEIVED",block["hash"][:10])

        except:
            pass

        conn.close()

# ---------------- BALANCE ----------------

def compute_balance(addr):

    chain=load_chain()

    bal=0

    for block in chain:

        if block.get("miner")==addr:

            bal+=block.get("reward",0)

    return bal

# ---------------- MINING ----------------

def mine(addr):

    while True:

        seed=random.randint(0,2**32)

        h=sha(str(seed))

        if int(h,16)<2**250:

            with lock:

                chain=load_chain()

                parents=get_last_hashes(chain,2)

                block={

                    "hash":h,
                    "parents":parents,
                    "miner":addr,
                    "reward":BLOCK_REWARD,
                    "timestamp":time.time()

                }

                chain.append(block)

                save_chain(chain)

            print("BLOCK MINED",h[:10])

            broadcast(block)

# ---------------- CLI ----------------

def menu():

    print()
    print("1 start mining")
    print("2 balance")
    print()

    c=input("> ")

    if c=="1":

        addr=input("miner address: ")

        mine(addr)

    if c=="2":

        addr=input("address: ")

        print("balance:",compute_balance(addr))

# ---------------- START ----------------

threading.Thread(target=server,daemon=True).start()

while True:
    menu()
