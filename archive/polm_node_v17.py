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

# ---------------- CHAIN ----------------

def load_chain():

    if not os.path.exists(CHAIN_FILE):

        genesis={
            "hash":"genesis",
            "parents":[],
            "transactions":[]
        }

        with open(CHAIN_FILE,"w") as f:
            json.dump([genesis],f)

    with open(CHAIN_FILE) as f:
        return json.load(f)


def save_chain(chain):

    with open(CHAIN_FILE,"w") as f:
        json.dump(chain,f)

# ---------------- NETWORK ----------------

def broadcast(block):

    for peer in PEERS:

        try:

            s=socket.socket()

            s.connect((peer,PORT))

            s.send(json.dumps(block).encode())

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

                if block["hash"]!=chain[-1]["hash"]:

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

        h=hashlib.sha256(str(seed).encode()).hexdigest()

        if int(h,16)<2**250:

            with lock:

                chain=load_chain()

                block={

                    "hash":h,
                    "parents":[chain[-1]["hash"]],
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
